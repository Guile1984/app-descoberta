"""Montagem da Proposta Comercial (sem gerar arquivos) e emissão com hash."""

import dataclasses
from datetime import UTC, datetime

import pytest

from descoberta.relatorio import (
    EmissaoProposta,
    emitir_proposta,
    exportar_docx,
    exportar_markdown,
    exportar_pdf,
    montar_proposta,
)
from descoberta.relatorio.consultor import AVISO_CONSULTOR_FICTICIO
from descoberta.relatorio.dados_proposta import RelatorioReferido
from descoberta.relatorio.documento import (
    FALTA,
    Assinatura,
    Aviso,
    Capa,
    Lista,
    Paragrafo,
    Tabela,
    Titulo,
)

EMITIDO_EM = datetime(2026, 10, 11, 17, 5, tzinfo=UTC)
ANEXO = "Anexo — Condições Gerais"

SECOES = [
    "1. Identificação das partes",
    "2. Contexto",
    "3. Escopo por fase",
    "4. Entregáveis e cronograma",
    "5. Investimento",
    "6. Condições de pagamento, impostos e reajuste",
    "7. Premissas e hipóteses",
    "8. Responsabilidades do cliente",
    "9. Critério de aceite",
    "10. Validade",
    "11. Aceite",
]


def _depois(documento, titulo: str, tipo=Tabela):
    indice = next(
        i for i, b in enumerate(documento.blocos) if isinstance(b, Titulo) and b.texto == titulo
    )
    return next(b for b in documento.blocos[indice + 1 :] if isinstance(b, tipo))


def _secao(documento, titulo: str) -> list:
    """Os blocos da seção, até o próximo título de nível 1."""
    blocos = documento.blocos
    inicio = next(i for i, b in enumerate(blocos) if isinstance(b, Titulo) and b.texto == titulo)
    fim = next(
        (
            i
            for i, b in enumerate(blocos[inicio + 1 :], start=inicio + 1)
            if isinstance(b, Titulo) and b.nivel == 1
        ),
        len(blocos),
    )
    return blocos[inicio + 1 : fim]


def test_secoes_na_ordem(dados_proposta_roberto, emissao_proposta):
    documento = montar_proposta(dados_proposta_roberto, emissao_proposta)
    assert documento.titulos(1)[: len(SECOES)] == SECOES
    assert documento.titulo == "Proposta Comercial — Construtora Alvorada"


def test_capa(dados_proposta_roberto, emissao_proposta):
    capa = montar_proposta(dados_proposta_roberto, emissao_proposta).blocos[0]
    assert isinstance(capa, Capa)
    assert (capa.titulo, capa.subtitulo) == ("Proposta Comercial", "Construtora Alvorada")
    linhas = dict(capa.linhas)
    assert linhas["Consultor"] == "Ana Exemplo · Exemplo Consultoria em IA Ltda"
    assert linhas["Atenção"] == AVISO_CONSULTOR_FICTICIO
    assert linhas["Validade"] == "até 26/10/2026 (15 dias)"
    assert linhas["Referência"] == (
        "Relatório de Descoberta da sessão de 07/10/2026 (ainda sem versão registrada)"
    )
    assert capa.logotipo is not None


def test_capa_cita_a_versao_registrada_do_relatorio(dados_proposta_roberto, emissao_proposta):
    referido = RelatorioReferido(2, EMITIDO_EM, "abcdef0123456789" * 4)
    dados = dataclasses.replace(dados_proposta_roberto, relatorio_registrado=referido)
    capa = montar_proposta(dados, emissao_proposta).blocos[0]
    assert dict(capa.linhas)["Referência"] == (
        "Relatório de Descoberta da sessão de 07/10/2026, versão 2, hash abcdef012345"
    )


def test_identificacao_das_partes(dados_proposta_roberto, emissao_proposta):
    documento = montar_proposta(dados_proposta_roberto, emissao_proposta)
    partes = {linha[0]: linha[1:] for linha in _depois(documento, SECOES[0]).linhas}
    assert partes["Nome ou razão social"] == [
        "Construtora Alvorada",
        "Exemplo Consultoria em IA Ltda",
    ]
    assert partes["CPF/CNPJ"] == ["12.ABC.345/01DE-35", "11.222.333/0001-81"]
    assert partes["Representante"] == ["Roberto (Sócio-diretor)", "Ana Exemplo"]
    assert partes["Cidade/UF"] == ["Campinas/SP", "São Paulo/SP"]


def test_contexto_com_a_frase_problema_e_a_recomendacao(dados_proposta_roberto, emissao_proposta):
    texto = montar_proposta(dados_proposta_roberto, emissao_proposta).texto()
    assert "Hoje o Marcos gasta cerca de 60 horas por mês" in texto
    assert "Seguir com fase 0 (score final 12 de 18)" in texto


def test_escopo_por_fase_e_exclusoes(dados_proposta_roberto, emissao_proposta):
    documento = montar_proposta(dados_proposta_roberto, emissao_proposta)
    assert (
        _depois(documento, "Fase 0 — preparação dos dados", Lista)
        .itens[0]
        .startswith("Diagnóstico das fontes")
    )
    assert (
        "Laudo técnico gerado automaticamente" in _depois(documento, "Fora do escopo", Lista).itens
    )
    fase_0 = _depois(documento, "Fase 0 — preparação dos dados", Lista).itens
    assert any(item.startswith("Guia de captura de fotos") for item in fase_0)
    assert any(item.startswith("Organização e rotulagem das cerca de 500 fotos") for item in fase_0)
    mvp = _depois(documento, "MVP", Lista).itens
    assert any("Triagem por foto" in item for item in mvp)
    assert not set(mvp) & set(fase_0)  # cada item numa fase só
    assert not any("rotulagem" in item or "Guia" in item for item in mvp)


def test_cronograma_e_investimento(dados_proposta_roberto, emissao_proposta):
    documento = montar_proposta(dados_proposta_roberto, emissao_proposta)
    cronograma = _depois(documento, SECOES[3])
    assert [linha[2:] for linha in cronograma.linhas] == [
        ["4 semanas", "semanas 1 a 4"],
        ["8 semanas", "semanas 5 a 12"],
    ]
    assert "• Guia de coleta de dados para a equipe" in cronograma.linhas[0][1]
    investimento = _depois(documento, SECOES[4])
    assert investimento.linhas == [
        ["Fase 0 — preparação dos dados", "R$ 6.000,00"],
        ["MVP", "R$ 14.000,00"],
        ["Total", "R$ 20.000,00"],  # o investimento da métrica, usado no payback
    ]


def test_fase_sem_valor_deixa_o_total_a_preencher(dados_proposta_roberto, emissao_proposta):
    fases = [dataclasses.replace(f, investimento=None) for f in dados_proposta_roberto.fases]
    dados = dataclasses.replace(dados_proposta_roberto, fases=fases)
    investimento = _depois(montar_proposta(dados, emissao_proposta), SECOES[4])
    assert investimento.linhas[-1] == ["Total", FALTA]


def test_condicoes_premissas_e_responsabilidades(dados_proposta_roberto, emissao_proposta):
    documento = montar_proposta(dados_proposta_roberto, emissao_proposta)
    texto = documento.texto()
    assert "Pagamento: 50% no aceite" in texto
    assert "IPCA" in texto
    premissas = _depois(documento, SECOES[6], Lista).itens
    assert any(p.startswith("Custo da hora: R$ 100,00 (hipótese") for p in premissas)
    responsabilidades = _depois(documento, SECOES[7], Lista).itens
    assert "Enviar a amostra com os 40 casos graves (fotos + laudo)" in responsabilidades


def test_criterio_de_aceite_com_indicadores_e_tabela_do_questionario(
    dados_proposta_roberto, emissao_proposta
):
    documento = montar_proposta(dados_proposta_roberto, emissao_proposta)
    secao = _secao(documento, SECOES[8])
    paragrafos = [b for b in secao if isinstance(b, Paragrafo)]
    tabelas = [b for b in secao if isinstance(b, Tabela)]
    aceite, negocio = paragrafos[:2]
    tecnicas, metas_de_negocio, fases = tabelas

    # Aceite das entregas: pelo que foi entregue; no MVP, a meta técnica e o piloto.
    assert aceite.rotulo == "Aceite das entregas:"
    assert "pelo que foi entregue" in aceite.texto
    assert "teste com dados históricos" in aceite.texto
    assert "piloto assistido" in aceite.texto
    assert tecnicas.colunas == ["Meta técnica", "Meta", "Prazo", "Como medir"]
    assert [linha[:2] for linha in tecnicas.linhas] == [["Recall de fissuras graves", "≥ 95%"]]

    # Metas de negócio: acompanhadas, nunca condição de aceite ou de pagamento.
    assert negocio.rotulo == "Metas de negócio:"
    assert "Não são condição de aceite nem de pagamento" in negocio.texto
    assert [linha[:2] for linha in metas_de_negocio.linhas] == [
        ["Horas do Marcos com chamados de fissura", "30 h/mês"],
        ["Prazo de resposta ao cliente", "1 dia"],
    ]
    assert fases.linhas[0][0] == "1. Teste com dados históricos"
    assert "Cada entrega é aceita quando atinge as metas" not in documento.texto()


def test_criterio_de_aceite_sem_indicadores(dados_proposta_roberto, emissao_proposta):
    relatorio = dataclasses.replace(dados_proposta_roberto.relatorio, indicadores=[])
    dados = dataclasses.replace(dados_proposta_roberto, relatorio=relatorio)
    secao = _secao(montar_proposta(dados, emissao_proposta), SECOES[8])
    assert sum(isinstance(b, Aviso) and b.texto == FALTA for b in secao) == 2


def test_validade(dados_proposta_roberto, emissao_proposta):
    texto = _depois(
        montar_proposta(dados_proposta_roberto, emissao_proposta), SECOES[9], Paragrafo
    ).texto
    assert "válida por 15 dias, até 26/10/2026" in texto


def test_aceite_com_as_duas_assinaturas(dados_proposta_roberto, emissao_proposta):
    documento = montar_proposta(dados_proposta_roberto, emissao_proposta)
    cliente, consultor = [b for b in documento.blocos if isinstance(b, Assinatura)]
    assert cliente.titulo == "Pelo contratante — Construtora Alvorada"
    assert dict(cliente.valores) == {"Nome": "Roberto", "Cargo": "Sócio-diretor"}
    assert dict(consultor.valores)["CPF/CNPJ"] == "11.222.333/0001-81"


def test_proposta_nao_traz_o_aviso_juridico_do_modelo(dados_proposta_roberto, emissao_proposta):
    """O aviso "revise com um advogado" é para o consultor, na tela; não vai ao cliente."""
    texto = montar_proposta(dados_proposta_roberto, emissao_proposta).texto()
    assert "advogado" not in texto


# --- Emissão ---


def test_rodape_do_rascunho_e_da_versao(dados_proposta_roberto, emissao_proposta):
    rascunho = emitir_proposta(dados_proposta_roberto, emissao_proposta)
    assert rascunho.rodape.startswith("Proposta · Rascunho não registrado, gerado em ")
    assert rascunho.rodape.endswith(f"hash {rascunho.hash_conteudo[:12]}")
    versao = emitir_proposta(dados_proposta_roberto, EmissaoProposta(3, EMITIDO_EM))
    assert "Proposta · Versão 3, emitida em 11/10/2026" in versao.rodape
    assert versao.hash_conteudo != rascunho.hash_conteudo


@pytest.mark.parametrize("exportar", [exportar_markdown, exportar_pdf, exportar_docx])
def test_exporta_nos_tres_formatos(dados_proposta_roberto, emissao_proposta, exportar):
    assert exportar(emitir_proposta(dados_proposta_roberto, emissao_proposta))


# --- Condições Gerais (anexo) ---


def _anexo(documento):
    indice = documento.blocos.index(Titulo(ANEXO))
    return documento.blocos[indice:]


def test_condicoes_gerais_no_anexo_final(dados_proposta_roberto, emissao_proposta):
    documento = montar_proposta(dados_proposta_roberto, emissao_proposta)
    assert documento.titulos(1)[-1] == ANEXO
    anexo = _anexo(documento)
    titulos = [b.texto for b in anexo if isinstance(b, Titulo) and b.nivel == 2]
    assert titulos[0] == "1. Alterações de escopo"
    assert titulos[-1] == "9. Contrato detalhado"
    # O aceite (com as assinaturas) vem antes e diz que o anexo faz parte da proposta.
    assert any(
        isinstance(b, Assinatura) for b in documento.blocos[: documento.blocos.index(Titulo(ANEXO))]
    )
    assert "Condições Gerais" in _depois(documento, SECOES[10], Paragrafo).texto


def test_marcadores_preenchidos(dados_proposta_roberto, emissao_proposta):
    texto = "\n".join(
        b.texto
        for b in _anexo(montar_proposta(dados_proposta_roberto, emissao_proposta))
        if isinstance(b, Paragrafo)
    )
    assert "Construtora Alvorada é a controladora" in texto
    assert "Exemplo Consultoria em IA Ltda é a operadora" in texto
    assert "foro da comarca de São Paulo/SP" in texto
    assert "{" not in texto


def test_ajuste_do_demo_aparece(dados_proposta_roberto, emissao_proposta):
    texto = montar_proposta(dados_proposta_roberto, emissao_proposta).texto()
    assert "Durante 60 dias depois da entrega de cada fase" in texto


def test_clausula_excluida_some_e_a_numeracao_segue(dados_proposta_roberto, emissao_proposta):
    clausulas = [c for c in dados_proposta_roberto.clausulas if c.id != "alteracoes_escopo"]
    dados = dataclasses.replace(dados_proposta_roberto, clausulas=clausulas)
    anexo = _anexo(montar_proposta(dados, emissao_proposta))
    titulos = [b.texto for b in anexo if isinstance(b, Titulo) and b.nivel == 2]
    assert titulos[0] == "1. Confidencialidade"
    assert len(titulos) == 8


def test_sem_perfil_o_foro_fica_a_preencher(dados_proposta_roberto, emissao_proposta):
    relatorio = dataclasses.replace(dados_proposta_roberto.relatorio, consultor=None)
    dados = dataclasses.replace(dados_proposta_roberto, relatorio=relatorio)
    texto = montar_proposta(dados, emissao_proposta).texto()
    assert f"foro da comarca de {FALTA}" in texto
