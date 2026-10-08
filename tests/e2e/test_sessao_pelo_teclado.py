"""Critério de aceite do Sprint 5: uma sessão completa conduzida só com o teclado.

O roteiro segue o caso Roberto: respostas, números, notas, sinais, anotação, cronômetro,
ajuda e encerramento, sem nenhum clique. No fim, o painel de cálculos precisa mostrar
os valores de referência (payback ≈ 7,7 meses; score final 12 → seguir com fase 0).
"""

import re
from decimal import Decimal

from playwright.sync_api import Page, expect

from descoberta.questionario import perguntas_visiveis
from descoberta.repositorio import (
    anotacoes_da_sessao,
    notas_da_sessao,
    obter_metricas,
    respostas_da_sessao,
    sinais_marcados,
)


def obrigatorias(questionario, bloco: int) -> int:
    """Quantas obrigatórias o bloco mostra (sessão sem tipo de solução: sem condicionais)."""
    return len(
        [p for p in perguntas_visiveis(questionario, bloco, None) if p.tipo == "obrigatoria"]
    )


def salvo(page: Page, alvo: str) -> None:
    expect(page.locator(f"#aviso-{alvo}")).to_contain_text("Salvo às")


def digitar(page: Page, texto: str) -> None:
    page.keyboard.type(texto)


def ir_para_bloco(page: Page, numero: int) -> None:
    page.keyboard.press(f"Alt+Digit{numero % 10}")
    expect(page.locator("#titulo-painel")).to_contain_text(f"{numero}.")


def test_sessao_completa_so_com_teclado(page: Page, url_sessao, banco, questionario_v1):
    url, sessao_id = url_sessao
    page.goto(url)

    # Cronômetro: Alt+T inicia.
    page.keyboard.press("Alt+t")
    expect(page.locator("#cronometro button")).to_have_text("Pausar")

    # Bloco 1: Alt+1 leva o cursor à primeira obrigatória; Tab anda entre os campos.
    ir_para_bloco(page, 1)
    expect(page.locator("#resposta-b1-o1")).to_be_focused()
    digitar(page, "Avaliar os chamados de fissura nas obras.")
    for _ in range(obrigatorias(questionario_v1, 1)):
        page.keyboard.press("Tab")
    # Depois das obrigatórias vêm os números do bloco 1.
    expect(page.locator("#metrica-horas_por_ocorrencia")).to_be_focused()
    digitar(page, "4")
    page.keyboard.press("Tab")
    digitar(page, "15")
    page.keyboard.press("Tab")
    page.keyboard.press("End")  # período: última opção, "por mês"
    page.keyboard.press("Tab")
    digitar(page, "100")
    page.keyboard.press("Tab")
    salvo(page, "metrica-custo_hora")

    # Sinal de alerta: Alt+S vai para os sinais do bloco; Espaço marca.
    page.keyboard.press("Alt+s")
    primeiro_sinal = page.locator("#sinais .botao-sinal").first
    expect(primeiro_sinal).to_be_focused()
    page.keyboard.press("Space")
    expect(page.locator("#sinais .botao-sinal").first).to_have_attribute("aria-pressed", "true")

    # Esc volta ao último campo de resposta.
    page.keyboard.press("Escape")
    expect(page.locator("#metrica-custo_hora")).to_be_focused()

    # Anotação: Alt+N escreve, Ctrl+Enter salva e devolve o cursor.
    page.keyboard.press("Alt+n")
    expect(page.locator("#anotacao-texto")).to_be_focused()
    digitar(page, "Marcos não participou.")
    page.keyboard.press("Control+Enter")
    expect(page.locator("#lista-anotacoes")).to_contain_text("Marcos não participou.")
    expect(page.locator("#lista-anotacoes")).to_contain_text("Bloco 1")
    expect(page.locator("#metrica-custo_hora")).to_be_focused()

    # Bloco 4: notas de dados (selects: digitar o número escolhe a nota).
    ir_para_bloco(page, 4)
    expect(page.locator("#resposta-b4-o1")).to_be_focused()
    for _ in range(obrigatorias(questionario_v1, 4)):
        page.keyboard.press("Tab")
    expect(page.locator("#nota-disponibilidade")).to_be_focused()
    for nota in "11101":
        digitar(page, nota)
        page.keyboard.press("Tab")
    salvo(page, "nota-acesso_legal")

    # Bloco 6: custo fixo de operação.
    ir_para_bloco(page, 6)
    expect(page.locator("#resposta-b6-o1")).to_be_focused()
    for _ in range(obrigatorias(questionario_v1, 6) + 2):  # + chamadas e custo por chamada
        page.keyboard.press("Tab")
    expect(page.locator("#metrica-custo_fixo_mes")).to_be_focused()
    digitar(page, "400")
    page.keyboard.press("Tab")
    salvo(page, "metrica-custo_fixo_mes")

    # Bloco 9: horas economizadas e investimento (formato brasileiro).
    ir_para_bloco(page, 9)
    expect(page.locator("#resposta-b9-o1")).to_be_focused()
    for _ in range(obrigatorias(questionario_v1, 9)):
        page.keyboard.press("Tab")
    expect(page.locator("#metrica-horas_economizadas_mes")).to_be_focused()
    digitar(page, "30")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")  # outros ganhos: em branco
    digitar(page, "20.000")
    page.keyboard.press("Tab")
    salvo(page, "metrica-investimento")

    # Bloco 10 (Alt+0): notas finais; a de prontidão dos dados é derivada.
    ir_para_bloco(page, 10)
    expect(page.locator("#titulo-painel")).to_be_focused()
    page.keyboard.press("Tab")
    expect(page.locator("#nota-dor_clara")).to_be_focused()
    for nota in "32222":
        digitar(page, nota)
        page.keyboard.press("Tab")
    salvo(page, "nota-comprometimento_cliente")

    # Painel de cálculos (Alt+C) com os valores do caso Roberto.
    page.keyboard.press("Alt+c")
    calculos = page.locator("#calculos")
    expect(calculos).to_contain_text("R$ 6.000,00/mês")
    expect(calculos).to_contain_text("7,7 meses")
    expect(calculos).to_contain_text("4 de 15")
    expect(calculos).to_contain_text("12 de 18")
    expect(calculos).to_contain_text("Seguir com fase 0")
    expect(calculos).to_contain_text("1 sinal")

    # Ajuda: Ctrl+/ abre, Esc fecha.
    page.keyboard.press("Control+/")
    expect(page.locator("#ajuda-atalhos")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("#ajuda-atalhos")).to_be_hidden()

    # Encerramento (Alt+R): resumo para ler ao cliente.
    page.keyboard.press("Alt+r")
    expect(page.locator("#titulo-painel")).to_have_text("Encerramento")
    expect(page.locator("#resposta-enc-resumo")).to_be_focused()
    digitar(page, "Os chamados de fissura tomam 60 h/mês do Marcos.")
    page.keyboard.press("Tab")
    resumo = page.locator("#resumo-leitura")
    expect(resumo).to_contain_text("Os chamados de fissura tomam 60 h/mês do Marcos.")
    expect(resumo).to_contain_text("Seguir com fase 0")

    # Pausa o cronômetro e confere o que ficou gravado.
    page.keyboard.press("Alt+t")
    expect(page.locator("#cronometro button")).to_have_text("Retomar")

    banco.expire_all()
    respostas = respostas_da_sessao(banco, sessao_id)
    assert respostas["b1.o1"] == "Avaliar os chamados de fissura nas obras."
    assert respostas["enc.resumo"] == "Os chamados de fissura tomam 60 h/mês do Marcos."
    metricas = obter_metricas(banco, sessao_id)
    assert metricas.investimento == Decimal(20000)
    assert metricas.frequencia_periodo == "mes"
    assert notas_da_sessao(banco, sessao_id)["qualidade"] == 0
    assert [s.sinal_id for s in sinais_marcados(banco, sessao_id)] == ["b1.s1"]
    assert [a.bloco for a in anotacoes_da_sessao(banco, sessao_id)] == [1]


def test_alt_p_percorre_as_pendentes_e_passa_de_bloco(page: Page, url_sessao, questionario_v1):
    url, _ = url_sessao
    page.goto(url)
    page.keyboard.press("Alt+p")
    expect(page.locator("#resposta-b1-o1")).to_be_focused()
    page.keyboard.press("Alt+p")
    expect(page.locator("#resposta-b1-o2")).to_be_focused()
    # Preenche todas as obrigatórias do bloco 1: o próximo Alt+P vai para o bloco 2.
    perguntas = perguntas_visiveis(questionario_v1, 1, None)
    obrigatorias_1 = [p for p in perguntas if p.tipo == "obrigatoria"]
    for pergunta in obrigatorias_1:
        campo = page.locator(f"#resposta-{pergunta.id.replace('.', '-')}")
        campo.focus()
        digitar(page, "ok")
    page.keyboard.press("Tab")
    expect(page.locator("#pendencias")).to_contain_text(f"{48 - len(obrigatorias_1)} obrigatórias")
    page.keyboard.press("Alt+p")
    expect(page.locator("#titulo-painel")).to_contain_text("2.")
    expect(page.locator("#resposta-b2-o1")).to_be_focused()


def test_altgr_nao_dispara_atalho(page: Page, url_sessao):
    # No teclado ABNT2, AltGr (Ctrl+Alt) digita caracteres como ² e °: não pode trocar de bloco.
    url, _ = url_sessao
    page.goto(f"{url}?bloco=3")
    page.locator("#resposta-b3-o1").focus()
    page.keyboard.press("Control+Alt+Digit1")
    expect(page.locator("#titulo-painel")).to_contain_text("3.")


def test_troca_de_aba_nao_perde_a_anotacao_em_andamento(page: Page, url_sessao):
    url, _ = url_sessao
    page.goto(url)
    page.keyboard.press("Alt+n")
    digitar(page, "Rascunho")
    page.keyboard.press("Alt+Digit5")
    expect(page.locator("#titulo-painel")).to_contain_text("5.")
    expect(page.locator("#anotacao-texto")).to_have_value("Rascunho")
    expect(page.locator("#anotacao-bloco")).to_have_value("5")
    expect(page).to_have_url(re.compile(r"\?bloco=5$"))  # o F5 reabre na mesma aba
    expect(page.locator("#sinais")).to_contain_text("bloco 5")
