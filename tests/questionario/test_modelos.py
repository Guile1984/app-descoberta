"""Regras de validação dos modelos Pydantic do questionário."""

import pytest
from pydantic import ValidationError

from descoberta.questionario import Questionario


def validar(dados: dict) -> Questionario:
    return Questionario.model_validate(dados)


def erro_de(dados: dict) -> str:
    with pytest.raises(ValidationError) as excinfo:
        validar(dados)
    return str(excinfo.value)


def test_questionario_minimo_e_valido(dados_minimos):
    questionario = validar(dados_minimos)
    assert questionario.versao == 1
    assert [bloco.numero for bloco in questionario.blocos] == [1, 2, 3, 4]


def test_modelos_sao_imutaveis(dados_minimos):
    questionario = validar(dados_minimos)
    with pytest.raises(ValidationError):
        questionario.versao = 2


def test_campo_desconhecido_gera_erro(dados_minimos):
    pergunta = dados_minimos["blocos"][0]["perguntas"][0]
    pergunta["texo"] = pergunta.pop("texto")
    mensagem = erro_de(dados_minimos)
    assert "texo" in mensagem
    assert "texto" in mensagem  # o campo certo também aparece, como ausente


def test_tipo_de_pergunta_invalido(dados_minimos):
    dados_minimos["blocos"][0]["perguntas"][0]["tipo"] = "obrigatorio"
    assert "obrigatorio" in erro_de(dados_minimos)


@pytest.mark.parametrize("texto", ["", "   "])
def test_texto_vazio_e_recusado(dados_minimos, texto):
    dados_minimos["blocos"][0]["perguntas"][0]["texto"] = texto
    erro_de(dados_minimos)


def test_id_com_espaco_e_recusado(dados_minimos):
    dados_minimos["blocos"][0]["perguntas"][0]["id"] = "b1 o1"
    erro_de(dados_minimos)


@pytest.mark.parametrize("numeros", [[1, 2, 4, 5], [1, 2, 2, 3], [2, 3, 4, 5], [1, 3, 2, 4]])
def test_blocos_precisam_ser_numerados_em_sequencia(dados_minimos, numeros):
    for bloco, numero in zip(dados_minimos["blocos"], numeros, strict=True):
        bloco["numero"] = numero
    assert "sequência" in erro_de(dados_minimos)


def test_ids_de_perguntas_duplicados(dados_minimos):
    dados_minimos["blocos"][1]["perguntas"][0]["id"] = "b1.o1"
    assert "id duplicado 'b1.o1'" in erro_de(dados_minimos)


def test_id_duplicado_entre_pergunta_e_sinal(dados_minimos):
    dados_minimos["blocos"][0]["sinais"][0]["id"] = "b1.o1"
    assert "id duplicado 'b1.o1'" in erro_de(dados_minimos)


def test_ids_de_blocos_duplicados(dados_minimos):
    dados_minimos["blocos"][1]["id"] = "bloco_1"
    assert "id duplicado 'bloco_1'" in erro_de(dados_minimos)


def test_ids_de_tipos_de_solucao_duplicados(dados_minimos):
    dados_minimos["tipos_solucao"][1]["id"] = "automacao_sem_ia"
    assert "id duplicado 'automacao_sem_ia'" in erro_de(dados_minimos)


def test_condicao_com_tipo_de_solucao_inexistente(dados_minimos):
    condicional = dados_minimos["blocos"][3]["perguntas"][2]
    condicional["condicao"]["tipos_solucao"] = ["visao_computacionall"]
    mensagem = erro_de(dados_minimos)
    assert "b4.vc1" in mensagem
    assert "visao_computacionall" in mensagem


def test_condicao_sem_tipos_e_recusada(dados_minimos):
    dados_minimos["blocos"][3]["perguntas"][2]["condicao"]["tipos_solucao"] = []
    erro_de(dados_minimos)


@pytest.mark.parametrize("indice_bloco", [0, 1, 2])
def test_condicional_so_pode_aparecer_depois_do_bloco_3(dados_minimos, indice_bloco):
    pergunta = dados_minimos["blocos"][indice_bloco]["perguntas"][0]
    pergunta["condicao"] = {"tipos_solucao": ["visao_computacional"]}
    mensagem = erro_de(dados_minimos)
    assert pergunta["id"] in mensagem
    assert "depois do bloco 3" in mensagem


@pytest.mark.parametrize(
    ("faixas", "trecho"),
    [
        ([(0, 1), (3, 3)], "lacuna"),
        ([(0, 2), (2, 3)], "sobrep"),
        ([(0, 1), (2, 2)], "máximo 3"),
        ([(1, 1), (2, 3)], "começar em 0"),
        ([(0, 4)], "máximo 3"),
    ],
)
def test_faixas_precisam_cobrir_de_0_ao_maximo(dados_minimos, faixas, trecho):
    dados_minimos["scores"]["prontidao_dados"]["faixas"] = [
        {"id": f"f{i}", "rotulo": "Faixa", "min": minimo, "max": maximo}
        for i, (minimo, maximo) in enumerate(faixas)
    ]
    mensagem = erro_de(dados_minimos)
    assert "prontidao_dados" in mensagem
    assert trecho in mensagem


def test_faixa_com_min_maior_que_max(dados_minimos):
    dados_minimos["scores"]["viabilidade_final"]["faixas"][0].update({"min": 1, "max": 0})
    assert "min" in erro_de(dados_minimos)


def test_ids_de_faixas_duplicados_no_mesmo_score(dados_minimos):
    dados_minimos["scores"]["prontidao_dados"]["faixas"][1]["id"] = "baixo"
    assert "id de faixa duplicado 'baixo'" in erro_de(dados_minimos)


def test_maximo_do_score_acompanha_numero_de_criterios(dados_minimos):
    score = dados_minimos["scores"]["viabilidade_final"]
    score["criterios"].append({"id": "riscos", "rotulo": "Riscos", "blocos_origem": [2]})
    # Com 2 critérios o máximo passa a 6, e as faixas atuais (até 3) não cobrem mais.
    assert "máximo 6" in erro_de(dados_minimos)
    score["faixas"][1]["max"] = 6
    assert validar(dados_minimos).scores.viabilidade_final.pontuacao_maxima == 6


def test_criterio_de_viabilidade_com_bloco_de_origem_inexistente(dados_minimos):
    criterio = dados_minimos["scores"]["viabilidade_final"]["criterios"][0]
    criterio["blocos_origem"] = [1, 7]
    mensagem = erro_de(dados_minimos)
    assert "dor_clara" in mensagem
    assert "7" in mensagem


def test_referencia_com_linha_de_tamanho_errado(dados_minimos):
    dados_minimos["blocos"][0]["referencias"] = [
        {"titulo": "Tabela", "colunas": ["A", "B"], "linhas": [["1", "2"], ["só uma"]]}
    ]
    assert "2 colunas" in erro_de(dados_minimos)


def test_sinal_nao_tem_mais_peso(dados_minimos):
    dados_minimos["blocos"][0]["sinais"][0]["peso"] = 1
    assert "peso" in erro_de(dados_minimos)


@pytest.mark.parametrize(
    ("conversao", "trecho"),
    [
        ([(0, 1, 0), (3, 3, 3)], "lacuna"),
        ([(0, 2, 0), (2, 3, 3)], "sobrep"),
        ([(0, 1, 0), (2, 2, 3)], "máximo 3"),
        ([(1, 1, 0), (2, 3, 3)], "começar em 0"),
    ],
)
def test_conversao_para_nota_precisa_cobrir_o_score(dados_minimos, conversao, trecho):
    dados_minimos["scores"]["prontidao_dados"]["conversao_para_nota"] = [
        {"min": minimo, "max": maximo, "nota": nota} for minimo, maximo, nota in conversao
    ]
    mensagem = erro_de(dados_minimos)
    assert "conversao_para_nota" in mensagem
    assert trecho in mensagem


@pytest.mark.parametrize("nota", [-1, 4])
def test_conversao_para_nota_fora_de_0_a_3(dados_minimos, nota):
    dados_minimos["scores"]["prontidao_dados"]["conversao_para_nota"][1]["nota"] = nota
    erro_de(dados_minimos)


def test_conversao_para_nota_nao_pode_diminuir(dados_minimos):
    conversao = dados_minimos["scores"]["prontidao_dados"]["conversao_para_nota"]
    conversao[0]["nota"], conversao[1]["nota"] = 3, 0
    assert "não pode diminuir" in erro_de(dados_minimos)


def test_conversao_para_nota_e_obrigatoria(dados_minimos):
    del dados_minimos["scores"]["prontidao_dados"]["conversao_para_nota"]
    assert "conversao_para_nota" in erro_de(dados_minimos)


def test_bloco_por_numero(dados_minimos):
    questionario = validar(dados_minimos)
    assert questionario.bloco(4).id == "bloco_4"
    with pytest.raises(KeyError):
        questionario.bloco(99)


# --- Sprint 5: duração da sessão, bloco dos scores, nota derivada e encerramento ---


def test_duracao_da_sessao(dados_minimos):
    duracao = validar(dados_minimos).duracao
    assert (duracao.aviso_minutos, duracao.limite_minutos) == (75, 90)


@pytest.mark.parametrize(("aviso", "limite"), [(90, 90), (100, 90)])
def test_aviso_de_duracao_precisa_vir_antes_do_limite(dados_minimos, aviso, limite):
    dados_minimos["duracao"] = {"aviso_minutos": aviso, "limite_minutos": limite}
    assert "aviso" in erro_de(dados_minimos)


@pytest.mark.parametrize("minutos", [0, -5])
def test_duracao_precisa_ser_positiva(dados_minimos, minutos):
    dados_minimos["duracao"]["aviso_minutos"] = minutos
    erro_de(dados_minimos)


@pytest.mark.parametrize("score", ["prontidao_dados", "viabilidade_final"])
def test_score_em_bloco_inexistente(dados_minimos, score):
    dados_minimos["scores"][score]["bloco"] = 9
    mensagem = erro_de(dados_minimos)
    assert score in mensagem
    assert "9" in mensagem


def test_criterio_final_precisa_existir_no_score_de_viabilidade(dados_minimos):
    dados_minimos["scores"]["prontidao_dados"]["criterio_final"] = "prazo"
    mensagem = erro_de(dados_minimos)
    assert "criterio_final" in mensagem
    assert "prazo" in mensagem


def test_item_de_encerramento_por_id(dados_minimos):
    questionario = validar(dados_minimos)
    assert questionario.item_encerramento("enc.resumo").titulo == "Resumo"
    with pytest.raises(KeyError):
        questionario.item_encerramento("b1.o1")
