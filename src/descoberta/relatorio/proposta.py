"""Montagem da Proposta Comercial: documento separado do Relatório de Descoberta.

Usa o mesmo documento de blocos e os mesmos exportadores do relatório. O conteúdo vem da
proposta da sessão (uma cópia editável do modelo e da revisão), do perfil do consultor e
do Painel (só para citar a recomendação). As contas da proposta (cronograma, total e
validade) são do domínio (`dominio.proposta`).
"""

from dataclasses import dataclass
from datetime import datetime

from descoberta.dominio.proposta import cronograma, investimento_total, valida_ate
from descoberta.formatos import moeda
from descoberta.proposta.clausulas import preencher_marcadores

from .consultor import AVISO_CONSULTOR_FICTICIO, assinatura_do_consultor, linha_do_consultor
from .dados_proposta import DadosProposta
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
from .montagem import data_br, data_hora_local

CARACTERES_DO_HASH = 12
TITULO_ANEXO = "Anexo — Condições Gerais"


@dataclass(frozen=True)
class EmissaoProposta:
    """Versão registrada (numero) ou rascunho (numero None), e quando foi emitida."""

    numero: int | None
    emitido_em: datetime


def descricao_da_emissao_proposta(emissao: EmissaoProposta) -> str:
    quando = data_hora_local(emissao.emitido_em)
    if emissao.numero is None:
        return f"Rascunho não registrado, gerado em {quando}"
    return f"Versão {emissao.numero}, emitida em {quando}"


def _ou_falta(valor: str | None) -> str:
    return valor if valor else FALTA


class _MontadorProposta:
    def __init__(self, dados: DadosProposta, emissao: EmissaoProposta):
        self.dados = dados
        self.emissao = emissao
        self.relatorio = dados.relatorio
        self.consultor = dados.relatorio.consultor
        self.validade = valida_ate(emissao.emitido_em.astimezone().date(), dados.validade_dias)

    # --- Capa ---

    def _referencia(self) -> str:
        texto = f"Relatório de Descoberta da sessão de {data_br(self.relatorio.data_sessao)}"
        registrado = self.dados.relatorio_registrado
        if registrado is None:
            return f"{texto} (ainda sem versão registrada)"
        resumo = registrado.hash_conteudo[:CARACTERES_DO_HASH]
        return f"{texto}, versão {registrado.numero}, hash {resumo}"

    def _capa(self) -> Capa:
        d = self.dados
        linhas = [
            ("Cliente", d.cliente_representante or self.relatorio.cliente),
            ("Consultor", linha_do_consultor(self.consultor)),
        ]
        if self.consultor and self.consultor.dados_ficticios:
            linhas.append(("Atenção", AVISO_CONSULTOR_FICTICIO))
        linhas += [
            ("Referência", self._referencia()),
            ("Emissão", descricao_da_emissao_proposta(self.emissao)),
            ("Validade", f"até {data_br(self.validade)} ({d.validade_dias} dias)"),
        ]
        return Capa(
            titulo=d.modelo.titulo,
            subtitulo=self.relatorio.empresa,
            linhas=linhas,
            nota=f"Documento confidencial, preparado para {self.relatorio.empresa}.",
            logotipo=self.consultor.logotipo if self.consultor else None,
        )

    # --- Seções ---

    def _partes(self) -> list[Bloco]:
        d, c = self.dados, self.consultor
        representante = d.cliente_representante
        if representante and d.cliente_cargo:
            representante = f"{representante} ({d.cliente_cargo})"
        linhas = [
            ["Nome ou razão social", self.relatorio.empresa, c.empresa if c else FALTA],
            ["CPF/CNPJ", _ou_falta(d.cliente_cpf_cnpj), _ou_falta(c and c.cpf_cnpj)],
            ["Representante", _ou_falta(representante), c.nome if c else FALTA],
            ["Contato", d.cliente_email or "—", (c and c.contato) or "—"],
            ["Cidade/UF", "—", _ou_falta(c and c.cidade_uf)],
        ]
        return [
            Tabela(
                ["", "Contratante (cliente)", "Contratada (consultor)"],
                linhas,
                larguras=[1.2, 2, 2],
            )
        ]

    def _contexto(self) -> list[Bloco]:
        blocos: list[Bloco] = [
            Paragrafo(
                "Esta proposta parte do Relatório de Descoberta, que registra o problema, os "
                "dados disponíveis, os riscos e a recomendação."
            )
        ]
        frase = self.relatorio.textos.get("frase_problema")
        blocos.append(Paragrafo(frase.strip() if frase else FALTA, rotulo="O problema:"))
        final = self.relatorio.painel.score_final
        if final.resultado is not None:
            recomendacao = (
                f"{final.resultado.faixa.rotulo} (score final {final.pontuacao} de {final.maximo})"
            )
        else:
            recomendacao = FALTA
        blocos.append(Paragrafo(recomendacao, rotulo="Recomendação do relatório:"))
        return blocos

    def _escopo(self) -> list[Bloco]:
        blocos: list[Bloco] = []
        if not self.dados.fases:
            blocos.append(Aviso(FALTA))
        for fase in self.dados.fases:
            blocos.append(Titulo(fase.nome, 2))
            if fase.objetivo:
                blocos.append(Paragrafo(fase.objetivo, rotulo="Objetivo:"))
            blocos.append(Lista(fase.escopo) if fase.escopo else Aviso(FALTA))
        blocos.append(Titulo("Fora do escopo", 2))
        if self.dados.exclusoes:
            blocos.append(Lista(self.dados.exclusoes))
        blocos.append(
            Paragrafo("O que não estiver descrito nesta proposta não faz parte do escopo.")
        )
        return blocos

    def _cronograma(self) -> list[Bloco]:
        if not self.dados.fases:
            return [Aviso(FALTA)]
        periodos = cronograma([f.duracao_semanas for f in self.dados.fases])
        linhas = [
            [
                fase.nome,
                "\n".join(f"• {e}" for e in fase.entregaveis) or FALTA,
                f"{fase.duracao_semanas} semana{'s' if fase.duracao_semanas > 1 else ''}"
                if fase.duracao_semanas
                else FALTA,
                str(periodo) if periodo else FALTA,
            ]
            for fase, periodo in zip(self.dados.fases, periodos, strict=True)
        ]
        return [
            Tabela(
                ["Fase", "Entregáveis", "Duração", "Quando"], linhas, larguras=[1.6, 3.4, 1, 1.2]
            ),
            Paragrafo(
                "As semanas contam a partir do aceite desta proposta e do recebimento dos "
                "dados e acessos necessários. As fases são feitas uma depois da outra."
            ),
        ]

    def _investimento(self) -> list[Bloco]:
        if not self.dados.fases:
            return [Aviso(FALTA)]
        valores = [f.investimento for f in self.dados.fases]
        total = investimento_total(valores)
        linhas = [
            [fase.nome, moeda(valor) if valor is not None else FALTA]
            for fase, valor in zip(self.dados.fases, valores, strict=True)
        ]
        linhas.append(["Total", moeda(total) if total is not None else FALTA])
        return [Tabela(["Fase", "Investimento"], linhas, larguras=[3, 1.2])]

    def _condicoes(self) -> list[Bloco]:
        d = self.dados
        return [
            Paragrafo(d.condicoes_pagamento, rotulo="Pagamento:"),
            Paragrafo(d.impostos, rotulo="Impostos:"),
            Paragrafo(d.reajuste, rotulo="Reajuste:"),
        ]

    def _premissas(self) -> list[Bloco]:
        if not self.dados.premissas:
            return [Paragrafo("Nenhuma premissa além do que está descrito nesta proposta.")]
        return [
            Paragrafo(
                "A proposta vale enquanto estas premissas se confirmarem. Valores marcados como "
                "hipótese foram estimados pelo consultor e precisam ser confirmados."
            ),
            Lista(self.dados.premissas),
        ]

    def _responsabilidades(self) -> list[Bloco]:
        if not self.dados.responsabilidades:
            return [Aviso(FALTA)]
        return [Lista(self.dados.responsabilidades)]

    def _criterio_de_aceite(self) -> list[Bloco]:
        blocos: list[Bloco] = [
            Paragrafo("Cada entrega é aceita quando atinge as metas abaixo, medidas como descrito.")
        ]
        indicadores = self.relatorio.indicadores
        if indicadores:
            linhas = [
                [i.nome, _ou_falta(i.meta), _ou_falta(i.prazo), _ou_falta(i.como_medir)]
                for i in indicadores
            ]
            blocos.append(
                Tabela(
                    ["Indicador", "Meta", "Prazo", "Como medir"], linhas, larguras=[2, 1, 1.3, 2]
                )
            )
        else:
            blocos.append(Aviso(FALTA))
        criterio = self.dados.modelo.criterio_de_aceite
        if criterio is not None:
            questionario = self.relatorio.questionario
            for referencia in questionario.bloco(criterio.bloco).referencias:
                if referencia.titulo == criterio.tabela:
                    blocos += [
                        Titulo(referencia.titulo, 2),
                        Tabela(list(referencia.colunas), [list(li) for li in referencia.linhas]),
                    ]
        return blocos

    def _validade(self) -> list[Bloco]:
        return [
            Paragrafo(
                f"Esta proposta é válida por {self.dados.validade_dias} dias, até "
                f"{data_br(self.validade)}. Depois disso, valores e prazos podem ser revistos."
            )
        ]

    def _aceite(self) -> list[Bloco]:
        d = self.dados
        valores = [("Nome", d.cliente_representante), ("Cargo", d.cliente_cargo)]
        return [
            Paragrafo(
                "Ao assinar, as partes aceitam esta proposta nos termos acima, incluindo as "
                "Condições Gerais do anexo, que fazem parte dela. A assinatura autoriza o "
                "início da primeira fase."
            ),
            Assinatura(
                f"Pelo contratante — {self.relatorio.empresa}",
                valores=tuple((campo, valor) for campo, valor in valores if valor),
            ),
            assinatura_do_consultor(self.consultor),
        ]

    def _condicoes_gerais(self) -> list[Bloco]:
        c = self.consultor
        valores = {
            "cliente.empresa": self.relatorio.empresa,
            "consultor.empresa": c.empresa if c else None,
            "consultor.nome": c.nome if c else None,
            "foro": c.cidade_uf if c else None,
        }
        blocos: list[Bloco] = [
            QuebraDePagina(),
            Titulo(TITULO_ANEXO),
            Paragrafo(
                "Estas Condições Gerais fazem parte da proposta e são aceitas com a assinatura "
                "da seção de aceite."
            ),
        ]
        for numero, clausula in enumerate(self.dados.clausulas, start=1):
            texto = preencher_marcadores(clausula.texto, valores, FALTA)
            blocos.append(Titulo(f"{numero}. {clausula.titulo}", 2))
            blocos += [Paragrafo(linha.strip()) for linha in texto.splitlines() if linha.strip()]
        return blocos

    def montar(self) -> Documento:
        secoes = [
            ("Identificação das partes", self._partes),
            ("Contexto", self._contexto),
            ("Escopo por fase", self._escopo),
            ("Entregáveis e cronograma", self._cronograma),
            ("Investimento", self._investimento),
            ("Condições de pagamento, impostos e reajuste", self._condicoes),
            ("Premissas e hipóteses", self._premissas),
            ("Responsabilidades do cliente", self._responsabilidades),
            ("Critério de aceite", self._criterio_de_aceite),
            ("Validade", self._validade),
            ("Aceite", self._aceite),
        ]
        blocos: list[Bloco] = [self._capa(), QuebraDePagina()]
        for numero, (titulo, montar) in enumerate(secoes, start=1):
            if montar == self._aceite:
                blocos.append(QuebraDePagina())  # as duas assinaturas na mesma página
            blocos += [Titulo(f"{numero}. {titulo}"), *montar()]
        blocos += self._condicoes_gerais()
        return Documento(f"{self.dados.modelo.titulo} — {self.relatorio.empresa}", blocos)


def montar_proposta(dados: DadosProposta, emissao: EmissaoProposta) -> Documento:
    return _MontadorProposta(dados, emissao).montar()
