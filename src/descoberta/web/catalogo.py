"""Questionários e modelos da proposta disponíveis, um arquivo por versão.

- config/questionario_v{n}.yaml: cada sessão guarda a versão com que foi aberta; a tela
  usa sempre o questionário dessa versão.
- config/proposta_v{n}.yaml: cada proposta guarda a versão do modelo com que foi criada;
  propostas novas usam a mais recente.

Tudo é carregado e validado quando a app liga: um YAML com erro impede a app de subir,
em vez de quebrar no meio de uma reunião.
"""

import re
from pathlib import Path

from descoberta.proposta import (
    ModeloProposta,
    carregar_modelo_proposta,
    problemas_com_o_questionario,
)
from descoberta.questionario import Questionario, carregar_questionario

_NOME_QUESTIONARIO = re.compile(r"questionario_v(\d+)\.yaml")
_NOME_MODELO_PROPOSTA = re.compile(r"proposta_v(\d+)\.yaml")


def _por_versao(pasta: Path, padrao: re.Pattern, carregar) -> dict:
    """Carrega os arquivos da pasta cujo nome segue o padrão, conferindo a versão."""
    carregados = {}
    for arquivo in sorted(pasta.glob("*.yaml")):
        casamento = padrao.fullmatch(arquivo.name)
        if casamento is None:
            continue
        conteudo = carregar(arquivo)
        versao = int(casamento.group(1))
        if conteudo.versao != versao:
            raise ValueError(
                f"{arquivo.name}: o arquivo diz versao {conteudo.versao}, "
                f"mas o nome indica a versão {versao}"
            )
        carregados[versao] = conteudo
    return carregados


class Catalogo:
    def __init__(self, pasta: Path | str):
        pasta = Path(pasta)
        self._por_versao: dict[int, Questionario] = _por_versao(
            pasta, _NOME_QUESTIONARIO, carregar_questionario
        )
        if not self._por_versao:
            raise FileNotFoundError(f"nenhum questionario_v*.yaml encontrado em {pasta}")
        self._modelos_proposta: dict[int, ModeloProposta] = _por_versao(
            pasta, _NOME_MODELO_PROPOSTA, carregar_modelo_proposta
        )
        self._pasta = pasta
        # Um modelo de proposta pode ser usado com sessões de qualquer questionário.
        problemas = [
            f"proposta_v{v}.yaml × questionario_v{q}.yaml: {problema}"
            for v, modelo in self._modelos_proposta.items()
            for q, questionario in self._por_versao.items()
            for problema in problemas_com_o_questionario(modelo, questionario)
        ]
        if problemas:
            raise ValueError("Modelo da proposta inválido:\n  - " + "\n  - ".join(problemas))

    @property
    def versao_mais_recente(self) -> int:
        return max(self._por_versao)

    def questionario(self, versao: int) -> Questionario:
        try:
            return self._por_versao[versao]
        except KeyError:
            raise LookupError(f"questionário da versão {versao} não encontrado") from None

    @property
    def versao_modelo_proposta(self) -> int:
        """Versão mais recente do modelo da proposta (0 se não houver nenhum)."""
        return max(self._modelos_proposta, default=0)

    def modelo_proposta(self, versao: int) -> ModeloProposta:
        try:
            return self._modelos_proposta[versao]
        except KeyError:
            raise LookupError(
                f"modelo da proposta da versão {versao} não encontrado "
                f"(config/proposta_v{versao}.yaml em {self._pasta})"
            ) from None
