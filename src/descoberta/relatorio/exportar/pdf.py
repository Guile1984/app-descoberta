"""PDF com ReportLab: Python puro, sem programas externos (funciona offline no Windows).

O ReportLab monta o PDF a partir de "flowables" (parágrafo, tabela, quebra de página),
que correspondem um a um aos blocos do documento. A fonte DejaVu Sans vai embutida no
arquivo: as fontes padrão do PDF não têm caracteres como "≥", "→" e "✓".
"""

import io
from pathlib import Path
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..documento import (
    Assinatura,
    Aviso,
    Capa,
    Lista,
    QuebraDePagina,
    Tabela,
    Titulo,
)
from ..documento import Paragrafo as ParagrafoDoc
from .estilo import COR_AVISO, COR_CABECALHO, COR_DESTAQUE, CORES_NIVEL

if TYPE_CHECKING:
    from ..emissao import RelatorioEmitido

PASTA_FONTES = Path(__file__).resolve().parents[1] / "fontes"
FONTE, FONTE_NEGRITO = "DejaVuSans", "DejaVuSans-Bold"
MARGEM = 2 * cm
LARGURA_UTIL = A4[0] - 2 * MARGEM


def _registrar_fontes() -> None:
    if FONTE in pdfmetrics.getRegisteredFontNames():
        return
    pdfmetrics.registerFont(TTFont(FONTE, PASTA_FONTES / "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont(FONTE_NEGRITO, PASTA_FONTES / "DejaVuSans-Bold.ttf"))
    # <b> dentro de um parágrafo usa a versão em negrito da família.
    pdfmetrics.registerFontFamily(
        FONTE, normal=FONTE, bold=FONTE_NEGRITO, italic=FONTE, boldItalic=FONTE_NEGRITO
    )


def _estilos() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("base", fontName=FONTE, fontSize=10, leading=14, spaceAfter=6)
    return {
        "base": base,
        "celula": ParagraphStyle("celula", parent=base, fontSize=8.5, leading=11, spaceAfter=0),
        "titulo1": ParagraphStyle(
            "titulo1",
            parent=base,
            fontName=FONTE_NEGRITO,
            fontSize=15,
            leading=19,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "titulo2": ParagraphStyle(
            "titulo2",
            parent=base,
            fontName=FONTE_NEGRITO,
            fontSize=11.5,
            leading=15,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "capa": ParagraphStyle(
            "capa",
            parent=base,
            fontName=FONTE_NEGRITO,
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "subcapa": ParagraphStyle(
            "subcapa", parent=base, fontSize=18, leading=24, alignment=TA_CENTER, spaceAfter=30
        ),
        "faixa": ParagraphStyle(
            "faixa",
            parent=base,
            fontName=FONTE_NEGRITO,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
    }


def _p(texto: str, estilo: ParagraphStyle) -> Paragraph:
    # O Paragraph do ReportLab lê uma marcação parecida com HTML: o texto precisa ser escapado.
    return Paragraph(escape(texto).replace("\n", "<br/>"), estilo)


def _tabela(tabela: Tabela, estilos) -> Table:
    larguras = tabela.larguras or [1] * len(tabela.colunas)
    total = sum(larguras)
    cabecalho = ParagraphStyle("cab", parent=estilos["celula"], fontName=FONTE_NEGRITO)
    dados = [[_p(c, cabecalho) for c in tabela.colunas]]
    dados += [[_p(c, estilos["celula"]) for c in linha] for linha in tabela.linhas]
    grade = Table(
        dados, colWidths=[LARGURA_UTIL * parte / total for parte in larguras], repeatRows=1
    )
    comandos = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COR_CABECALHO)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i, linha in enumerate(tabela.niveis or []):
        for j, nivel in enumerate(linha):
            if nivel:
                comandos.append(
                    ("BACKGROUND", (j, i + 1), (j, i + 1), colors.HexColor(CORES_NIVEL[nivel]))
                )
    grade.setStyle(TableStyle(comandos))
    return grade


def _caixa(conteudo, fundo: str) -> Table:
    caixa = Table([[conteudo]], colWidths=[LARGURA_UTIL])
    caixa.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fundo)),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return caixa


def _logotipo(dados: bytes) -> Image:
    """O logotipo cabe em 6 × 2,5 cm, sem distorcer."""
    imagem = Image(io.BytesIO(dados))
    escala = min(6 * cm / imagem.imageWidth, 2.5 * cm / imagem.imageHeight)
    imagem.drawWidth = imagem.imageWidth * escala
    imagem.drawHeight = imagem.imageHeight * escala
    return imagem


def _assinatura(bloco: Assinatura, estilos) -> KeepTogether:
    linhas = [
        [_p(f"{campo}:", estilos["base"]), _p(bloco.valor(campo) or "", estilos["base"])]
        for campo in bloco.campos
    ]
    # A última linha (a assinatura em si) é mais alta, para caber a assinatura à mão.
    alturas = [22] * (len(bloco.campos) - 1) + [40]
    grade = Table(linhas, colWidths=[3 * cm, LARGURA_UTIL - 3 * cm], rowHeights=alturas)
    grade.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (1, 0), (1, -1), 0.6, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ]
        )
    )
    titulo = Paragraph(f"<b>{escape(bloco.titulo)}</b>", estilos["base"])
    return KeepTogether([Spacer(1, 16), titulo, grade])


def _flowables(bloco, estilos) -> list:
    match bloco:
        case Capa():
            itens: list = [Spacer(1, 4 * cm)]
            if bloco.logotipo:
                itens = [Spacer(1, 1.5 * cm), _logotipo(bloco.logotipo), Spacer(1, 1.5 * cm)]
            if bloco.faixa:
                itens += [_caixa(_p(bloco.faixa, estilos["faixa"]), COR_DESTAQUE), Spacer(1, 20)]
            itens += [_p(bloco.titulo, estilos["capa"]), _p(bloco.subtitulo, estilos["subcapa"])]
            linhas = [
                [Paragraph(f"<b>{escape(r)}</b>", estilos["base"]), _p(v, estilos["base"])]
                for r, v in bloco.linhas
            ]
            itens.append(Table(linhas, colWidths=[4 * cm, LARGURA_UTIL - 4 * cm]))
            if bloco.nota:
                itens += [Spacer(1, 30), Paragraph(f"<i>{escape(bloco.nota)}</i>", estilos["base"])]
            return itens
        case Titulo():
            return [_p(bloco.texto, estilos["titulo1" if bloco.nivel == 1 else "titulo2"])]
        case ParagrafoDoc():
            texto = escape(bloco.texto)
            if bloco.rotulo:
                texto = f"<b>{escape(bloco.rotulo)}</b> {texto}"
            return [Paragraph(texto, estilos["base"])]
        case Aviso():
            return [_caixa(_p(bloco.texto, estilos["base"]), COR_AVISO), Spacer(1, 6)]
        case Lista():
            return [Paragraph(escape(i), estilos["base"], bulletText="•") for i in bloco.itens]
        case Tabela():
            return [_tabela(bloco, estilos), Spacer(1, 8)]
        case Assinatura():
            return [_assinatura(bloco, estilos)]
        case QuebraDePagina():
            return [PageBreak()]
    raise TypeError(f"bloco desconhecido: {bloco!r}")


def _canvas_com_rodape(rodape: str) -> type[canvas.Canvas]:
    """Canvas que escreve o rodapé com "Página X de Y".

    O total de páginas só é conhecido no fim: cada página é guardada ao terminar e o
    rodapé é desenhado em todas de uma vez, na hora de salvar.
    """

    class CanvasComRodape(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._paginas: list[dict] = []

        def showPage(self):  # noqa: N802 (nome do ReportLab)
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas)
            for estado in self._paginas:
                self.__dict__.update(estado)
                self.setFont(FONTE, 7)
                self.setFillColor(colors.HexColor("#656d76"))
                self.drawString(MARGEM, 1.2 * cm, rodape)
                self.drawRightString(
                    A4[0] - MARGEM, 1.2 * cm, f"Página {self._pageNumber} de {total}"
                )
                super().showPage()
            super().save()

    return CanvasComRodape


def exportar_pdf(emitido: "RelatorioEmitido") -> bytes:
    _registrar_fontes()
    estilos = _estilos()
    saida = io.BytesIO()
    pdf = SimpleDocTemplate(
        saida,
        pagesize=A4,
        leftMargin=MARGEM,
        rightMargin=MARGEM,
        topMargin=MARGEM,
        bottomMargin=MARGEM,
        title=emitido.documento.titulo,
        author="App de Descoberta",
    )
    historia = [f for bloco in emitido.documento.blocos for f in _flowables(bloco, estilos)]
    pdf.build(historia, canvasmaker=_canvas_com_rodape(emitido.rodape))
    return saida.getvalue()
