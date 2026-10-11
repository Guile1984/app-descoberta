"""Revisão pós-sessão no navegador: um risco incluído pelo teclado aparece na matriz."""

from playwright.sync_api import Page, expect

from descoberta.repositorio import Risco, itens_da_sessao


def test_incluir_risco_pelo_teclado_atualiza_matriz_e_pendencias(page: Page, url_sessao, banco):
    url, sessao_id = url_sessao
    page.goto(f"{url}/revisao")
    pendencias = page.locator("#pendencias-revisao")
    expect(pendencias).to_contain_text("nenhum risco cadastrado")

    page.locator("#novo-riscos-descricao").focus()
    page.keyboard.type("Fotos mostram o interior das casas")
    page.keyboard.press("Tab")  # categoria: digitar a inicial escolhe a opção
    page.keyboard.type("L")
    page.keyboard.press("Tab")
    page.keyboard.press("End")  # probabilidade: alta
    page.keyboard.press("Tab")
    page.keyboard.press("End")  # impacto: alto
    page.keyboard.press("Tab")  # mitigação em branco
    page.keyboard.press("Tab")
    page.keyboard.press("Enter")  # botão "Incluir"

    expect(page.locator("#lista-riscos")).to_contain_text("Fotos mostram o interior das casas")
    celula = page.locator('#matriz-riscos td[data-impacto="alto"][data-probabilidade="alto"]')
    expect(celula).to_contain_text("R1")
    expect(pendencias).not_to_contain_text("nenhum risco cadastrado")
    expect(pendencias).to_contain_text("exigem mitigação")
    # Depois de incluir, o cursor volta para a descrição de um risco novo.
    expect(page.locator("#novo-riscos-descricao")).to_be_focused()

    banco.expire_all()
    [risco] = itens_da_sessao(banco, Risco, sessao_id)
    assert (risco.categoria, risco.probabilidade, risco.impacto) == ("lgpd", "alto", "alto")
