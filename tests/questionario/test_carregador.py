"""Carregamento do YAML e mensagens de erro legíveis."""

import pytest

from descoberta.questionario import Questionario, QuestionarioInvalido, carregar_questionario


def erro_ao_carregar(caminho) -> QuestionarioInvalido:
    with pytest.raises(QuestionarioInvalido) as excinfo:
        carregar_questionario(caminho)
    return excinfo.value


def test_carrega_yaml_valido(escrever_yaml, dados_minimos):
    questionario = carregar_questionario(escrever_yaml(dados_minimos))
    assert isinstance(questionario, Questionario)


def test_aceita_caminho_como_texto(escrever_yaml, dados_minimos):
    assert carregar_questionario(str(escrever_yaml(dados_minimos))).versao == 1


def test_arquivo_inexistente(tmp_path):
    erro = erro_ao_carregar(tmp_path / "nao_existe.yaml")
    assert "não encontrado" in str(erro)


def test_yaml_mal_formado_informa_linha(escrever_yaml):
    caminho = escrever_yaml("versao: 1\ntitulo: [aberto\nblocos: []\n")
    erro = erro_ao_carregar(caminho)
    assert "YAML mal formado" in str(erro)
    assert "linha" in str(erro)


@pytest.mark.parametrize("conteudo", ["", "# só comentário\n"])
def test_arquivo_vazio(escrever_yaml, conteudo):
    assert "vazio" in str(erro_ao_carregar(escrever_yaml(conteudo)))


def test_raiz_precisa_ser_mapeamento(escrever_yaml):
    assert "mapeamento" in str(erro_ao_carregar(escrever_yaml("- a\n- b\n")))


def test_mensagem_cita_arquivo_e_caminho_do_campo(escrever_yaml, dados_minimos):
    dados_minimos["blocos"][1]["perguntas"][0]["tipo"] = "obrigatorio"
    erro = erro_ao_carregar(escrever_yaml(dados_minimos, nome="meu_questionario.yaml"))
    mensagem = str(erro)
    assert "meu_questionario.yaml" in mensagem
    assert "blocos[id=bloco_2].perguntas[id=b2.o1].tipo" in mensagem
    assert "valor 'obrigatorio' inválido" in mensagem
    assert "'obrigatoria' ou 'aprofundamento'" in mensagem


def test_item_sem_id_usa_posicao_contando_de_1(escrever_yaml, dados_minimos):
    dados_minimos["blocos"][0]["referencias"] = [
        {"titulo": "Tabela", "colunas": ["A"], "linhas": [["ok"], [123]]}
    ]
    mensagem = str(erro_ao_carregar(escrever_yaml(dados_minimos)))
    assert "referencias[nº 1].linhas[nº 2][nº 1]" in mensagem


def test_campo_ausente(escrever_yaml, dados_minimos):
    del dados_minimos["blocos"][0]["titulo"]
    mensagem = str(erro_ao_carregar(escrever_yaml(dados_minimos)))
    assert "blocos[id=bloco_1].titulo: campo obrigatório ausente" in mensagem


def test_campo_desconhecido(escrever_yaml, dados_minimos):
    dados_minimos["blocos"][0]["perguntas"][0]["texo"] = "Pergunta?"
    mensagem = str(erro_ao_carregar(escrever_yaml(dados_minimos)))
    assert "perguntas[id=b1.o1].texo: campo desconhecido" in mensagem


def test_erro_de_regra_aparece_sem_prefixo_tecnico(escrever_yaml, dados_minimos):
    dados_minimos["blocos"][1]["perguntas"][0]["id"] = "b1.o1"
    mensagem = str(erro_ao_carregar(escrever_yaml(dados_minimos)))
    assert "id duplicado 'b1.o1'" in mensagem
    assert "Value error" not in mensagem


def _alterar_pergunta(campo, valor):
    def alterar(dados):
        dados["blocos"][0]["perguntas"][0][campo] = valor

    return alterar


def _alterar_bloco(campo, valor):
    def alterar(dados):
        dados["blocos"][0][campo] = valor

    return alterar


@pytest.mark.parametrize(
    ("alterar", "trecho"),
    [
        (_alterar_pergunta("texto", ""), "o texto não pode ficar vazio"),
        (_alterar_pergunta("id", "B1.O1"), "id 'B1.O1' inválido"),
        (_alterar_pergunta("texto", 42), "esperava um texto, recebeu 42"),
        (_alterar_bloco("numero", "um"), "esperava um número inteiro, recebeu 'um'"),
        (_alterar_bloco("numero", 0), "o valor deve ser no mínimo 1"),
        (_alterar_bloco("perguntas", "nenhuma"), "esperava uma lista"),
        (_alterar_pergunta("condicao", "visao"), "esperava um mapeamento"),
        (_alterar_pergunta("condicao", {"tipos_solucao": []}), "a lista não pode ficar vazia"),
        (_alterar_bloco("numero", 1.5), "valor recebido: 1.5"),
    ],
)
def test_mensagens_traduzidas(escrever_yaml, dados_minimos, alterar, trecho):
    alterar(dados_minimos)
    assert trecho in str(erro_ao_carregar(escrever_yaml(dados_minimos)))


def test_lista_todos_os_erros(escrever_yaml, dados_minimos):
    dados_minimos["blocos"][0]["perguntas"][0]["tipo"] = "x"
    del dados_minimos["encerramento"]["objetivo"]
    erro = erro_ao_carregar(escrever_yaml(dados_minimos))
    assert len(erro.erros) == 2
    assert erro.caminho.name == "questionario.yaml"
