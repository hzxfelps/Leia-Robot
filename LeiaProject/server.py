from flask import Flask, request, jsonify, render_template
import time

app = Flask(__name__)

estado_escuta = False
historico_atendimentos = []


estado_sistema = {
    "modo": "idle",  # idle | indo | atendendo | ouvindo
    "grupo_atual": None,
    "fila": [],
    "urgente": None,
    "conteudo": "inicio",
}


def gerar_resumo_dashboard():
    total = len(historico_atendimentos)
    em_andamento = sum(1 for item in historico_atendimentos if item["fim"] is None)
    finalizados = total - em_andamento
    tempo_total = 0
    atendimentos_com_fim = 0

    for item in historico_atendimentos:
        if item["fim"] is not None:
            tempo_total += item["fim"] - item["inicio"]
            atendimentos_com_fim += 1

    media = tempo_total / atendimentos_com_fim if atendimentos_com_fim else 0

    return {
        "total_atendimentos": total,
        "em_andamento": em_andamento,
        "finalizados": finalizados,
        "fila_atual": len(estado_sistema["fila"]),
        "grupo_atual": estado_sistema["grupo_atual"],
        "modo": estado_sistema["modo"],
        "ouvindo": estado_escuta,
        "urgente": estado_sistema["urgente"],
        "conteudo": estado_sistema["conteudo"],
        "tempo_medio_segundos": round(media, 1),
    }


# ------------------------
# PAGINAS
# ------------------------


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/laser")
def laser():
    return render_template("laser.html")


@app.route("/biologia")
def biologia():
    return render_template("biologia.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ------------------------
# ESP32 ENVIA DADOS
# ------------------------


@app.route("/update")
def update():
    grupo = int(request.args.get("grupo"))
    nivel = int(request.args.get("nivel"))
    urgente = request.args.get("urgente") == "1"

    if urgente:
        estado_sistema["urgente"] = grupo
    else:
        estado_sistema["fila"].append(
            {
                "grupo": grupo,
                "nivel": nivel,
                "tempo": time.time(),
            }
        )

    return jsonify(
        {
            "ok": True,
            "grupo": grupo,
            "nivel": nivel,
            "urgente": urgente,
            "fila_tamanho": len(estado_sistema["fila"]),
        }
    )


# ------------------------
# CONTROLE DE ESCUTA
# ------------------------


@app.route("/estado")
def estado():
    global estado_escuta

    ouvir = request.args.get("ouvindo")

    if ouvir is not None:
        estado_escuta = ouvir == "1"
        if estado_sistema["modo"] in ("idle", "ouvindo"):
            estado_sistema["modo"] = "ouvindo" if estado_escuta else "idle"

    return jsonify({"ouvindo": estado_escuta})


# ------------------------
# PEPPER PEGA PROXIMO GRUPO
# ------------------------


@app.route("/next")
def next_group():
    if estado_sistema["urgente"] is not None:
        grupo = estado_sistema["urgente"]
        estado_sistema["urgente"] = None
        estado_sistema["grupo_atual"] = grupo
        estado_sistema["modo"] = "indo"
        return jsonify({"grupo": grupo})

    if estado_sistema["fila"]:
        proximo = min(estado_sistema["fila"], key=lambda x: (x["nivel"], x["tempo"]))
        estado_sistema["fila"].remove(proximo)
        estado_sistema["grupo_atual"] = proximo["grupo"]
        estado_sistema["modo"] = "indo"
        return jsonify({"grupo": proximo["grupo"]})

    return jsonify({"grupo": None})


# ------------------------
# CONTEUDO ATUAL
# ------------------------


@app.route("/conteudo")
def conteudo():
    return jsonify({"conteudo": estado_sistema["conteudo"]})


@app.route("/conteudo_set")
def conteudo_set():
    conteudo_atual = request.args.get("conteudo", "inicio").strip() or "inicio"
    estado_sistema["conteudo"] = conteudo_atual
    return jsonify({"ok": True, "conteudo": estado_sistema["conteudo"]})


# ------------------------
# ESTADO E DASHBOARD
# ------------------------


@app.route("/estado_sistema")
def estado_sistema_api():
    return jsonify(estado_sistema)


@app.route("/resumo")
def resumo():
    return jsonify(gerar_resumo_dashboard())


# ------------------------
# HISTORICO DE ATENDIMENTO
# ------------------------


@app.route("/atendimento_start")
def atendimento_start():
    grupo = int(request.args.get("grupo"))

    registro = {
        "grupo": grupo,
        "inicio": time.time(),
        "fim": None,
        "conteudo": estado_sistema["conteudo"],
    }

    estado_sistema["grupo_atual"] = grupo
    estado_sistema["modo"] = "atendendo"
    historico_atendimentos.append(registro)

    return jsonify({"ok": True})


@app.route("/atendimento_end")
def atendimento_end():
    grupo = int(request.args.get("grupo"))

    for item in reversed(historico_atendimentos):
        if item["grupo"] == grupo and item["fim"] is None:
            item["fim"] = time.time()
            item["conteudo"] = estado_sistema["conteudo"]
            break

    estado_sistema["grupo_atual"] = None
    estado_sistema["modo"] = "ouvindo" if estado_escuta else "idle"

    return jsonify({"ok": True})


@app.route("/historico")
def historico():
    return jsonify(historico_atendimentos)


app.run(host="0.0.0.0", port=5000)
