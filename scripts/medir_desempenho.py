"""Mede tempos de resposta, de geração de documentos e de volume (evidências da ISO 25010).

Uso (na raiz do projeto):

    uv run python scripts/medir_desempenho.py                    # mostra a tabela
    uv run python scripts/medir_desempenho.py --saida docs/qualidade/medicoes.json

Tudo roda nesta máquina, com bancos temporários (o caso Roberto do demo e um volume
sintético); o banco real nunca é tocado. Os pedidos vão direto à app (TestClient), sem a
rede nem o navegador: o tempo é o do servidor. Os números variam de uma máquina para
outra, por isso o script não é um teste do CI: serve para registrar a medição, com os
dados da máquina, e comparar entre versões.
"""

import argparse
import json
import os
import platform
import statistics
import sys
import tempfile
import time
import tracemalloc
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session

import descoberta
from descoberta.demo import popular_demo
from descoberta.repositorio import criar_cliente, criar_engine, criar_sessao, migrar
from descoberta.web.app import criar_app

RAIZ = Path(__file__).resolve().parents[1]
PASTA_CONFIG = RAIZ / "config"


def _tempos(funcao: Callable[[], object], repeticoes: int) -> dict[str, float]:
    funcao()  # aquecimento: a primeira vez carrega módulos e templates
    medidas = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        funcao()
        medidas.append((time.perf_counter() - inicio) * 1000)
    medidas.sort()
    return {
        "n": repeticoes,
        "p50_ms": round(statistics.median(medidas), 1),
        "p95_ms": round(medidas[max(0, round(0.95 * repeticoes) - 1)], 1),
        "max_ms": round(medidas[-1], 1),
    }


def _ok(resposta):
    if resposta.status_code >= 400:
        raise RuntimeError(f"{resposta.request.url}: HTTP {resposta.status_code}")
    return resposta


def _cliente(caminho: Path) -> TestClient:
    app = criar_app(caminho_banco=caminho, pasta_config=PASTA_CONFIG)
    return TestClient(app, base_url="http://127.0.0.1", follow_redirects=False)


def medir_inicio(pasta: Path) -> dict[str, dict]:
    """Tempo para ligar a app (inclui carregar o questionário e migrar o banco)."""

    def ligar(caminho: Path) -> float:
        inicio = time.perf_counter()
        with _cliente(caminho):
            pass
        return round((time.perf_counter() - inicio) * 1000, 1)

    novo = ligar(pasta / "inicio-novo.db")
    em_dia = ligar(pasta / "inicio-novo.db")
    legado = pasta / "inicio-legado.db"
    popular_demo(legado, hoje=date.today())
    engine = criar_engine(legado)
    with engine.begin() as conexao:
        conexao.execute(text("DROP TABLE alembic_version"))
    engine.dispose()
    return {
        "banco_novo_ms": novo,
        "banco_em_dia_ms": em_dia,
        "banco_legado_reconhecido_ms": ligar(legado),
    }


def medir_tela(cliente: TestClient, sessao_id: int, repeticoes: int) -> dict[str, dict]:
    s = f"/sessoes/{sessao_id}"
    htmx = {"HX-Request": "true"}
    contador = iter(range(10**9))
    return {
        "abrir_sessao": _tempos(lambda: _ok(cliente.get(s)), repeticoes),
        "trocar_de_aba": _tempos(
            lambda: _ok(cliente.get(f"{s}?bloco=4", headers=htmx)), repeticoes
        ),
        "salvar_resposta": _tempos(
            lambda: _ok(
                cliente.post(
                    f"{s}/respostas/b1.o2",
                    data={"texto": f"Cerca de 15 chamados por mês ({next(contador)})."},
                    headers=htmx,
                )
            ),
            repeticoes,
        ),
        "salvar_numero_e_recalcular": _tempos(
            lambda: (
                _ok(
                    cliente.post(
                        f"{s}/metricas/investimento", data={"valor": "20.000"}, headers=htmx
                    )
                ),
                _ok(cliente.get(f"{s}/calculos", headers=htmx)),
            ),
            repeticoes,
        ),
        "abrir_revisao": _tempos(lambda: _ok(cliente.get(f"{s}/revisao")), repeticoes),
        "previa_do_relatorio": _tempos(lambda: _ok(cliente.get(f"{s}/relatorio")), repeticoes),
    }


def medir_documentos(cliente: TestClient, sessao_id: int, repeticoes: int) -> dict[str, dict]:
    s = f"/sessoes/{sessao_id}"
    documentos = {
        "relatorio_markdown": f"{s}/relatorio.md?versao=cliente",
        "relatorio_docx": f"{s}/relatorio.docx?versao=cliente",
        "relatorio_pdf": f"{s}/relatorio.pdf?versao=cliente",
        "relatorio_pdf_interno": f"{s}/relatorio.pdf?versao=interna",
        "proposta_docx": f"{s}/proposta.docx",
        "proposta_pdf": f"{s}/proposta.pdf",
        "relatorio_e_proposta_pdf": f"{s}/proposta/relatorio-e-proposta.pdf",
    }
    resultado = {}
    for nome, url in documentos.items():
        medida = _tempos(lambda url=url: _ok(cliente.get(url)), repeticoes)
        medida["tamanho_kb"] = round(len(cliente.get(url).content) / 1024, 1)
        resultado[nome] = medida
    resultado["registrar_versao_do_relatorio"] = _tempos(
        lambda: _ok(cliente.post(f"{s}/relatorio/versoes", data={"versao": "cliente"})),
        max(3, repeticoes // 4),
    )
    return resultado


def medir_memoria(cliente: TestClient, sessao_id: int) -> dict[str, float]:
    """Pico de memória do Python ao gerar o PDF maior (relatório + proposta)."""
    tracemalloc.start()
    _ok(cliente.get(f"/sessoes/{sessao_id}/proposta/relatorio-e-proposta.pdf"))
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"pico_python_ao_gerar_pdf_mb": round(pico / 2**20, 1)}


def medir_volume(pasta: Path, clientes: int, sessoes_por_cliente: int, repeticoes: int) -> dict:
    """Escalabilidade (fora do escopo, só para registro): listas com muitos registros."""
    caminho = pasta / "volume.db"
    engine = criar_engine(caminho)
    migrar(engine)
    inicio = time.perf_counter()
    with Session(engine) as session:
        for i in range(clientes):
            cliente = criar_cliente(session, nome=f"Cliente {i}", empresa=f"Empresa Sintética {i}")
            for j in range(sessoes_por_cliente):
                criar_sessao(
                    session,
                    cliente_id=cliente.id,
                    data=date(2026, 1, 1 + j % 28),
                    versao_questionario=1,
                )
    carga = time.perf_counter() - inicio
    engine.dispose()
    with _cliente(caminho) as cliente:
        _ok(cliente.get("/perfil"))
        _ok(cliente.post("/perfil", data={"nome": "Consultor", "empresa": "Consultoria"}))
        lista = _ok(cliente.get("/"))
        if lista.status_code != 200 or f"Empresa Sintética {clientes - 1}" not in lista.text:
            raise RuntimeError("a lista de clientes não mostrou todos os clientes")
        resultado = {
            "clientes": clientes,
            "sessoes": clientes * sessoes_por_cliente,
            "carga_s": round(carga, 1),
            "lista_de_clientes": _tempos(lambda: _ok(cliente.get("/")), repeticoes),
            "detalhe_de_um_cliente": _tempos(
                lambda: _ok(cliente.get(f"/clientes/{clientes // 2}")), repeticoes
            ),
        }
    resultado["tamanho_do_banco_kb"] = round(caminho.stat().st_size / 1024, 1)
    return resultado


def maquina() -> dict[str, str]:
    return {
        "sistema": f"{platform.system()} {platform.release()} ({platform.version()})",
        "processador": platform.processor() or platform.machine(),
        "nucleos": str(os.cpu_count()),
        "python": platform.python_version(),
    }


def main(argumentos: list[str] | None = None) -> int:
    leitor = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    leitor.add_argument("--repeticoes", type=int, default=30)
    leitor.add_argument("--clientes", type=int, default=500)
    leitor.add_argument("--sessoes-por-cliente", type=int, default=2)
    leitor.add_argument("--saida", type=Path, help="grava o resultado em JSON neste arquivo")
    opcoes = leitor.parse_args(argumentos)

    with tempfile.TemporaryDirectory() as temporaria:
        pasta = Path(temporaria)
        demo = pasta / "demo.db"
        sessao_id = popular_demo(demo, hoje=date.today())
        tamanho_demo = round(demo.stat().st_size / 1024, 1)
        resultado = {
            "medido_em": datetime.now().isoformat(timespec="seconds"),
            "versao_da_app": descoberta.__version__,
            "maquina": maquina(),
            "inicio_da_app": medir_inicio(pasta),
        }
        with _cliente(demo) as cliente:
            resultado["tela_ao_vivo"] = medir_tela(cliente, sessao_id, opcoes.repeticoes)
            resultado["documentos"] = medir_documentos(
                cliente, sessao_id, max(5, opcoes.repeticoes // 3)
            )
            resultado["memoria"] = medir_memoria(cliente, sessao_id)
        resultado["banco_do_caso_roberto_kb"] = tamanho_demo
        resultado["volume"] = medir_volume(
            pasta, opcoes.clientes, opcoes.sessoes_por_cliente, max(5, opcoes.repeticoes // 3)
        )

    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    print(texto)
    if opcoes.saida:
        opcoes.saida.write_text(texto + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
