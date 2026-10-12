"""Logotipo do consultor: conferido e regravado antes de ir para o banco.

- Aceita só PNG ou JPEG de até 1 MB; o formato é lido do conteúdo, não da extensão.
- Regrava como PNG a partir dos pixels, numa imagem nova. Isso apaga os metadados: uma
  foto de celular pode trazer a localização (GPS), o modelo do aparelho e a data.
- Reduz imagens grandes (o maior lado fica com até 800 px), suficiente para a capa.
"""

import io

from PIL import Image, UnidentifiedImageError

TAMANHO_MAXIMO = 1_000_000  # 1 MB
MAIOR_LADO = 800
FORMATOS = {"PNG", "JPEG"}
# Uma imagem pequena no disco pode virar bilhões de pixels na memória ("bomba de
# descompressão"); 25 milhões de pixels já é muito mais do que um logotipo precisa.
MAXIMO_DE_PIXELS = 25_000_000


def preparar_logotipo(dados: bytes) -> bytes:
    """O logotipo pronto para guardar (PNG limpo); ValueError com o motivo se recusado."""
    if not dados:
        raise ValueError("o arquivo do logotipo está vazio")
    if len(dados) > TAMANHO_MAXIMO:
        raise ValueError(f"o logotipo tem {len(dados) / 1_000_000:.1f} MB; o limite é 1 MB")
    try:
        with Image.open(io.BytesIO(dados)) as imagem:
            if imagem.format not in FORMATOS:
                raise ValueError("o logotipo precisa ser uma imagem PNG ou JPEG")
            if imagem.width * imagem.height > MAXIMO_DE_PIXELS:
                raise ValueError("o logotipo é grande demais (dimensões em pixels)")
            imagem.load()
            modo = "RGBA" if imagem.mode in ("RGBA", "LA", "P") else "RGB"
            pixels = imagem.convert(modo)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError("o logotipo precisa ser uma imagem PNG ou JPEG") from None
    # Imagem nova só com os pixels: nenhum metadado do arquivo original vem junto.
    limpa = Image.frombytes(modo, pixels.size, pixels.tobytes())
    limpa.thumbnail((MAIOR_LADO, MAIOR_LADO))
    saida = io.BytesIO()
    limpa.save(saida, "PNG", optimize=True)
    return saida.getvalue()
