"""Proposta no navegador: criar, ajustar e excluir cláusulas, incluir uma fase, registrar
uma versão e baixar o PDF."""

from playwright.sync_api import Page, expect

from descoberta.repositorio import (
    ajustes_das_clausulas,
    obter_proposta,
    salvar_perfil,
    versoes_da_proposta,
)


def test_fluxo_da_proposta(page: Page, url_sessao, banco):
    url, sessao_id = url_sessao
    salvar_perfil(
        banco, nome="Ana Exemplo", empresa="Exemplo Consultoria", cidade="Campinas", uf="SP"
    )
    page.goto(f"{url}/proposta")
    expect(page.locator("main")).to_contain_text("O que entra ao criar")
    page.get_by_role("button", name="Criar proposta").click()
    # Só a página de edição tem as listas (a de criação tem o mesmo título).
    expect(page.locator("#lista-fases")).to_be_visible()
    banco.expire_all()
    assert obter_proposta(banco, sessao_id) is not None

    # Cláusula ajustada: o texto salva sozinho ao sair do campo.
    suporte = page.locator("#clausula-texto-suporte_garantia")
    suporte.fill("Garantia de 90 dias depois de cada entrega.")
    suporte.press("Tab")
    expect(page.locator("#aviso-clausula-texto-suporte_garantia")).to_contain_text("Salvo")

    # Cláusula removível excluída; a não removível nem tem o botão.
    cancelamento = page.locator("#clausula-cancelamento")
    cancelamento.get_by_role("button", name="Excluir desta proposta").click()
    expect(cancelamento).to_contain_text("Fora desta proposta")
    expect(page.locator("#clausula-foro").get_by_role("button")).to_have_count(0)

    # Fase nova: o seletor de fase do escopo se atualiza sozinho (evento fases-mudaram).
    page.locator("#novo-fases-nome").fill("Sustentação")
    page.locator("#novo-fases-duracao_semanas").fill("4")
    page.locator("#lista-fases").get_by_role("button", name="Incluir").click()
    expect(page.locator("#lista-fases")).to_contain_text("Sustentação")
    expect(page.locator("#novo-escopo-fase_id option", has_text="Sustentação")).to_have_count(1)

    banco.expire_all()
    ajustes = ajustes_das_clausulas(banco, sessao_id)
    assert ajustes["suporte_garantia"].texto.startswith("Garantia de 90 dias")
    assert ajustes["cancelamento"].excluida is True

    # Documento: o texto ajustado e o foro do perfil; registrar a versão e baixar o PDF.
    page.get_by_role("link", name="Documento da proposta →").click()
    documento = page.locator("article.documento")
    expect(documento).to_contain_text("Garantia de 90 dias depois de cada entrega.")
    expect(documento).to_contain_text("foro da comarca de Campinas/SP")
    expect(documento).not_to_contain_text("Cancelamento")
    page.get_by_role("button", name="Registrar versão enviada").click()
    versoes = page.locator("#versoes")
    expect(versoes.locator("tbody tr")).to_have_count(1)
    with page.expect_download() as download:
        versoes.get_by_role("link", name="PDF").click()
    assert download.value.suggested_filename.endswith("-v1.pdf")

    banco.expire_all()
    [versao] = versoes_da_proposta(banco, sessao_id)
    assert "cancelamento" not in [c["id"] for c in versao.clausulas]
