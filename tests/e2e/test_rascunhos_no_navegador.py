"""Rascunho por LLM no navegador, no caso Roberto: sugestão de nome, prévia obrigatória,
gerar (LLM falso) e aceitar. Nada sai da máquina."""

from playwright.sync_api import Page, expect
from sqlmodel import Session

from descoberta.repositorio import pessoas_citadas, textos_da_sessao

COM_NOMES = (
    "Seguir com fase 0 para a Construtora Alvorada: o Marcos valida o critério de gravidade."
)


def test_rascunho_da_recomendacao(page: Page, servidor_demo):
    app, url, sessao_id, falso = servidor_demo
    page.goto(f"{url}/revisao")
    painel = page.locator(".painel-llm")
    expect(painel).to_contain_text("falso · falso-1")
    expect(page.locator("#anotacoes-internas")).not_to_be_checked()

    # A Cida é sugerida; um clique a põe na lista de pessoas citadas.
    painel.get_by_role("button", name="+ Cida").click()
    expect(painel.locator(".lista-pessoas")).to_contain_text("Cida")

    # Gerar antes da prévia é recusado, com o motivo.
    bloco = page.locator("#bloco-texto-recomendacao")
    bloco.get_by_role("button", name="Sugerir rascunho").click()
    expect(bloco).to_contain_text("veja a prévia")
    assert falso.pedidos == []

    # Prévia: o pedido sai com marcadores; confirmar libera os rascunhos.
    painel.get_by_role("button", name="Ver prévia").click()
    pedido = page.locator(".previa-pedido")
    expect(pedido).to_contain_text("[CLIENTE]")
    expect(pedido).not_to_contain_text("Roberto")
    expect(pedido).not_to_contain_text("Cida")
    page.get_by_role("button", name="Confirmar: está anonimizado").click()
    expect(painel).to_contain_text("Prévia confirmada")

    # Gerar: o rascunho aparece com os nomes de volta, ao lado do texto do consultor.
    bloco.get_by_role("button", name="Sugerir rascunho").click()
    expect(bloco.locator(".texto-rascunho")).to_have_text(COM_NOMES)
    [enviado] = falso.pedidos
    assert "Roberto" not in enviado.mensagem
    assert "Cida" not in enviado.mensagem
    assert "Anotações do consultor" not in enviado.mensagem

    # Aceitar (com confirmação): a caixa de texto passa a ter o rascunho.
    page.once("dialog", lambda dialogo: dialogo.accept())
    bloco.get_by_role("button", name="Aceitar").click()
    expect(page.locator("#texto-recomendacao")).to_have_value(COM_NOMES)
    with Session(app.state.engine) as banco:
        assert textos_da_sessao(banco, sessao_id)["recomendacao"] == COM_NOMES
        assert [p.nome for p in pessoas_citadas(banco, sessao_id)] == ["Marcos", "Cida"]
