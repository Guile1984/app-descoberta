"""O que vai no pedido ao LLM: os fatos da sessão, já com os números calculados pela app."""

import dataclasses

import pytest

from descoberta.llm.anonimizacao import Anonimizador
from descoberta.llm.contexto import (
    conhecidos_da_sessao,
    contexto_da_proposta,
    contexto_da_sessao,
    pedido_da_proposta,
    pedido_da_revisao,
)


def test_numeros_vem_prontos_do_painel(dados_roberto):
    texto = contexto_da_sessao(dados_roberto)
    assert "Horas da dor por mês: 60 h" in texto
    assert "Custo da hora: R$ 100,00 (hipótese)" in texto
    assert "Payback: 7,7 meses (depende de hipótese)" in texto
    assert "Score de prontidão de dados: 4 de 15 — " in texto
    assert "Score final de viabilidade: 12 de 18 — Seguir com fase 0" in texto
    assert "Investimento: R$ 20.000,00" in texto


def test_respostas_anotacoes_e_saidas_da_revisao(dados_roberto):
    texto = contexto_da_sessao(dados_roberto)
    assert "Não há padrão de distância, luz ou ângulo." in texto  # b4.vc2
    assert "Pedir uma amostra com os 40 casos graves" in texto  # anotação
    assert "Uma fissura grave classificada como simples pela IA." in texto  # risco
    assert "Recall de fissuras graves" in texto  # indicador
    assert "Fica de fora: Laudo técnico gerado automaticamente" in texto
    assert "Enviar a amostra com os 40 casos graves (fotos + laudo) (cliente)" in texto
    assert "Bloco 4 — " in texto


def test_sinais_de_alerta_pelo_texto(dados_roberto, questionario_v1):
    sinal = next(s for b in questionario_v1.blocos for s in b.sinais if s.id == "b1.s4")
    assert sinal.texto in contexto_da_sessao(dados_roberto)


def test_respostas_de_condicionais_ocultas_ficam_de_fora(dados_roberto, questionario_v1):
    outro = next(t.id for t in questionario_v1.tipos_solucao if t.id != "visao_computacional")
    texto = contexto_da_sessao(dataclasses.replace(dados_roberto, tipo_solucao=outro))
    assert "Não há padrão de distância, luz ou ângulo." not in texto


def test_texto_do_alvo_nao_entra_nos_outros_textos(dados_roberto):
    frase = dados_roberto.textos["frase_problema"]
    assert frase in contexto_da_sessao(dados_roberto)
    assert frase not in contexto_da_sessao(dados_roberto, sem_o_texto="frase_problema")


def test_pedido_da_revisao(prompts, dados_roberto):
    pedido = pedido_da_revisao(prompts["rascunho_revisao"], dados_roberto, "frase_problema")
    assert 'a seção "Frase-problema"' in pedido.mensagem
    assert "O sucesso será" in pedido.mensagem  # orientação do YAML
    assert dados_roberto.textos["frase_problema"] in pedido.mensagem  # texto atual
    assert "Horas da dor por mês: 60 h" in pedido.mensagem
    assert "{{" not in pedido.mensagem


def test_pedido_da_revisao_sem_texto_atual(prompts, dados_roberto):
    dados = dataclasses.replace(dados_roberto, textos={})
    pedido = pedido_da_revisao(prompts["rascunho_revisao"], dados, "recomendacao")
    assert "(vazio)" in pedido.mensagem


def test_texto_de_revisao_desconhecido(prompts, dados_roberto):
    with pytest.raises(KeyError):
        pedido_da_revisao(prompts["rascunho_revisao"], dados_roberto, "nao_existe")


def test_contexto_da_proposta(proposta_roberto):
    texto = contexto_da_proposta(proposta_roberto)
    assert "Fase 0 — preparação dos dados: 4 semanas, R$ 6.000,00" in texto
    assert "Guia de captura de fotos" in texto
    assert "Fora do escopo: Laudo técnico gerado automaticamente" in texto
    assert "Total: R$ 20.000,00" in texto


def test_pedido_do_contexto_da_proposta(prompts, proposta_roberto):
    pedido = pedido_da_proposta(prompts["rascunho_proposta"], proposta_roberto, "contexto")
    assert "o texto de contexto que abre a proposta" in pedido.mensagem
    assert "Sem preços nem prazos" in pedido.mensagem
    assert "Score final de viabilidade: 12 de 18" in pedido.mensagem


def test_pedido_do_objetivo_da_fase(prompts, proposta_roberto):
    pedido = pedido_da_proposta(
        prompts["rascunho_proposta"], proposta_roberto, "objetivo_fase", fase=1, texto_atual=""
    )
    assert 'o objetivo da fase "MVP"' in pedido.mensagem
    assert "(vazio)" in pedido.mensagem


@pytest.mark.parametrize(
    ("alvo", "fase"), [("objetivo_fase", None), ("objetivo_fase", 9), ("outro", None)]
)
def test_alvo_da_proposta_invalido(prompts, proposta_roberto, alvo, fase):
    with pytest.raises(ValueError, match="alvo|fase"):
        pedido_da_proposta(prompts["rascunho_proposta"], proposta_roberto, alvo, fase=fase)


# --- Quem é conhecido para a anonimização ---


def test_conhecidos_do_caso_roberto(dados_roberto, proposta_roberto):
    conhecidos = conhecidos_da_sessao(dados_roberto, proposta_roberto, ["Marcos", "Cida"])
    por_papel = {(c.papel, c.valor) for c in conhecidos}
    assert ("CLIENTE", "Roberto") in por_papel
    assert ("EMPRESA", "Construtora Alvorada") in por_papel
    assert ("CONSULTOR", "Ana Exemplo") in por_papel
    assert ("EMPRESA_CONSULTOR", "Exemplo Consultoria em IA Ltda") in por_papel
    assert ("EMAIL", "ana@example.com") in por_papel
    assert ("EMAIL", "roberto@example.com") in por_papel
    assert ("CNPJ", "11.222.333/0001-81") in por_papel
    assert ("CNPJ", "12.ABC.345/01DE-35") in por_papel
    assert ("TELEFONE", "(11) 90000-0000") in por_papel
    assert ("CIDADE", "Campinas") in por_papel
    assert ("CIDADE", "São Paulo") in por_papel
    assert ("PESSOA", "Marcos") in por_papel
    assert ("PESSOA", "Cida") in por_papel


def test_sem_perfil_e_sem_proposta(dados_roberto):
    dados = dataclasses.replace(dados_roberto, consultor=None)
    papeis = {c.papel for c in conhecidos_da_sessao(dados, None, [])}
    assert papeis == {"CLIENTE", "EMPRESA"}


def test_contexto_anonimizado_do_roberto_nao_tem_nomes(dados_roberto, proposta_roberto):
    a = Anonimizador(conhecidos_da_sessao(dados_roberto, proposta_roberto, ["Marcos", "Cida"]))
    texto = a.anonimizar(
        contexto_da_sessao(dados_roberto) + "\n" + contexto_da_proposta(proposta_roberto)
    )
    for nome in ("Roberto", "Alvorada", "Marcos", "Cida", "Campinas"):
        assert nome not in texto
    assert a.restantes(texto) == []
