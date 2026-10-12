"""Geração de um rascunho: anonimiza, envia, desfaz; falha sem gravar nada pela metade."""

import pytest

from descoberta.llm.anonimizacao import Anonimizador, Conhecido
from descoberta.llm.falso import ProvedorFalso
from descoberta.llm.prompts import Pedido
from descoberta.llm.provedor import LLMIndisponivel, Resposta
from descoberta.llm.rascunho import gerar_rascunho, previa_do_pedido

PEDIDO = Pedido("Escreva sobre a empresa.", "O Roberto, da Construtora Alvorada, e o Marcos.")


def _anonimizador():
    return Anonimizador(
        [
            Conhecido.pessoa("Roberto", "CLIENTE"),
            Conhecido.empresa("Construtora Alvorada", "EMPRESA"),
            Conhecido.pessoa("Marcos"),
        ]
    )


def test_envia_anonimizado_e_devolve_com_os_dados():
    falso = ProvedorFalso("Rascunho: o [CLIENTE] e o [PESSOA_1].", modelo="falso-1")
    rascunho = gerar_rascunho(falso, "rascunho_revisao_v1", PEDIDO, _anonimizador())
    [enviado] = falso.pedidos
    assert enviado.mensagem == "O [CLIENTE], da [EMPRESA], e o [PESSOA_1]."
    assert rascunho.texto == "Rascunho: o Roberto e o Marcos."
    assert (rascunho.provedor, rascunho.modelo) == ("falso", "falso-1")
    assert rascunho.versao_prompt == "rascunho_revisao_v1"
    assert rascunho.alertas == ()


def test_alertas_de_marcador_inventado_e_resposta_cortada():
    class Cortado(ProvedorFalso):
        def redigir(self, pedido):
            super().redigir(pedido)
            return Resposta("O [PESSOA_7] disse", "falso-1", alerta="A resposta foi cortada.")

    rascunho = gerar_rascunho(Cortado(), "p_v1", PEDIDO, _anonimizador())
    assert rascunho.texto == "O [PESSOA_7] disse"
    assert len(rascunho.alertas) == 2
    assert "[PESSOA_7]" in rascunho.alertas[0]
    assert rascunho.alertas[1] == "A resposta foi cortada."


def test_falha_do_provedor_passa_adiante():
    falso = ProvedorFalso(erro=LLMIndisponivel("Sem conexão."))
    with pytest.raises(LLMIndisponivel, match="Sem conexão"):
        gerar_rascunho(falso, "p_v1", PEDIDO, _anonimizador())


def test_conferencia_final_impede_o_envio():
    class Quebrado(Anonimizador):
        def anonimizar(self, texto):
            return texto  # um defeito que deixasse passar tudo

    falso = ProvedorFalso("x")
    with pytest.raises(LLMIndisponivel, match="não foi enviado"):
        gerar_rascunho(falso, "p_v1", PEDIDO, Quebrado([Conhecido.pessoa("Roberto")]))
    assert falso.pedidos == []


def test_previa_mostra_exatamente_o_que_sai():
    previa = previa_do_pedido(PEDIDO, _anonimizador())
    assert previa.pedido.mensagem == "O [CLIENTE], da [EMPRESA], e o [PESSOA_1]."
    assert previa.substituicoes == {
        "[CLIENTE]": "Roberto",
        "[EMPRESA]": "Construtora Alvorada",
        "[PESSOA_1]": "Marcos",
    }


@pytest.mark.parametrize(
    ("texto", "alerta"),
    [
        (" ".join(["palavra"] * 330), "cerca de 330 palavras"),
        ("Curto demais.", "cerca de 2 palavras"),
        (" ".join(["palavra"] * 200), None),
    ],
)
def test_alerta_quando_o_tamanho_sai_do_limite(texto, alerta):
    rascunho = gerar_rascunho(
        ProvedorFalso(texto), "p_v2", PEDIDO, _anonimizador(), limite_palavras=(150, 250)
    )
    if alerta is None:
        assert rascunho.alertas == ()
    else:
        [aviso] = rascunho.alertas
        assert alerta in aviso
        assert "150 a 250" in aviso


def test_contagem_ignora_marcas_de_lista():
    texto = "1. Primeiro passo aqui.\n2. Segundo passo aqui.\n- Terceiro passo aqui."
    rascunho = gerar_rascunho(
        ProvedorFalso(texto), "p_v2", PEDIDO, _anonimizador(), limite_palavras=(9, 9)
    )
    assert rascunho.alertas == ()
