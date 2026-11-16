# PROPOSTA — Divisão do ValidaRota em telas

**Status**: proposta. Nada foi implementado a partir deste documento.
**Base**: leitura de `App.tsx` (154 l.), `SimulationForm.tsx` (292), `Comparativo.tsx` (118), `IntegridadePanel.tsx` (65), `StopOrderTable.tsx` (73), `routes_simulacao.py` (228) e `routes_analise.py`; mais duas medições contra o backend em `127.0.0.1:8000` e uma medição de layout em Chromium 1280×900, todas em 16/11/2026.

---

## 1. O que existe hoje

Uma tela. `App.tsx` monta um grid de duas colunas — formulário à esquerda com largura fixa, resultado à direita — e uma faixa de integridade abaixo de tudo.

Medido no navegador, com uma simulação aprovada na tela:

| Medida | Valor |
| --- | --- |
| Altura da página | 1891 px (viewport de 900 px = 2,1 telas) |
| Largura do formulário | 440 px fixos |
| Largura da tabela de ordem | 718 px |
| Topo do painel *Previsto × realizado* | y = 1279 — **379 px abaixo da dobra** |
| Painéis na coluna de resultado | 5 ou 6, conforme a rota tenha pedágio |

O último item não é detalhe: `VpoPanel` devolve `null` quando a rota não tem praça nem cobertura, então a coluna de resultado **muda de altura conforme o dado**. Layout de coluna única empilhada não tem como acomodar isso sem reflow.

Estado, todo dentro de `App`:

| Estado | Origem | Vive até |
| --- | --- | --- |
| `catalogos` | `GET /api/catalogos` no mount | reload |
| `form` | `FORM_INICIAL` + edição | reload |
| `resultado` | resposta de `POST /api/simular` | reload (não é reidratável hoje) |
| `erro` | falha de rede ou 422 | próxima ação |
| `diagnostico` | `GET /api/diagnostico` | reload |

### 1.1 Duas recusas, duas naturezas

Isto é o fato estrutural mais importante para a divisão em telas, e ele não está visível na interface atual — as duas recusas caem na mesma coluna.

**Recusa de cadastro — medida agora:**

```
POST /api/simular  (parada repetida)
→ 422
detail.codigo   = "DADOS_DIVERGENTES"
detail.avisos[0].detalhe.campo = "paradas"
```

Nada é persistido. **Não existe id.** A simulação nunca existiu no banco.

**Recusa de operação — medida agora:**

```
POST /api/simular  (carreta-02, revisão vencida)
→ 200
status = "rejeitada"
id     = "sim-8bcfef10dca8"
avisos = CONSUMO_FORA_FAIXA (aviso), REVISAO_VENCIDA (rejeicao), OCUPACAO_BAIXA (aviso)
```

Persistida, com id, reaberta por `GET /api/simulacoes/{id}`.

Hoje a primeira é desenhada como *erro* (`InlineError`) e a segunda como *resultado* (`ResultHeader`). A distinção não é cosmética: uma pode ser endereçada por URL, a outra não pode existir como tela.

### 1.2 Problemas concretos da tela única

1. **O veredito compete com cinco painéis.** A tese do projeto é o gate responder `aprovada | aprovada_com_avisos | rejeitada` com evidência. Na tela atual esse veredito é o primeiro de seis blocos empilhados e sai de vista assim que o usuário rola.
2. **A densidade vertical empurra o trabalho para fora da tela.** Registrar a execução real — o passo que fecha o ciclo do produto — começa 379 px abaixo da dobra.
3. **Falha de catálogo trava a tela num estado morto.** `App.tsx:94` renderiza `catalogos ? <SimulationForm/> : "Carregando cadastros…"`, e o erro vai para a **outra coluna** (`App.tsx:110`). Se `GET /api/catalogos` falhar, a coluna esquerda fica em "Carregando cadastros…" para sempre e o usuário lê o erro no lado oposto da tela.
4. **Três trabalhos de frequências diferentes na mesma tela**: montar e validar uma rota (operacional, repetitivo), registrar execução e comparar (posterior à viagem, ocasional), varrer a integridade do cadastro (administrativo, diagnóstico). Compartilham a tela, não o momento.
5. **`GET /api/simulacoes` existe e não tem interface.** O backend lista as 50 últimas simulações; nenhuma tela usa.
6. **Recarregar perde o resultado.** Ele vive só em memória, embora esteja no banco.

---

## 2. Etapas identificadas

Extraídas do código, não inventadas. Cada uma corresponde a um bloco que já existe.

| # | Etapa | Onde está hoje |
| --- | --- | --- |
| S1 | Identificar a rota: origem, paradas, janelas, peso, prioridade | `fieldset` "Rota" |
| S2 | Alocar recursos: veículo, motorista, perfil, partida | `fieldset` "Veículo e jornada" |
| S3 | Precificar: placa, receita, modo de pedágio, VPO, flags | `fieldset` "Custo e pedágio" |
| S4 | Submeter ao gate | botão "Validar rota" |
| S5 | Ler o veredito e as métricas | `ResultHeader` |
| S6 | Ler as evidências da recusa | `AlertList` |
| S7 | Ler a ordem calculada | `StopOrderTable` |
| S8 | Ler a composição do custo | `CostBreakdown` |
| S9 | Ler pedágio e cobertura do VPO | `VpoPanel` |
| S10 | Registrar execução real e comparar | `Comparativo` |
| S11 | Varrer a integridade do cadastro | `IntegridadePanel` |
| S12 | Consultar simulações anteriores | **não existe** — `GET /api/simulacoes` pronto |

---

## 3. Critério de agrupamento

Quatro critérios, nesta ordem. Nenhum é estético.

**a) Atomicidade do payload.** `POST /api/simular` recebe S1, S2 e S3 num único corpo `SimulacaoIn`, com todos os campos obrigatórios. Não há endpoint de rascunho nem validação parcial. Separar S1–S3 em telas distintas obrigaria a manter um payload inválido entre telas — ou a criar um endpoint novo só para sustentar a navegação.

**b) Regras cruzadas do gate.** As rejeições de operação cruzam os três grupos: `OCUPACAO_BAIXA` precisa de peso (S1) **e** capacidade do veículo (S2); `JORNADA_EXCEDIDA` precisa de janelas (S1) **e** jornada do motorista (S2); `TAG_NAO_VINCULADO_A_PLACA` precisa de placa (S3) **e** VPO (S3) **e** o resultado do roteamento. Esconder um grupo atrás de um passo torna a correção da recusa um exercício de adivinhação.

**c) Natureza da recusa.** Recusa sem id não pode ser tela; recusa com id pode. (Seção 1.1.)

**d) Momento de uso.** Montar rota acontece antes da viagem; registrar execução acontece depois; varrer integridade acontece por rotina administrativa. Frequências diferentes pedem entradas diferentes.

Aplicando os quatro:

- S1 + S2 + S3 + S4 → **uma tela** (critérios a e b).
- S5 + S6 → **inseparáveis por tese**: veredito sem evidência é exatamente o vício que o projeto existe para corrigir.
- S7 + S8 + S9 → **acompanham S5/S6**: são a mesma resposta, lida em três recortes. Separar produziria três telas que só fazem sentido juntas.
- S10 → **tela própria** (critério d, mais o estado 409 descrito em 4.3).
- S11 → **tela própria** (critério d; zero dependência de simulação).
- S12 → **tela própria** (é o índice que torna as outras reentráveis).

---

## 4. As telas

Cinco telas. Três são destinos de navegação; duas são vistas de detalhe, alcançadas por contexto.

### 4.1 Simulação — `/`

**Propósito**: montar a rota e submetê-la ao gate. É a tela de trabalho e a porta de entrada.

**Etapas**: S1, S2, S3, S4.

**Conteúdo**: as três seções numeradas na mesma tela — 1 Rota, 2 Recursos, 3 Precificação — em grid interno de duas colunas a partir de 1280 px, e o botão de submissão no fim. As seções são numeradas para dar a leitura de etapa, mas **não são um wizard**: ver 4.1.1.

**O que não entra**: veredito, evidência, custo, comparativo, integridade.

**Estados**: catálogo carregando · **catálogo indisponível, com "tentar de novo"** · pronto · submetendo · recusa de cadastro ancorada no grupo de campos.

O estado de catálogo indisponível corrige o defeito 1.2.3: hoje a coluna do formulário fica em "Carregando cadastros…" para sempre e o erro aparece do outro lado da tela. Numa tela só para o formulário, a falha tem um lugar óbvio para morar.

#### 4.1.1 Por que não um wizard de três passos

Porque as três seções não são independentes (critério b) e porque o payload é atômico (critério a). Um wizard esconderia campos que a recusa do gate referencia em conjunto — o usuário leria `OCUPACAO_BAIXA` num passo e precisaria voltar dois passos para corrigir o peso. Em desktop, com 1280 px de largura, esconder campos custa mais do que mostra.

A numeração dá o roteiro de leitura sem cobrar cliques por isso.

### 4.2 Resultado — `/simulacoes/:id`

**Propósito**: responder "esta rota passa?" e provar a resposta. Nada além disso.

**Etapas**: S5, S6, S7, S8, S9.

**Conteúdo**: faixa de veredito em largura total no topo (`ResultHeader`); abaixo, grid de duas colunas — ordem de entrega à esquerda, composição do custo à direita; pedágio e VPO em seguida. Os três recortes da mesma resposta ficam visíveis na mesma dobra.

**Ações**: "Ajustar e validar de novo" (leva o payload desta simulação para o rascunho e volta a `/`) · "Registrar execução" (vai para 4.3) · "Voltar ao histórico".

**O que não entra**: formulário de edição, registro de execução, integridade.

**Estados**: carregando · não encontrada (404) · aprovada · aprovada_com_avisos · rejeitada. Toda rejeitada aqui tem id e evidência — recusa sem id nunca chega nesta tela (ver 5.2).

**Ganho esperado, com a conta à mostra**: hoje o comparativo começa em y=1279, 379 px abaixo da dobra. Somando as alturas medidas dos blocos que permanecem — veredito 214, ordem 235, custo 401 — e colocando ordem e custo lado a lado, a coluna cai para cerca de 615 px, mais o painel de VPO quando houver praça (~150 px). Ou seja: ~765 px contra 1891. É **projeção aritmética a partir das alturas medidas**, não medição — a medição só existe depois de implementar. Se o VPO entrar, o rodapé da tela encosta na dobra em vez de passar dela.

### 4.3 Execução — `/simulacoes/:id/execucao`

**Propósito**: registrar o que aconteceu de fato e medir o desvio contra a mesma fórmula de custo.

**Etapas**: S10.

**Máquina de estados explícita** — hoje ela está implícita dentro de `Comparativo.tsx`:

| Estado | Como é detectado | O que a tela mostra |
| --- | --- | --- |
| `sem-execucao` | `GET /comparativo` → 404 `EXECUCAO_NAO_REGISTRADA` | formulário de valores reais, pré-preenchido com os previstos |
| `registrando` | requisição em curso | botão desabilitado |
| `registrada` | `GET /comparativo` → 200 | classificação (`dentro`/`atencao`/`critico`) e tabela previsto × real |
| `conflito` | `POST /api/execucoes` → 409 `DADOS_DIVERGENTES` | recarrega o comparativo existente em vez de mostrar erro cru |

A regra que o código atual não tem: **o formulário nunca aparece se já existe execução.** Hoje, reabrir a tela depois de registrar mostra o formulário de novo e o usuário só descobre o impedimento ao clicar. O probe por `GET /comparativo` resolve isso com uma chamada que já existe e cujo 404 tem código próprio.

**O que não entra**: edição da simulação, segundo registro (o 409 é definitivo neste MVP — decisão em aberto na seção 9).

### 4.4 Integridade — `/integridade`

**Propósito**: varrer o cadastro com os mesmos códigos do gate, sem depender de simulação nenhuma.

**Etapas**: S11.

**Conteúdo**: total de ocorrências, chips por código que passam a **filtrar** a lista, e a lista completa. Hoje `IntegridadePanel` corta em `slice(0, 8)` porque divide espaço com tudo o mais; numa tela própria o corte deixa de ter motivo.

**Ações**: atualizar (revarre).

**O que não entra**: qualquer coisa de simulação.

### 4.5 Histórico — `/simulacoes` (recomendada, cortável)

**Propósito**: reentrar numa simulação anterior. É o índice que torna 4.2 e 4.3 alcançáveis sem depender de memória.

**Etapas**: S12.

**Conteúdo**: tabela com id curto, quando, status, km e margem — exatamente os cinco campos que `GET /api/simulacoes` já devolve, sem mudança de backend. Linha abre o Resultado.

**É a única tela que pode sair** se o MVP precisar encolher: o fluxo Simulação → Resultado → Execução continua completo sem ela. A consequência de cortar é declarada: perde-se a reentrada por lista; uma simulação antiga só é acessível por URL direta.

---

## 5. Navegação

### 5.1 Rotas

| Rota | Tela | Entrada |
| --- | --- | --- |
| `/` | Simulação | navegação principal |
| `/simulacoes` | Histórico | navegação principal |
| `/integridade` | Integridade | navegação principal |
| `/simulacoes/:id` | Resultado | após submeter, ou a partir do histórico |
| `/simulacoes/:id/execucao` | Execução | a partir do Resultado |

Três destinos na navegação principal, dois detalhes contextuais. Resultado e Execução **não entram no menu**: não são lugares, são consequências de uma simulação específica. Colocá-los na barra produziria itens que não levam a lugar nenhum quando não há id.

### 5.2 Os dois caminhos de recusa

```
                      ┌─ 422 (sem id) ─→ recusa na própria Simulação,
                      │                   ancorada em detalhe.campo
POST /api/simular ────┤
                      └─ 200 (com id) ──→ navega para /simulacoes/:id
                                          (veredito pode ser rejeitada)
```

A assimetria é do backend e a interface deve refleti-la, não escondê-la. Recusa de cadastro é algo que **impede a simulação de existir**; recusa de operação é o gate **funcionando sobre uma simulação que existe**. Tratá-las como a mesma tela — como hoje — apaga a diferença entre "não deu para simular" e "simulei, e reprovou".

### 5.3 Transições

- Simulação → Resultado: só em 200. Em 422, permanece e ancora a recusa.
- Resultado → Execução: sempre disponível; a tela de execução decide sozinha se mostra formulário ou comparativo.
- Resultado → Simulação: por "Ajustar e validar de novo", que **carrega o payload** no rascunho. Sem isso, o laço de iteração custaria redigitar a rota.
- Qualquer tela → Histórico: pela navegação principal.
- Voltar do navegador funciona em todas, porque cada tela tem URL.

### 5.4 Escolha de roteador

Recomendação: **`react-router-dom`**. Custo: uma dependência, ~20 kB gzip. Ganho: parâmetros de rota, histórico do navegador, links reais e o padrão `state` para pintar antes da revalidação — tudo que as cinco telas usam.

Alternativa sem dependência: um roteador de hash de ~60 linhas. Funciona para cinco rotas, mas reimplementa histórico, parsing de parâmetro e o estado de navegação. Para um projeto de portfólio, a dependência convencional comunica mais do que a artesanal.

---

## 6. Onde mora o estado

| Estado | Onde | Tempo de vida | Por quê |
| --- | --- | --- | --- |
| `catalogos` | `CatalogosProvider` acima do roteador | sessão | três telas consomem; refetch por navegação produziria flicker sem ganho |
| `form` (rascunho) | `RascunhoProvider` + espelho em `sessionStorage` | sessão, sobrevive a reload | precisa atravessar Simulação → Resultado → volta |
| `resultado` | **não é estado global** — a URL carrega o id | enquanto a URL existir | o dado é do servidor; duplicá-lo em memória cria duas verdades |
| `execucao` | estado local da tela Execução | enquanto a tela existir | formulário de uso único |
| `diagnostico` | estado local da tela Integridade | enquanto a tela existir | uma tela só consome |

### 6.1 O resultado vem do servidor, não da memória

Depois do `POST`, o objeto já está na resposta: passa-se por `navigate('/simulacoes/' + id, { state: { resultado } })` para pintar sem esperar. A tela usa esse objeto **se** `state.resultado.id === params.id`; caso contrário, busca `GET /api/simulacoes/{id}`. É o padrão de pintar do estado e revalidar do servidor — e é o que faz um reload na tela de Resultado funcionar, coisa que hoje não acontece.

### 6.2 Por que não um store

Há **um** dado compartilhado entre telas (o rascunho) e nenhuma atualização cruzada entre telas simultâneas. Contexto mais estado local resolve. Redux ou Zustand aqui seria cerimônia sem problema correspondente — e o projeto tem como regra não pagar por isso.

### 6.3 O rascunho é reidratável de graça

`GET /api/simulacoes/{id}` devolve `{ id, created_at, payload, resultado }`. O `payload` tem os mesmos 17 campos de `SimulacaoIn` — que é exatamente o formato de `SimulacaoForm` no frontend. Então "Ajustar e validar de novo" é:

```
setRascunho(payload) ; navigate('/')
```

Sem transformação, sem endpoint novo. É o argumento mais forte a favor da tela de Resultado separada: o laço de iteração não perde nada.

### 6.4 Detalhes que costumam ser esquecidos

- `FORM_INICIAL` sai de `App.tsx` para `lib/rascunho.ts`; é semente de rascunho, não configuração de tela.
- `sessionStorage` e não `localStorage`: rascunho é de sessão, não preferência. Fechar o navegador descarta.
- O rascunho precisa de ação explícita "limpar", porque agora ele sobrevive a um reload — comportamento novo, que pode surpreender quem espera começar do zero.
- Ao abrir uma simulação do histórico e clicar em "Ajustar", o rascunho atual é **sobrescrito**. Isso é intencional, mas pede confirmação quando houver edição não submetida.

---

## 7. Impacto nos componentes existentes

| Arquivo | Hoje | Depois | Trabalho |
| --- | --- | --- | --- |
| `App.tsx` (154 l.) | dono de todo o estado e do layout de duas colunas | `AppShell`: header, navegação, `<Outlet/>`, providers | reescrito, ~50 l. |
| `components/AppHeader.tsx` (16) | marca e subtítulo | + navegação principal com estado ativo + badge de integridade | ~40 l. |
| `components/SimulationForm.tsx` (292) | formulário e submit | recebe a recusa 422 para ancorar por `detalhe.campo`; seções numeradas; grid interno de duas colunas | +40 l., **campos intactos** |
| `StopList` (interno, ~107 l.) | dentro de `SimulationForm` | extraído para `components/StopList.tsx` | mover, zero lógica |
| `components/ResultHeader.tsx` (55) | bloco no topo da coluna | faixa de veredito em largura total | +10 l. |
| `components/AlertList.tsx` (40) | lista de avisos | idem, com âncora visual por campo | +15 l. |
| `components/StopOrderTable.tsx` (73) | painel empilhado | coluna esquerda do grid de resultado | ~0 |
| `components/CostBreakdown.tsx` (53) | painel empilhado | coluna direita do grid | ~0 |
| `components/VpoPanel.tsx` (46) | devolve `null` quando não há pedágio | declara "sem pedágio nesta rota" em vez de desaparecer | +10 l. |
| `components/Comparativo.tsx` (118) | painel com formulário e botão | vira a tela Execução, com a máquina de estados da seção 4.3 | reescrito, ~160 l. |
| `components/IntegridadePanel.tsx` (65) | faixa abaixo de tudo | vira tela, com filtro por código e lista completa | +35 l. |
| `components/EmptyState.tsx` (13) | resultado vazio | reusado em Histórico, Integridade e 404 | ~0 |
| `components/InlineError.tsx` (27) | erro de submissão | reusado para 404 e falha de catálogo | ~0 |
| `lib/api.ts` (97) | 8 chamadas | + `simulacao(id)` e `simulacoes()` | +2 funções |
| `types.ts` (137) | tipos de resposta | + `SimulacaoResumo`, `SimulacaoDetalhe` | +12 l. |
| `styles.css` (556) | grid de duas colunas | + navegação, + grid do resultado, + telas | +80 l. |

**Arquivos novos**: `router.tsx`; `screens/{Simulacao,Resultado,Execucao,Integridade,Historico}.tsx`; `state/catalogos.tsx`; `state/rascunho.tsx`; `lib/rascunho.ts`.

**O que não muda**: o backend, byte por byte. Todos os endpoints necessários já existem — inclusive `GET /api/simulacoes` e `GET /api/simulacoes/{id}`, que hoje ninguém chama. Os 55 testes continuam válidos porque testam a API, não a tela. Fórmula de custo, códigos de validação e gate ficam intocados. A mudança é inteiramente de camada de apresentação.

---

## 8. Desktop como escopo declarado

O MVP passa a ter alvo único: **1280 a 1680 px**. Isso não é indiferença a telas menores, é escopo — e precisa estar escrito, não implícito.

**O que o escopo libera**

- Grid de resultado em duas colunas sem media query, porque a largura mínima é conhecida.
- Tabela de ordem sem rolagem horizontal a partir de 1280 px (ela mede 718 px).
- Formulário em duas colunas internas em vez de 440 px fixos, o que devolve largura aos campos de janela e peso.
- Navegação principal fixa, sem menu colapsado.

**O que fica como está**

Os breakpoints de 1050, 760 e 420 px permanecem no CSS como degradação. Já existem, já foram medidos, não custam manutenção. O que eles **não** recebem é trabalho novo: nenhuma tela será desenhada para 390 px.

**O que se declara**

Abaixo de 1024 px o app não é suportado. O README deve dizer isso, em vez de sugerir uma responsividade que ninguém vai testar. A varredura que mede reflow a 320 px continua rodando como sinal, mas deixa de ser critério de aceite.

---

## 9. Decisões em aberto

1. **Histórico entra no MVP?** Recomendo sim — é a única tela cortável e o custo é uma tabela sobre um endpoint pronto. Sem ela, simulação antiga só é alcançável por URL direta.
2. **Roteador**: `react-router-dom` ou hash próprio de ~60 linhas. Recomendo o primeiro, pela convenção.
3. **Rascunho sobrevive a reload?** Recomendo sim, em `sessionStorage`. Muda comportamento: hoje recarregar zera tudo.
4. **Execução já registrada**: o 409 é definitivo neste MVP. Permitir correção exigiria `PUT` ou versionamento no backend — fora do escopo de uma divisão de telas, mas é uma pergunta de produto que vai voltar.

---

## 10. Ordem de implementação sugerida

Cada passo deixa o app funcionando; nenhum exige os seguintes.

| Passo | O que entra | Como se verifica |
| --- | --- | --- |
| 1 | Roteador + `AppShell`, com `/` servindo a tela atual sem mudança de comportamento | app idêntico ao de hoje; navegação presente |
| 2 | Resultado em `/simulacoes/:id`, com busca por id e `state` para pintar antes | reload na tela de resultado mantém o veredito |
| 3 | Execução em `/simulacoes/:id/execucao`, com a máquina de quatro estados | registrar, recarregar e ver comparativo — não o formulário |
| 4 | Integridade em `/integridade`, com filtro por código | badge na navegação bate com o total da tela |
| 5 | Histórico em `/simulacoes`, se aprovado | abrir uma simulação antiga e ajustá-la |
| 6 | `npm run a11y` parametrizado por rota | cinco rotas, zero paradas sem anel |

O passo 6 não é opcional: o script atual abre `/` e clica em "Validar rota". Depois da divisão ele cobriria uma tela de cinco, e a afirmação "45 paradas de foco, nenhuma sem anel" passaria a ser verdadeira só para a primeira. Verificação que não acompanha a mudança de estrutura vira decoração.

---

## 11. Resumo em uma frase

O formulário fica sozinho porque é atômico; o veredito fica com a evidência porque a tese do projeto não admite separá-los; execução, integridade e histórico saem porque acontecem em outros momentos — e o resultado passa a ter URL, o que hoje ele não tem.
