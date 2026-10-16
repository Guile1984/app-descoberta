"""Segredos e rede: a chave nunca vai para o Git e os testes nunca saem da máquina."""

import json
import re
import socket
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
# Montado em partes para este arquivo não conter o próprio padrão que procura.
PREFIXO_CHAVE = "sk-" + "ant-"


def _arquivos_versionados() -> list[Path]:
    saida = subprocess.run(
        ["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, check=True
    ).stdout.decode("utf-8")
    return [RAIZ / nome for nome in saida.split("\0") if nome]


def test_nenhum_arquivo_versionado_tem_chave_de_api():
    com_chave = []
    for arquivo in _arquivos_versionados():
        if not arquivo.is_file():
            continue
        try:
            texto = arquivo.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binário (PDF, fonte, imagem)
        if PREFIXO_CHAVE in texto:
            com_chave.append(arquivo.relative_to(RAIZ).as_posix())
    assert com_chave == []


def test_env_fora_do_git_e_env_example_dentro():
    def ignorado(nome: str) -> bool:
        resultado = subprocess.run(["git", "check-ignore", "-q", nome], cwd=RAIZ)
        return resultado.returncode == 0

    for nome in (".env", ".env.local", ".env.production", ".env.qualquer"):
        assert ignorado(nome), nome
    assert not ignorado(".env.example")
    assert ".env.example" in {p.name for p in _arquivos_versionados()}


def test_env_example_sem_valores():
    for linha in (RAIZ / ".env.example").read_text(encoding="utf-8").splitlines():
        if linha.strip() and not linha.lstrip().startswith("#"):
            nome, _, valor = linha.partition("=")
            assert valor.strip() == "", f"{nome} não pode ter valor no exemplo"


def test_claude_code_nao_le_nem_edita_o_env():
    regras = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
    negadas = set(regras["permissions"]["deny"])
    for ferramenta in ("Read", "Edit"):
        assert f"{ferramenta}(**/.env)" in negadas
        assert f"{ferramenta}(**/.env.local)" in negadas
    assert not any(".env.example" in regra for regra in negadas)


# --- Os testes não saem da máquina (fixture automática do conftest) ---


def test_conexao_externa_e_bloqueada():
    # ConnectionRefusedError: para a app, é o mesmo que estar sem internet.
    with pytest.raises(ConnectionRefusedError, match="bloqueada nos testes"):
        socket.create_connection(("api.anthropic.com", 443), timeout=1)
    with socket.socket() as s, pytest.raises(ConnectionRefusedError, match="bloqueada"):
        s.connect(("93.184.216.34", 80))


def test_conexao_local_continua_permitida():
    servidor = socket.socket()
    servidor.bind(("127.0.0.1", 0))
    servidor.listen()
    try:
        with socket.create_connection(servidor.getsockname(), timeout=1):
            pass
    finally:
        servidor.close()


def test_chave_e_provedor_fora_do_ambiente_dos_testes():
    import os

    assert "ANTHROPIC_API_KEY" not in os.environ
    assert "DESCOBERTA_LLM_PROVEDOR" not in os.environ


def test_actions_do_ci_fixadas_pelo_hash():
    # Uma tag (v4) pode ser movida para outro código; o hash do commit, não.
    soltas = []
    for workflow in (RAIZ / ".github" / "workflows").glob("*.yml"):
        for linha in workflow.read_text(encoding="utf-8").splitlines():
            if "uses:" in linha and not re.search(r"@[0-9a-f]{40}\b", linha):
                soltas.append(f"{workflow.name}: {linha.strip()}")
    assert soltas == []


# A única exceção: o job que publica o site no GitHub Pages precisa escrever no Pages e
# provar ao GitHub de qual workflow veio (id-token). Nenhum job escreve no repositório.
PERMISSOES_DE_JOB = {("docs.yml", "publicar"): {"pages": "write", "id-token": "write"}}


def test_workflows_so_com_permissao_de_leitura():
    for workflow in (RAIZ / ".github" / "workflows").glob("*.yml"):
        texto = workflow.read_text(encoding="utf-8")
        assert "permissions:\n  contents: read" in texto, workflow.name
        fluxo = yaml.safe_load(texto)
        assert fluxo["permissions"] == {"contents": "read"}, workflow.name
        for nome, job in fluxo["jobs"].items():
            if "permissions" in job:
                esperado = PERMISSOES_DE_JOB.get((workflow.name, nome))
                assert job["permissions"] == esperado, f"{workflow.name}: job {nome}"


def test_jobs_do_ci_tem_limite_de_tempo():
    # Sem limite, um teste travado prende o runner por 6 horas (o padrão do GitHub).
    for workflow in (RAIZ / ".github" / "workflows").glob("*.yml"):
        texto = workflow.read_text(encoding="utf-8")
        jobs = len(re.findall(r"^    runs-on:", texto, re.M))
        assert texto.count("timeout-minutes:") == jobs, workflow.name
