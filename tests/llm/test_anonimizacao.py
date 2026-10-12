"""Anonimização antes do LLM: dados pessoais viram marcadores e voltam só na resposta."""

import random

import pytest

from descoberta.llm.anonimizacao import Anonimizador, Conhecido, sugerir_nomes


def _roberto() -> Anonimizador:
    return Anonimizador(
        [
            Conhecido.pessoa("Roberto", "CLIENTE"),
            Conhecido.empresa("Construtora Alvorada", "EMPRESA"),
            Conhecido.pessoa("Ana Exemplo", "CONSULTOR"),
            Conhecido.empresa("Exemplo Consultoria em IA Ltda", "EMPRESA_CONSULTOR"),
            Conhecido.literal("Campinas", "CIDADE"),
            Conhecido.pessoa("Marcos"),
            Conhecido.pessoa("Cida"),
        ]
    )


# --- Dados conhecidos da sessão ---


def test_nomes_e_empresas_conhecidos():
    a = _roberto()
    texto = "O Roberto, da Construtora Alvorada, pediu ao Marcos e à Cida um laudo."
    assert a.anonimizar(texto) == (
        "O [CLIENTE], da [EMPRESA], pediu ao [PESSOA_1] e à [PESSOA_2] um laudo."
    )


def test_maiusculas_e_acentos_nao_escapam():
    a = Anonimizador([Conhecido.pessoa("José Antônio"), Conhecido.literal("São Paulo", "CIDADE")])
    assert a.anonimizar("JOSÉ ANTÔNIO mora em sao paulo") == "[PESSOA_1] mora em [CIDADE_1]"


def test_partes_do_nome_tambem_sao_trocadas():
    a = Anonimizador([Conhecido.pessoa("Marcos Pereira da Silva")])
    texto = "Marcos Pereira da Silva assina; o Marcos decide; Silva confirma."
    assert a.anonimizar(texto) == "[PESSOA_1] assina; o [PESSOA_1] decide; [PESSOA_1] confirma."


def test_parte_do_nome_so_com_maiuscula_inicial():
    # "Rosa" é nome; "rosa" é cor.
    a = Anonimizador([Conhecido.pessoa("Maria Rosa")])
    assert a.anonimizar("A Rosa pintou a parede de rosa.") == (
        "A [PESSOA_1] pintou a parede de rosa."
    )


def test_nome_da_empresa_sem_as_palavras_genericas():
    a = _roberto()
    assert a.anonimizar("A Alvorada é uma construtora.") == "A [EMPRESA] é uma construtora."
    # "Exemplo" é parte do nome da empresa; "exemplo" minúsculo não.
    so_empresa = Anonimizador([Conhecido.empresa("Exemplo Consultoria em IA Ltda")])
    assert so_empresa.anonimizar("Por exemplo, a Exemplo Consultoria") == (
        "Por exemplo, a [EMPRESA] Consultoria"
    )
    # No demo, "Exemplo" é também sobrenome da consultora (cadastrada antes): vale o 1º.
    assert a.anonimizar("a Exemplo") == "a [CONSULTOR]"


def test_palavra_dentro_de_outra_nao_e_trocada():
    a = Anonimizador([Conhecido.pessoa("Cida")])
    assert a.anonimizar("A Cidade e a Cida") == "A Cidade e a [PESSOA_1]"


def test_marcadores_estaveis_pela_ordem_de_cadastro():
    a = _roberto()
    assert a.anonimizar("Cida") == "[PESSOA_2]"  # Marcos foi cadastrado antes
    assert a.anonimizar("Marcos") == "[PESSOA_1]"


def test_mesmo_valor_em_dois_papeis_fica_com_o_primeiro():
    a = Anonimizador(
        [Conhecido.pessoa("Roberto", "CLIENTE"), Conhecido.pessoa("Roberto", "REPRESENTANTE")]
    )
    assert a.anonimizar("Roberto assina") == "[CLIENTE] assina"


def test_valores_vazios_sao_ignorados():
    a = Anonimizador([Conhecido.pessoa(""), Conhecido.pessoa("  "), Conhecido.literal(None)])
    assert a.anonimizar("Texto sem nada") == "Texto sem nada"


# --- Dados reconhecidos pelo formato ---


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("CPF 123.456.789-09.", "CPF [CPF_1]."),
        ("CPF 12345678909", "CPF [CPF_1]"),
        ("CNPJ 11.222.333/0001-81", "CNPJ [CNPJ_1]"),
        ("CNPJ 11222333000181", "CNPJ [CNPJ_1]"),
        ("CNPJ 12.ABC.345/01DE-35", "CNPJ [CNPJ_1]"),
        ("Escreva para roberto.s+obra@construtora.com.br hoje", "Escreva para [EMAIL_1] hoje"),
        ("Ligue (11) 90000-0000", "Ligue [TELEFONE_1]"),
        ("Ligue 11 3333-4444", "Ligue [TELEFONE_1]"),
        ("Ligue +55 19 98765-4321", "Ligue [TELEFONE_1]"),
        ("Celular 98765-4321", "Celular [TELEFONE_1]"),
        ("CEP 13010-000", "CEP [CEP_1]"),
        ("Obra na Rua das Flores, 123, centro", "Obra na [ENDERECO_1], centro"),
        ("Fica na Av. Brasil nº 1500", "Fica na [ENDERECO_1]"),
        ("na Rodovia Anhanguera km 90", "na [ENDERECO_1]"),
    ],
)
def test_padroes(texto, esperado):
    assert Anonimizador([]).anonimizar(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "Investimento de R$ 20.000 e economia de R$ 3.000/mês",
        "Payback de 7,7 meses; 15 chamados × 4 h = 60 h/mês",
        "Período 2026-2027, sessão de 07/10/2026",
        "Score 12 de 18; recall ≥ 95%",
        "A obra fica na rua do cliente, a até 80 km",
    ],
)
def test_numeros_de_negocio_ficam(texto):
    assert Anonimizador([]).anonimizar(texto) == texto


def test_mesmo_documento_em_formatos_diferentes_tem_o_mesmo_marcador():
    a = Anonimizador([])
    assert a.anonimizar("11.222.333/0001-81 e 11222333000181") == "[CNPJ_1] e [CNPJ_1]"
    assert a.anonimizar("outro: 12.ABC.345/01DE-35") == "outro: [CNPJ_2]"


# --- Volta na resposta ---


def test_desfazer_devolve_os_valores():
    a = _roberto()
    enviado = a.anonimizar("O Roberto e o Marcos, da Construtora Alvorada. CPF 123.456.789-09")
    resposta = f"Resumo: {enviado}"
    desfeito = a.desfazer(resposta)
    assert desfeito.texto == (
        "Resumo: O Roberto e o Marcos, da Construtora Alvorada. CPF 123.456.789-09"
    )
    assert desfeito.desconhecidos == ()


def test_marcador_inventado_pela_resposta_fica_e_e_avisado():
    a = _roberto()
    a.anonimizar("O Roberto")
    desfeito = a.desfazer("O [CLIENTE] e o [PESSOA_9] e [EMAIL_1]")
    assert desfeito.texto == "O Roberto e o [PESSOA_9] e [EMAIL_1]"
    assert desfeito.desconhecidos == ("[PESSOA_9]", "[EMAIL_1]")


def test_colchetes_do_proprio_texto_nao_sao_marcadores():
    a = _roberto()
    texto = "2. A IA faz a triagem. [IA]\n3. O Marcos revisa. [revisão humana]"
    anonimo = a.anonimizar(texto)
    assert anonimo == "2. A IA faz a triagem. [IA]\n3. O [PESSOA_1] revisa. [revisão humana]"
    desfeito = a.desfazer(anonimo)
    assert desfeito.texto == texto
    assert desfeito.desconhecidos == ()


def test_papel_desconhecido_vira_dado():
    a = Anonimizador([Conhecido.literal("segredo", "outro papel")])
    assert a.anonimizar("um segredo") == "um [DADO_1]"


def test_parte_do_nome_volta_como_foi_cadastrada():
    a = Anonimizador([Conhecido.pessoa("Marcos Pereira")])
    a.anonimizar("o Marcos")
    assert a.desfazer("[PESSOA_1] decide").texto == "Marcos Pereira decide"


def test_substituicoes_para_a_previa():
    a = _roberto()
    a.anonimizar("Roberto, roberto@example.com")
    assert a.substituicoes["[CLIENTE]"] == "Roberto"
    assert a.substituicoes["[EMAIL_1]"] == "roberto@example.com"


def test_restantes_encontra_o_que_escapou():
    a = _roberto()
    assert a.restantes(a.anonimizar("Roberto, (11) 90000-0000, Marcos")) == []
    assert a.restantes("Texto com Marcos e (11) 90000-0000") == ["Marcos", "(11) 90000-0000"]


# --- Casos gerados (nenhum dado sobra) ---


def _cpf(rng):
    d = "".join(str(rng.randint(0, 9)) for _ in range(11))
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def _telefone(rng):
    return f"({rng.randint(11, 99)}) 9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"


def _email(rng):
    nome = "".join(rng.choice("abcdefghij") for _ in range(6))
    return f"{nome}.{rng.randint(1, 99)}@empresa{rng.randint(1, 9)}.com.br"


@pytest.mark.parametrize("semente", range(25))
def test_casos_gerados_nao_deixam_dados(semente):
    rng = random.Random(semente)
    cpf, telefone, email = _cpf(rng), _telefone(rng), _email(rng)
    texto = f"Contato: {email}; tel. {telefone}; CPF {cpf}. Investimento R$ 20.000."
    a = Anonimizador([])
    anonimo = a.anonimizar(texto)
    for dado in (cpf, telefone, email):
        assert dado not in anonimo
    assert "R$ 20.000" in anonimo
    assert a.restantes(anonimo) == []
    assert a.desfazer(anonimo).texto == texto


# --- Sugestão de nomes para a lista de pessoas citadas ---


def test_sugere_nomes_no_meio_da_frase():
    textos = [
        "O chamado chega pela recepção (a Cida anota num caderno) ou pelo WhatsApp.",
        "Só o Marcos, único engenheiro. Marcos decide; o laudo vai em Word.",
        "O Roberto decide sobre o investimento com a Ana Paula.",
        "Casos graves: laudo. Na dúvida, o caso vai como grave.",
    ]
    assert sugerir_nomes(textos, ignorar=["Roberto"]) == ["Cida", "Marcos", "Ana Paula"]


def test_sugestao_ignora_siglas_e_ferramentas():
    textos = [
        "Sem ERP, só a planilha do Excel e o Google Drive; ART do engenheiro e LGPD.",
        "O consultor entrega o Relatório de Descoberta e a Proposta.",
    ]
    assert sugerir_nomes(textos) == []
