"""Montagem do relatório (sem gerar arquivos): conteúdo, versões, anexos e termo."""

import dataclasses
from datetime import UTC, datetime

import pytest

from descoberta.relatorio import Emissao, coletar_dados, montar_relatorio
from descoberta.relatorio.consultor import AVISO_CONSULTOR_FICTICIO
from descoberta.relatorio.documento import (
    FALTA,
    Assinatura,
    Aviso,
    Capa,
    QuebraDePagina,
    Tabela,
    Titulo,
)
from descoberta.repositorio import (
    RegistroNaoEncontrado,
    Risco,
    TipoVersao,
    atualizar_sessao,
    editar_item,
    itens_da_sessao,
    marcar_hipotese,
    salvar_metricas,
)

EMITIDO_EM = datetime(2026, 10, 11, 17, 5, tzinfo=UTC)


def _titulos_das_secoes(documento) -> list[str]:
    return [t for t in documento.titulos(1) if t[0].isdigit()]


def _tabela_apos(documento, titulo: str) -> Tabela:
    """A primeira tabela que aparece depois do título."""
    indice = next(
        i for i, b in enumerate(documento.blocos) if isinstance(b, Titulo) and b.texto == titulo
    )
    return next(b for b in documento.blocos[indice:] if isinstance(b, Tabela))


# --- Estrutura ---


def test_capa_e_as_12_secoes_na_ordem_do_yaml(dados_roberto, emissao_cliente, questionario_v1):
    documento = montar_relatorio(dados_roberto, emissao_cliente)
    assert isinstance(documento.blocos[0], Capa)
    secoes = questionario_v1.bloco(10).secoes_relatorio
    esperados = [f"{n}. {s.titulo_para_cliente}" for n, s in enumerate(secoes, start=1)]
    assert _titulos_das_secoes(documento) == esperados
    assert "(bloco" not in "\n".join(documento.titulos(1))


def test_ordem_capa_secoes_anexos_e_termo(dados_roberto, emissao_cliente):
    titulos = montar_relatorio(dados_roberto, emissao_cliente).titulos(1)
    assert titulos[12:] == [
        "Anexo A — Respostas da sessão",
        "Anexo B — Memória de cálculo",
        "Termo de ciência e validação",
    ]


def test_capa_do_roberto(dados_roberto, emissao_cliente):
    capa = montar_relatorio(dados_roberto, emissao_cliente).blocos[0]
    assert capa.titulo == "Relatório de Descoberta"
    assert capa.subtitulo == "Construtora Alvorada"
    linhas = dict(capa.linhas)
    assert linhas["Cliente"] == "Roberto"
    assert linhas["Data da sessão"] == "07/10/2026"
    assert "rascunho" in linhas["Emissão"].lower()
    assert capa.faixa is None


def test_capa_de_versao_registrada(dados_roberto):
    emissao = Emissao(TipoVersao.cliente, numero=3, emitido_em=EMITIDO_EM)
    capa = montar_relatorio(dados_roberto, emissao).blocos[0]
    emissao_texto = dict(capa.linhas)["Emissão"]
    assert emissao_texto.startswith("Versão 3")
    assert "11/10/2026" in emissao_texto


# --- Números do caso Roberto (vêm do Painel) ---


def test_numeros_do_roberto(dados_roberto, emissao_cliente):
    texto = montar_relatorio(dados_roberto, emissao_cliente).texto()
    assert "60 h" in texto
    assert "R$ 6.000,00" in texto  # custo mensal da dor
    assert "R$ 3.000,00" in texto  # economia mensal
    assert "R$ 400,00" in texto  # operação
    assert "R$ 20.000,00" in texto  # investimento
    assert "7,7 meses" in texto
    assert "4 de 15" in texto
    assert "12 de 18" in texto
    assert "Seguir com fase 0" in texto
    assert "Visão computacional" in texto


def test_saidas_da_revisao_entram_nas_secoes(dados_roberto, emissao_cliente):
    documento = montar_relatorio(dados_roberto, emissao_cliente)
    texto = documento.texto()
    for trecho in (
        "Hoje o Marcos gasta cerca de 60 horas",  # frase-problema
        "Recall de fissuras graves",  # indicador
        "Laudo técnico gerado automaticamente",  # escopo: fica de fora
        "Enviar a proposta da fase 0",  # próximo passo
        "25/10/2026",  # prazo: 14 dias depois da criação do demo (fixada no conftest)
        "1. Teste com dados históricos",  # tabela de critério de aceite do YAML
    ):
        assert trecho in texto
    riscos = _tabela_apos(documento, "8. Matriz de riscos e mitigações")
    assert riscos.linhas[0][:5] == [
        "R1",
        "As fotos mostram pessoas e o interior das casas dos clientes.",
        "LGPD",
        "Alta",
        "Alto",
    ]


def test_matriz_de_riscos_colorida(dados_roberto, emissao_cliente):
    documento = montar_relatorio(dados_roberto, emissao_cliente)
    matriz = next(b for b in documento.blocos if isinstance(b, Tabela) and b.niveis)
    assert matriz.colunas[1:] == [
        "Probabilidade baixa",
        "Probabilidade média",
        "Probabilidade alta",
    ]
    assert [linha[0] for linha in matriz.linhas] == [
        "Impacto alto",
        "Impacto médio",
        "Impacto baixo",
    ]
    assert matriz.linhas[0][3] == "R1\nnível alto"  # alto × alto
    assert matriz.niveis[0][3] == "alto"
    assert matriz.niveis[2][1] == "baixo"


def test_respostas_dos_blocos_nas_secoes(dados_roberto, emissao_cliente):
    texto = montar_relatorio(dados_roberto, emissao_cliente).texto()
    assert "Não há ERP: só a planilha de obras e o WhatsApp." in texto  # bloco 8
    assert "Em fases, de R$ 15 mil a R$ 20 mil." in texto  # bloco 9


# --- Versões ---


def test_versao_cliente_nao_tem_sinais_nem_anotacoes(dados_roberto, emissao_cliente):
    texto = montar_relatorio(dados_roberto, emissao_cliente).texto()
    assert "Anexo C" not in texto
    assert "Sinais de alerta" not in texto
    assert "Roberto prefere fases" not in texto  # anotação livre
    assert "100% de acerto" not in texto  # sinal b1.s4
    assert "USO INTERNO" not in texto


def test_versao_interna_tem_sinais_e_anotacoes(dados_roberto, emissao_interna):
    documento = montar_relatorio(dados_roberto, emissao_interna)
    texto = documento.texto()
    assert documento.blocos[0].faixa.startswith("USO INTERNO")
    assert "Anexo C — Uso interno: sinais de alerta e anotações" in documento.titulos(1)
    assert "100% de acerto" in texto
    assert "Roberto prefere fases; não falar em valor fechado antes do relatório." in texto
    # O termo continua sendo a última parte.
    assert documento.titulos(1)[-1] == "Termo de ciência e validação"


# --- Anexo A ---


def test_anexo_a_tem_as_respostas_por_bloco_e_o_encerramento(dados_roberto, emissao_cliente):
    documento = montar_relatorio(dados_roberto, emissao_cliente)
    subtitulos = documento.titulos(2)
    assert "Bloco 1 — Problema de negócio" in subtitulos
    assert "Bloco 10 — Relatório de Descoberta" not in subtitulos  # sem respostas
    texto = documento.texto()
    assert "Cerca de 500 fotos em 2 anos." in texto
    assert "Quem tira as fotos" in texto  # condicional visível (visão computacional)


def test_anexo_a_ignora_condicionais_ocultas(banco_roberto, questionario_v1, emissao_cliente):
    session, sessao_id = banco_roberto
    atualizar_sessao(session, sessao_id, tipo_solucao="llm_rag")  # b4.vc* ficam ocultas
    texto = montar_relatorio(coletar_dados(session, sessao_id, questionario_v1), emissao_cliente)
    assert "Fotos recebidas pelo WhatsApp, guardadas no celular do Marcos." not in texto.texto()
    assert "Quem tira as fotos" not in texto.texto()
    assert "Cerca de 500 fotos em 2 anos." in texto.texto()  # obrigatória comum continua


def test_secao_de_operacao_esconde_as_entradas_vazias(dados_roberto, emissao_cliente):
    documento = montar_relatorio(dados_roberto, emissao_cliente)
    titulo = _titulos_das_secoes(documento)[6]
    assert titulo.startswith("7. ")
    linhas = {linha[0]: linha[1] for linha in _tabela_apos(documento, titulo).linhas}
    assert linhas == {"Custo fixo mensal": "R$ 400,00 *", "Custo de operação": "R$ 400,00/mês *"}
    # No Anexo B as entradas vazias continuam, para mostrar o que não foi informado.
    entradas = _tabela_apos(documento, "Anexo B — Memória de cálculo")
    por_campo = {linha[0]: linha for linha in entradas.linhas}
    assert por_campo["Chamadas por dia"][1] == "—"


def test_secao_de_operacao_vazia_mostra_so_o_que_falta(dados_vazios, emissao_cliente):
    documento = montar_relatorio(dados_vazios, emissao_cliente)
    tabela = _tabela_apos(documento, _titulos_das_secoes(documento)[6])
    assert tabela.linhas == [["Custo de operação", FALTA]]


# --- Anexo B ---


def test_anexo_b_destaca_as_hipoteses(dados_roberto, emissao_cliente):
    documento = montar_relatorio(dados_roberto, emissao_cliente)
    entradas = _tabela_apos(documento, "Anexo B — Memória de cálculo")
    por_campo = {linha[0]: linha for linha in entradas.linhas}
    assert por_campo["Custo da hora"][1:] == ["R$ 100,00", "Hipótese"]
    assert por_campo["Investimento"][1:] == ["R$ 20.000,00", "Informado na sessão"]
    calculos = next(
        b for b in documento.blocos if isinstance(b, Tabela) and b.colunas[0] == "Resultado"
    )
    por_resultado = {linha[0]: linha for linha in calculos.linhas}
    assert por_resultado["Payback"][2] == "7,7 meses"
    assert "depende de hipótese" in por_resultado["Payback"][3]
    assert "custo da hora" in por_resultado["Payback"][3]
    assert por_resultado["Ocorrências por mês"][3] == ""  # sem hipótese


def test_valores_com_hipotese_marcados_no_corpo(dados_roberto, emissao_cliente):
    documento = montar_relatorio(dados_roberto, emissao_cliente)
    texto = documento.texto()
    assert "7,7 meses *" in texto
    assert any(
        isinstance(b, Aviso) and b.texto.startswith("* Calculado com hipóteses")
        for b in documento.blocos
    )


def test_sem_hipoteses_nao_ha_asterisco(banco_roberto, questionario_v1, emissao_cliente):
    session, sessao_id = banco_roberto
    for campo in ("custo_hora", "horas_economizadas_mes", "custo_fixo_mes"):
        marcar_hipotese(session, sessao_id, campo, False)
    documento = montar_relatorio(
        coletar_dados(session, sessao_id, questionario_v1), emissao_cliente
    )
    assert "7,7 meses *" not in documento.texto()
    assert "7,7 meses" in documento.texto()


# --- Termo ---


def test_termo_de_ciencia(dados_roberto, emissao_cliente):
    documento = montar_relatorio(dados_roberto, emissao_cliente)
    indice = documento.blocos.index(Titulo("Termo de ciência e validação"))
    assert isinstance(documento.blocos[indice - 1], QuebraDePagina)
    termo = documento.blocos[indice:]
    assinaturas = [b for b in termo if isinstance(b, Assinatura)]
    cliente, consultor = assinaturas
    assert cliente.titulo == "Pelo cliente — Construtora Alvorada"
    assert cliente.campos == ("Nome", "Cargo", "Data", "Assinatura")
    assert cliente.valores == ()
    # O consultor vem do perfil: nome, empresa e CPF/CNPJ já preenchidos.
    assert consultor.titulo.startswith("Pelo consultor — Exemplo Consultoria em IA Ltda")
    assert consultor.campos == ("Nome", "CPF/CNPJ", "Data", "Assinatura")
    assert dict(consultor.valores) == {"Nome": "Ana Exemplo", "CPF/CNPJ": "11.222.333/0001-81"}
    avisos = [b.texto for b in termo if isinstance(b, Aviso)]
    assert any("não é proposta comercial nem contrato" in a for a in avisos)


def test_termo_sem_perfil_deixa_o_consultor_em_branco(dados_vazios, emissao_cliente):
    documento = montar_relatorio(dados_vazios, emissao_cliente)
    consultor = [b for b in documento.blocos if isinstance(b, Assinatura)][-1]
    assert consultor.titulo == "Pelo consultor"
    assert consultor.valores == ()


# --- Consultor (perfil) ---


def test_capa_mostra_o_consultor_e_o_logotipo(dados_roberto, emissao_cliente):
    capa = montar_relatorio(dados_roberto, emissao_cliente).blocos[0]
    linhas = dict(capa.linhas)
    assert linhas["Consultor"] == "Ana Exemplo · Exemplo Consultoria em IA Ltda"
    assert capa.logotipo.startswith(b"\x89PNG")


def test_demo_avisa_que_os_dados_do_consultor_sao_ficticios(dados_roberto, emissao_cliente):
    documento = montar_relatorio(dados_roberto, emissao_cliente)
    assert AVISO_CONSULTOR_FICTICIO in dict(documento.blocos[0].linhas).values()
    consultor = [b for b in documento.blocos if isinstance(b, Assinatura)][-1]
    assert "dados fictícios" in consultor.titulo


def test_sem_perfil_o_consultor_fica_a_preencher(dados_vazios, emissao_cliente):
    capa = montar_relatorio(dados_vazios, emissao_cliente).blocos[0]
    assert dict(capa.linhas)["Consultor"] == FALTA
    assert capa.logotipo is None
    assert AVISO_CONSULTOR_FICTICIO not in dict(capa.linhas).values()


# --- O que falta ---


def test_sessao_vazia_gera_relatorio_com_marcas_do_que_falta(dados_vazios, emissao_cliente):
    documento = montar_relatorio(dados_vazios, emissao_cliente)
    texto = documento.texto()
    assert len(_titulos_das_secoes(documento)) == 12
    assert texto.count(FALTA) >= 12
    assert "Padaria Sol" in texto


def test_risco_alto_sem_mitigacao_aparece_como_pendente(
    banco_roberto, questionario_v1, emissao_cliente
):
    session, sessao_id = banco_roberto
    primeiro = itens_da_sessao(session, Risco, sessao_id)[0]
    editar_item(session, Risco, primeiro.id, mitigacao="")
    documento = montar_relatorio(
        coletar_dados(session, sessao_id, questionario_v1), emissao_cliente
    )
    riscos = _tabela_apos(documento, "8. Matriz de riscos e mitigações")
    assert riscos.linhas[0][5] == FALTA


def test_coletar_dados_de_sessao_inexistente(banco_roberto, questionario_v1):
    session, _ = banco_roberto
    with pytest.raises(RegistroNaoEncontrado):
        coletar_dados(session, 999, questionario_v1)


@pytest.mark.parametrize(
    ("metricas", "esperado"),
    [
        ({"investimento": 200_000}, "acima de 12 meses: difícil de aprovar"),
        ({"custo_fixo_mes": 5_000}, "não se paga"),
    ],
)
def test_payback_dificil_ou_que_nao_se_paga(
    banco_roberto, questionario_v1, emissao_cliente, metricas, esperado
):
    session, sessao_id = banco_roberto
    salvar_metricas(session, sessao_id, **metricas)
    documento = montar_relatorio(
        coletar_dados(session, sessao_id, questionario_v1), emissao_cliente
    )
    assert esperado in documento.texto()


def test_secao_do_yaml_sem_montagem_e_erro_claro(dados_roberto, emissao_cliente):
    dados = dados_roberto.questionario.model_dump()
    dados["blocos"][9]["secoes_relatorio"].append({"id": "rel.nova", "titulo": "Nova"})
    questionario = type(dados_roberto.questionario).model_validate(dados)
    com_secao_nova = dataclasses.replace(dados_roberto, questionario=questionario)
    with pytest.raises(ValueError, match="rel.nova"):
        montar_relatorio(com_secao_nova, emissao_cliente)
