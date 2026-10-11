"""Montagem do Relatório de Descoberta: capa, 12 seções do bloco 10, anexos e termo.

Cada seção do YAML (`secoes_relatorio`, com id) tem uma função aqui em `_SECOES`. Depois
do conteúdo próprio da seção entram as respostas dos blocos e as tabelas de referência que
o YAML indicar. Os números vêm do Painel (`dados.painel`); nenhuma conta é feita aqui.

Versão cliente × interna: a interna acrescenta o Anexo C (sinais de alerta e anotações)
e o aviso "USO INTERNO" na capa e no rodapé.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from descoberta.campos import CAMPO_POR_NOME, CAMPOS_METRICAS, PERIODOS
from descoberta.dominio.painel import Calculo
from descoberta.dominio.revisao import matriz_de_riscos
from descoberta.formatos import moeda, numero
from descoberta.questionario import SecaoRelatorio, perguntas_visiveis
from descoberta.repositorio import TipoVersao
from descoberta.rotulos import CAMADAS, IMPACTOS, NIVEIS, PROBABILIDADES, RESPONSAVEIS

from .dados import DadosRelatorio
from .documento import (
    FALTA,
    Assinatura,
    Aviso,
    Bloco,
    Capa,
    Documento,
    Lista,
    Paragrafo,
    QuebraDePagina,
    Tabela,
    Titulo,
)

FAIXA_INTERNA = "USO INTERNO — não enviar ao cliente"
NOTA_HIPOTESE = "* Calculado com hipóteses do consultor, a confirmar (ver Anexo B)."

TERMO = (
    "Declaro que li este Relatório de Descoberta e que ele reflete as informações "
    "fornecidas na sessão de {data}. Estou ciente de que os valores marcados como hipótese "
    "foram estimados pelo consultor e precisam ser confirmados, e de que os indicadores, as "
    "metas e o critério de aceite da seção 6 serão a referência para avaliar a solução."
)
AVISO_TERMO = (
    "Este documento não é proposta comercial nem contrato: não cria obrigação de "
    "contratação, preço ou prazo para nenhuma das partes. A proposta comercial, se houver, "
    "será apresentada em documento próprio."
)

# Fórmulas em palavras, para a memória de cálculo. Só descrevem: a conta é do domínio.
_RESULTADOS = (
    ("Ocorrências por mês", "ocorrencias_mes", "frequência convertida para mês"),
    ("Horas da dor por mês", "horas_dor_mes", "horas por ocorrência × ocorrências por mês"),
    ("Custo da dor por mês", "custo_dor_mes", "horas da dor por mês × custo da hora"),
    (
        "Custo de operação por mês",
        "operacao_mes",
        "chamadas por dia × custo por chamada × dias úteis + custo fixo mensal",
    ),
    (
        "Economia por mês",
        "economia_mes",
        "horas economizadas por mês × custo da hora + outros ganhos mensais",
    ),
    ("Payback", "payback", "investimento ÷ (economia por mês − custo de operação por mês)"),
)


@dataclass(frozen=True)
class Emissao:
    """Para quem é o relatório e se é uma versão registrada (numero) ou um rascunho."""

    tipo: TipoVersao
    numero: int | None
    emitido_em: datetime


def data_br(momento) -> str:
    return momento.strftime("%d/%m/%Y")


def data_hora_local(momento: datetime) -> str:
    return momento.astimezone().strftime("%d/%m/%Y %H:%M")


def descricao_da_emissao(emissao: Emissao) -> str:
    quando = data_hora_local(emissao.emitido_em)
    if emissao.numero is None:
        return f"Rascunho não registrado ({emissao.tipo}), gerado em {quando}"
    return f"Versão {emissao.numero} ({emissao.tipo}), emitida em {quando}"


def _paragrafos(texto: str | None) -> list[Bloco]:
    """Texto do consultor: uma linha, um parágrafo; em branco, a marca do que falta."""
    if not texto or not texto.strip():
        return [Aviso(FALTA)]
    return [Paragrafo(linha.strip()) for linha in texto.splitlines() if linha.strip()]


class _Montador:
    def __init__(self, dados: DadosRelatorio, emissao: Emissao):
        self.dados = dados
        self.emissao = emissao
        self.questionario = dados.questionario
        self.painel = dados.painel
        self._usou_hipotese = False

    # --- Números (sempre do Painel) ---

    def _com_hipotese(self, texto: str, entradas: Iterable[str]) -> str:
        if self.dados.hipoteses & set(entradas):
            self._usou_hipotese = True
            return f"{texto} *"
        return texto

    def _calculo(self, calculo: Calculo, formatar: Callable[[Decimal], str]) -> str:
        if calculo.valor is None:
            return FALTA
        return self._com_hipotese(formatar(calculo.valor), calculo.entradas)

    def _payback(self) -> str:
        payback = self.painel.payback
        if payback.faltando:
            return FALTA
        if payback.nunca_se_paga:
            texto = "não se paga (a economia não supera a operação)"
        else:
            texto = f"{numero(payback.meses)} meses"
            if payback.dificil_de_aprovar:
                texto += " (acima de 12 meses: difícil de aprovar)"
        return self._com_hipotese(texto, payback.entradas)

    @staticmethod
    def _score(parcial) -> str:
        if parcial.resultado is None:
            return FALTA
        return f"{parcial.pontuacao} de {parcial.maximo} — {parcial.resultado.faixa.rotulo}"

    def _metrica(self, campo: str) -> str:
        valor = getattr(self.dados.entradas, campo)
        if valor is None:
            return "—"
        if campo == "frequencia_periodo":
            return PERIODOS.get(valor, valor)
        unidade = CAMPO_POR_NOME[campo].unidade
        valor = Decimal(valor)
        if unidade == "R$":
            return moeda(valor)
        return f"{numero(valor, 2)} h" if unidade == "h" else numero(valor, 2)

    def _entrada(self, campo: str) -> str:
        """Valor de uma entrada no corpo do relatório: falta, ou o valor (com * se hipótese)."""
        if getattr(self.dados.entradas, campo) is None:
            return FALTA
        return self._com_hipotese(self._metrica(campo), [campo])

    def _metricas(self, campos: Iterable[str]) -> Tabela:
        linhas = [
            [CAMPO_POR_NOME[c].rotulo, self._com_hipotese(self._metrica(c), [c])] for c in campos
        ]
        return Tabela(["Item", "Valor"], linhas, larguras=[2, 1])

    # --- Respostas ---

    def _rotulo_e_resposta(self, id_: str) -> tuple[str, str | None]:
        try:
            _, pergunta = self.questionario.pergunta(id_)
            return pergunta.texto, self.dados.respostas.get(id_)
        except KeyError:
            item = self.questionario.item_encerramento(id_)
            return item.titulo, self.dados.respostas.get(id_)

    def _visiveis(self, bloco: int, so_obrigatorias: bool) -> list:
        perguntas = perguntas_visiveis(self.questionario, bloco, self.dados.tipo_solucao)
        return [p for p in perguntas if p.tipo == "obrigatoria" or not so_obrigatorias]

    def _respostas_da_secao(self, secao: SecaoRelatorio) -> list[Bloco]:
        ids = [p.id for n in secao.blocos for p in self._visiveis(n, so_obrigatorias=True)]
        ids += secao.respostas
        linhas = [list(self._rotulo_e_resposta(id_)) for id_ in ids]
        linhas = [[pergunta, resposta] for pergunta, resposta in linhas if resposta]
        blocos: list[Bloco] = [Titulo("O que foi levantado na sessão", 2)]
        if not linhas:
            return [*blocos, Aviso(FALTA)]
        return [*blocos, Tabela(["Pergunta", "Resposta"], linhas, larguras=[2, 3])]

    def _tabelas_da_secao(self, secao: SecaoRelatorio) -> list[Bloco]:
        blocos: list[Bloco] = []
        for titulo in secao.tabelas:
            for n in secao.blocos:
                for referencia in self.questionario.bloco(n).referencias:
                    if referencia.titulo == titulo:
                        blocos += [
                            Titulo(referencia.titulo, 2),
                            Tabela(
                                list(referencia.colunas),
                                [list(linha) for linha in referencia.linhas],
                            ),
                        ]
        return blocos

    # --- As 12 seções ---

    def _resumo(self) -> list[Bloco]:
        p = self.painel
        quadro = Tabela(
            ["Indicador", "Valor"],
            [
                ["Custo da dor", self._calculo(p.custo_dor_mes, lambda v: f"{moeda(v)}/mês")],
                ["Payback", self._payback()],
                ["Prontidão dos dados", self._score(p.score_dados)],
                ["Viabilidade (score final)", self._score(p.score_final)],
            ],
            larguras=[1, 2],
        )
        return [*_paragrafos(self.dados.textos.get("resumo_executivo")), quadro]

    def _problema(self) -> list[Bloco]:
        p = self.painel
        quadro = Tabela(
            ["Item", "Valor"],
            [
                ["Ocorrências por mês", self._calculo(p.ocorrencias_mes, numero)],
                ["Horas por ocorrência", self._entrada("horas_por_ocorrencia")],
                [
                    "Horas da dor por mês",
                    self._calculo(p.horas_dor_mes, self._formato("horas_dor_mes")),
                ],
                ["Custo da hora", self._entrada("custo_hora")],
                ["Custo da dor por mês", self._calculo(p.custo_dor_mes, moeda)],
            ],
            larguras=[2, 1],
        )
        return [*_paragrafos(self.dados.textos.get("frase_problema")), quadro]

    def _fluxos(self) -> list[Bloco]:
        return [
            Titulo("Como é hoje (as-is)", 2),
            *_paragrafos(self.dados.textos.get("fluxo_as_is")),
            Titulo("Como ficaria (to-be)", 2),
            *_paragrafos(self.dados.textos.get("fluxo_to_be")),
        ]

    def _solucao(self) -> list[Bloco]:
        tipo = next(
            (t for t in self.questionario.tipos_solucao if t.id == self.dados.tipo_solucao), None
        )
        return [
            Paragrafo(tipo.rotulo if tipo else FALTA, rotulo="Tipo de solução:"),
            *_paragrafos(self.dados.textos.get("justificativa_solucao")),
        ]

    def _dados(self) -> list[Bloco]:
        score = self.questionario.scores.prontidao_dados
        linhas = [
            [c.rotulo, str(self.dados.notas[c.id]) if c.id in self.dados.notas else FALTA]
            for c in score.criterios
        ]
        parcial = self.painel.score_dados
        blocos: list[Bloco] = [
            Titulo("Score de prontidão de dados", 2),
            Tabela(["Critério", "Nota (0 a 3)"], linhas, larguras=[3, 1]),
            Paragrafo(self._score(parcial), rotulo="Resultado:"),
        ]
        if parcial.resultado is not None and parcial.resultado.faixa.descricao:
            blocos.append(Paragrafo(parcial.resultado.faixa.descricao))
        return blocos

    def _indicadores(self) -> list[Bloco]:
        if not self.dados.indicadores:
            return [Aviso(FALTA)]
        linhas = [
            [
                i.nome,
                CAMADAS[i.camada],
                i.valor_atual or FALTA,
                i.meta or FALTA,
                i.prazo or FALTA,
                i.como_medir or FALTA,
            ]
            for i in self.dados.indicadores
        ]
        return [
            Tabela(
                ["Indicador", "Camada", "Valor atual", "Meta", "Prazo", "Como medir"],
                linhas,
                larguras=[2, 1, 1.3, 1, 1.3, 2],
            ),
            Paragrafo(
                "Os indicadores e as metas acima, com o critério de aceite abaixo, são "
                "validados pelo cliente no termo ao final deste relatório."
            ),
        ]

    def _operacao(self) -> list[Bloco]:
        tabela = self._metricas(("chamadas_por_dia", "custo_por_chamada", "custo_fixo_mes"))
        total = self._calculo(self.painel.operacao_mes, lambda v: f"{moeda(v)}/mês")
        return [
            Tabela(tabela.colunas, [*tabela.linhas, ["Custo de operação", total]], None, [2, 1])
        ]

    def _riscos(self) -> list[Bloco]:
        if not self.dados.riscos:
            return [Aviso(FALTA)]
        rotulos = {c.id: c.rotulo for c in self.questionario.revisao.categorias_risco}
        linhas = []
        for n, r in enumerate(self.dados.riscos, start=1):
            exige = r.probabilidade == r.impacto == "alto"
            mitigacao = r.mitigacao or (FALTA if exige else "—")
            linhas.append(
                [
                    f"R{n}",
                    r.descricao,
                    rotulos.get(r.categoria, r.categoria),
                    PROBABILIDADES[r.probabilidade],
                    IMPACTOS[r.impacto],
                    mitigacao,
                ]
            )
        matriz = matriz_de_riscos(self.dados.riscos)
        return [
            Tabela(
                ["#", "Risco", "Categoria", "Probabilidade", "Impacto", "Mitigação"],
                linhas,
                larguras=[0.45, 2.6, 1.6, 1.55, 1.15, 2.8],
            ),
            Titulo("Matriz de riscos", 2),
            Tabela(
                [
                    "",
                    *(
                        f"Probabilidade {PROBABILIDADES[c.probabilidade].lower()}"
                        for c in matriz[0]
                    ),
                ],
                [
                    [
                        f"Impacto {IMPACTOS[linha[0].impacto].lower()}",
                        *(self._celula_da_matriz(c) for c in linha),
                    ]
                    for linha in matriz
                ],
                niveis=[[None, *(str(c.severidade) for c in linha)] for linha in matriz],
            ),
            Paragrafo(
                "Cada célula mostra os riscos e o nível (no PDF e no Word, também em cor: "
                "verde, amarelo e vermelho). Riscos altos em probabilidade e impacto exigem "
                "mitigação definida antes do início."
            ),
        ]

    @staticmethod
    def _celula_da_matriz(celula) -> str:
        riscos = ", ".join(f"R{n}" for n, _ in celula.riscos) or "—"
        return f"{riscos}\nnível {NIVEIS[celula.severidade]}"

    def _integracoes(self) -> list[Bloco]:
        return []  # só as respostas do bloco 8 (YAML)

    def _escopo(self) -> list[Bloco]:
        entra = [i.texto for i in self.dados.escopo if i.entra]
        fora = [i.texto for i in self.dados.escopo if not i.entra]
        return [
            Titulo("Entra no MVP", 2),
            Lista(entra) if entra else Aviso(FALTA),
            Titulo("Fica de fora", 2),
            Lista(fora) if fora else Aviso(FALTA),
        ]

    def _orcamento(self) -> list[Bloco]:
        p = self.painel
        return [
            Tabela(
                ["Item", "Valor"],
                [
                    ["Investimento", self._entrada("investimento")],
                    ["Economia por mês", self._calculo(p.economia_mes, moeda)],
                    ["Custo de operação por mês", self._calculo(p.operacao_mes, moeda)],
                    ["Payback", self._payback()],
                ],
                larguras=[2, 1],
            )
        ]

    def _recomendacao(self) -> list[Bloco]:
        final = self.painel.score_final
        blocos: list[Bloco] = [Paragrafo(self._score(final), rotulo="Score final de viabilidade:")]
        if final.resultado is not None and final.resultado.faixa.descricao:
            blocos.append(Paragrafo(final.resultado.faixa.descricao))
        blocos += _paragrafos(self.dados.textos.get("recomendacao"))
        blocos.append(Titulo("Próximos passos", 2))
        if self.dados.proximos_passos:
            linhas = [
                [p.acao, RESPONSAVEIS[p.responsavel], data_br(p.prazo) if p.prazo else FALTA]
                for p in self.dados.proximos_passos
            ]
            blocos.append(Tabela(["Ação", "Responsável", "Prazo"], linhas, larguras=[4, 1, 1]))
        else:
            blocos.append(Aviso(FALTA))
        return blocos

    _SECOES: dict[str, Callable[["_Montador"], list[Bloco]]] = {
        "rel.resumo": _resumo,
        "rel.problema": _problema,
        "rel.fluxos": _fluxos,
        "rel.solucao": _solucao,
        "rel.dados": _dados,
        "rel.indicadores": _indicadores,
        "rel.operacao": _operacao,
        "rel.riscos": _riscos,
        "rel.integracoes": _integracoes,
        "rel.escopo": _escopo,
        "rel.orcamento": _orcamento,
        "rel.recomendacao": _recomendacao,
    }

    def _secao(self, numero_secao: int, secao: SecaoRelatorio) -> list[Bloco]:
        if secao.id not in self._SECOES:
            raise ValueError(f"o relatório não sabe montar a seção '{secao.id}' do questionário")
        self._usou_hipotese = False
        blocos: list[Bloco] = [Titulo(f"{numero_secao}. {secao.titulo_para_cliente}")]
        blocos += self._SECOES[secao.id](self)
        blocos += self._tabelas_da_secao(secao)
        if secao.blocos or secao.respostas:
            blocos += self._respostas_da_secao(secao)
        if self._usou_hipotese:
            blocos.append(Aviso(NOTA_HIPOTESE))
        return blocos

    # --- Capa, anexos e termo ---

    def _capa(self) -> Capa:
        d = self.dados
        linhas = [("Cliente", d.cliente)]
        if d.setor:
            linhas.append(("Setor", d.setor))
        linhas += [
            ("Data da sessão", data_br(d.data_sessao)),
            ("Emissão", descricao_da_emissao(self.emissao)),
            ("Questionário", f"{self.questionario.titulo} · versão {self.questionario.versao}"),
        ]
        interna = self.emissao.tipo == TipoVersao.interna
        return Capa(
            titulo="Relatório de Descoberta",
            subtitulo=d.empresa,
            linhas=linhas,
            faixa=FAIXA_INTERNA if interna else None,
            nota=f"Documento confidencial, preparado para {d.empresa}.",
        )

    def _anexo_a(self) -> list[Bloco]:
        blocos: list[Bloco] = [
            Titulo("Anexo A — Respostas da sessão"),
            Paragrafo(
                "Todas as perguntas respondidas, por bloco. Perguntas que não se aplicam ao "
                "tipo de solução escolhido não aparecem."
            ),
        ]
        for bloco in self.questionario.blocos:
            linhas = [
                [p.texto, self.dados.respostas[p.id]]
                for p in self._visiveis(bloco.numero, so_obrigatorias=False)
                if self.dados.respostas.get(p.id, "").strip()
            ]
            if linhas:
                blocos += [
                    Titulo(f"Bloco {bloco.numero} — {bloco.titulo}", 2),
                    Tabela(["Pergunta", "Resposta"], linhas, larguras=[2, 3]),
                ]
        encerramento = [
            [item.titulo, self.dados.respostas[item.id]]
            for item in self.questionario.encerramento.itens
            if self.dados.respostas.get(item.id, "").strip()
        ]
        if encerramento:
            blocos += [
                Titulo("Encerramento", 2),
                Tabela(["Item", "Resposta"], encerramento, larguras=[1, 3]),
            ]
        return blocos

    def _anexo_b(self) -> list[Bloco]:
        hipoteses = self.dados.hipoteses
        entradas = [
            [
                campo.rotulo,
                self._metrica(campo.nome),
                "—"
                if getattr(self.dados.entradas, campo.nome) is None
                else ("Hipótese" if campo.nome in hipoteses else "Informado na sessão"),
            ]
            for campo in CAMPOS_METRICAS
        ]
        rotulos = {c.nome: c.rotulo.lower() for c in CAMPOS_METRICAS}
        calculos = []
        for rotulo, atributo, formula in _RESULTADOS:
            calculo = getattr(self.painel, atributo)
            if atributo == "payback":
                valor = self._payback().removesuffix(" *")
            else:
                valor = self._calculo(calculo, self._formato(atributo)).removesuffix(" *")
            usadas = [rotulos[c] for c in calculo.entradas if c in hipoteses]
            observacao = "depende de hipótese: " + ", ".join(usadas) if usadas else ""
            calculos.append([rotulo, formula, valor, observacao])
        return [
            Titulo("Anexo B — Memória de cálculo"),
            Paragrafo(
                "Os números levantados na sessão e como cada resultado foi calculado. Valores "
                "marcados como Hipótese foram estimados pelo consultor e precisam ser "
                "confirmados com o cliente."
            ),
            Titulo("Entradas", 2),
            Tabela(["Entrada", "Valor", "Origem"], entradas, larguras=[2, 1.2, 1.3]),
            Titulo("Cálculos", 2),
            Tabela(
                ["Resultado", "Como é calculado", "Valor", "Observação"],
                calculos,
                larguras=[1.4, 2.6, 1.2, 1.6],
            ),
            *self._memoria_dos_scores(),
        ]

    @staticmethod
    def _formato(atributo: str) -> Callable[[Decimal], str]:
        if atributo in ("custo_dor_mes", "operacao_mes", "economia_mes"):
            return lambda v: f"{moeda(v)}/mês"
        if atributo == "horas_dor_mes":
            return lambda v: f"{numero(v)} h"
        return numero

    def _memoria_dos_scores(self) -> list[Bloco]:
        scores = self.questionario.scores
        notas = self.dados.notas
        dados = [
            [c.rotulo, str(notas[c.id]) if c.id in notas else FALTA]
            for c in scores.prontidao_dados.criterios
        ]
        finais = []
        for c in scores.viabilidade_final.criterios:
            if c.id == scores.prontidao_dados.criterio_final:
                nota = self.painel.nota_prontidao
                texto = FALTA if nota is None else f"{nota} (derivada do score de dados)"
            else:
                texto = str(notas[c.id]) if c.id in notas else FALTA
            blocos_origem = ", ".join(str(n) for n in c.blocos_origem)
            finais.append([c.rotulo, blocos_origem, texto])
        return [
            Titulo("Score de prontidão de dados", 2),
            Tabela(["Critério", "Nota (0 a 3)"], dados, larguras=[3, 1]),
            Paragrafo(self._score(self.painel.score_dados), rotulo="Total:"),
            Titulo("Score final de viabilidade", 2),
            Tabela(["Critério", "Blocos de origem", "Nota (0 a 3)"], finais, larguras=[3, 1, 1.5]),
            Paragrafo(self._score(self.painel.score_final), rotulo="Total:"),
        ]

    def _anexo_c(self) -> list[Bloco]:
        sinais_por_id = {
            s.id: (b.numero, s.texto) for b in self.questionario.blocos for s in b.sinais
        }
        sinais = [
            [str(sinais_por_id[s.id][0]), sinais_por_id[s.id][1], s.observacao or "—"]
            for s in self.dados.sinais
            if s.id in sinais_por_id
        ]
        contagem = [
            [f"{n}. {self.questionario.bloco(n).titulo}", str(total)]
            for n, total in self.painel.sinais_por_bloco.items()
            if total
        ]
        anotacoes = [
            [
                data_hora_local(a.criado_em),
                f"Bloco {a.bloco}" if a.bloco else "Geral",
                a.texto,
            ]
            for a in self.dados.anotacoes
        ]
        return [
            Titulo("Anexo C — Uso interno: sinais de alerta e anotações"),
            Aviso(FAIXA_INTERNA),
            Titulo("Sinais de alerta marcados", 2),
            Tabela(["Bloco", "Sinal", "Observação"], sinais, larguras=[0.6, 3, 2])
            if sinais
            else Paragrafo("Nenhum sinal marcado."),
            Titulo("Sinais por bloco", 2),
            Tabela(["Bloco", "Sinais"], contagem, larguras=[3, 1])
            if contagem
            else Paragrafo("Nenhum sinal marcado."),
            Titulo("Anotações livres", 2),
            Tabela(["Quando", "Bloco", "Anotação"], anotacoes, larguras=[1.2, 0.8, 4])
            if anotacoes
            else Paragrafo("Nenhuma anotação."),
        ]

    def _termo(self) -> list[Bloco]:
        return [
            QuebraDePagina(),
            Titulo("Termo de ciência e validação"),
            Paragrafo(TERMO.format(data=data_br(self.dados.data_sessao))),
            Aviso(AVISO_TERMO),
            Assinatura(f"Pelo cliente — {self.dados.empresa}"),
            Assinatura("Pelo consultor"),
        ]

    def montar(self) -> Documento:
        blocos: list[Bloco] = [self._capa(), QuebraDePagina()]
        secoes = [s for bloco in self.questionario.blocos for s in bloco.secoes_relatorio]
        for numero_secao, secao in enumerate(secoes, start=1):
            blocos += self._secao(numero_secao, secao)
        blocos += [QuebraDePagina(), *self._anexo_a(), QuebraDePagina(), *self._anexo_b()]
        if self.emissao.tipo == TipoVersao.interna:
            blocos += [QuebraDePagina(), *self._anexo_c()]
        blocos += self._termo()
        return Documento(f"Relatório de Descoberta — {self.dados.empresa}", blocos)


def montar_relatorio(dados: DadosRelatorio, emissao: Emissao) -> Documento:
    return _Montador(dados, emissao).montar()
