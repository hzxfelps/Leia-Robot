function formatModo(modo) {
    const labels = {
        idle: "Aguardando",
        ouvindo: "Ouvindo",
        indo: "Em deslocamento",
        atendendo: "Atendendo",
    };
    return labels[modo] || modo || "--";
}

function renderFila(fila) {
    const container = document.getElementById("fila-lista");

    if (!fila.length) {
        container.className = "queue-list empty-state";
        container.textContent = "Nenhum grupo aguardando no momento.";
        return;
    }

    container.className = "queue-list";
    const ordenada = [...fila].sort((a, b) => {
        if (a.nivel !== b.nivel) {
            return a.nivel - b.nivel;
        }
        return a.tempo - b.tempo;
    });

    container.innerHTML = ordenada
        .map((item, index) => {
            const esperaSegundos = Math.max(0, Math.round(Date.now() / 1000 - item.tempo));
            return `
                <article class="queue-item">
                    <div class="queue-topline">
                        <strong>Grupo ${item.grupo}</strong>
                        <span class="tag">${index === 0 ? "Proximo" : "Na fila"}</span>
                    </div>
                    <div class="meta-row">
                        <span>Nivel ${item.nivel}</span>
                        <span>Espera ${esperaSegundos}s</span>
                    </div>
                </article>
            `;
        })
        .join("");
}

async function carregarEstado() {
    const [estadoResponse, sistemaResponse, conteudoResponse] = await Promise.all([
        fetch("/estado"),
        fetch("/estado_sistema"),
        fetch("/conteudo"),
    ]);

    const estado = await estadoResponse.json();
    const sistema = await sistemaResponse.json();
    const conteudo = await conteudoResponse.json();

    const ouvindo = Boolean(estado.ouvindo);
    const modo = formatModo(sistema.modo);

    const pill = document.getElementById("listen-pill");
    pill.textContent = ouvindo ? "Escuta ativa" : "Escuta desativada";
    pill.classList.toggle("active", ouvindo);

    const toggleButton = document.getElementById("toggle-listen-button");
    toggleButton.textContent = ouvindo ? "Desativar escuta" : "Ativar escuta";
    toggleButton.classList.toggle("warning", ouvindo);

    document.getElementById("modo-atual").textContent = modo;
    document.getElementById("modo-descricao").textContent =
        ouvindo ? "Pepper pronto para interacoes por voz." : "Sistema em modo de espera.";
    document.getElementById("grupo-atual").textContent = sistema.grupo_atual ?? "--";
    document.getElementById("fila-total").textContent = sistema.fila.length;
    document.getElementById("grupo-urgente").textContent = sistema.urgente ?? "Nenhum";
    document.getElementById("conteudo-atual").textContent = conteudo.conteudo || "inicio";
    document.getElementById("conteudo-select").value = conteudo.conteudo || "inicio";

    document.getElementById("dot-pepper").classList.toggle("active", ouvindo);
    document.getElementById("escuta-descricao").textContent = ouvindo
        ? "O reconhecimento de voz esta habilitado para o Pepper."
        : "O reconhecimento de voz esta pausado.";
    document.getElementById("fluxo-descricao").textContent =
        sistema.grupo_atual !== null
            ? `Grupo ${sistema.grupo_atual} esta no fluxo atual com modo ${modo.toLowerCase()}.`
            : "Nenhum grupo em atendimento neste instante.";

    renderFila(sistema.fila);
}

async function alternarEscuta() {
    const pillActive = document.getElementById("listen-pill").classList.contains("active");
    await fetch("/estado", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            ouvindo: !pillActive
        })
    });
    await carregarEstado();
}

async function atualizarConteudo() {
    const select = document.getElementById("conteudo-select");
    const feedback = document.getElementById("conteudo-feedback");

    feedback.textContent = "Atualizando conteudo...";
    await fetch(`/conteudo_set?conteudo=${encodeURIComponent(select.value)}`);
    feedback.textContent = `Conteudo sincronizado para ${select.value}.`;
    await carregarEstado();
}

document.getElementById("toggle-listen-button").addEventListener("click", alternarEscuta);
document.getElementById("save-content-button").addEventListener("click", atualizarConteudo);

carregarEstado();
setInterval(carregarEstado, 2000);
