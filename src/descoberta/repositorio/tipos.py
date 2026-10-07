"""Tipo de coluna para guardar `Decimal` no SQLite sem perder precisão.

O SQLite não tem tipo decimal exato: uma coluna `Numeric` do SQLAlchemy vira número de
ponto flutuante por baixo, e R$ 0,10 poderia voltar como 0,1000000000000000055. Aqui o
valor é gravado como texto ("0.10") e relido como `Decimal("0.10")`, idêntico.
Como as contas são feitas em Python (camada `dominio`), e não em SQL, guardar como texto
não atrapalha nada.
"""

from decimal import Decimal

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator


class DecimalTexto(TypeDecorator):
    impl = String
    cache_ok = True  # o tipo não tem estado; o SQLAlchemy pode reaproveitar consultas

    def process_bind_param(self, value, dialect):
        """Python → banco."""
        if value is None:
            return None
        if not isinstance(value, Decimal):
            raise TypeError(f"esperava Decimal para gravar no banco (recebido {value!r})")
        return str(value)

    def process_result_value(self, value, dialect):
        """Banco → Python."""
        return None if value is None else Decimal(value)
