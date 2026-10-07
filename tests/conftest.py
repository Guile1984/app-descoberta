"""Fixtures compartilhadas por todos os testes."""

from pathlib import Path

import pytest

from descoberta.questionario import Questionario, carregar_questionario

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
CAMINHO_QUESTIONARIO_V1 = RAIZ_PROJETO / "config" / "questionario_v1.yaml"


@pytest.fixture(scope="session")
def questionario_v1() -> Questionario:
    return carregar_questionario(CAMINHO_QUESTIONARIO_V1)
