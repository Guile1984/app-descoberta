"""Catálogo de questionários por versão, carregado quando a app liga."""

import shutil
from pathlib import Path

import pytest
import yaml

from descoberta.web.catalogo import Catalogo

QUESTIONARIO_V1 = Path(__file__).resolve().parents[2] / "config" / "questionario_v1.yaml"


def _copiar_como(pasta: Path, versao_no_nome: int, versao_no_arquivo: int) -> None:
    dados = yaml.safe_load(QUESTIONARIO_V1.read_text(encoding="utf-8"))
    dados["versao"] = versao_no_arquivo
    destino = pasta / f"questionario_v{versao_no_nome}.yaml"
    destino.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")


def test_versao_mais_recente_e_questionario_por_versao(tmp_path):
    shutil.copy(QUESTIONARIO_V1, tmp_path)
    _copiar_como(tmp_path, 2, 2)
    (tmp_path / "questionario_v2_rascunho.yaml").write_text("não é questionário", "utf-8")
    catalogo = Catalogo(tmp_path)
    assert catalogo.versao_mais_recente == 2
    assert catalogo.questionario(1).versao == 1


def test_versao_inexistente(tmp_path):
    shutil.copy(QUESTIONARIO_V1, tmp_path)
    with pytest.raises(LookupError, match="versão 7"):
        Catalogo(tmp_path).questionario(7)


def test_nome_e_conteudo_com_versoes_diferentes(tmp_path):
    _copiar_como(tmp_path, 2, 1)
    with pytest.raises(ValueError, match="versao 1"):
        Catalogo(tmp_path)


def test_pasta_sem_questionario(tmp_path):
    with pytest.raises(FileNotFoundError):
        Catalogo(tmp_path)
