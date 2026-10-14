"""Critério de aceite do Sprint 8: o caso Roberto de ponta a ponta, num banco vazio.

Tudo pela tela, como o consultor faria na primeira vez: perfil → cliente → sessão
(respostas, números, notas, sinais, anotações) → revisão pós-sessão → relatório → versão
registrada. Os dados são os do demo (descoberta.demo), digitados no navegador em vez de
gravados direto no banco. No fim, os números de referência do caso (60 h/mês, score de
dados 4, payback ≈ 7,7 meses, score final 12 → seguir com fase 0) aparecem na tela e no
PDF registrado, e o hash do rodapé do PDF é o da versão gravada.
"""

import re
from datetime import date, timedelta

from playwright.sync_api import Page, expect
from pypdf import PdfReader

from descoberta.demo import (
    ANOTACOES,
    CLIENTE,
    CONSULTOR,
    ESCOPO,
    HIPOTESES,
    INDICADORES,
    METRICAS,
    NOTAS,
    PROXIMOS_PASSOS,
    RESPOSTAS,
    RISCOS,
    SINAIS,
    TEXTOS,
)
from descoberta.repositorio import (
    listar_clientes,
    obter_metricas,
    respostas_da_sessao,
    sinais_marcados,
    versoes_da_sessao,
)

NUMERO_DE_BLOCOS = 10


def _salvo(page: Page, alvo: str) -> None:
    expect(page.locator(f"#aviso-{alvo}")).to_contain_text("Salvo")


def _texto(page: Page, campo: str, alvo: str, valor: str) -> None:
    caixa = page.locator(campo)
    caixa.fill(valor)
    caixa.press("Tab")  # sair do campo salva (como o consultor faz)
    _salvo(page, alvo)


def _opcao(page: Page, campo: str, alvo: str, valor: str) -> None:
    page.locator(campo).select_option(valor)
    _salvo(page, alvo)


def _numero(valor) -> str:
    """No formato que o consultor digita: 20000 → "20.000"."""
    return f"{valor:,}".replace(",", ".") if isinstance(valor, int) else str(valor)


def _preencher_aba(page: Page, url_sessao: str, aba: str, prefixo: str) -> None:
    page.goto(
        f"{url_sessao}/encerramento" if aba == "encerramento" else f"{url_sessao}?bloco={aba}"
    )
    for pergunta, resposta in RESPOSTAS.items():
        if pergunta.startswith(prefixo):
            alvo = pergunta.replace(".", "-")
            _texto(page, f"#resposta-{alvo}", alvo, resposta)
    for campo, valor in METRICAS.items():
        if page.locator(f"#metrica-{campo}").count():
            if campo == "frequencia_periodo":
                _opcao(page, f"#metrica-{campo}", f"metrica-{campo}", valor)
            else:
                _texto(page, f"#metrica-{campo}", f"metrica-{campo}", _numero(valor))
    for criterio, nota in NOTAS.items():
        if page.locator(f"#nota-{criterio}").count():
            _opcao(page, f"#nota-{criterio}", f"nota-{criterio}", str(nota))
    for sinal in SINAIS:
        botao = page.locator(f"#sinal-{sinal.replace('.', '-')} .botao-sinal")
        if botao.count():
            botao.click()
            expect(
                page.locator(f"#sinal-{sinal.replace('.', '-')} .botao-sinal")
            ).to_have_attribute("aria-pressed", "true")
    for texto, bloco in ANOTACOES:
        if bloco is not None and str(bloco) == aba:
            page.locator("#anotacao-texto").fill(texto)
            page.locator("#anotacao-texto").press("Control+Enter")
            expect(page.locator("#lista-anotacoes")).to_contain_text(texto)


def _incluir(page: Page, lista: str, campos: dict[str, str], conferir: str) -> None:
    for campo, valor in campos.items():
        seletor = f"#novo-{lista}-{campo}"
        if page.locator(seletor).evaluate("e => e.tagName") == "SELECT":
            page.locator(seletor).select_option(valor)
        else:
            page.locator(seletor).fill(valor)
    page.locator(f"#lista-{lista}").get_by_role("button", name="Incluir").click()
    expect(page.locator(f"#lista-{lista} .itens-revisao")).to_contain_text(conferir)


def test_caso_roberto_ponta_a_ponta(page: Page, servidor, banco):
    _, base = servidor
    hoje = date.today()

    # 1. Primeiro uso: a tela inicial pede o perfil do consultor.
    page.goto(base)
    expect(page.locator("main")).to_contain_text("perfil")
    for campo in ("nome", "empresa", "cpf_cnpj", "email", "telefone", "cidade"):
        page.locator(f'form [name="{campo}"]').fill(CONSULTOR[campo])
    page.locator('form [name="uf"]').select_option(CONSULTOR["uf"])
    page.get_by_role("button", name="Salvar").click()

    # 2. Cliente novo.
    page.goto(f"{base}/clientes/novo")
    for campo in ("nome", "empresa", "setor"):
        page.locator(f'form [name="{campo}"]').fill(CLIENTE[campo])
    page.locator('form [name="num_funcionarios"]').fill(str(CLIENTE["num_funcionarios"]))
    page.get_by_role("button", name="Salvar").click()
    expect(page.locator("main")).to_contain_text(CLIENTE["empresa"])

    # 3. Sessão nova, com a data de hoje (os prazos dos próximos passos vêm depois dela).
    page.get_by_role("button", name="Abrir nova sessão").click()
    expect(page).to_have_url(re.compile(r"/sessoes/\d+"))
    url_sessao = page.url.split("?")[0]
    sessao_id = int(url_sessao.rsplit("/", 1)[1])

    # 4. Sessão: tipo de solução (abre as condicionais de visão computacional), as
    #    respostas, os números e as notas de cada bloco, os sinais e as anotações.
    page.goto(f"{url_sessao}?bloco=3")
    _opcao(page, ".tipo-solucao select", "tipo_solucao", "visao_computacional")
    for bloco in range(1, NUMERO_DE_BLOCOS + 1):
        _preencher_aba(page, url_sessao, str(bloco), f"b{bloco}.")
    _preencher_aba(page, url_sessao, "encerramento", "enc.")

    # Painel de cálculos com os números de referência do caso.
    page.goto(f"{url_sessao}?bloco=10")
    calculos = page.locator("#calculos")
    expect(calculos).to_contain_text("60 h/mês")
    expect(calculos).to_contain_text("4 de 15")
    expect(calculos).to_contain_text("7,7 meses")
    expect(calculos).to_contain_text("12 de 18")
    expect(calculos).to_contain_text("Seguir com fase 0")

    # 5. Revisão pós-sessão: hipóteses, riscos, indicadores, escopo, passos e textos.
    page.goto(f"{url_sessao}/revisao")
    for campo in HIPOTESES:
        page.locator(f"#hipotese-{campo}").check()
        _salvo(page, f"hipotese-{campo}")
    for risco in RISCOS:
        _incluir(page, "riscos", risco, risco["descricao"])
    for indicador in INDICADORES:
        _incluir(page, "indicadores", indicador, indicador["nome"])
    for texto, entra in ESCOPO:
        _incluir(page, "escopo", {"texto": texto, "entra": "sim" if entra else "nao"}, texto)
    for acao, responsavel, dias in PROXIMOS_PASSOS:
        prazo = (hoje + timedelta(days=dias)).isoformat()
        _incluir(page, "passos", {"acao": acao, "responsavel": responsavel, "prazo": prazo}, acao)
    for secao, texto in TEXTOS.items():
        _texto(page, f"#texto-{secao}", f"texto-{secao}", texto)
    page.reload()
    expect(page.locator("#pendencias-revisao")).to_contain_text("Nada falta")

    # 6. Relatório (versão cliente): prévia, registro da versão enviada e o PDF.
    page.goto(f"{url_sessao}/relatorio")
    documento = page.locator("article.documento")
    expect(documento).to_contain_text(CLIENTE["empresa"])
    expect(documento).to_contain_text("7,7 meses")
    expect(documento).to_contain_text("Seguir com fase 0")
    page.get_by_role("button", name=re.compile("Registrar versão enviada")).click()
    versoes = page.locator("#versoes")
    expect(versoes.locator("tbody tr")).to_have_count(1)
    with page.expect_download() as download:
        versoes.get_by_role("link", name="PDF").click()
    assert download.value.suggested_filename == (
        f"relatorio-descoberta-construtora-alvorada-{hoje.isoformat()}-cliente-v1.pdf"
    )
    pdf = PdfReader(download.value.path())
    texto_pdf = "\n".join(pagina.extract_text() for pagina in pdf.pages)

    # 7. O que ficou gravado: um cliente, as respostas, os números e a versão com hash.
    banco.expire_all()
    [cliente] = listar_clientes(banco)
    assert cliente.empresa == CLIENTE["empresa"]
    respostas = respostas_da_sessao(banco, sessao_id)
    assert {k: respostas.get(k) for k in RESPOSTAS} == RESPOSTAS
    assert obter_metricas(banco, sessao_id).investimento == METRICAS["investimento"]
    assert sorted(s.sinal_id for s in sinais_marcados(banco, sessao_id)) == sorted(SINAIS)
    [versao] = versoes_da_sessao(banco, sessao_id)
    assert versao.numero == 1
    # O rodapé de cada página traz o começo do hash do conteúdo: a cópia confere.
    resumo = re.search(r"hash ([0-9a-f]{8,})", texto_pdf).group(1)
    assert versao.hash_conteudo.startswith(resumo)
    assert texto_pdf.count(f"hash {resumo}") == len(pdf.pages)
    for numero in ("7,7", "Seguir com fase 0"):
        assert numero in texto_pdf
