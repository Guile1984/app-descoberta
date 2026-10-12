"""Perfil do consultor: uma linha só no banco local, preenchida no primeiro uso."""

import re
from typing import Any

from sqlmodel import Session

from descoberta.dominio.documento_fiscal import formatar_cpf_cnpj
from descoberta.imagens import preparar_logotipo
from descoberta.rotulos import UFS

from ._comum import aplicar_campos, booleano, gravar, texto_obrigatorio, texto_opcional
from .modelos import PerfilConsultor, agora

ID_PERFIL = 1
_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _cpf_cnpj(nome: str, valor: Any) -> str | None:
    texto = texto_opcional(nome, valor)
    return None if texto is None else formatar_cpf_cnpj(texto)


def _email(nome: str, valor: Any) -> str | None:
    texto = texto_opcional(nome, valor)
    if texto is not None and not _EMAIL.fullmatch(texto):
        raise ValueError(f"e-mail {texto!r} inválido")
    return texto


def _uf(nome: str, valor: Any) -> str | None:
    texto = texto_opcional(nome, valor)
    if texto is None:
        return None
    if texto.upper() not in UFS:
        raise ValueError(f"UF {texto!r} inválida; use a sigla, como SP ou MG")
    return texto.upper()


def _logotipo(nome: str, valor: Any) -> bytes | None:
    return None if valor is None else preparar_logotipo(valor)


_VALIDADORES = {
    "nome": texto_obrigatorio,
    "empresa": texto_obrigatorio,
    "cpf_cnpj": _cpf_cnpj,
    "email": _email,
    "telefone": texto_opcional,
    "cidade": texto_opcional,
    "uf": _uf,
    "logotipo": _logotipo,
    "dados_ficticios": booleano,
}


def obter_perfil(session: Session) -> PerfilConsultor | None:
    return session.get(PerfilConsultor, ID_PERFIL)


def salvar_perfil(session: Session, **campos: Any) -> PerfilConsultor:
    """Cria o perfil (nome e empresa obrigatórios) ou atualiza só os campos informados.

    Tudo é conferido antes de gravar qualquer coisa: com um logotipo recusado, nem os
    outros campos são gravados. `logotipo` recebe o arquivo como veio (bytes) e guarda a
    versão limpa (PNG sem metadados); None apaga o logotipo.
    """
    perfil = obter_perfil(session)
    if perfil is None:
        faltando = [nome for nome in ("nome", "empresa") if nome not in campos]
        if faltando:
            raise ValueError(f"{faltando[0]} é obrigatório para criar o perfil")
        perfil = PerfilConsultor(id=ID_PERFIL, nome="", empresa="")
    aplicar_campos(perfil, campos, _VALIDADORES)
    perfil.atualizado_em = agora()
    return gravar(session, perfil)


def salvar_logotipo(session: Session, dados: bytes) -> PerfilConsultor:
    """Confere, limpa (sem metadados) e guarda o logotipo. ValueError se recusado."""
    if obter_perfil(session) is None:
        raise ValueError("preencha o perfil antes de enviar o logotipo")
    return salvar_perfil(session, logotipo=dados)


def remover_logotipo(session: Session) -> PerfilConsultor | None:
    if obter_perfil(session) is None:
        return None
    return salvar_perfil(session, logotipo=None)
