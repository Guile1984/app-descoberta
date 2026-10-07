"""Fixtures compartilhadas por todos os testes."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from descoberta.questionario import Questionario, carregar_questionario

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
CAMINHO_QUESTIONARIO_V1 = RAIZ_PROJETO / "config" / "questionario_v1.yaml"


@pytest.fixture(scope="session")
def questionario_v1() -> Questionario:
    return carregar_questionario(CAMINHO_QUESTIONARIO_V1)


@dataclass(frozen=True)
class CasoRoberto:
    """Entradas brutas do caso de referência "Construtora Alvorada / Roberto".

    Hipóteses registradas (não ditas pelo cliente, assumidas pelo consultor):
    - custo da hora: R$ 100 (Modelo de Descoberta: "30 horas economizadas por mês valem
      R$ 3.000");
    - a solução economiza 30 das 60 horas mensais;
    - a operação de R$ 400/mês é custo fixo (sem cobrança por chamada).
    """

    horas_por_ocorrencia: int = 4
    frequencia_quantidade: int = 15
    frequencia_periodo: str = "mes"
    custo_hora: int = 100  # hipótese
    horas_economizadas_mes: int = 30  # hipótese
    investimento: int = 20_000
    custo_fixo_mes: int = 400
    notas_dados: dict[str, int] = field(
        default_factory=lambda: {
            "disponibilidade": 1,
            "volume": 1,
            "rotulos": 1,
            "qualidade": 0,
            "acesso_legal": 1,
        }
    )
    # Sem "prontidao_dados": essa nota é derivada do score de dados.
    notas_viabilidade: dict[str, int] = field(
        default_factory=lambda: {
            "dor_clara": 3,
            "ia_caminho_certo": 2,
            "retorno_viavel": 2,
            "riscos_controlaveis": 2,
            "comprometimento_cliente": 2,
        }
    )
    # Sinais de alerta marcados na sessão: id → trecho do texto no YAML.
    sinais_marcados: dict[str, str] = field(
        default_factory=lambda: {
            "b1.s4": "100% de acerto ou zero intervenção humana",
            "b2.s2": "concentrado em uma pessoa que não participa",
            "b2.s3": "informação que não é registrada",
            "b8.s4": "ninguém para manter a solução",
            "b9.s1": "Orçamento indefinido",
        }
    )


@pytest.fixture(scope="session")
def caso_roberto() -> CasoRoberto:
    return CasoRoberto()
