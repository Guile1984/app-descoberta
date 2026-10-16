# App de Descoberta para IA

Uma app local para o consultor conduzir, ao vivo, a **sessão de descoberta** com uma
pequena ou média empresa que quer uma solução de inteligência artificial, e sair dela com
o **Relatório de Descoberta** e a **Proposta Comercial** prontos para revisar e enviar.

Ela segue o [Modelo de Descoberta — Apps de IA para PMEs](modelo-descoberta.md): 10 blocos
de perguntas e o encerramento, com cálculos ao vivo (custo da dor, prontidão dos dados,
payback e score final de viabilidade). Funciona **sem internet** e guarda tudo **no seu
computador**.

!!! warning "Uso local, por uma pessoa só"
    A app escuta só em `127.0.0.1` e não tem login nem HTTPS. Não a exponha à rede sem as
    medidas do guia de [uso em produção](explicacao/uso-em-producao.md).

Para instalar, siga o
[README no GitHub](https://github.com/Guile1984/app-descoberta#instalação-no-windows-passo-a-passo):
o passo a passo para Windows, com dois cliques no `iniciar.bat`.

## Como esta documentação está organizada

Ela segue o modelo [Diátaxis](https://diataxis.fr/), em quatro partes, cada uma para um
momento diferente:

<div class="grid cards" markdown>

-   **[Tutorial](tutorial/primeira-sessao.md)**

    *Para aprender fazendo.* Sua primeira sessão, do zero até o relatório e a proposta do
    caso Roberto.

-   **Guias práticos**

    *Para uma tarefa específica.*
    [Sessão ao vivo](guias/sessao-ao-vivo.md) ·
    [Revisão pós-sessão](guias/revisao-pos-sessao.md) ·
    [Relatório e proposta](guias/relatorio-e-proposta.md) ·
    [Adaptar o questionário](guias/adaptar-questionario.md) ·
    [Adaptar as cláusulas](guias/adaptar-clausulas.md) ·
    [Configurar o LLM](guias/configurar-llm.md) ·
    [Backup](guias/backup-e-restauracao.md) ·
    [Atualizar](guias/atualizar-a-app.md)

-   **Referência**

    *Para consultar.*
    [Atalhos](referencia/atalhos.md) ·
    [Arquivos YAML](referencia/yaml.md) ·
    [Fórmulas e scores](referencia/formulas-e-scores.md) ·
    [Modelo de dados](referencia/modelo-de-dados.md) ·
    [Ambiente e comandos](referencia/ambiente-e-comandos.md)

-   **Explicação**

    *Para entender o porquê.*
    [A metodologia](explicacao/metodologia.md) ·
    [Arquitetura e decisões](explicacao/arquitetura.md) ·
    [Privacidade e LGPD](explicacao/privacidade-lgpd.md) ·
    [Qualidade (ISO/IEC 25010)](qualidade/evidencias.md) ·
    [Uso em produção](explicacao/uso-em-producao.md)

</div>

## Contribuir

Achou um erro, inclusive nesta documentação? Veja como contribuir no
[CONTRIBUTING.md](https://github.com/Guile1984/app-descoberta/blob/main/CONTRIBUTING.md).
Para relatar uma vulnerabilidade, **não abra uma issue pública**: siga o
[SECURITY.md](https://github.com/Guile1984/app-descoberta/blob/main/SECURITY.md).

Esta app foi desenvolvida com o Claude Code, sob direção e revisão do autor, Guilherme
Ferraz Stauffer. Código em MIT; metodologia em CC BY 4.0.
