"""Formulários HTML: tudo chega como texto e é convertido aqui antes de ir ao repositório.

A validação de verdade (texto obrigatório, número negativo…) continua no repositório;
aqui só se transforma "40" em 40 e "2026-10-07" em data.
"""

from datetime import date
from typing import Any

from pydantic import BaseModel


def inteiro_ou_nada(rotulo: str, texto: str) -> int | None:
    texto = texto.strip()
    if not texto:
        return None
    try:
        return int(texto)
    except ValueError:
        raise ValueError(f"{rotulo} precisa ser um número inteiro (recebido '{texto}')") from None


def data_iso(rotulo: str, texto: str) -> date:
    # O <input type="date"> do navegador sempre envia no formato AAAA-MM-DD.
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ValueError(f"{rotulo} inválida (recebido '{texto}')") from None


class FormularioCliente(BaseModel):
    nome: str = ""
    empresa: str = ""
    setor: str = ""
    num_funcionarios: str = ""
    contato: str = ""

    def campos(self) -> dict[str, Any]:
        """Campos prontos para o repositório (campo em branco vira "sem valor")."""
        return {
            "nome": self.nome,
            "empresa": self.empresa,
            "setor": self.setor,
            "num_funcionarios": inteiro_ou_nada("Nº de funcionários", self.num_funcionarios),
            "contato": self.contato,
        }
