// Atalhos de teclado da sessão ao vivo.
//
// A lista de atalhos não está aqui: vem do servidor (web/atalhos.py), num JSON dentro da
// página (#atalhos-dados), a mesma lista que monta a tela de ajuda. Este arquivo só diz o
// que cada ação faz. Todo o resto (salvar, trocar de aba, recarregar painéis) continua
// com o HTMX: as ações daqui apenas "clicam" nos links e botões que já existem.
(function () {
  "use strict";

  const dados = document.getElementById("atalhos-dados");
  if (!dados) return;
  const atalhos = JSON.parse(dados.textContent);

  // Último campo de resposta usado: Esc e Ctrl+Enter (na anotação) voltam para ele.
  let ultimoCampo = null;
  // Depois de trocar de aba pelo teclado, o cursor vai para o painel novo.
  let focarAposTroca = null;
  // Sinal marcado pelo teclado: o botão é trocado pelo servidor e o foco volta ao novo.
  let sinalComFoco = null;

  function campoDeTexto(el) {
    if (!el) return false;
    if (el.tagName === "TEXTAREA" || el.tagName === "SELECT" || el.isContentEditable) return true;
    return el.tagName === "INPUT" && !["checkbox", "radio", "button", "submit"].includes(el.type);
  }

  function combina(c, e) {
    // AltGr chega como Ctrl+Alt: é usado para digitar (², °, / no ABNT2), nunca é atalho.
    if (e.ctrlKey && e.altKey) return false;
    if (Boolean(c.alt) !== e.altKey) return false;
    if (Boolean(c.ctrl) !== (e.ctrlKey || e.metaKey)) return false;
    if (c.code && c.code !== e.code) return false;
    if (c.key && c.key !== e.key) return false;
    if (c.fora_de_campo && campoDeTexto(e.target)) return false;
    if (c.alvo && e.target.id !== c.alvo) return false;
    return true;
  }

  function focar(seletor) {
    const el = document.querySelector(seletor);
    if (!el) return false;
    el.focus();
    el.scrollIntoView({ block: "nearest" });
    return true;
  }

  function abaAtual() {
    const atual = document.querySelector('#abas [aria-current="page"]');
    return atual ? atual.dataset.aba : null;
  }

  function abrirAba(aba, depois) {
    const link = document.querySelector(`#abas [data-aba="${aba}"]`);
    if (!link) return;
    if (aba === abaAtual()) {
      depois();
      return;
    }
    focarAposTroca = depois;
    // Pede o painel ao HTMX direto (em vez de link.click()): se a barra de abas acabou de
    // ser recarregada, o link novo pode ainda não estar "ativado" pelo HTMX, e o clique
    // viraria uma navegação comum. Com o link como origem, o hx-push-url dele vale.
    htmx.ajax("GET", link.getAttribute("hx-get"), {
      source: link,
      target: "#conteudo-bloco",
      swap: "innerHTML",
    });
  }

  function pendentesDoPainel() {
    return Array.from(document.querySelectorAll("#conteudo-bloco textarea[data-obrigatoria]"))
      .filter((campo) => campo.value.trim() === "");
  }

  // Primeira obrigatória sem resposta; senão o primeiro campo; senão o título do painel.
  function focarPrimeiroCampo() {
    const [pendente] = pendentesDoPainel();
    if (pendente) pendente.focus();
    else if (!focar("#conteudo-bloco textarea")) focar("#titulo-painel");
  }

  const ajuda = () => document.getElementById("ajuda-atalhos");

  // Cada função tem o nome de uma ação de web/atalhos.py (um teste confere).
  // Devolver false quer dizer "não fiz nada": a tecla segue o comportamento normal.
  const acoes = {
    ajuda() {
      const dialogo = ajuda();
      if (dialogo.open) dialogo.close();
      else dialogo.showModal();
    },
    bloco(numero) {
      abrirAba(String(numero), focarPrimeiroCampo);
    },
    encerramento() {
      abrirAba("encerramento", focarPrimeiroCampo);
    },
    proxima_pendente() {
      const pendentes = pendentesDoPainel();
      if (pendentes.length) {
        // A próxima depois do cursor; se o cursor já passou de todas, a primeira.
        const depois = pendentes.find(
          (campo) => document.activeElement.compareDocumentPosition(campo) & Node.DOCUMENT_POSITION_FOLLOWING,
        );
        (depois || pendentes[0]).focus();
        return;
      }
      // Bloco em dia: vai para o próximo bloco com pendências (dá a volta no fim).
      const abas = Array.from(document.querySelectorAll("#abas [data-aba]"));
      const atual = abas.findIndex((aba) => aba.dataset.aba === abaAtual());
      const ordem = [...abas.slice(atual + 1), ...abas.slice(0, atual + 1)];
      const proxima = ordem.find((aba) => Number(aba.dataset.pendentes) > 0);
      if (proxima) abrirAba(proxima.dataset.aba, focarPrimeiroCampo);
      else focar("#pendencias");
    },
    sinais() {
      return focar("#sinais .botao-sinal");
    },
    anotacao() {
      return focar("#anotacao-texto");
    },
    salvar_anotacao() {
      const formulario = document.getElementById("form-anotacao");
      if (!document.getElementById("anotacao-texto").value.trim()) return;
      formulario.requestSubmit(); // o HTMX intercepta o envio (hx-post)
      if (ultimoCampo && document.body.contains(ultimoCampo)) ultimoCampo.focus();
    },
    calculos() {
      return focar("#calculos");
    },
    cronometro() {
      const botao = document.querySelector("#cronometro button");
      if (!botao) return false;
      botao.click();
    },
    voltar_ao_campo() {
      if (ajuda().open) return false; // o próprio <dialog> fecha com Esc
      if (!ultimoCampo || !document.body.contains(ultimoCampo)) return false;
      ultimoCampo.focus();
    },
  };

  document.addEventListener("focusin", (e) => {
    if (e.target.closest("#conteudo-bloco") && campoDeTexto(e.target)) ultimoCampo = e.target;
  });

  document.addEventListener("keydown", (e) => {
    for (const atalho of atalhos) {
      const combinacao = atalho.combinacoes.find((c) => combina(c, e));
      if (!combinacao) continue;
      // Com a ajuda aberta, só o atalho da própria ajuda (e o Esc do navegador) vale.
      if (ajuda().open && atalho.acao !== "ajuda") return;
      if (acoes[atalho.acao](combinacao.argumento) !== false) e.preventDefault();
      return;
    }
  });

  // Botão "Atalhos (Ctrl+/)" do topo.
  document.addEventListener("click", (e) => {
    const botao = e.target.closest("[data-acao]");
    if (botao && acoes[botao.dataset.acao]) acoes[botao.dataset.acao]();
  });

  document.body.addEventListener("htmx:beforeRequest", (e) => {
    const botao = e.detail.elt;
    if (botao.classList.contains("botao-sinal") && botao === document.activeElement) {
      sinalComFoco = botao.closest(".sinal").id;
    }
  });

  document.body.addEventListener("htmx:afterSettle", (e) => {
    // Painel novo no lugar (troca de aba): aplica o foco pedido pelo atalho.
    if (e.detail.target && e.detail.target.id === "conteudo-bloco" && focarAposTroca) {
      const focarAgora = focarAposTroca;
      focarAposTroca = null;
      focarAgora();
    }
    // Troca do sinal marcado pelo teclado (outros painéis também assentam, como os cálculos).
    if (sinalComFoco && e.detail.target && e.detail.target.id === sinalComFoco) {
      // Só devolve o cursor ao botão novo se ele se perdeu com a troca (foi para o body).
      // Se a pessoa já foi para outro campo enquanto o servidor respondia, fica onde está.
      const ativo = document.activeElement;
      if (!ativo || ativo === document.body) focar(`#${sinalComFoco} .botao-sinal`);
      sinalComFoco = null;
    }
  });
})();
