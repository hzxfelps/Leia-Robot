import argparse
import time

import requests


def montar_url(base_url, rota):
    return base_url.rstrip("/") + rota


def obter_json(session, base_url, rota, timeout=3):
    response = session.get(montar_url(base_url, rota), timeout=timeout)
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(
        description="Simulador simples do Pepper para testar o servidor Flask."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="IP ou hostname do notebook que roda o Flask.",
    )
    parser.add_argument(
        "--port",
        default=5000,
        type=int,
        help="Porta do servidor Flask.",
    )
    parser.add_argument(
        "--intervalo",
        default=2.0,
        type=float,
        help="Intervalo entre leituras do servidor, em segundos.",
    )
    parser.add_argument(
        "--simular-atendimento",
        action="store_true",
        help="Chama /atendimento_start e /atendimento_end ao receber um grupo.",
    )
    parser.add_argument(
        "--duracao-atendimento",
        default=5.0,
        type=float,
        help="Tempo de atendimento simulado, em segundos.",
    )
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    session = requests.Session()

    estado_anterior = None
    grupo_anterior = None
    conteudo_anterior = None

    print(f"Simulador Pepper conectado a {base_url}")
    print("Pressione Ctrl+C para encerrar.")

    while True:
        try:
            estado = obter_json(session, base_url, "/estado").get("ouvindo", False)
            sistema = obter_json(session, base_url, "/estado_sistema")
            conteudo = obter_json(session, base_url, "/conteudo").get("conteudo", "inicio")

            if estado != estado_anterior:
                if estado:
                    print("Pepper: escuta ativada.")
                else:
                    print("Pepper: escuta desativada.")
                estado_anterior = estado

            if conteudo != conteudo_anterior:
                print(f"Tablet: exibindo conteudo '{conteudo}'.")
                conteudo_anterior = conteudo

            prox = obter_json(session, base_url, "/next")
            grupo = prox.get("grupo")

            if grupo is not None and grupo != grupo_anterior:
                fila = len(sistema.get("fila", []))
                urgente = sistema.get("urgente")
                print(f"Pepper: indo atender grupo {grupo}. Fila restante: {fila}. Urgente atual: {urgente}.")
                grupo_anterior = grupo

                if args.simular_atendimento:
                    session.get(
                        montar_url(base_url, f"/atendimento_start?grupo={grupo}"),
                        timeout=3,
                    ).raise_for_status()
                    print(f"Pepper: atendimento do grupo {grupo} iniciado.")
                    time.sleep(args.duracao_atendimento)
                    session.get(
                        montar_url(base_url, f"/atendimento_end?grupo={grupo}"),
                        timeout=3,
                    ).raise_for_status()
                    print(f"Pepper: atendimento do grupo {grupo} finalizado.")

            time.sleep(args.intervalo)

        except KeyboardInterrupt:
            print("\nSimulador encerrado.")
            break
        except requests.RequestException as exc:
            print(f"Erro de conexao com o servidor: {exc}")
            time.sleep(args.intervalo)
        except Exception as exc:
            print(f"Erro inesperado: {exc}")
            time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
