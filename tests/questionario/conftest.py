"""Fixtures compartilhadas pelos testes do questionário."""

import copy
from pathlib import Path

import pytest
import yaml


def _bloco(numero: int, perguntas: list[dict] | None = None) -> dict:
    return {
        "numero": numero,
        "id": f"bloco_{numero}",
        "titulo": f"Bloco {numero}",
        "objetivo": "Objetivo do bloco.",
        "saida_esperada": "Saída do bloco.",
        "perguntas": perguntas
        or [{"id": f"b{numero}.o1", "tipo": "obrigatoria", "texto": "Pergunta?"}],
        "sinais": [{"id": f"b{numero}.s1", "texto": "Sinal de alerta."}],
    }


def _faixas_ate_3() -> list[dict]:
    return [
        {"id": "baixo", "rotulo": "Baixo", "min": 0, "max": 1},
        {"id": "alto", "rotulo": "Alto", "min": 2, "max": 3},
    ]


# Menor questionário válido: 4 blocos, uma condicional no bloco 4 e um critério por score.
QUESTIONARIO_MINIMO = {
    "versao": 1,
    "titulo": "Questionário de teste",
    "duracao": {"aviso_minutos": 75, "limite_minutos": 90},
    "tipos_solucao": [
        {"id": "automacao_sem_ia", "rotulo": "Automação", "situacao": "Regras claras"},
        {"id": "visao_computacional", "rotulo": "Visão", "situacao": "Imagens ou vídeo"},
    ],
    "blocos": [
        _bloco(1),
        _bloco(2),
        _bloco(3),
        _bloco(
            4,
            [
                {"id": "b4.o1", "tipo": "obrigatoria", "texto": "Onde ficam os dados?"},
                {"id": "b4.a1", "tipo": "aprofundamento", "texto": "Seguem um padrão?"},
                {
                    "id": "b4.vc1",
                    "tipo": "obrigatoria",
                    "texto": "Quem tira as fotos?",
                    "condicao": {"tipos_solucao": ["visao_computacional"]},
                },
            ],
        ),
    ],
    "encerramento": {
        "objetivo": "Fechar a sessão.",
        "itens": [{"id": "enc.resumo", "titulo": "Resumo", "descricao": "A frase-problema."}],
    },
    "revisao": {
        "categorias_risco": [
            {"id": "lgpd", "rotulo": "LGPD"},
            {"id": "outro", "rotulo": "Outro"},
        ],
        "textos": [
            {
                "id": "frase_problema",
                "titulo": "Frase-problema",
                "orientacao": "Hoje [quem] gasta [quanto]…",
                "apoio": ["b1.o1", "enc.resumo"],
            }
        ],
    },
    "scores": {
        "prontidao_dados": {
            "bloco": 4,
            # No mínimo, o único critério final faz o papel da nota derivada do score de dados.
            "criterio_final": "dor_clara",
            "criterios": [
                {
                    "id": "disponibilidade",
                    "rotulo": "Disponibilidade",
                    "ancora_0": "Não existe",
                    "ancora_3": "Exportável hoje",
                }
            ],
            "faixas": _faixas_ate_3(),
            "conversao_para_nota": [
                {"min": 0, "max": 1, "nota": 0},
                {"min": 2, "max": 3, "nota": 3},
            ],
        },
        "viabilidade_final": {
            "bloco": 4,
            "criterios": [{"id": "dor_clara", "rotulo": "Dor clara", "blocos_origem": [1]}],
            "faixas": _faixas_ate_3(),
        },
    },
}


@pytest.fixture
def dados_minimos() -> dict:
    """Cópia nova do questionário mínimo, que cada teste pode alterar à vontade."""
    return copy.deepcopy(QUESTIONARIO_MINIMO)


@pytest.fixture
def escrever_yaml(tmp_path):
    """Grava um dicionário (ou texto cru) como YAML em tmp_path e devolve o caminho."""

    def escrever(conteudo: dict | str, nome: str = "questionario.yaml") -> Path:
        caminho = tmp_path / nome
        if isinstance(conteudo, str):
            texto = conteudo
        else:
            texto = yaml.safe_dump(conteudo, allow_unicode=True, sort_keys=False)
        caminho.write_text(texto, encoding="utf-8")
        return caminho

    return escrever
