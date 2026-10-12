"""Contagem de palavras dos rascunhos, alinhada com a do Word: tudo o que fica entre
espaços conta como palavra (números, valores como "R$ 6.000,00", siglas, "1." digitado).

Caso de referência: o resumo executivo do caso Roberto gerado pela API real com o prompt
rascunho_revisao_v2 (12/10/2026), copiado do banco de demonstração. No Word: 268 palavras.
A contagem antiga ignorava números e dava 249, dentro do limite de 150 a 250: o alerta não
apareceu.
"""

import pytest

from descoberta.llm.anonimizacao import Anonimizador
from descoberta.llm.falso import ProvedorFalso
from descoberta.llm.prompts import Pedido
from descoberta.llm.rascunho import contar_palavras, gerar_rascunho

RESUMO_EXECUTIVO_ROBERTO_V2 = (
    "Os chamados de fissura tomam cerca de 60 h por mês do Marcos, único engenheiro da "
    "Construtora Alvorada: são cerca de 15 chamados por mês, de 4 h cada. O cliente "
    "espera 3 dias pela resposta, e já houve um processo judicial. Com a hora estimada em"
    " R$ 100,00, essa dor custa R$ 6.000,00 por mês. O valor da hora é uma estimativa a "
    "confirmar.\n\n"
    "A solução proposta é uma triagem por foto, com visão computacional. O mestre de obra"
    " fotografa a fissura seguindo um guia de captura, e a IA indica se o caso parece "
    "grave ou simples. A decisão final é sempre do Marcos, que revisa todos os casos e "
    "assina os laudos. As metas são reduzir essas horas para 30 h por mês e responder ao "
    "cliente em 1 dia.\n\n"
    "Pelas estimativas, ainda a confirmar, a economia é de R$ 3.000,00 por mês e o custo "
    "de operação, de R$ 400,00 por mês. Com um investimento de R$ 20.000,00, o payback "
    "fica em 7,7 meses.\n\n"
    "O ponto fraco são os dados, com score de prontidão de 4 de 15. As fotos não têm "
    "padrão de distância, luz ou ângulo, e só cerca de 40 casos têm laudo. Também é "
    "preciso cuidar da LGPD, porque as fotos mostram pessoas e o interior das casas.\n\n"
    "O score final de viabilidade é de 12 de 18. A recomendação é seguir com a fase 0, "
    "que padroniza a captura das fotos, organiza e rotula o histórico com o critério do "
    "Marcos e mede a qualidade dos dados. Quando o score de dados chegar a 6, o MVP pode "
    "começar."
)


def test_caso_de_referencia_conta_como_o_word():
    assert contar_palavras(RESUMO_EXECUTIVO_ROBERTO_V2) == 268


def test_caso_de_referencia_passa_do_limite_e_gera_o_alerta():
    rascunho = gerar_rascunho(
        ProvedorFalso(RESUMO_EXECUTIVO_ROBERTO_V2),
        "rascunho_revisao_v2",
        Pedido("Instruções.", "Pedido."),
        Anonimizador([]),
        limite_palavras=(150, 250),
    )
    [alerta] = rascunho.alertas
    assert "cerca de 268 palavras" in alerta
    assert "150 a 250" in alerta


@pytest.mark.parametrize(
    ("texto", "palavras"),
    [
        ("R$ 3.000,00 por mês", 4),  # "R$" e o valor contam, como no Word
        ("payback de 7,7 meses", 4),
        ("score 12 de 18.", 4),
        ("fase 0, que padroniza", 4),
        ("60 h/mês", 2),
        ("1. Primeiro passo\n2. Segundo passo", 6),  # "1." digitado conta, como no Word
        ("a — b", 3),  # travessão solto também é uma "palavra" para o Word
        ("  várias   linhas\n\n e espaços  ", 4),
        ("", 0),
    ],
)
def test_regra_da_contagem(texto, palavras):
    assert contar_palavras(texto) == palavras
