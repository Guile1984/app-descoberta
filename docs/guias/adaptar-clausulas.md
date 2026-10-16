# Adaptar as cláusulas da proposta

As **Condições Gerais** são o anexo final da Proposta Comercial, coberto pela mesma
assinatura e pelo mesmo hash. Elas vêm do modelo `config/proposta_v1.yaml` e podem ser
adaptadas em dois níveis:

- **numa proposta só**, pela tela: ajustar o texto ou excluir uma cláusula removível, sem
  mudar o modelo;
- **no modelo**, para todas as propostas novas: uma versão nova do arquivo.

!!! warning "Ponto de partida, não aconselhamento jurídico"
    O texto do modelo é um ponto de partida. Revise a proposta e as Condições Gerais com um
    advogado antes de usar com clientes, e adapte-as ao seu caso.

## Numa proposta só (pela tela)

Na página da proposta, a seção **Condições Gerais** mostra todas as cláusulas do modelo:

- **Ajustar o texto:** edite na caixa **Texto nesta proposta**. Salva sozinho, e a cláusula
  ganha o selo "Ajustada nesta proposta".
- **Restaurar texto padrão:** volta ao texto do modelo (a app pede confirmação).
- **Excluir desta proposta:** só nas cláusulas removíveis. A cláusula fica com o selo
  "Fora desta proposta" e sai do documento. **Incluir de volta** desfaz.

As cláusulas que não podem ser excluídas mostram o selo "Não removível" e não têm o botão
de excluir. Dá para ajustar o texto delas, com o advogado.

**Quando você registra uma versão** da proposta, o texto impresso de cada cláusula fica
**congelado** com ela. Ajustes feitos depois valem só para as versões seguintes.

### Marcadores

Os textos podem usar estes marcadores, que o documento troca pelo valor:

| Marcador | Vira |
| --- | --- |
| `{cliente.empresa}` | a empresa do cliente |
| `{consultor.empresa}` | a sua empresa (perfil do consultor) |
| `{consultor.nome}` | o seu nome (perfil do consultor) |
| `{foro}` | a sua cidade/UF (perfil do consultor) |

Sem o valor (por exemplo, sem cidade no perfil), o documento mostra "A preencher". Um
marcador fora da lista, como `{cliente.cnpj}`, é recusado: "marcador desconhecido".

## Cláusulas que não podem ser excluídas

No modelo v1, estas cláusulas não têm `removivel: true` e por isso ficam em toda proposta:

- **Confidencialidade**
- **Proteção de dados pessoais (LGPD)**: quem é controladora e quem é operadora dos dados
- **Limitação de responsabilidade**
- **Foro**: usa o marcador `{foro}`, a cidade/UF do seu perfil
- **Contrato detalhado**: se as partes assinarem um contrato mais detalhado, ele prevalece
  em caso de conflito

A proteção vem do campo `removivel` do modelo, e um teste confere essa lista no modelo v1.
Num modelo seu, você decide. Pense bem antes de tornar uma delas removível.

## No modelo (para as propostas novas)

Cada proposta guarda a versão do modelo com que foi criada. Propostas novas, e as
recriadas com **Recriar a partir da revisão**, usam a versão mais recente. Por isso, para
mudar o modelo:

1. **Copie** `config/proposta_v1.yaml` para `config/proposta_v2.yaml` e mude `versao: 2`
   dentro dele.
2. **Edite** as cláusulas. Cada uma tem `id`, `titulo`, `texto` e, se puder ser excluída,
   `removivel: true`:

    ```yaml
    clausulas:
      - id: suporte_garantia
        titulo: Suporte e garantia
        removivel: true
        texto: >-
          Durante 60 dias depois da entrega de cada fase, {consultor.empresa} corrige sem
          custo as falhas dos entregáveis em relação ao que esta proposta descreve.
    ```

    (No modelo v1 são 30 dias; o banco de demonstração ajusta para 60 só na proposta do
    Roberto, pela tela.)

    O `>-` junta as linhas seguintes num parágrafo só. Para um `id` novo, use letras
    minúsculas sem acento, números e `_`. **Não renomeie** um id existente: os ajustes que
    as propostas fizeram nele deixariam de valer.

3. **Confira o arquivo:**

    ```powershell
    uv run --no-dev python -c "from descoberta.proposta import carregar_modelo_proposta as c; c('config/proposta_v2.yaml'); print('ok')"
    ```

4. **Abra a app de novo.** Ela confere o modelo com todos os questionários ao ligar. Com
   erro, não sobe e mostra o problema.
5. **Não apague a v1** enquanto houver propostas criadas com ela.

O mesmo arquivo define o **padrão** da proposta: validade, pagamento, impostos, reajuste,
fases, premissas e responsabilidades. A referência de todos os campos está em
[Arquivos YAML](../referencia/yaml.md#modelo-da-proposta).
