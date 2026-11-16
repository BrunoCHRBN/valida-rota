# PROPOSTA — Design System: ValidaRota

**Data**: 16/11/2026 · **Status**: proposta para decisão · **Base**: decisões do plano `cosmic-beacon-darwin-mglD_umX.md`

## 1. Objetivo e princípios

A interface é uma ferramenta de decisão, não uma vitrine. O usuário precisa responder três perguntas em poucos segundos: *a rota foi aprovada?*, *por quê?*, *o que eu faço agora?*.

| Princípio | Decisão | Consequência prática |
|---|---|---|
| Dados antes de decoração | tabelas e números são o conteúdo principal | sem visual de mapa, sem Three.js, sem "hero art" |
| Estado é informação | todo alerta traz `codigo` + evidência | nunca só um ícone vermelho ou texto livre |
| Anti-slop é requisito | sem gradiente decorativo, sem glassmorphism, sem emoji em botão | ícones `lucide-react` com peso 1.5, sem animação de entrada |
| Herdar a identidade do portfólio | mesma família de papel/tinta/terracota | o projeto se reconhece como parte do conjunto do Bruno |
| Acessibilidade é parte do contrato | WCAG 2.2 AA como meta | contraste medido, foco visível, navegação por teclado |

Fora do escopo visual: tema escuro, modo de alta densidade, animações com movimento, mapa interativo.

## 2. Tokens visuais

Fonte dos tokens: `~/Projetos/bruno-portfolio-starter/src/styles.css`, lido em 16/11/2026. Contraste calculado com a fórmula WCAG relativa; números abaixo são medidos, não estimados.

### 2.1 Cor

```css
:root {
  --paper:      #f5f3ee;  /* fundo */
  --paper-2:    #efede6;  /* superfície alternada / cabeçalho de tabela */
  --ink:        #202724;  /* texto principal — 13.75:1 sobre paper */
  --muted:      #5c645d;  /* texto secundário — 5.51:1 sobre paper */
  --line:       #dbd9d1;  /* bordas e separadores */
  --dark:       #17211f;  /* botão primário — branco sobre ele: 16.49:1 */

  --accent:     #8a4f37;  /* terracota escurecido — 5.82:1 sobre paper */
  --accent-soft:#e7d4c6;  /* preenchimento suave, nunca texto */
  --sage:       #4f6b59;  /* sálvia escurecido — 5.29:1 sobre paper */
  --sage-soft:  #dce3d8;
  --info:       #4f6669;  /* azul petróleo — 5.51:1 sobre paper */
  --danger:     #9c4a3c;  /* erro — 5.48:1 sobre paper */
  --danger-soft:#f2ded9;
  --warning:    #8a4f37;  /* reusa terracota, sem inventar amarelo */
}
```

Ajuste em relação ao portfólio: os originais `--muted: #737a73` (3.98:1), `--terracotta: #c77d59` (2.91:1) e `--sage: #a2b8a8` (baixo contraste) falham AA para texto. Continuam válidos como preenchimento decorativo; para texto, usar as variantes escurecidas acima. Foco: `#8a4f37`, 2px, `outline-offset: 2px`.

Roles semânticas:

| Role | Cor | Uso |
|---|---|---|
| Aprovada | `--sage` + `--sage-soft` | status `aprovada` |
| Aprovada com avisos | `--warning` + `--accent-soft` | status `aprovada_com_avisos` |
| Rejeitada | `--danger` + `--danger-soft` | status `rejeitada` |
| Informativo | `--info` | metadados, contadores |

Todo status traz o texto do código, além da cor.

### 2.2 Tipografia

```css
--font-ui:   'DM Sans', system-ui, sans-serif;
--font-mono: 'DM Mono', ui-monospace, monospace;
```

- `DM Sans` para texto, rótulos e botões.
- `DM Mono` para números, códigos de alerta, km, R$ e percentuais, com alinhamento previsível em tabela.
- Sem `Playfair Display` no app: a serif pertence à vitrine, não à ferramenta.
- Escala: 11 / 12 / 13 / 15 / 20 / 28 px. Nada abaixo de 11px.
- Números em tabela: `font-variant-numeric: tabular-nums`, alinhamento à direita.

### 2.3 Espaço, raio e borda

```css
--space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
--space-5: 24px; --space-6: 32px; --space-7: 48px; --space-8: 64px;
--radius: 3px;          /* mesmo do portfólio */
--border: 1px solid var(--line);
--shadow: 0 6px 20px rgba(23, 33, 31, .06); /* só em elevação real */
```

Sem `backdrop-filter`, sem `linear-gradient` decorativo, sem `box-shadow` em repouso.

## 3. Componentes

Inventário mínimo para o MVP. Cada componente prevê estado de erro e estado vazio.

| Componente | Responsabilidade | Estados |
|---|---|---|
| `AppHeader` | identidade ValidaRota + link para o repo + filtro de perfil | padrão |
| `SimulationForm` | origem, paradas, veículo, motorista, placa, receita, VPO, `modo_pedagio` | padrão / validando / erro de servidor |
| `StopList` | adicionar/remover paradas com janela, peso e prioridade 0–9 | vazio / preenchido / limite de 8 |
| `ResultHeader` | status do gate + km + tempo + margem | aprovada / com avisos / rejeitada |
| `StopOrderTable` | ordem ótima, chegada prevista, janela, setor | padrão / vazio |
| `CostBreakdown` | diesel, pedágio, depreciação, manutenção, motorista, total | padrão / divergente |
| `AlertList` | `codigo`, severidade, evidência em `detalhe_json`, ação de resolver | vazio / lista / resolvido |
| `Comparativo` | previsto × real: km, custo, desvio | sem execução / preenchido |
| `IntegridadePanel` | contadores por código de alerta no diagnóstico | padrão / carregando / erro |
| `VpoPanel` | saldo, validade, TAG × placa, praças previstas × cobradas | padrão / saldo baixo / vencido |
| `InlineError` | erro de API com `codigo` e ação sugerida | — |
| `EmptyState` | texto + próxima ação explícita | — |

Regra de composição: `AlertList` é o único lugar onde se decide o que fazer com um alerta. `ResultHeader`, `IntegridadePanel` e `VpoPanel` consomem a mesma função `severidadeDe(codigo)`.

## 4. Padrões de interface

- **Fluxo principal**: formulário → resultado → alertas → comparativo. Uma tela por etapa, sem modal encadeado.
- **Gate pós-simulação**: o resultado sempre mostra `aprovada | aprovada_com_avisos | rejeitada` no topo, com a lista de motivos logo abaixo. Nunca esconder rejeição em tooltip.
- **Erro de validação**: mostrar o trecho/nó exato (`409` com `codigo`), não mensagem genérica.
- **Ações destrutivas** (remover parada, resolver alerta): confirmação inline, sem dialog de sistema.
- **Linguagem**: português do Brasil, termos do domínio — parada, aresta, praça, jornada, ocupação, VPO. Sem inglês misturado em rótulo.
- **Densidade**: uma linha por parada, sem cards grandes. O usuário compara números; tabela é melhor que grade.

## 5. Acessibilidade

- Meta: **WCAG 2.2 AA**. Contrastes medidos na seção 2; revalidar com ferramenta no navegador antes de fechar a UI (evidência, não cálculo de planilha).
- Foco visível em `:focus-visible`, 2px, `--accent`, com `outline-offset: 2px`.
- Todo input tem `<label>` associado; erro ligado por `aria-describedby`.
- `aria-live="polite"` na região de alertas e no status do gate.
- Tabela com `<th scope="col">`; quando o cabeçalho não for suficientemente explícito, usar `aria-label` em português, ex.: `aria-label="Distância em quilômetros"`.
- Navegação completa por teclado: Tab, Enter para ações, Escape para fechar expansões.
- Alvos de toque mínimo 44×44px.
- `prefers-reduced-motion: reduce` desliga transições, padrão já usado no portfólio.
- Zoom de 200% sem perda de informação; sem `overflow: hidden` em containeres de conteúdo.
- Status por cor + texto: nunca só a cor.

## 6. Responsividade

Abordagem mobile-first, mas com prioridade de leitura de tabela.

| Largura | Comportamento |
|---|---|
| < 640px | formulário em uma coluna; `StopOrderTable` vira lista de linhas empilhadas com rótulo; `Comparativo` em duas colunas empilhadas |
| 640–1023px | formulário em duas colunas; tabelas com scroll horizontal contido no próprio componente |
| ≥ 1024px | layout de duas colunas: formulário à esquerda, resultado à direita; tabelas completas |
| ≥ 1440px | largura máxima 1320px, centrado |

Breakpoints reutilizam os do portfólio: 760px e 1050px. Sem `min-width` global acima de 320px; o portfólio usa `body { min-width: 320px }`.

## 7. Pontos que ainda precisam ser validados

1. Contraste medido aqui é cálculo feito fora do navegador; confirmar com inspeção no navegador após implementar.
2. A família DM Sans/DM Mono vem do Google Fonts no portfólio — decidir se o app replica a dependência externa ou usa `system-ui` + `ui-monospace` para evitar requisição de rede em runtime.
3. Quantas paradas cabem confortavelmente na tela antes de paginação — o limite algorítmico é 8, o visual pode ser menor em mobile.
4. Se o painel de integridade precisa de filtro por severidade desde o MVP ou se a lista simples resolve.
