"""Modelo da Proposta Comercial (config/proposta_v*.yaml): forma e conferências."""

import copy
from pathlib import Path

import pytest
import yaml

from descoberta.proposta import (
    ModeloProposta,
    ModeloPropostaInvalido,
    carregar_modelo_proposta,
    problemas_com_o_questionario,
)

RAIZ = Path(__file__).resolve().parents[2]
MODELO_V1 = RAIZ / "config" / "proposta_v1.yaml"


@pytest.fixture
def dados_v1() -> dict:
    return yaml.safe_load(MODELO_V1.read_text(encoding="utf-8"))


@pytest.fixture
def escrever(tmp_path):
    def escrever(dados: dict) -> Path:
        caminho = tmp_path / "proposta_v1.yaml"
        caminho.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
        return caminho

    return escrever


def test_modelo_v1_carrega(questionario_v1):
    modelo = carregar_modelo_proposta(MODELO_V1)
    assert isinstance(modelo, ModeloProposta)
    assert modelo.versao == 1
    assert "advogado" in modelo.aviso
    assert [f.nome for f in modelo.padrao.fases] == ["Fase 0 — preparação dos dados", "MVP"]
    assert problemas_com_o_questionario(modelo, questionario_v1) == []


def test_so_uma_fase_recebe_o_escopo_e_o_investimento_da_sessao(dados_v1, escrever):
    dados = copy.deepcopy(dados_v1)
    dados["padrao"]["fases"][0]["escopo_da_revisao"] = True
    with pytest.raises(ModeloPropostaInvalido, match="escopo_da_revisao"):
        carregar_modelo_proposta(escrever(dados))


def test_campo_desconhecido(dados_v1, escrever):
    dados = copy.deepcopy(dados_v1)
    dados["padrao"]["validade"] = 10
    with pytest.raises(ModeloPropostaInvalido, match="campo desconhecido"):
        carregar_modelo_proposta(escrever(dados))


def test_aviso_obrigatorio(dados_v1, escrever):
    dados = copy.deepcopy(dados_v1)
    del dados["aviso"]
    with pytest.raises(ModeloPropostaInvalido, match="aviso"):
        carregar_modelo_proposta(escrever(dados))


def test_faixas_e_tabela_conferidas_com_o_questionario(dados_v1, questionario_v1):
    dados = copy.deepcopy(dados_v1)
    dados["alerta_score_final"] = ["nao_existe"]
    dados["padrao"]["fases"][0]["faixas_score_final"] = ["outra"]
    dados["criterio_de_aceite"]["tabela"] = "Tabela que não existe"
    problemas = problemas_com_o_questionario(ModeloProposta.model_validate(dados), questionario_v1)
    assert len(problemas) == 3
    assert any("nao_existe" in p for p in problemas)
    assert any("outra" in p for p in problemas)
    assert any("Tabela que não existe" in p for p in problemas)


# --- Cláusulas (Condições Gerais) ---

NAO_REMOVIVEIS = {
    "foro",
    "prevalencia_contrato",
    "confidencialidade",
    "lgpd",
    "limitacao_responsabilidade",
}


def test_clausulas_do_modelo_v1():
    modelo = carregar_modelo_proposta(MODELO_V1)
    ids = [c.id for c in modelo.clausulas]
    assert ids == [
        "alteracoes_escopo",
        "confidencialidade",
        "propriedade_intelectual",
        "lgpd",
        "limitacao_responsabilidade",
        "suporte_garantia",
        "cancelamento",
        "foro",
        "prevalencia_contrato",
    ]
    assert {c.id for c in modelo.clausulas if not c.removivel} == NAO_REMOVIVEIS
    lgpd = modelo.clausula("lgpd")
    assert "controladora" in lgpd.texto
    assert "operadora" in lgpd.texto
    assert "prevalece o contrato" in modelo.clausula("prevalencia_contrato").texto
    assert "{foro}" in modelo.clausula("foro").texto


def test_clausula_inexistente():
    with pytest.raises(KeyError, match="xyz"):
        carregar_modelo_proposta(MODELO_V1).clausula("xyz")


def test_marcador_desconhecido_e_recusado(dados_v1, escrever):
    dados = copy.deepcopy(dados_v1)
    dados["clausulas"][0]["texto"] = "Vale para {cliente.cnpj}."
    with pytest.raises(ModeloPropostaInvalido, match=r"cliente\.cnpj"):
        carregar_modelo_proposta(escrever(dados))


def test_ids_de_clausula_repetidos(dados_v1, escrever):
    dados = copy.deepcopy(dados_v1)
    dados["clausulas"][1]["id"] = dados["clausulas"][0]["id"]
    with pytest.raises(ModeloPropostaInvalido, match="repetido"):
        carregar_modelo_proposta(escrever(dados))


def test_removivel_e_falso_por_padrao(dados_v1, escrever):
    dados = copy.deepcopy(dados_v1)
    del dados["clausulas"][0]["removivel"]
    assert carregar_modelo_proposta(escrever(dados)).clausulas[0].removivel is False
