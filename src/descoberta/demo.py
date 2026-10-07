"""Banco de demonstração com o caso de referência "Construtora Alvorada / Roberto".

    uv run python -m descoberta.demo              # cria data/demo.db
    uv run python -m descoberta.demo outro.db     # ou outro arquivo

Rodar de novo recria o arquivo do zero. O banco real (data/descoberta.db) nunca é tocado.

As respostas usam só os fatos levantados com o cliente; perguntas sem informação ficam em
branco. Os números (métricas, notas e sinais) são os do caso de referência dos testes
(`tests/conftest.py`), incluindo as hipóteses registradas lá (custo da hora de R$ 100 e
30 h economizadas por mês).
"""

import sys
from datetime import date
from pathlib import Path

from sqlmodel import Session

from descoberta.repositorio import (
    CAMINHO_BANCO_PADRAO,
    StatusSessao,
    criar_cliente,
    criar_engine,
    criar_sessao,
    criar_tabelas,
    marcar_sinal,
    salvar_metricas,
    salvar_nota,
    salvar_resposta,
)

CAMINHO_DEMO = Path("data") / "demo.db"
VERSAO_QUESTIONARIO = 1

CLIENTE = {
    "nome": "Roberto",
    "empresa": "Construtora Alvorada",
    "setor": "Construção civil: obras residenciais e pequenas reformas comerciais",
    "num_funcionarios": 35,
}

METRICAS = {
    "horas_por_ocorrencia": 4,
    "frequencia_quantidade": 15,
    "frequencia_periodo": "mes",
    "custo_hora": 100,  # hipótese do caso de referência
    "horas_economizadas_mes": 30,  # hipótese: metade das 60 h/mês do Marcos
    "investimento": 20_000,
    "custo_fixo_mes": 400,
}

NOTAS = {
    # Prontidão de dados (score 4 → "fase 0").
    "disponibilidade": 1,
    "volume": 1,
    "rotulos": 1,
    "qualidade": 0,
    "acesso_legal": 1,
    # Viabilidade final (a nota de prontidão de dados é derivada do score acima).
    "dor_clara": 3,
    "ia_caminho_certo": 2,
    "retorno_viavel": 2,
    "riscos_controlaveis": 2,
    "comprometimento_cliente": 2,
}

SINAIS = ["b1.s4", "b2.s2", "b2.s3", "b8.s4", "b9.s1"]

RESPOSTAS = {
    # Bloco 1 — Problema de negócio
    "b1.o1": (
        "Avaliar os chamados de fissura nas obras, tanto em obra em andamento quanto depois "
        "da entrega."
    ),
    "b1.o2": "Cerca de 15 chamados de fissura por mês.",
    "b1.o3": (
        "Só o Marcos, único engenheiro: cada chamado toma meio dia dele (4 h), com obras a "
        "até 80 km. A Cida, na recepção, anota os chamados."
    ),
    "b1.o4": "Já houve processo judicial.",
    "b1.o5": (
        "As horas do Marcos com chamados cairiam pela metade, e a resposta ao cliente "
        "passaria de 3 dias para 1."
    ),
    "b1.o6": "No dia a dia, os mestres de obra (pelo celular) e o Marcos.",
    "b1.o7": "O Marcos: é ele quem decide cada caso, pela experiência.",
    # Bloco 2 — Processo atual × futuro
    "b2.o1": (
        "O chamado chega pela recepção (a Cida anota num caderno) ou pelo WhatsApp. Os "
        "mestres de obra ou o próprio cliente mandam fotos pelo WhatsApp. O Marcos avalia, "
        "mede a abertura com régua no local e decide. Nos casos graves, faz um laudo em "
        "Word; nos simples, responde só pelo WhatsApp."
    ),
    "b2.o2": "Caderno da recepção, WhatsApp, Word (laudos) e a planilha de obras.",
    "b2.o3": (
        "Na avaliação pelo Marcos: meio dia por chamado, com deslocamento de até 80 km; o "
        "cliente espera 3 dias pela resposta."
    ),
    "b2.o4": (
        "A gravidade da fissura, decidida pela experiência do Marcos: abertura medida com "
        "régua no local, posição, inclinação, proximidade de viga ou janela. Não há "
        "critério escrito."
    ),
    # Bloco 3 — Adequação de IA
    "b3.o1": "Não: o Marcos decide pela experiência e não há critério escrito.",
    "b3.o2": (
        "Em parte: cerca de 500 fotos em 2 anos. Só os casos graves (cerca de 40) têm "
        "laudo; os simples foram respondidos só no WhatsApp."
    ),
    "b3.o3": "Imagens: fotos das fissuras.",
    # Bloco 4 — Dados
    "b4.o1": (
        "Fotos no celular do Marcos (recebidas pelo WhatsApp), laudos em Word, o caderno da "
        "recepção e a planilha de obras."
    ),
    "b4.o2": "Cerca de 500 fotos em 2 anos.",
    "b4.o3": (
        "Só nos casos graves (cerca de 40), que têm laudo em Word. Os simples foram "
        "respondidos só no WhatsApp."
    ),
    "b4.o4": "As fotos ficam no celular do Marcos.",
    "b4.o5": "Sim: as fotos mostram pessoas e o interior das casas.",
    "b4.vc1": "Os mestres de obra ou o próprio cliente, que mandam pelo WhatsApp.",
    "b4.vc2": "Não há padrão de distância, luz ou ângulo.",
    "b4.vc3": "Não. A abertura é medida pelo Marcos com régua, no local.",
    "b4.vc4": "Fotos recebidas pelo WhatsApp, guardadas no celular do Marcos.",
    # Bloco 5 — Critérios de sucesso
    "b5.o1": "As horas do Marcos com chamados e o prazo de resposta ao cliente.",
    "b5.o2": (
        "Horas do Marcos: cerca de 60 h/mês (15 chamados × 4 h), meta de reduzir pela "
        "metade. Resposta ao cliente: de 3 dias para 1."
    ),
    # Bloco 6 — Requisitos não funcionais
    "b6.o1": "No celular, pelos mestres de obra, em campo.",
    "b6.o2": "Não: o sinal é fraco nas obras.",
    "b6.o3": "Os mestres de obra; cerca de 15 chamados por mês.",
    "b6.o4": "Resposta no mesmo dia é suficiente.",
    "b6.o6": "De R$ 300 a R$ 400 por mês.",
    # Bloco 7 — Riscos e compliance
    "b7.o1": "Sim: as fotos mostram pessoas e o interior das casas dos clientes.",
    # Bloco 8 — Integração e infraestrutura
    "b8.o1": "Não há ERP: só a planilha de obras e o WhatsApp.",
    "b8.o3": 'O sobrinho do Roberto ajuda com o computador "quando dá".',
    # Bloco 9 — Restrições do projeto
    "b9.o1": "Em fases, de R$ 15 mil a R$ 20 mil.",
    "b9.o3": "O Marcos, com 3 horas por semana.",
}


def popular_demo(caminho: Path | str = CAMINHO_DEMO) -> int:
    """Recria o banco de demonstração e devolve o id da sessão do Roberto."""
    caminho = Path(caminho)
    if caminho.resolve() == CAMINHO_BANCO_PADRAO.resolve():
        raise ValueError(f"{caminho} é o banco real; a demonstração usa um arquivo próprio")
    caminho.unlink(missing_ok=True)

    engine = criar_engine(caminho)
    try:
        criar_tabelas(engine)
        with Session(engine) as session:
            cliente = criar_cliente(session, **CLIENTE)
            sessao = criar_sessao(
                session,
                cliente_id=cliente.id,
                data=date(2026, 10, 7),
                versao_questionario=VERSAO_QUESTIONARIO,
                tipo_solucao="visao_computacional",
                status=StatusSessao.em_andamento,
            )
            salvar_metricas(session, sessao.id, **METRICAS)
            for criterio_id, nota in NOTAS.items():
                salvar_nota(session, sessao.id, criterio_id, nota)
            for sinal_id in SINAIS:
                marcar_sinal(session, sessao.id, sinal_id)
            for pergunta_id, texto in RESPOSTAS.items():
                salvar_resposta(session, sessao.id, pergunta_id, texto)
            return sessao.id
    finally:
        engine.dispose()  # no Windows, o arquivo só pode ser apagado depois de fechado


def main(argumentos: list[str] | None = None) -> None:
    argumentos = sys.argv[1:] if argumentos is None else argumentos
    caminho = Path(argumentos[0]) if argumentos else CAMINHO_DEMO
    try:
        popular_demo(caminho)
    except PermissionError:
        sys.exit(f"Não foi possível recriar {caminho}: feche a app (uvicorn) e tente de novo.")
    banco = caminho.as_posix()
    rodar = "uv run uvicorn descoberta.web.app:app --reload"
    print(f"Banco de demonstração criado em {banco}. Para abrir a app com ele:")
    print(f'  PowerShell: $env:DESCOBERTA_BANCO = "{banco}"; {rodar}')
    print(f"  Bash:       DESCOBERTA_BANCO={banco} {rodar}")


if __name__ == "__main__":
    main()
