"""O consultor nos documentos (relatório e proposta), a partir do perfil da app."""

from dataclasses import dataclass

from .documento import FALTA, Assinatura

AVISO_CONSULTOR_FICTICIO = "Documento de demonstração: os dados do consultor são fictícios."
CAMPOS_ASSINATURA_CONSULTOR = ("Nome", "CPF/CNPJ", "Data", "Assinatura")


@dataclass(frozen=True)
class Consultor:
    nome: str
    empresa: str
    cpf_cnpj: str | None
    email: str | None
    telefone: str | None
    cidade: str | None
    uf: str | None
    logotipo: bytes | None
    dados_ficticios: bool

    @classmethod
    def do_perfil(cls, perfil) -> "Consultor | None":
        if perfil is None:
            return None
        return cls(
            nome=perfil.nome,
            empresa=perfil.empresa,
            cpf_cnpj=perfil.cpf_cnpj,
            email=perfil.email,
            telefone=perfil.telefone,
            cidade=perfil.cidade,
            uf=perfil.uf,
            logotipo=perfil.logotipo,
            dados_ficticios=perfil.dados_ficticios,
        )

    @property
    def contato(self) -> str:
        return " · ".join(c for c in (self.email, self.telefone) if c)

    @property
    def cidade_uf(self) -> str | None:
        return cidade_uf(self.cidade, self.uf)


def cidade_uf(cidade: str | None, uf: str | None) -> str | None:
    """ "São Paulo/SP"; só a cidade ou só a UF quando falta a outra."""
    if cidade and uf:
        return f"{cidade}/{uf}"
    return cidade or uf


def linha_do_consultor(consultor: Consultor | None) -> str:
    """ "Ana Exemplo · Exemplo Consultoria em IA Ltda" (ou a marca do que falta)."""
    if consultor is None:
        return FALTA
    return f"{consultor.nome} · {consultor.empresa}"


def assinatura_do_consultor(consultor: Consultor | None) -> Assinatura:
    """Bloco de assinatura com nome e CPF/CNPJ já preenchidos (em branco sem perfil)."""
    if consultor is None:
        return Assinatura("Pelo consultor")
    titulo = f"Pelo consultor — {consultor.empresa}"
    if consultor.dados_ficticios:
        titulo += " (dados fictícios, demonstração)"
    valores = [("Nome", consultor.nome)]
    if consultor.cpf_cnpj:
        valores.append(("CPF/CNPJ", consultor.cpf_cnpj))
    return Assinatura(titulo, CAMPOS_ASSINATURA_CONSULTOR, tuple(valores))
