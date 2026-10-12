# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [Não publicado] — Sprint 7: LLM

### Adicionado
- Configuração do LLM em `config/llm.yaml` (pacote `llm.configuracao`, validada com
  Pydantic quando a app liga): provedor `desligado` (padrão), `claude` ou `ollama`;
  modelo padrão da API `claude-opus-5-5` com esforço `medium`; Ollama aceito só nesta
  máquina (localhost). A variável `DESCOBERTA_LLM_PROVEDOR` vale mais que o arquivo; um
  valor inválido impede a app de ligar, com mensagem clara.
- Chave da API só na variável de ambiente `ANTHROPIC_API_KEY`, lida na hora de usar e
  guardada como `SecretStr` (aparece como `**********` em log, erro ou repr).
- `.env.example` com `DESCOBERTA_LLM_PROVEDOR` e `ANTHROPIC_API_KEY` em branco; a app lê o
  `.env` com `uv run --env-file .env uvicorn ...`, sem dependência nova.
- `.claude/settings.json`: o Claude Code não lê nem edita `.env` e variações (exceto o
  `.env.example`) e não exibe a `ANTHROPIC_API_KEY` no terminal.
- Testes que nunca saem da máquina: uma fixture automática tira a chave e o provedor do
  ambiente e bloqueia conexões para fora (as locais, como as dos testes no navegador,
  continuam); testes de que nenhum arquivo versionado contém chave de API, de que o `.env`
  e variações ficam fora do Git e de que a chave nunca aparece ao ser exibida.

### Alterado
- `.gitignore`: além do `.env`, ignora `.env.*` (menos o `.env.example`).
- Regra de arquitetura: `llm` não importa `web` nem `repositorio`.

## [0.9.0] — 2026-10-11 — Sprint 6c: Proposta comercial

### Adicionado
- Perfil do consultor (tabela `perfil_consultor`, uma linha só, no banco local):
  - nome, empresa, CPF ou CNPJ, e-mail, telefone, cidade/UF e logotipo opcional;
  - tela `/perfil`; no primeiro uso, a tela inicial leva ao perfil (as outras páginas
    continuam abertas);
  - CPF e CNPJ conferidos pelos dígitos verificadores (`dominio.documento_fiscal`),
    inclusive o CNPJ alfanumérico, em vigor desde julho de 2026;
  - logotipo só PNG ou JPEG até 1 MB, regravado como PNG sem metadados (uma foto de
    celular pode trazer a localização) e reduzido a 800 px (`descoberta.imagens`);
  - no relatório: consultor e logotipo na capa e assinatura do consultor com nome e
    CPF/CNPJ preenchidos.
- Modelo da proposta em `config/proposta_v1.yaml` (pacote `proposta`, validado com
  Pydantic e conferido com o questionário quando a app liga):
  - valores padrão (validade, pagamento, impostos, reajuste), fases (fase 0 e MVP, com as
    faixas do score em que entram), premissas e responsabilidades do cliente;
  - faixas do score final que pedem alerta e a tabela do critério de aceite;
  - Condições Gerais: alterações de escopo, confidencialidade, propriedade intelectual,
    LGPD (controladora e operadora), limitação de responsabilidade, suporte e garantia,
    cancelamento, foro e prevalência do contrato detalhado. Foro, prevalência,
    confidencialidade, LGPD e limitação não são removíveis;
  - marcadores numa lista fechada (`{cliente.empresa}`, `{consultor.empresa}`,
    `{consultor.nome}`, `{foro}`); marcador desconhecido é recusado;
  - aviso de que o modelo é ponto de partida e deve ser revisado por advogado (na tela,
    não no documento do cliente).
- Proposta Comercial, documento separado do relatório:
  - tabelas `proposta`, `fase_proposta`, `item_proposta`, `clausula_proposta` e
    `versao_proposta` (sem migração);
  - criada como cópia do modelo e da revisão (escopo do MVP, exclusões, hipóteses e passos
    do cliente): mudar a revisão depois não altera a proposta;
  - capa (com a referência à última versão registrada do relatório), identificação das
    partes, contexto, escopo por fase, entregáveis e cronograma em semanas a partir do
    aceite, investimento por fase e total, pagamento, impostos e reajuste, premissas e
    hipóteses, responsabilidades do cliente, critério de aceite, validade, aceite com as
    duas assinaturas e o anexo "Condições Gerais", coberto pela mesma assinatura e pelo
    mesmo hash;
  - contas da proposta (cronograma, total, validade) em `dominio.proposta`;
  - em cada proposta, o consultor ajusta o texto de uma cláusula ou exclui as removíveis,
    sem mudar o modelo; "Restaurar texto padrão" volta ao modelo;
  - score final em "não seguir agora": a app avisa antes e só cria com confirmação;
  - versões registradas com numeração própria, hash no rodapé e as Condições Gerais
    congeladas (texto impresso de cada cláusula e versão do modelo);
  - telas `/sessoes/{id}/proposta` (edição com salvamento automático) e
    `/proposta/documento` (prévia, downloads, versões); links a partir da revisão e do
    relatório.
- Relatório e proposta num PDF só (`/proposta/relatorio-e-proposta.pdf`): a última versão
  registrada do relatório para o cliente (nunca a interna) e a última da proposta, ou os
  rascunhos; cada parte mantém rodapé, versão, hash e numeração.
- Demo: consultora fictícia (Ana Exemplo, CNPJ de teste 11.222.333/0001-81, e-mails
  `@example.com`, logotipo "EXEMPLO"), com aviso de dados fictícios nos documentos; proposta
  do Roberto (fase 0 R$ 6.000, MVP R$ 14.000: total de R$ 20.000, o investimento do
  payback e dentro do orçamento de R$ 15 a 20 mil), cliente em Campinas/SP, guia de captura
  e rotulagem das fotos na fase 0 (e não no MVP) e a cláusula de suporte ajustada para 60
  dias.
- Avisos na tela da proposta (só alertam; nada é mudado), na criação e na edição, onde se
  recarregam a cada mudança:
  - item de escopo que parece estar em mais de uma fase: comparação por palavras, sem LLM
    (`dominio.proposta.itens_repetidos`), que pega o mesmo item escrito de outro jeito,
    mas não sinônimos;
  - total da proposta diferente do investimento da métrica, o do payback do relatório.
- Cidade/UF do cliente nos dados da proposta (na identificação das partes).
- Critério de aceite separado em duas partes, com os textos no modelo da proposta: o
  aceite das entregas (pelo que foi entregue em cada fase; no MVP, a meta técnica no
  teste com dados históricos e o piloto concluído, com a tabela das metas técnicas) e as
  metas de negócio, acompanhadas, mas que não são condição de aceite nem de pagamento.
- Testes: modelo da proposta, CPF/CNPJ, logotipo, repositório, montagem, versões
  congeladas, PDF único, telas e um teste no navegador do fluxo da proposta.

### Alterado
- Dependências: `pillow` passa a ser direta (já vinha com o ReportLab; o código agora o
  importa) e `pypdf` passa de desenvolvimento para a app (juntar os PDFs). Nenhum pacote
  novo foi baixado.
- As rotas de listas da revisão viraram genéricas (`web/listas.py`, templates em
  `listas/`) e atendem também a proposta.
- O leitor de YAML do questionário passou a servir também ao modelo da proposta.
- O validador de UF do perfil passou para `repositorio._comum` e serve também à proposta.
- Especificação: fluxo, modelo de dados, camadas e linha do Sprint 6c.

### Pendências resolvidas do Sprint 6b
- No PDF, títulos não ficam mais sozinhos no pé da página (`keepWithNext`; no Word,
  `keep_with_next`), com teste que confere todas as páginas do caso Roberto.

### Pendências
- Inclusão de cláusulas extras numa proposta (hoje: ajustar o texto e excluir as
  removíveis).
- Sprint 7: a anonimização antes do LLM inclui os dados do perfil do consultor e os dados
  do cliente da proposta.
- Na seção 10 do relatório, informar que a divisão do escopo em fases está na Proposta
  Comercial.
- Ao copiar os próximos passos do cliente para as responsabilidades da proposta, ajustar o
  texto para soar como responsabilidade (ex.: "Participar da reunião…").

## [0.8.1] — 2026-10-11 — Correção do CI

### Corrigido
- Foco roubado depois de marcar um sinal pelo teclado: se a resposta do servidor chegava
  quando a pessoa já estava em outro campo (por exemplo, escrevendo a anotação), o cursor
  voltava ao botão do sinal, as letras se perdiam e um Espaço desmarcava o sinal. Agora o
  cursor só volta ao botão se tiver se perdido com a troca, e só na troca do próprio sinal.
  Era a causa da falha intermitente do teste e2e `test_sessao_completa_so_com_teclado`
  (anotação gravada como "Maão participou.").
- Número salvo como "Não salvo" (erro 500) numa sessão nova: todas as métricas ficam numa
  linha só, e dois números gravados quase juntos (por exemplo, quantidade e período da
  frequência) chegavam em pedidos paralelos que tentavam criar essa linha ao mesmo tempo
  (`UNIQUE constraint failed: metricas.sessao_id`). Agora o segundo pedido desfaz e grava
  de novo sobre a linha criada pelo primeiro. Foi a segunda falha intermitente do mesmo
  teste e2e no CI; um teste do repositório encena essa ordem sem threads.
- Teste e2e novo que segura a resposta do sinal até o meio da digitação, reproduzindo a
  corrida de forma determinística; o teste do roteiro completo agora espera o cursor
  voltar ao sinal antes de seguir.
- Testes do relatório e da web criam o demo com data fixa (`popular_demo(hoje=...)`), em
  vez de depender do dia em que rodam.

## [0.8.0] — 2026-10-11 — Sprint 6b: Relatório

### Adicionado
- Dependências `python-docx` (MIT) e `reportlab` (BSD) para exportar DOCX e PDF; `pypdf`
  (BSD) no grupo dev, para os testes lerem o PDF gerado. As três instalam só com `uv sync`
  no Windows, sem programas externos (WeasyPrint, que exige GTK, pandoc, wkhtmltopdf e
  LibreOffice foram descartados).
- Fonte DejaVu Sans (normal e negrito) em `relatorio/fontes/`, com o arquivo de licença:
  as fontes padrão do PDF não têm "≥", "→" nem "✓".
- `descoberta.relatorio`:
  - `coletar_dados()`: lê a sessão inteira e calcula o `Painel` uma vez;
  - documento neutro (`documento.py`): capa, título, parágrafo, aviso, lista, tabela,
    assinatura e quebra de página. Markdown, DOCX, PDF e a prévia na tela desenham os
    mesmos blocos, então os formatos nunca divergem;
  - `montar_relatorio()`, nas versões cliente e interna:
    - capa;
    - as 12 seções do bloco 10, com os textos e as saídas da revisão, os números do
      Painel, as respostas dos blocos indicados no YAML e a tabela "critério de aceite em
      três fases";
    - Anexo A: respostas por bloco e do encerramento, sem condicionais ocultas;
    - Anexo B: memória de cálculo com fórmulas em palavras, entradas com a origem
      ("Hipótese" ou "Informado na sessão") e resultados com "depende de hipótese";
    - termo de ciência e validação, com o aviso de que não é proposta comercial nem
      contrato e campos de nome, cargo, data e assinatura para o cliente e o consultor;
    - versão interna: Anexo C (sinais de alerta, contagem por bloco e anotações) e "USO
      INTERNO" na capa e no rodapé de todas as páginas;
    - no corpo do relatório, valores calculados com hipóteses levam "*" e uma nota;
      conteúdo faltando aparece como "⚠ A preencher";
  - `emitir()`: texto canônico (Markdown) e hash SHA-256 do conteúdo; rodapé com a
    versão, a data de emissão e os 12 primeiros caracteres do hash (ou "Rascunho não
    registrado");
  - exportadores `exportar_markdown`, `exportar_docx` e `exportar_pdf`. O PDF e o DOCX
    trazem "Página X de Y" no rodapé.
- Questionário: `secoes_relatorio` com `id`, `titulo` e, opcionalmente, `blocos`,
  `respostas` e `tabelas` (validados). `titulo_para_cliente` tira o parêntese final, que é
  nota para o consultor ("(bloco 4)", "(meia página, lido em 2 minutos)").
- `dominio.painel`: cada cálculo informa de quais entradas depende (`entradas`), e
  `EntradasPainel.de(registro)` lê as métricas de qualquer objeto.
- `repositorio`: tabelas novas, sem migração:
  - `HipoteseMetrica`, com `marcar_hipotese()` e `hipoteses_da_sessao()`;
  - `VersaoRelatorio`, com `registrar_versao()`, `versoes_da_sessao()`, `obter_versao()` e
    `proximo_numero_versao()`. Guarda o PDF emitido, o tipo, a data, o Markdown canônico,
    o hash do conteúdo e o hash do PDF; número único por sessão.
- Tela:
  - página do relatório (`/sessoes/{id}/relatorio`) com abas "versão cliente" e "versão
    interna", prévia, aviso de quantos trechos faltam e downloads em PDF, Word e
    Markdown (rascunho, gerado na hora);
  - botão "Registrar versão enviada" e lista das versões registradas, com download do PDF
    guardado (o mesmo arquivo, byte a byte);
  - revisão pós-sessão: seção "Hipóteses dos cálculos", com uma caixa por métrica que
    salva sozinha;
  - links "Relatório →" na tela da sessão e na revisão.
- Banco de demonstração: hipóteses (custo da hora, horas economizadas e custo fixo de
  operação) e respostas do encerramento.
- Testes: relatório do Roberto nos três formatos com a rede bloqueada (critério de
  aceite); rodapé com hash em todas as páginas do PDF; regra de arquitetura que proíbe
  `relatorio` de importar `web`, `llm` e os módulos de cálculo do domínio.

### Alterado
- `web/numeros.py` → `descoberta/formatos.py` e `web/campos.py` → `descoberta/campos.py`;
  rótulos das escalas em `descoberta/rotulos.py`. São usados pela web e pelo relatório.
- Especificação: relatório no fluxo de uso e no modelo de dados; bibliotecas de
  exportação; Sprint 8 (validação e lançamento, com SECURITY.md, aviso de uso local e
  verificações de segurança no CI) e Sprint 9 (documentação Diátaxis com MkDocs, guia de
  produção com modelo de ameaças, CONTRIBUTING e CI da documentação).
- Ajustes do teste manual:
  - tabela de riscos com colunas largas o bastante para nenhuma palavra quebrar no PDF e
    no Word, com teste que mede cada palavra de todas as tabelas do PDF;
  - seção 7 sem as entradas vazias (elas continuam no Anexo B);
  - demo: decisão do investimento é do Roberto (b1.o6); "o consultor entrega";
    "a partir de 6"; prazos dos próximos passos contados a partir do dia em que o
    demo é criado, para ficarem sempre depois da emissão.

### Pendências resolvidas do Sprint 6a
- O relatório usa `dominio.painel` (mesmos números da tela), os itens do encerramento e as
  saídas da revisão, e ignora respostas de condicionais ocultas pelo tipo de solução.

### Pendências
- Sprint 6c: no PDF, um título de seção não pode ficar sozinho no pé da página, separado
  do conteúdo (hoje acontece com "Próximos passos" e "Score final de viabilidade"); o
  título deve ir para a página seguinte junto com o início do conteúdo.
- Sprint 7: os rascunhos do LLM para os textos narrativos ficam numa tabela própria (com
  modelo e versão do prompt), sem sobrescrever o texto do consultor.
- Continuam valendo as pendências "antes do primeiro uso com cliente real" do Sprint 3.
  O banco agora guarda também os PDFs enviados, o que reforça a necessidade de backup e de
  criptografia do disco.

## [0.7.0] — 2026-10-11 — Sprint 6a: Saídas estruturadas da sessão

### Adicionado
- Questionário: seção `revisao` no YAML (sem mudar nenhum id da v1):
  - `categorias_risco`: as 6 linhas da tabela "Principais riscos" do bloco 7, mais `outro`;
  - `textos`: as 6 partes narrativas do relatório (resumo executivo, frase-problema,
    fluxos as-is e to-be, justificativa do tipo de solução e recomendação), cada uma com
    orientação e `apoio` (perguntas ou itens do encerramento mostrados ao lado);
  - validação: ids únicos em todo o questionário e `apoio` citando só ids que existem;
    `Questionario.categoria_risco(id)` e `texto_revisao(id)`.
- `dominio.revisao`:
  - escalas `Nivel` (baixo/médio/alto), `Camada` (negócio/técnica) e `Responsavel`
    (cliente/consultor);
  - `matriz_de_riscos()`: grade 3×3 (impacto × probabilidade) com os riscos numerados
    R1, R2… e o nível de cada célula (`severidade()`);
  - `pendencias_da_revisao()`: textos em branco; nenhum risco, ou risco alto × alto sem
    mitigação (regra do bloco 7); nenhum indicador de negócio, ou indicador sem valor
    atual, meta, prazo ou como medir (tabela do bloco 5); escopo sem item que entra ou sem
    item que fica fora; nenhum próximo passo, ou passo sem prazo.
- `repositorio`: 5 tabelas novas, criadas sem migração em bancos existentes: `Risco`,
  `Indicador`, `ItemEscopo`, `ProximoPasso` e `TextoSecao`. As quatro listas usam as mesmas
  funções (`adicionar_item`, `editar_item`, `excluir_item`, `itens_da_sessao`), com
  validação por campo; textos com `salvar_texto_secao` (em branco apaga) e
  `textos_da_sessao`. Valor atual, meta e prazo dos indicadores são texto (misturam
  unidades e não entram em cálculos); o prazo dos próximos passos é data.
- Página "Revisão pós-sessão" (`/sessoes/{id}/revisao`), separada da tela ao vivo e ligada
  a ela nos dois sentidos:
  - textos do relatório com salvamento automático e "O que foi dito na sessão" recolhido;
  - riscos, indicadores, escopo e próximos passos: incluir, editar e excluir sem recarregar
    a página. Categoria fora do YAML, escala inválida ou data fora do formato são recusadas
    com a mensagem ao lado, sem perder o que foi digitado. Depois de incluir, o cursor
    volta ao primeiro campo;
  - matriz 3×3 em HTML e CSS, com o nível escrito em cada célula (não depende só da cor);
  - quadro "Falta preencher", com links para cada seção e as obrigatórias ainda sem
    resposta na sessão;
  - matriz e quadro se atualizam sozinhos com o evento `revisao-mudou`.
- Banco de demonstração: revisão do Roberto completa (4 riscos, 3 indicadores, 7 itens de
  escopo, 4 próximos passos e os 6 textos), sem nenhuma pendência. O que o cliente não
  disse está marcado como hipótese no `demo.py`.
- Teste no navegador: incluir um risco só com o teclado e vê-lo na matriz.

### Alterado
- Especificação: Sprint 6 dividido em 6a (saídas estruturadas) e 6b (relatório com versão
  cliente e versão interna, anexos, memória de cálculo e termo de ciência); revisão
  pós-sessão no fluxo de uso; novas entidades no modelo de dados; Sprint 7 inclui os
  rascunhos dos textos narrativos.

### Pendências resolvidas do Sprint 5
- Notas do score final: "bloco 1" no singular quando o critério tem um só bloco de origem.
- Cronômetro: ponto pulsando (só CSS) enquanto roda; parado para quem desativou animações
  no sistema (`prefers-reduced-motion`).

### Pendências
- Sprint 6b: o relatório deve usar `dominio.painel` (mesmos números da tela), os itens do
  encerramento e as saídas da revisão, e ignorar respostas de condicionais ocultas pelo
  tipo de solução atual.
- Sprint 7: os rascunhos do LLM para os textos narrativos ficam numa tabela própria (com
  modelo e versão do prompt), sem sobrescrever o texto do consultor.
- Continuam valendo as pendências "antes do primeiro uso com cliente real" do Sprint 3.

## [0.6.0] — 2026-10-08 — Sprint 5: Uso ao vivo

### Adicionado
- Dependência de desenvolvimento `pytest-playwright` (com o Chromium do Playwright): testes
  no navegador que provam o critério de aceite "sessão completa só com teclado", que
  depende do JavaScript dos atalhos e o `TestClient` não executa. Marcados como `e2e`:
  `uv run pytest -m "not e2e"` roda só os rápidos; o CI roda todos.
- Questionário (YAML e modelos):
  - `duracao`: aviso aos 75 min e limite aos 90 min (aviso precisa vir antes do limite);
  - `bloco` em cada score (dados no bloco 4, final no bloco 10), validado;
  - `prontidao_dados.criterio_final`: qual critério do score final recebe a nota derivada
    do score de dados, em vez de o código presumir `prontidao_dados`;
  - `Questionario.item_encerramento(id)`.
- `dominio`:
  - `painel.calcular_painel()`: aplica os cálculos existentes ao que já foi levantado e,
    para cada resultado ainda impossível, diz quais entradas faltam. Não tem conta
    própria: só chama `dor`, `operacao`, `payback`, `scores` e `sinais`. Operação só com
    custo fixo (ou só a parte variável) conta o resto como zero; nota dada à mão para o
    critério derivado é recusada;
  - `scores.score_prontidao_parcial()` e `score_viabilidade_parcial()` (soma até agora e
    critérios que faltam), reaproveitando a mesma validação dos scores completos;
  - `cronometro`: tempo decorrido com pausas e situação normal/atenção/limite;
  - `pendencias.obrigatorias_pendentes()`, respeitando as condicionais.
- `repositorio`: tabela `Cronometro` (1 por sessão) com `alternar_cronometro()` e
  `tempo_do_cronometro()`; `anotar_sinal()` (troca ou apaga a observação de um sinal).
  Tabela nova em vez de colunas em `Sessao`: bancos existentes (como o `data/demo.db`)
  ganham a tabela sem migração.
- Tela da sessão ao vivo:
  - sinais de alerta do bloco aberto na coluna direita, marcados com um clique ou
    Espaço (`aria-pressed`), com observação opcional que salva sozinha;
  - anotações livres: criar (ligada ao bloco aberto ou geral), editar e excluir; a troca
    de aba não perde uma anotação em andamento (`hx-swap-oob`);
  - números de cada bloco (bloco 1: dor; 6: operação; 9: retorno) e notas dos scores
    (bloco 4 com as âncoras do YAML; bloco 10 com a nota de prontidão só para leitura),
    com salvamento automático; números em formato brasileiro (`20.000`, `7,5`;
    `7.5` é recusado com pedido de vírgula);
  - painel de cálculos ao vivo (custo da dor, operação, economia, payback com alerta
    acima de 12 meses ou "não se paga", score de dados, score final, sinais por bloco),
    atualizado sozinho pelo evento `HX-Trigger` depois de cada salvamento;
  - obrigatórias pendentes no topo e em cada aba;
  - cronômetro com iniciar/pausar/retomar, que muda de cor (atenção e depois vermelho)
    nos limites do YAML, sem som nem janela; atualiza a cada 30 s sem JavaScript;
  - aba de encerramento com os 5 itens do YAML (guardados como respostas `enc.*`) e
    resumo "para ler ao cliente", com a indicação do score final e o payback;
  - atalhos de teclado (lista única em `web/atalhos.py`, que gera a ajuda e o JSON do
    `static/atalhos.js`): Ctrl+/ ou ? (ajuda), Alt+1…Alt+0 (blocos), Alt+R
    (encerramento), Alt+P (próxima obrigatória pendente, passando de bloco), Alt+S
    (sinais), Alt+N e Ctrl+Enter (anotação), Alt+C (cálculos), Alt+T (cronômetro), Esc
    (volta ao último campo). AltGr (Ctrl+Alt, teclado ABNT2) nunca dispara atalho;
  - tela de ajuda dos atalhos em `<dialog>`, também aberta pelo botão "Atalhos (Ctrl+/)".
- Banco de demonstração com 3 anotações de exemplo.

### Alterado
- `aviso()` aceita um evento para o cabeçalho `HX-Trigger` (só quando o valor foi salvo).
  Respostas e tipo de solução disparam `pendencias-mudaram`; métricas e notas,
  `calculos-mudaram`; sinais, `sinais-mudaram`.
- Partes que se recarregam sozinhas (abas, pendências, cálculos, resumo) têm moldura fixa
  e trocam só o conteúdo: trocando o elemento inteiro, um evento que chegasse durante uma
  recarga se perdia (o teste no navegador pegou o caso).
- CI instala o Chromium do Playwright; CLAUDE.md e especificação atualizados.

### Pendências resolvidas do Sprint 4
- Métricas, notas e sinais aparecem e são editáveis na tela (inclusive os do banco de
  demonstração).

### Pendências
- Sprint 6: o relatório deve usar `dominio.painel` (mesmos números da tela) e os itens
  do encerramento; continua valendo ignorar respostas de condicionais ocultas.
- Sprint 6 (teste manual do Sprint 5):
  - notas do score final: usar "bloco" no singular quando o critério tem um só bloco de
    origem (hoje aparece "blocos 1");
  - cronômetro: indicador discreto de que está rodando (um ponto pulsando, só com CSS),
    porque com hh:mm o primeiro minuto parece parado.
- Atalhos testados no Chromium (Chrome/Edge). No Firefox, Alt+S e Alt+T podem abrir
  menus do navegador.
- Continuam valendo as pendências "antes do primeiro uso com cliente real" do Sprint 3.

## [0.5.0] — 2026-10-07 — Sprint 4: Web básica

### Adicionado
- Dependências `fastapi`, `jinja2`, `uvicorn` (sem extras) e `python-multipart` (leitura de
  formulários HTML); `httpx2` no grupo dev, exigido pelo `TestClient` (o Starlette 1.7
  marca o `httpx` antigo como obsoleto).
- htmx 2.0.4 copiado para `src/descoberta/web/static/htmx.min.js` (sem CDN, para funcionar
  sem internet). Integridade conferida com o SRI oficial
  `sha384-HGfztofotfshcF7+8n44JQL2oJmowVChPTg48S+jvZoztPfvwD79OC/LTtG6dMp+`.
- `descoberta.web`: app FastAPI com `criar_app()` (banco e pasta de questionários
  configuráveis; banco pela variável `DESCOBERTA_BANCO`) e telas em Jinja2 + HTMX:
  - clientes: lista, cadastro, edição e exclusão (com confirmação; apaga as sessões em
    cascata). Formulários comuns, com erro em português e sem perder o que foi digitado;
  - sessão: abertura com a versão mais recente do questionário; página com cabeçalho,
    status, preparação (contexto prévio e amostra recebida), 10 abas por bloco (objetivo,
    saída esperada, notas, tabelas de referência, seções do relatório no bloco 10),
    obrigatórias em destaque e aprofundamento recolhido; tipo de solução no bloco 3; coluna
    direita reservada para o Sprint 5;
  - abas trocam só o painel (`hx-get` + `hx-push-url`); F5 reabre na mesma aba;
  - salvamento automático de respostas e campos da sessão: envio 800 ms depois de parar de
    digitar ou ao sair do campo, em ordem (`hx-sync`); aviso "Salvo às…", indicador
    "Salvando…" só com CSS (classe `htmx-request`) e aviso "⚠ Não salvo" quando a app não
    responde (`hx-on::after-request`, a exceção de JS aprovada) ou recusa o valor (422);
  - histórico do HTMX sem cópias das páginas no navegador (`historyCacheSize: 0`): dados de
    clientes não ficam no `localStorage`.
- `web.catalogo`: carrega todos os `config/questionario_v{n}.yaml` ao ligar a app (YAML com
  erro impede a app de subir) e confere se a versão do nome bate com a do arquivo.
- `Questionario.pergunta(id)` e `pergunta_visivel()` na camada do questionário.
- `uv run python -m descoberta.demo`: cria `data/demo.db` com o caso Roberto (visão
  computacional; respostas só com os fatos levantados, incluindo as 4 condicionais
  `b4.vc*`; métricas, notas e sinais do caso de referência). Recusa o banco real.
- Testes da camada web com `TestClient` em banco temporário, incluindo: só o fragmento
  volta no salvamento, HTML escapado, nenhum recurso externo carregado.

### Alterado
- `criar_engine()` usa `check_same_thread=False`: o FastAPI atende pedidos em várias
  threads; cada pedido tem sua própria Session.
- CLAUDE.md: "JS mínimo: atalhos de teclado e avisos de falha de salvamento".

### Pendências resolvidas do Sprint 3
- Ids conferidos no questionário da versão da sessão: pergunta inexistente → 404; tipo de
  solução inexistente → 422; resposta para condicional invisível → 422.
- Mudança do tipo de solução esconde as condicionais que deixaram de valer sem apagar as
  respostas; se o tipo voltar, elas reaparecem.

### Pendências
- Sprint 6: o relatório deve ignorar respostas de condicionais ocultas pelo tipo de solução
  atual (elas continuam no banco).
- Sprint 5: mostrar e editar métricas, notas e sinais (o banco de demonstração já os tem).
- Continuam valendo as pendências "antes do primeiro uso com cliente real" do Sprint 3.

## [0.4.0] — 2026-10-07 — Sprint 3: Persistência

### Adicionado
- Dependência `sqlmodel` (traz o SQLAlchemy): persistência em SQLite, como definido na stack.
- `descoberta.repositorio`, com 8 tabelas: `Cliente`, `Sessao`, `Resposta`, `SinalMarcado`,
  `Anotacao`, `Metricas` (1 por sessão), `NotaCriterio` e `Relatorio`.
  - Ids do questionário (`pergunta_id`, `sinal_id`, `criterio_id`, `tipo_solucao`)
    guardados como texto, exatamente como no YAML; formato inválido (ex.: `"B2.S3"`) é
    recusado. A sessão registra a `versao_questionario`, que não pode ser alterada depois.
  - Métricas em campos numéricos próprios, com os mesmos nomes dos parâmetros de `dominio`.
    Dinheiro, horas e quantidades em `Decimal`, gravados como texto no SQLite
    (`DecimalTexto`) para voltar idênticos; `float`, negativos e não finitos são recusados
    (reaproveita `como_decimal()`).
  - Notas dos scores numa tabela própria (critério → nota 0–3), sem escrever os critérios do
    YAML no código. A nota de `prontidao_dados` do score final não é gravada: é derivada.
  - Funções de CRUD que validam a entrada e gravam numa transação própria (pensadas para o
    salvamento automático): resposta vazia apaga a resposta; marcar um sinal duas vezes não
    duplica; atualização parcial das métricas; relatório por LLM exige modelo e versão do prompt.
  - Chaves estrangeiras ligadas no SQLite (`PRAGMA foreign_keys=ON`) com exclusão em
    cascata: excluir um cliente apaga suas sessões e tudo delas.
  - Banco padrão em `data/descoberta.db` (fora do Git).
- Testes em banco temporário (arquivo SQLite em `tmp_path`), incluindo o caso Roberto
  gravado, relido do zero e recalculado (60 h/mês, score de dados 4, payback ≈ 7,7,
  score final 12, sinais por bloco).
- Regra de arquitetura: `repositorio` não importa `web`, `llm` nem `relatorio`.

### Alterado
- Horários (`criado_em`, `marcado_em`…) gravados com fuso, em UTC, que é o padrão do
  SQLModel 0.0.48; a tela converte para a hora local ao mostrar. (O plano previa hora local.)
- Entradas do caso Roberto viraram a fixture `caso_roberto` (`tests/conftest.py`), usada
  pelos testes de `dominio` e de `repositorio`.
- `PADRAO_ID` exposto em `questionario.modelos` para o repositório validar ids.
- Especificação: campos de contexto prévio e amostra de dados na sessão; notas dos scores
  como tabela própria.

### Pendências
- Sprint 4: conferir se os ids gravados existem no questionário da versão da sessão (na
  camada web, que tem o questionário carregado).
- Sprint 4: quando o tipo de solução da sessão mudar, esconder na tela as respostas das
  perguntas condicionais que deixaram de valer, sem apagá-las do banco (se o tipo voltar,
  as respostas reaparecem).
- Antes do primeiro uso com cliente real:
  - migrações de banco (Alembic); hoje as tabelas são criadas com `create_all`, que não
    altera tabelas existentes;
  - rotina de backup do `data/descoberta.db`;
  - criptografia do disco do notebook (BitLocker), já que o banco guarda dados pessoais
    dos clientes sem criptografia própria.

## [0.3.0] — 2026-10-07 — Sprint 2: Cálculos

### Adicionado
- `descoberta.dominio`: cálculos puros, com dinheiro e horas em `Decimal` (float é recusado).
  - `dor`: `ocorrencias_por_mes()` (dia → × 22 dias úteis; semana → × 52/12),
    `horas_dor_mes()` e `custo_dor_mes()`.
  - `operacao`: `custo_operacao_mes()` = chamadas/dia × custo por chamada × 22 + custo fixo.
  - `payback`: `economia_mes()` = horas economizadas × custo da hora + outros ganhos
    (opcional, padrão 0); `payback_meses()` devolve `None` quando a economia não supera a
    operação; `payback_dificil_de_aprovar()` sinaliza payback acima de 12 meses.
  - `scores`: `score_prontidao()`, `score_viabilidade()` (pontuação, máximo e faixa do YAML)
    e `nota_prontidao_para_viabilidade()`. Notas fora de 0–3, critério faltando ou
    desconhecido geram erro.
  - `sinais`: `contar_sinais_por_bloco()`, com todos os blocos (inclusive os com 0); id
    repetido conta uma vez; id inexistente gera erro.
  - `faixas`: `classificar()` escolhe a faixa sem nenhum limite escrito no código.
- `scores.prontidao_dados.conversao_para_nota` no YAML: score de dados 0–2 → nota 0,
  3–5 → 1, 6–10 → 2, 11–15 → 3; validado (cobre 0–15, notas 0–3, nunca diminui).
- Teste de referência ponta a ponta do caso Roberto (`tests/dominio/test_caso_roberto.py`):
  15 ocorrências × 4 h = 60 h/mês; score de dados 4 → nota 1; payback 20.000 / (3.000 − 400)
  ≈ 7,7 meses; score final 12 → "Seguir com fase 0"; sinais marcados por bloco
  1 = 1, 2 = 2, 8 = 1, 9 = 1, demais = 0. Hipóteses registradas no teste: custo
  da hora R$ 100, 30 h economizadas por mês, operação de R$ 400 como custo fixo.

### Alterado
- Fixture `questionario_v1` movida para `tests/conftest.py`, compartilhada por todos os testes.
- Especificação: tabela de métricas detalhada com os campos que os cálculos usam.

### Removido
- Campo `peso` dos sinais de alerta (modelo, YAML e especificação): o que importa é a
  contagem de sinais marcados por bloco.

## [0.2.0] — 2026-10-07 — Sprint 1: Questionário

### Adicionado
- `config/questionario_v1.yaml`: transcrição do Modelo de Descoberta com os 10 blocos
  (48 obrigatórias, 34 de aprofundamento, 31 sinais de alerta), notas e tabelas de
  consulta de cada bloco, as 12 seções do relatório (bloco 10), o encerramento (5 itens),
  os 6 tipos de solução da árvore de decisão do bloco 3 e os dois scores com suas faixas
  (prontidão de dados 0–15; viabilidade final 0–18).
- Condicionais de visão computacional: 4 perguntas no bloco 4, exibidas só quando o tipo
  de solução é `visao_computacional`.
- `descoberta.questionario`: modelos Pydantic imutáveis, `carregar_questionario()` e
  `perguntas_visiveis()`.
- Validações: campos desconhecidos, ids únicos, blocos numerados em sequência,
  condicionais citando tipos existentes e só depois do bloco 3, faixas de score
  contíguas cobrindo de 0 ao máximo, blocos de origem existentes e tabelas com todas
  as colunas.
- `QuestionarioInvalido`: erros em português, com o arquivo e o caminho do campo
  (ex.: `blocos[id=processo].perguntas[id=b2.o1].tipo: valor 'obrigatorio' inválido`),
  incluindo a linha e a coluna quando o YAML está mal formado.
- `docs/modelo-descoberta.md` versionado no repositório.

### Alterado
- Dependências `pydantic` e `pyyaml` adicionadas.
- `[tool.uv] python-preference = "only-managed"`: o uv usa apenas o Python que ele
  mesmo instala, nunca o do sistema nem o do Anaconda.

### Pendências para o Sprint 2
- Definir o uso do campo `peso` dos sinais de alerta (hoje é 1 em todos e não entra em
  nenhum cálculo) ou removê-lo do modelo e do YAML.
- Definir a regra de conversão do score de prontidão de dados (0–15) para a nota do
  critério `prontidao_dados` do score final (0–3), validando com o caso Roberto
  (score 4 → nota 1).

## [0.1.0] — 2026-10-07 — Sprint 0: Setup

### Adicionado
- Projeto Python gerenciado com uv (layout `src/`, Python ≥ 3.12).
- Pacote `descoberta` com as camadas `questionario`, `dominio`, `repositorio`,
  `relatorio`, `llm` e `web` (vazias), além das pastas `config/` e `prompts/`.
- Ferramentas de desenvolvimento: pytest + pytest-cov, ruff (lint e formatação), pre-commit.
- Teste automático da regra de arquitetura: `dominio` não importa `web`,
  `repositorio` nem `llm`.
- CI no GitHub Actions rodando ruff e pytest a cada push e pull request.
- `.gitignore` (banco SQLite, `.env` e exportações fora do Git), `.env.example`,
  `.gitattributes` (fim de linha LF).
