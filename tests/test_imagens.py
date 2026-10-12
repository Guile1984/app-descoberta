"""Logotipo do consultor: só PNG ou JPEG, até 1 MB, regravado como PNG sem metadados."""

import io

import pytest
from PIL import Image

from descoberta.imagens import MAIOR_LADO, TAMANHO_MAXIMO, preparar_logotipo


def _imagem(formato: str, tamanho=(120, 60), modo="RGB", **opcoes) -> bytes:
    saida = io.BytesIO()
    Image.new(modo, tamanho, "navy").save(saida, formato, **opcoes)
    return saida.getvalue()


def _abrir(dados: bytes) -> Image.Image:
    return Image.open(io.BytesIO(dados))


@pytest.mark.parametrize("formato", ["PNG", "JPEG"])
def test_png_e_jpeg_viram_png(formato):
    resultado = _abrir(preparar_logotipo(_imagem(formato)))
    assert resultado.format == "PNG"
    assert resultado.size == (120, 60)


def test_transparencia_do_png_e_mantida():
    resultado = _abrir(preparar_logotipo(_imagem("PNG", modo="RGBA")))
    assert resultado.mode == "RGBA"


def test_metadados_sao_apagados():
    """Uma foto de celular pode trazer a localização (GPS) e o modelo do aparelho."""
    exif = Image.Exif()
    exif[0x010F] = "Fabricante do celular"  # Make
    exif[0x8825] = {2: (23.0, 33.0, 0.0)}  # GPSInfo: latitude
    original = _imagem("JPEG", exif=exif)
    assert _abrir(original).getexif()  # o original tem EXIF

    resultado = preparar_logotipo(original)
    assert not _abrir(resultado).getexif()
    assert b"Exif" not in resultado
    assert b"Fabricante" not in resultado


def test_imagem_grande_e_reduzida():
    resultado = _abrir(preparar_logotipo(_imagem("PNG", tamanho=(2000, 500))))
    assert resultado.size == (MAIOR_LADO, MAIOR_LADO // 4)


@pytest.mark.parametrize(
    ("dados", "erro"),
    [
        (b"", "vazio"),
        (b"nao sou uma imagem", "PNG ou JPEG"),
        (_imagem("GIF"), "PNG ou JPEG"),
        (_imagem("BMP"), "PNG ou JPEG"),
        (_imagem("PNG")[:40], "PNG ou JPEG"),  # arquivo cortado
    ],
    ids=["vazio", "texto", "gif", "bmp", "cortado"],
)
def test_arquivos_recusados(dados, erro):
    with pytest.raises(ValueError, match=erro):
        preparar_logotipo(dados)


def test_arquivo_maior_que_o_limite():
    with pytest.raises(ValueError, match="1 MB"):
        preparar_logotipo(b"\x89PNG" + b"0" * TAMANHO_MAXIMO)


def test_imagem_com_dimensoes_absurdas_e_recusada():
    """Uma "bomba de descompressão": arquivo pequeno que vira bilhões de pixels."""
    with pytest.raises(ValueError, match="grande demais"):
        preparar_logotipo(_imagem("PNG", tamanho=(9000, 9000), modo="1"))
