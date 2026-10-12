"""Perfil do consultor: formulário comum (fora da reunião), como o de clientes.

O formulário envia também um arquivo (o logotipo), por isso usa
enctype="multipart/form-data". O logotipo é conferido junto com os outros campos: se ele
for recusado, nada é gravado e o formulário volta com o que foi digitado.
"""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from descoberta.imagens import TAMANHO_MAXIMO
from descoberta.repositorio import PerfilConsultor, obter_perfil, salvar_perfil
from descoberta.rotulos import UFS

from ..dependencias import Banco, html, redirecionar

router = APIRouter()


Texto = Annotated[str, Form()]


def _formulario(
    request: Request,
    valores: dict,
    perfil: PerfilConsultor | None,
    *,
    primeiro_uso: bool,
    salvo: bool = False,
    erro: str | None = None,
):
    return html(
        request,
        "perfil/formulario.html",
        status_code=422 if erro else 200,
        valores=valores,
        tem_logotipo=bool(perfil and perfil.logotipo),
        dados_ficticios=bool(perfil and perfil.dados_ficticios),
        primeiro_uso=primeiro_uso,
        salvo=salvo,
        erro=erro,
        ufs=UFS,
    )


@router.get("/perfil")
def formulario(request: Request, banco: Banco, primeiro_uso: bool = False, salvo: bool = False):
    perfil = obter_perfil(banco)
    valores = perfil.model_dump(exclude={"logotipo"}) if perfil else {}
    return _formulario(request, valores, perfil, primeiro_uso=primeiro_uso, salvo=salvo)


@router.post("/perfil")
def salvar(
    request: Request,
    banco: Banco,
    nome: Texto = "",
    empresa: Texto = "",
    cpf_cnpj: Texto = "",
    email: Texto = "",
    telefone: Texto = "",
    cidade: Texto = "",
    uf: Texto = "",
    remover_logotipo: Texto = "",
    primeiro_uso: Texto = "",
    logotipo: UploadFile | None = None,
):
    # Campos um a um (e não um modelo de formulário): o FastAPI não junta um modelo de
    # formulário com um arquivo enviado no mesmo pedido.
    campos = {
        "nome": nome,
        "empresa": empresa,
        "cpf_cnpj": cpf_cnpj,
        "email": email,
        "telefone": telefone,
        "cidade": cidade,
        "uf": uf,
    }
    if remover_logotipo:
        campos["logotipo"] = None
    elif logotipo is not None and logotipo.filename:
        # Lê no máximo 1 byte além do limite: o suficiente para saber que passou dele.
        campos["logotipo"] = logotipo.file.read(TAMANHO_MAXIMO + 1)
    try:
        salvar_perfil(banco, **campos)
    except (ValueError, TypeError) as erro:
        banco.rollback()
        return _formulario(
            request,
            campos,
            obter_perfil(banco),
            primeiro_uso=bool(primeiro_uso),
            erro=str(erro),
        )
    return redirecionar(request, "/" if primeiro_uso else "/perfil?salvo=1")


@router.get("/perfil/logotipo.png")
def logotipo(banco: Banco):
    perfil = obter_perfil(banco)
    if perfil is None or perfil.logotipo is None:
        raise HTTPException(404, "Nenhum logotipo cadastrado.")
    # no-store: depois de trocar o logotipo, a tela mostra o novo, sem cópia antiga.
    return Response(perfil.logotipo, media_type="image/png", headers={"Cache-Control": "no-store"})
