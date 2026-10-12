"""O que vai no pedido ao LLM: os fatos da sessão e da proposta, em texto simples.

Os rascunhos são para textos que o cliente lê. Por isso, como na versão cliente do
relatório, as anotações do consultor e os sinais de alerta (com as observações) só entram
com `anotacoes_internas=True`, opção que o consultor liga na tela.

Os números vêm prontos do Painel do domínio (os mesmos da tela e do relatório) e só são
formatados aqui: o LLM recebe "Payback: 7,7 meses" e é instruído a copiar, nunca a
calcular. Respostas de perguntas condicionais ocultas pelo tipo de solução ficam de fora,
como no relatório.

`conhecidos_da_sessao` lista os dados pessoais que a anonimização troca por marcadores.
O texto montado aqui ainda tem os dados reais: quem envia anonimiza antes (llm.rascunho).
"""

import re
from collections.abc import Callable, Sequence
from decimal import Decimal

from descoberta.campos import CAMPO_POR_NOME
from descoberta.dominio.painel import Calculo
from descoberta.dominio.proposta import investimento_total
from descoberta.formatos import moeda, numero
from descoberta.questionario import perguntas_visiveis
from descoberta.relatorio.dados import DadosRelatorio
from descoberta.relatorio.dados_proposta import DadosProposta
from descoberta.rotulos import CAMADAS, NIVEIS, RESPONSAVEIS

from .anonimizacao import Conhecido
from .prompts import Pedido, Prompt

VAZIO = "(vazio)"
NAO_INFORMADO = "não informado"


# --- Sessão ---


def _horas(valor: Decimal) -> str:
    return f"{numero(valor, 2)} h"


def _formatar_entrada(campo: str, valor) -> str:
    unidade = CAMPO_POR_NOME[campo].unidade
    if unidade == "R$":
        return moeda(Decimal(valor))
    if unidade == "h":
        return _horas(Decimal(valor))
    return numero(Decimal(valor), 2)


class _Numeros:
    def __init__(self, dados: DadosRelatorio):
        self.dados = dados

    def entrada(self, rotulo: str, campo: str) -> str:
        valor = getattr(self.dados.entradas, campo)
        if valor is None:
            return f"{rotulo}: {NAO_INFORMADO}"
        marca = " (hipótese)" if campo in self.dados.hipoteses else ""
        return f"{rotulo}: {_formatar_entrada(campo, valor)}{marca}"

    def _marca(self, entradas) -> str:
        return " (depende de hipótese)" if self.dados.hipoteses & set(entradas) else ""

    def calculo(self, rotulo: str, calculo: Calculo, formatar: Callable[[Decimal], str]) -> str:
        if calculo.valor is None:
            return f"{rotulo}: {NAO_INFORMADO}"
        return f"{rotulo}: {formatar(calculo.valor)}{self._marca(calculo.entradas)}"

    def payback(self) -> str:
        payback = self.dados.painel.payback
        if payback.faltando:
            return f"Payback: {NAO_INFORMADO}"
        if payback.nunca_se_paga:
            texto = "não se paga (a economia não supera a operação)"
        else:
            texto = f"{numero(payback.meses)} meses"
            if payback.dificil_de_aprovar:
                texto += " (acima de 12 meses: difícil de aprovar)"
        return f"Payback: {texto}{self._marca(payback.entradas)}"

    @staticmethod
    def score(rotulo: str, parcial) -> str:
        if parcial.resultado is None:
            return f"{rotulo}: incompleto ({parcial.pontuacao} de {parcial.maximo} até agora)"
        return (
            f"{rotulo}: {parcial.pontuacao} de {parcial.maximo} — {parcial.resultado.faixa.rotulo}"
        )

    def linhas(self) -> list[str]:
        p = self.dados.painel
        return [
            self.calculo("Ocorrências por mês", p.ocorrencias_mes, numero),
            self.entrada("Horas por ocorrência", "horas_por_ocorrencia"),
            self.calculo("Horas da dor por mês", p.horas_dor_mes, _horas),
            self.entrada("Custo da hora", "custo_hora"),
            self.calculo("Custo da dor por mês", p.custo_dor_mes, moeda),
            self.entrada("Horas economizadas por mês", "horas_economizadas_mes"),
            self.entrada("Outros ganhos mensais", "outros_ganhos_mes"),
            self.calculo("Economia por mês", p.economia_mes, moeda),
            self.calculo("Custo de operação por mês", p.operacao_mes, moeda),
            self.entrada("Investimento", "investimento"),
            self.payback(),
            self.score("Score de prontidão de dados", p.score_dados),
            self.score("Score final de viabilidade", p.score_final),
        ]


def _secao(titulo: str, linhas: Sequence[str]) -> str:
    corpo = "\n".join(linhas) if linhas else "(nada registrado)"
    return f"## {titulo}\n{corpo}"


def _respostas(dados: DadosRelatorio) -> list[str]:
    q = dados.questionario
    secoes = []
    for bloco in q.blocos:
        linhas = [
            f"- {pergunta.texto}\n  {dados.respostas[pergunta.id].strip()}"
            for pergunta in perguntas_visiveis(q, bloco.numero, dados.tipo_solucao)
            if (dados.respostas.get(pergunta.id) or "").strip()
        ]
        if linhas:
            secoes.append(_secao(f"Bloco {bloco.numero} — {bloco.titulo}", linhas))
    encerramento = [
        f"- {item.titulo}\n  {dados.respostas[item.id].strip()}"
        for item in q.encerramento.itens
        if (dados.respostas.get(item.id) or "").strip()
    ]
    if encerramento:
        secoes.append(_secao("Encerramento", encerramento))
    return secoes


def _sinais(dados: DadosRelatorio) -> list[str]:
    textos = {s.id: s.texto for b in dados.questionario.blocos for s in b.sinais}
    return [
        f"- {textos.get(s.id, s.id)}" + (f" ({s.observacao})" if s.observacao else "")
        for s in dados.sinais
    ]


def _revisao(dados: DadosRelatorio) -> list[str]:
    q = dados.questionario
    riscos = [
        f"- {r.descricao} (categoria: {q.categoria_risco(r.categoria).rotulo}; "
        f"probabilidade {NIVEIS[r.probabilidade]}, impacto {NIVEIS[r.impacto]})"
        + (f". Mitigação: {r.mitigacao}" if r.mitigacao else "")
        for r in dados.riscos
    ]
    indicadores = [
        f"- {i.nome} ({CAMADAS[i.camada]}): atual {i.valor_atual or NAO_INFORMADO}; "
        f"meta {i.meta or NAO_INFORMADO}; prazo {i.prazo or NAO_INFORMADO}; "
        f"como medir: {i.como_medir or NAO_INFORMADO}"
        for i in dados.indicadores
    ]
    escopo = [
        f"- {'Entra no MVP' if item.entra else 'Fica de fora'}: {item.texto}"
        for item in dados.escopo
    ]
    passos = [
        f"- {p.acao} ({RESPONSAVEIS[p.responsavel].lower()})"
        + (f", até {p.prazo:%d/%m/%Y}" if p.prazo else "")
        for p in dados.proximos_passos
    ]
    return [
        _secao("Riscos", riscos),
        _secao("Indicadores de sucesso", indicadores),
        _secao("Escopo do MVP", escopo),
        _secao("Próximos passos", passos),
    ]


def contexto_da_sessao(
    dados: DadosRelatorio, sem_o_texto: str | None = None, anotacoes_internas: bool = False
) -> str:
    """Os fatos da sessão; `sem_o_texto` deixa de fora o texto que está sendo rascunhado.

    Sem `anotacoes_internas`, ficam de fora as anotações e os sinais de alerta.
    """
    q = dados.questionario
    tipo = next((t.rotulo for t in q.tipos_solucao if t.id == dados.tipo_solucao), None)
    empresa = [
        f"Empresa: {dados.empresa}",
        f"Pessoa de contato: {dados.cliente}",
        f"Setor: {dados.setor or NAO_INFORMADO}",
        f"Tipo de solução: {tipo or NAO_INFORMADO}",
        f"Data da sessão: {dados.data_sessao:%d/%m/%Y}",
    ]
    anotacoes = [
        f"- (bloco {a.bloco}) {a.texto}" if a.bloco else f"- {a.texto}" for a in dados.anotacoes
    ]
    textos = [
        f"{t.titulo}:\n{dados.textos[t.id].strip()}"
        for t in q.revisao.textos
        if t.id != sem_o_texto and (dados.textos.get(t.id) or "").strip()
    ]
    partes = [
        _secao("Empresa e sessão", empresa),
        _secao(
            "Números calculados pela app (copie exatamente; não recalcule)",
            _Numeros(dados).linhas(),
        ),
        *_respostas(dados),
    ]
    if anotacoes_internas:
        partes += [
            _secao("Sinais de alerta marcados na sessão (uso interno)", _sinais(dados)),
            _secao("Anotações do consultor (uso interno)", anotacoes),
        ]
    partes += [
        *_revisao(dados),
        _secao("Outros textos já escritos pelo consultor", textos),
    ]
    return "\n\n".join(partes)


def pedido_da_revisao(
    prompt: Prompt, dados: DadosRelatorio, texto_id: str, anotacoes_internas: bool = False
) -> Pedido:
    """O pedido de rascunho de um texto da revisão (KeyError se o id não existe)."""
    texto = dados.questionario.texto_revisao(texto_id)
    return prompt.preencher(
        titulo=texto.titulo,
        orientacao=texto.orientacao,
        texto_atual=(dados.textos.get(texto_id) or "").strip() or VAZIO,
        contexto=contexto_da_sessao(
            dados, sem_o_texto=texto_id, anotacoes_internas=anotacoes_internas
        ),
    )


# --- Proposta ---


def contexto_da_proposta(dados: DadosProposta) -> str:
    fases = []
    for fase in dados.fases:
        duracao = (
            f"{fase.duracao_semanas} semana{'s' if fase.duracao_semanas != 1 else ''}"
            if fase.duracao_semanas
            else "duração a definir"
        )
        valor = moeda(fase.investimento) if fase.investimento is not None else "valor a definir"
        linhas = [f"- {fase.nome}: {duracao}, {valor}"]
        if fase.objetivo:
            linhas.append(f"  Objetivo: {fase.objetivo}")
        if fase.escopo:
            linhas.append("  Escopo: " + "; ".join(fase.escopo))
        if fase.entregaveis:
            linhas.append("  Entregáveis: " + "; ".join(fase.entregaveis))
        fases.append("\n".join(linhas))
    total = investimento_total([f.investimento for f in dados.fases])
    fases.append(f"Total: {moeda(total) if total is not None else 'a definir'}")
    return "\n\n".join(
        [
            _secao("Fases (uma depois da outra, a partir do aceite)", fases),
            _secao("Fora do escopo", [f"- Fora do escopo: {e}" for e in dados.exclusoes]),
            _secao("Premissas", [f"- {p}" for p in dados.premissas]),
            _secao("Responsabilidades do cliente", [f"- {r}" for r in dados.responsabilidades]),
        ]
    )


def pedido_da_proposta(
    prompt: Prompt,
    dados: DadosProposta,
    alvo: str,
    fase: int | None = None,
    texto_atual: str = "",
    anotacoes_internas: bool = False,
) -> Pedido:
    """Pedido de rascunho de um texto da proposta.

    `alvo`: "contexto" (o texto que abre a proposta) ou "objetivo_fase" (com `fase`, a
    posição da fase na proposta, contando de 0).
    """
    if alvo == "contexto":
        descricao = "o texto de contexto que abre a proposta"
    elif alvo == "objetivo_fase":
        if fase is None or not 0 <= fase < len(dados.fases):
            raise ValueError(f"fase {fase!r} inválida para o alvo {alvo!r}")
        descricao = f'o objetivo da fase "{dados.fases[fase].nome}"'
    else:
        raise ValueError(f"alvo desconhecido: {alvo!r}")
    if alvo not in prompt.alvos:
        raise ValueError(f"o prompt {prompt.rotulo} não tem orientação para o alvo {alvo!r}")
    return prompt.preencher(
        alvo=descricao,
        orientacao=prompt.alvos[alvo],
        texto_atual=texto_atual.strip() or VAZIO,
        proposta=contexto_da_proposta(dados),
        contexto=contexto_da_sessao(dados.relatorio, anotacoes_internas=anotacoes_internas),
    )


# --- Dados pessoais conhecidos ---


def textos_para_sugestao(dados: DadosRelatorio) -> list[str]:
    """Os textos livres da sessão, crus (sem os títulos do contexto), para sugerir nomes
    de pessoas citadas: respostas visíveis, anotações, textos e saídas da revisão."""
    q = dados.questionario
    visiveis = {
        p.id for b in q.blocos for p in perguntas_visiveis(q, b.numero, dados.tipo_solucao)
    } | {item.id for item in q.encerramento.itens}
    textos = [r for pid, r in dados.respostas.items() if pid in visiveis]
    textos += [a.texto for a in dados.anotacoes]
    textos += list(dados.textos.values())
    textos += [s.observacao for s in dados.sinais if s.observacao]
    for r in dados.riscos:
        textos += [r.descricao, r.mitigacao or ""]
    for i in dados.indicadores:
        textos += [i.nome, i.valor_atual or "", i.meta or "", i.prazo or "", i.como_medir or ""]
    textos += [item.texto for item in dados.escopo]
    textos += [p.acao for p in dados.proximos_passos]
    return [t for t in textos if t and t.strip()]


def _documento(valor: str | None) -> Conhecido:
    so_letras_e_numeros = re.sub(r"[^0-9A-Z]", "", (valor or "").upper())
    return Conhecido.literal(valor, "CPF" if len(so_letras_e_numeros) == 11 else "CNPJ")


def conhecidos_da_sessao(
    dados: DadosRelatorio, proposta: DadosProposta | None, pessoas: Sequence[str]
) -> list[Conhecido]:
    """Os dados pessoais que a sessão conhece, na ordem que define os marcadores."""
    conhecidos = [
        Conhecido.pessoa(dados.cliente, "CLIENTE"),
        Conhecido.empresa(dados.empresa, "EMPRESA"),
    ]
    if proposta is not None:
        conhecidos += [
            Conhecido.pessoa(proposta.cliente_representante, "REPRESENTANTE"),
            Conhecido.literal(proposta.cliente_email, "EMAIL"),
            _documento(proposta.cliente_cpf_cnpj),
            Conhecido.literal(proposta.cliente_cidade, "CIDADE"),
        ]
    consultor = dados.consultor
    if consultor is not None:
        conhecidos += [
            Conhecido.pessoa(consultor.nome, "CONSULTOR"),
            Conhecido.empresa(consultor.empresa, "EMPRESA_CONSULTOR"),
            Conhecido.literal(consultor.email, "EMAIL"),
            Conhecido.literal(consultor.telefone, "TELEFONE"),
            _documento(consultor.cpf_cnpj),
            Conhecido.literal(consultor.cidade, "CIDADE"),
        ]
    conhecidos += [Conhecido.pessoa(nome, "PESSOA") for nome in pessoas]
    return [c for c in conhecidos if c.valor]
