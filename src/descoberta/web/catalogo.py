"""Questionários disponíveis, um arquivo por versão (config/questionario_v{n}.yaml).

Cada sessão guarda a versão com que foi aberta; a tela usa sempre o questionário dessa
versão. Todos são carregados e validados quando a app liga: um YAML com erro impede a app
de subir, em vez de quebrar no meio de uma reunião.
"""

import re
from pathlib import Path

from descoberta.questionario import Questionario, carregar_questionario

_NOME_ARQUIVO = re.compile(r"questionario_v(\d+)\.yaml")


class Catalogo:
    def __init__(self, pasta: Path | str):
        self._por_versao: dict[int, Questionario] = {}
        for arquivo in sorted(Path(pasta).glob("questionario_v*.yaml")):
            casamento = _NOME_ARQUIVO.fullmatch(arquivo.name)
            if casamento is None:
                continue
            questionario = carregar_questionario(arquivo)
            versao = int(casamento.group(1))
            if questionario.versao != versao:
                raise ValueError(
                    f"{arquivo.name}: o arquivo diz versao {questionario.versao}, "
                    f"mas o nome indica a versão {versao}"
                )
            self._por_versao[versao] = questionario
        if not self._por_versao:
            raise FileNotFoundError(f"nenhum questionario_v*.yaml encontrado em {pasta}")

    @property
    def versao_mais_recente(self) -> int:
        return max(self._por_versao)

    def questionario(self, versao: int) -> Questionario:
        try:
            return self._por_versao[versao]
        except KeyError:
            raise LookupError(f"questionário da versão {versao} não encontrado") from None
