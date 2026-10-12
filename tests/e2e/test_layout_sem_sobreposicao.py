"""Nenhum painel cobre outro conteúdo durante a rolagem (a revisão do caso Roberto, com a
prévia do LLM aberta, que deixa a coluna da direita comprida)."""

from playwright.sync_api import Page, expect

# Mede, na posição atual da rolagem, quais elementos o quadro "Falta preencher" cobre.
_SOBREPOSTOS = """
(seletores) => {
  const quadro = document.querySelector("#pendencias-revisao").getBoundingClientRect();
  const cobertos = [];
  for (const seletor of seletores) {
    for (const el of document.querySelectorAll(seletor)) {
      const r = el.getBoundingClientRect();
      const largura = Math.min(quadro.right, r.right) - Math.max(quadro.left, r.left);
      const altura = Math.min(quadro.bottom, r.bottom) - Math.max(quadro.top, r.top);
      if (largura > 1 && altura > 1) cobertos.push(seletor);
    }
  }
  return cobertos;
}
"""

OUTROS = [
    ".painel-llm h2",
    "#painel-llm",
    ".previa-llm table",
    ".previa-llm .doc-aviso",
    ".previa-pedido",
    "#textos",
    "#lista-riscos",
]


def test_quadro_falta_preencher_nao_cobre_nada_ao_rolar(page: Page, servidor_demo):
    _, url, _, _ = servidor_demo
    page.set_viewport_size({"width": 1280, "height": 720})
    page.goto(f"{url}/revisao")
    expect(page.locator("#pendencias-revisao")).to_be_visible()
    page.locator(".painel-llm").get_by_role("button", name="Ver prévia").click()
    expect(page.locator(".previa-llm table")).to_be_visible()

    altura = page.evaluate("document.documentElement.scrollHeight")
    assert altura > 2 * 720  # a página rola bastante: o teste tem o que medir
    for y in range(0, altura, 200):
        page.evaluate(f"window.scrollTo(0, {y})")
        cobertos = page.evaluate(_SOBREPOSTOS, OUTROS)
        assert cobertos == [], f"rolagem em {y}px: o quadro cobre {cobertos}"
