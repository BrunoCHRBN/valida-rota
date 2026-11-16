# Plano — ValidaRota: projeto de portfólio em logística rodoviária

Nota de integridade: este arquivo foi reconstruído em 16/11/2026 a partir das decisões registradas na memória do projeto e nos documentos `PROPOSTA_DESIGN_SYSTEM.md` e `PROPOSTA_SYSTEM_DESIGN.md`. A versão anterior havia voltado a uma cópia antiga de 106 linhas; o backup dessa cópia está em `cosmic-beacon-darwin-mglD_umX.md.bak`. Cópia canônica: `~/Projetos/valida-rota/docs/PLANO_VALIDA_ROTA.md`.

## 1. Decisões fechadas

- Objetivo: demonstrar engenharia full-stack de ponta a ponta — backend, regras de negócio, persistência, API, frontend e verificação.
- Stack: Python + FastAPI + React.
- Escopo: MVP focado, uma tese verificável, com superfície pequena o suficiente para ser defendida em entrevista.
- Temas cobertos: custos e tarifação, roteirização e última milha, frota e manutenção.
- Nome: ValidaRota. Slug: `valida-rota`.
- Prioridade de automação: gate de aceitação pós-simulação.
- Tese: validação baseada em dados reduz revisão manual de rotas, trajetos inexistentes e divergências entre previsto e executado.

## 2. Nome, slug e vitrine

O nome ValidaRota substitui a designação anterior porque descreve a ação do sistema: validar antes de emplacar. A consulta à API do GitHub em 16/11/2026 retornou 404 para `BrunoCHRBN/valida-rota` e para `BrunoCHRBN/validarota`, indicando que ambos os slugs estavam livres naquele momento.

Card planejado para `~/Projetos/bruno-portfolio-starter/src/data/project-overrides.ts`:

```ts
{
  slug: 'valida-rota',
  title: 'ValidaRota',
  description: 'Valide rotas de entrega antes de emplacar: trajetos inexistentes, jornada, ocupação e custo real, com o motivo de cada rejeição.',
  category: 'Operações',
  tags: ['Python', 'FastAPI', 'React', 'SQLite', 'pytest'],
  featured: true,
  accent: 'blue',
  mark: 'V',
  status: 'Em evolução',
}
```

A vitrine monta `repoUrl` a partir de `repo?.html_url ?? https://github.com/${siteConfig.githubUsername}/${override.slug}`. Se o repositório público não existir, o card aponta para um endereço inventado. Por isso a entrada do card vem depois da criação do repositório e do deploy, não antes.

Local do código: `/home/bruno-vsantos/Projetos/valida-rota/`, ao lado do `bruno-portfolio-starter`. Não criar dentro do workspace da sessão.

## 3. Ideias avaliadas

| Ideia | Roteirização | Custos | Frota |
| --- | --- | --- | --- |
| ValidaRota (escolhida) | validação de existência, ordem de paradas e gate | diesel, pedágio, depreciação, manutenção, motorista, VPO | perfil define consumo e custo; revisão e jornada geram alerta |
| JanelaCerta | VRPTW-lite com janelas de entrega | custo por atribuição | capacidade e disponibilidade restringem |
| FrotaSaudável | km derivados das rotas | manutenção versus falha | manutenção preventiva e disponibilidade |
| CotaçãoLM | distância e pedágio do corredor | cotação com margem explícita | veículo e motorista aptos para a linha |

ValidaRota cobre as três frentes com um único mecanismo de validação reutilizável, em vez de espalhar regras por três projetos pequenos. Isso mantém o escopo verificável de ponta a ponta.

## 4. Arquitetura

```
React (formulário)
   |  POST /api/simular · GET /api/simulacoes/{id}/comparativo
   v
FastAPI ──> validacao.py  (gate único, antes e depois)
   |            |
   |            +--> grafo.py / supermatrix.py  (Dijkstra + matriz pairwise)
   |            +--> otimizador.py             (permutações limitadas a 8)
   |            +--> custo.py                  (fórmula + margens + VPO)
   |            +--> geocodificacao.py         (porta + provider sintético)
   |            +--> pedagio.py                (conciliação previsto x TAG)
   v
SQLite <── models.py / schemas.py ──> JSON ──> React
```

Monosserviço em duas frentes: backend FastAPI e frontend React. Fila, cache e serviços externos ficam fora desta versão. A simulação é exercitada em `TestClient`; o deploy é verificado com `curl` contra o endpoint ao vivo.

`validacao.py` é a única fonte de regras. `/api/simular` e `/api/diagnostico` chamam a mesma função; não existe uma segunda implementação das regras no caminho do diagnóstico.

## 5. Entidades

- `Veiculo(id, nome, perfil, consumo_km_l, depreciacao_rs_km, manutencao_rs_km, capacidade_kg, km_atual, km_proxima_revisao, disponivel)`.
- `No(id, nome, setor_id, qualidade_geo, lat, lon)` — coordenadas sintéticas usadas apenas na validação de geocodificação, sem renderização de mapa.
- `Aresta(de, para, km, pedagio_rs, velocidade_media_km_h)`.
- `Motorista(id, custo_hora, jornada_max_h)`.
- `Parada(no_id, janela_inicio, janela_fim, peso_kg, prioridade, minutos_servico)`.
- `PerfilRoteirizacao(id, nome, mu, nu, xi, ocupacao_minima_pct, raio_setor_km)` — parâmetros salvos e clonáveis.
- `Simulacao(id, created_at, payload, resultado_json)` — previsto.
- `ExecucaoReal(id, simulacao_id, km_real, diesel_real, pedagio_real, rota_executada)` — fato, relação 1:1 com `Simulacao`; o previsto nunca é sobrescrito.
- `Alerta(id, codigo, severidade, entidade_id, detalhe_json, criado_em)`.
- `ValePedagio(id, operadora, tag, placa, saldo_rs, validade)`, `LancamentoPedagio(id, vale_id, praca, valor_rs, data, tag)`, `TarifaPedagio(praca, valor_rs, vigente_de, vigente_ate)`.

## 6. Endpoints

- `GET/POST /api/veiculos` — frota.
- `GET /api/nos`, `GET /api/arestas` — transparência do grafo e fixture de teste.
- `GET/POST /api/perfis` — perfis de roteirização.
- `POST /api/simular` — corpo com `origem_id`, `paradas[]`, `veiculo_id`, `motorista_id`, `perfil_id`, `placa`, `receita_rs`, `modo_pedagio`, `vpo`, `evitar_pedagio`; resposta com `status`, `ordem`, `distancia_km`, `tempo_h`, `custos{}`, `total_rs`, `margem_rs`, `margem_pct`, `avisos[]`.
- `GET /api/simulacoes` — histórico; `GET /api/simulacoes/{id}/comparativo` — previsto versus real; `GET /api/simulacoes/{id}/pedagio` — praças previstas, cobradas e cobertura do VPO.
- `POST /api/execucoes` — registro da execução real.
- `GET /api/diagnostico` — varredura de integridade do cadastro e do histórico.
- `GET/POST /api/vales-pedagio`, `POST /api/lancamentos-pedagio` — VPO e extrato TAG.

## 7. Lógica central

Dijkstra sobre `Aresta.km`. Com `evitar_pedagio`, o peso da aresta passa a ser `km + λ·pedagio_rs`. A SuperMatrix pré-computa distância e tempo para cada par de nós com Dijkstra por origem; com cerca de 10 nós no corredor sintético, o custo é irrelevante.

Para até 8 paradas, `otimizador.py` enumera permutações (8! = 40.320) e escolhe a menor pontuação:

```
score = distancia_total
      + μ · Σ violacao_janela
      + ν · Σ penalidade_prioridade
      + ξ · desvio_setor
```

`tempo_h` é o tempo de direção: soma de `km / velocidade_media_km_h` por aresta. `tempo_total_h` é a jornada: direção mais `minutos_servico` por parada mais espera quando a chegada antecede a janela. O custo de motorista e o limite de jornada usam `tempo_total_h`; exibir apenas `tempo_h` subestimaria o turno. Sem velocidade por aresta e minutos de serviço por parada, nenhum dos dois teria origem calculável.

Custo e margem:

```
diesel       = (km / consumo_km_l) · preco_diesel
pedagio      = Σ pedagio_rs das arestas do caminho
depreciacao  = km · depreciacao_rs_km
manutencao   = km · manutencao_rs_km + extra se km_atual + km > km_proxima_revisao
motorista    = tempo_total_h · custo_hora
total        = diesel + pedagio + depreciacao + manutencao + motorista
margem       = receita_rs - total
margem_pct   = margem / receita_rs
```

Com vale-pedágio na mão do embarcador, o pedágio sai do custo de bolso da transportadora, mas continua custo logístico da operação:

```
margem_transportadora       = receita_frete_rs - (diesel + depreciacao + manutencao + motorista)
custo_logistico_embarcador  = receita_frete_rs + vpo_consumido_rs
```

`custo.py` é chamado tanto no previsto quanto no real, com a mesma fórmula. Sem essa regra, o comparativo mediria diferença de implementação, não diferença de execução.

## 8. Conceitos extraídos do ITB.BRA-M220

Fonte: `~/Downloads/ITB.BRA-M220 Roteirização - CNC (1).pdf`, 42 páginas, extraído com `pdftotext -layout` para `/tmp/roteirizacao_cnc.txt` em 16/11/2026. O que segue é leitura do texto extraído, não transcrição de norma e não afirmação de que o documento prescreve regras além das aqui descritas.

| Conceito do ITB | Tradução para o MVP |
| --- | --- |
| Perfil do veículo | `Veiculo.perfil` define consumo, capacidade e custos por km |
| Setor de atendimento | `No.setor_id` e penalidade `ξ` para paradas fora do setor |
| Qualidade da geocodificação | `No.qualidade_geo` com `exata`, `alta`, `media`, `baixa`, `ambigua`, `fornecida_usuario` |
| Prioridade de parada | `Parada.prioridade` de 0 a 9 entra em `ν` na pontuação |
| Perfil de roteirização | `PerfilRoteirizacao` guarda `μ`, `ν`, `ξ` e limites, clonável entre simulações |
| KM roteirizado versus KM realizado | SuperMatrix para o previsto; `ExecucaoReal` para o fato; `comparativo.py` mede o desvio |
| Janela e jornada | `Parada.janela_inicio/fim` e `Motorista.jornada_max_h` alimentam o gate |

A ideia central aproveitada do documento é calcular o trajeto roteirizado próximo do real e confrontedá-lo com o executado. O sistema não se limita a desenhar uma ordem de paradas: ele registra a diferença e explica a origem dela.

## 9. Gate de aceitação pós-simulação

Escolhido como prioridade 1 entre as automações propostas porque é a única que intercepta o erro antes do emplacamento e gera evidência reutilizável no diagnóstico. `validacao.py` roda antes da otimização (existência, alcançabilidade, geocodificação, revisão, jornada estimada) e depois dela (ocupação, setor, coerência de janelas). O resultado traz `aprovada`, `aprovada_com_avisos` ou `rejeitada`, sempre acompanhado dos códigos e do detalhe.

| Código | Gatilho | Evidência mínima |
| --- | --- | --- |
| `NO_NAO_EXISTE` | ponto de origem ou parada fora do cadastro | id informado |
| `ARESTA_INCOMPLETA` | velocidade ou km ausentes na aresta | ids da aresta |
| `TRECHO_INALCANCAVEL` | Dijkstra não encontra caminho | par de nós |
| `COORDENADAS_DIVERGENTES` | distância entre cadastrada e obtida acima do raio | latitude, longitude, distância em metros |
| `GEOCODIFICACAO_BAIXA` | qualidade `baixa` ou `ambigua` | qualidade e fonte |
| `REVISAO_VENCIDA` | km previsto ultrapassa a próxima revisão | km_atual, km previsto, limite |
| `JORNADA_EXCEDIDA` | tempo calculado passa `jornada_max_h` | horas calculadas e limite |
| `CONSUMO_FORA_FAIXA` | consumo do veículo fora da faixa do perfil | consumo e faixa |
| `OCUPACAO_BAIXA` | ocupação do veículo abaixo do mínimo do perfil | kg previsto, capacidade, mínimo |
| `DESVIO_SETOR` | parada fora do raio de setor permitido | setor esperado e setor da parada |
| `DESVIO_ROTA_RECORRENTE` | desvio repetido em múltiplas execuções | contagem e simulações relacionadas |
| `PEDAGIO_DIVERGENTE` | pedágio previsto difere do lançado | valores previsto e cobrado, praça |
| `TARIFA_DIVERGENTE` | tarifa da praça divergente da vigente | tarifa usada e vigente |
| `PRACA_NAO_PREVISTA` | praça cobrada não estava no grafo | praça e rota executada |
| `PEDAGIO_EMBUTIDO_NO_FRETE` | frete inclui pedágio sem VPO separado | receita, modo_pedagio |
| `VPO_SALDO_INSUFICIENTE` | saldo não cobre o pedágio previsto | saldo, previsto, diferença |
| `VPO_VENCIDO` | validade anterior à data da viagem | validade e data |
| `TAG_NAO_VINCULADO_A_PLACA` | TAG do lançamento não corresponde à placa informada | tag, placa, tag esperada |
| `DADOS_DIVERGENTES` | campos obrigatórios inconsistentes entre entidades | entidades e campos |
| `EXECUCAO_NAO_REGISTRADA` | diagnóstico encontra simulação antiga sem execução | id da simulação, idade |

O texto do detalhe é montado no backend, em português do Brasil, e viaja junto com o `codigo`. A interface nunca mostra apenas uma cor ou um ícone para explicar uma rejeição.

### 9.1 Geocodificação automatizada

No dia a dia da empresa, a conferência de Latitude/Longitude no Google Maps é manual e depende do operador. O plano automatiza a comparação, mas não escolhe o Google Maps como provider: a diretriz de compliance de mapas deste ambiente não permite esse uso. Providers permitidos são Tencent Maps, AMap, Baidu Maps e Tianditu, com Tencent como padrão quando houver implementação real. Nenhuma chave fica no repositório; em integração futura, a chave passa por proxy.

```python
@dataclass(frozen=True)
class ResultadoGeo:
    lat: float
    lon: float
    qualidade: str   # exata | alta | media | baixa | ambigua | fornecida_usuario
    fonte: str       # sintetico | tencent | usuario

def validar(cadastrado: ResultadoGeo, obtido: ResultadoGeo, raio_max_m: float = 150) -> list[str]:
    alertas: list[str] = []
    if obtido.qualidade in {"baixa", "ambigua"}:
        alertas.append("GEOCODIFICACAO_BAIXA")
    if distancia_m(cadastrado, obtido) > raio_max_m:
        alertas.append("COORDENADAS_DIVERGENTES")
    return alertas
```

`ProvedorGeocodificacao` é um `Protocol`; `ProvedorSintetico` atende ao MVP e `ProvedorTencent` fica como adaptador futuro via `_TMapSecurityConfig`. A confirmação humana fica restrita às exceções: quando a qualidade é baixa ou a divergência passa do raio, a fila de exceção registra a origem da correção e muda a qualidade para `fornecida_usuario` com auditoria. Cobertura de geocodificação em endereço brasileiro com provider permitido ainda não foi medida.

### 9.2 Vale-pedágio eletrônico

Levantamento de 16/11/2026: publicação do setor (FETRANSPAR, fevereiro de 2025, citando ANTT) indica que o vale-pedágio é eletrônico e TAG-based desde 01/01/2025. A Lei 10.209/2001 está confirmada no texto oficial. A resolução citada pela publicação como 6.024/2024 tem ano incorreto: a base legislativa oficial da ANTT (`anttlegis.antt.gov.br`, consultada em 16/11/2026) contém a Resolução ANTT nº 6.024, de 3 de agosto de 2023, que estabelece normas para o Vale-Pedágio obrigatório, a habilitação de fornecedoras e as infrações. A alegação de exclusividade eletrônica desde 01/01/2025 não consta dessa resolução nem das páginas oficiais consultadas; continua como referência de setor, não verdade codificada. A modelagem TAG-based do MVP não depende dessa alegação.

No modelo, `ValePedagio` guarda operadora, TAG, placa, saldo e validade; `LancamentoPedagio` registra praça, valor, data e TAG lidos de extrato CSV; `TarifaPedagio` é versionada no tempo. `pedagio.py` cruza as praças previstas no grafo com os lançamentos e com o saldo do VPO. O MVP importa CSV da operadora: sem API de tag, sem token, sem segredo versionado. CIOT, CT-e e free flow ficam registrados como evolução.

### 9.3 Modo sombra

`POST /api/execucoes` registra km real, diesel real, pedágio real e rota executada. `comparativo.py` recalcula o custo da rota executada com a mesma `custo.py` usada no previsto. O desvio vira métrica; desvio recorrente vira alerta de processo, não de pessoa. Essa distinção evita que o sistema seja usado para responsabilizar indivíduos por dados de cadastro inconsistentes.

## 10. Testes

- Serviços puros primeiro, com valores esperados calculados à mão antes de escrever o código.
- Cada regra do gate ganha um teste que falha quando a regra é removida. Teste verde isolado não fecha o caso: reintroduzir o defeito, confirmar a falha, restaurar.
- `TestClient` cobre os endpoints com o banco recriável do zero e seed determinístico.
- Asserções de presença de código usam regex ancorada, não `String.includes()` — um identificador mutado pode conter o original como substring, e a string procurada pode estar num comentário.
- A asserção precisa usar a forma real do dado da API. Três testes de confinamento de caminho já passaram pelo motivo errado porque a fixture usava o nome de sessão sem o sufixo `.jsonl`.

## 11. Estrutura de pastas

```
~/Projetos/valida-rota/
  backend/
    app/{main.py, db.py, models.py, schemas.py, api/routes.py,
         services/{grafo.py, supermatrix.py, otimizador.py, custo.py,
                   validacao.py, comparativo.py, diagnostico.py,
                   geocodificacao.py, pedagio.py},
         data/sementes.py}
    tests/{test_grafo.py, test_supermatrix.py, test_otimizador.py,
           test_custo.py, test_validacao.py, test_comparativo.py,
           test_pedagio.py, test_api.py}
    pyproject.toml
  frontend/
    src/{App.tsx, types.ts, lib/api.ts,
         components/{AppHeader, SimulationForm, StopList, ResultHeader,
                     StopOrderTable, CostBreakdown, AlertList, Comparativo,
                     IntegridadePanel, VpoPanel, InlineError, EmptyState}.tsx,
         styles.css}
    package.json, index.html
  docs/{PLANO_VALIDA_ROTA.md, PROPOSTA_DESIGN_SYSTEM.md,
        PROPOSTA_SYSTEM_DESIGN.md, plano-implementacao.md}
  README.md
```

## 12. Etapas de execução

1. Criar venv e fixar versões no `pyproject.toml`; confirmar instalação de FastAPI em Python 3.14.9 e a compatibilidade de React 19 com Vite 7 no Node 26.13.0.
2. Esqueleto do backend com os serviços puros `grafo`, `supermatrix`, `otimizador` e `custo`, testes com valores esperados calculados à mão.
3. Gate de teste por mutação: para cada regra, reintroduzir o defeito, confirmar que o teste falha, restaurar. Sem essa etapa, a suíte verde não prova nada.
4. `validacao.py`, `comparativo.py` e `diagnostico.py` com a tabela de códigos da seção 9.
5. FastAPI + SQLite + `TestClient` nos endpoints, com seed determinístico e banco recriável.
6. `geocodificacao.py` com `ProvedorSintetico`; `pedagio.py` com importação de CSV e conciliação.
7. Frontend consumindo a API, seguindo os tokens e componentes de `PROPOSTA_DESIGN_SYSTEM.md`. Sem gradiente decorativo, sem glassmorphism, sem emoji em botão.
8. Verificação no navegador: contraste medido com ferramenta, foco visível, navegação por teclado e zoom a 200%.
9. Escrita dos documentos em `docs/` no padrão da casa: tese, evidência medida, explícito sobre o que não foi verificado.
10. Publicação, na ordem: commit local → criar repositório público `BrunoCHRBN/valida-rota` → configurar remote e push → deploy do artefato único (o container entrega API e interface no mesmo processo; o SQLite exige volume persistente) → preencher `homepage` do repositório com a URL do deploy → inclusão do card no portfólio. A vitrine lê `repo.homepage` (`src/App.tsx`), então o card pode entrar antes do deploy sem link quebrado — o ícone de demonstração simplesmente não aparece.
11. Verificação ao vivo com `curl` no endpoint deployado e conferência do card na vitrine.

## 13. Prioridade para uso real

Entre as automações cogitadas — conferência manual de coordenadas, detecção de trajeto inexistente, conciliação de pedágio, verificação de jornada e gate pós-simulação — a escolhida foi o gate pós-simulação.

Motivo: é a única que reúne todas as condições antes da saída do veículo. Ela detecta nó inexistente, aresta incompleta, trecho inalcançável, revisão vencida, jornada excedida, ocupação baixa e desvio de setor, e devolve o motivo de cada recusa com evidência. As outras automações continuam no plano, mas entram depois: geocodificação automatizada e conciliação de VPO são fase 2, e o comparativo previsto × real depende de execuções registradas.

## 14. Auditoria de 16/11 — pontos encontrados antes de implementar

| Ponto | Problema | Correção no plano |
| --- | --- | --- |
| `tempo_h` sem origem | grafo tinha km e pedágio, mas não velocidade nem tempo de serviço | `Aresta.velocidade_media_km_h` e `Parada.minutos_servico` adicionados |
| "sem coordenadas" versus validação de Lat/Long | texto contraditório | reescrito como "sem renderização de mapa; coordenadas sintéticas apenas para validação" |
| VPO sem dados na requisição | alertas de TAG e saldo dependiam de `placa` e `modo_pedagio` | ambos incluídos no corpo de `/api/simular` |
| Card antes do repo | vitrine apontaria para URL inventada | ordem de publicação corrigida na seção 12 |
| Gate duplicado | `/api/diagnostico` poderia reimplementar regras | `validacao.py` como única fonte |
| Resolução ANTT 6.024/2024 | ano incorreto na fonte de setor | corrigido para 6.024/2023 após leitura da base legislativa oficial; exclusividade eletrônica desde 2025 segue não confirmada |
| Google Maps | não permitido pela diretriz de compliance | provider sintético no MVP, Tencent como padrão futuro, sem chave embutida |
| Deploy do backend | define sobrevivência do SQLite e exposição de escrita | pendente, registrada na seção 16 |

## 15. Riscos e mitigação

- Escopo escapar para VRPTW completo: limite de 8 paradas documentado e testado.
- Teste verde com defeito presente: etapa 3 é gate obrigatório, com reintrodução do bug.
- Cold start em serverless: aceitável para demonstração, declarado em `docs/`.
- Comparativo medir código, não operação: a mesma `custo.py` para previsto e real.
- Rejeição sem explicação: todo aviso carrega `codigo` e `detalhe` com evidência.
- Reversão silenciosa de arquivos de planejamento: backup, escrita em arquivo temporário, validação e troca atômica; cópia canônica dentro do projeto.
- Referência legal não verificada usada como fato: manter o rótulo de "referência de setor" até leitura do texto oficial.

## 16. Pontos ainda não validados

1. Deploy do backend: container com volume persistente ou serverless. Define se o SQLite sobrevive e se endpoints de escrita ficam expostos sem auth.
2. Publicação do repositório `BrunoCHRBN/valida-rota` é ação externa e depende de autorização; a vitrine não tem remote configurado.
3. Ambiente Python: `fastapi` não está instalado globalmente em 3.14.9; `venv` e `pip 26.2.2` disponíveis. Resolver na etapa 1 com venv e versões fixadas. Medido em 16/11/2026.
4. Dependências do frontend: no portfólio existente, sob Node 26.13.0, estão instalados React 19.3.1, React DOM 19.3.1, Vite 7.3.7 e TypeScript 5.9.3, sem conflito de instalação observado. O build do projeto novo ainda não foi exercitado. Medido em 16/11/2026.
5. Valores de velocidade por aresta e minutos de serviço por parada ainda não estão no seed.
6. Texto oficial da Resolução ANTT 6.024/2023 recuperado em 16/11/2026 na base legislativa da ANTT. A alegação de exclusividade eletrônica desde 01/01/2025 continua sem confirmação em fonte oficial.
7. Cobertura de geocodificação em endereço brasileiro com provider permitido não foi medida.
8. Distâncias do corredor paulista são sintéticas e plausíveis, não confrontadas com fonte externa.
9. Contrastes medidos no navegador em 16/11: texto principal 13,75:1, secundário 5,51:1, status de rejeição 7,02:1. Todos acima de AA para texto normal.
10. Decidido em 16/11: origem e destino são isentos da restrição de setor; paradas de entrega fora do setor geram `DESVIO_SETOR`, com rejeição quando o perfil não permite múltiplos setores e aviso quando permite.

## 17. Fora do MVP

Auth e multi-tenant, mapa interativo e tiles, coordenadas reais de clientes, APIs de frete e tarifas de pedágio, integração com operadora de TAG, pagamentos, aplicativo móvel, OR-Tools, trânsito ao vivo, CIOT, CT-e, free flow e tema escuro.

## 18. Arquivos críticos

- `/home/bruno-vsantos/.workbuddy-ai/plans/cosmic-beacon-darwin-mglD_umX.md` (este plano, com backup `.bak`)
- `/home/bruno-vsantos/Projetos/valida-rota/docs/PLANO_VALIDA_ROTA.md` (cópia canônica)
- `/home/bruno-vsantos/Projetos/valida-rota/docs/PROPOSTA_DESIGN_SYSTEM.md`
- `/home/bruno-vsantos/Projetos/valida-rota/docs/PROPOSTA_SYSTEM_DESIGN.md`
- `/home/bruno-vsantos/Projetos/valida-rota/docs/AUDITORIA_PRE_EXECUCAO.md` (estado das pendências em 16/11)
- `/home/bruno-vsantos/Projetos/valida-rota/docs/plano-implementacao.md` (estado da execução)
- `/home/bruno-vsantos/Projetos/bruno-portfolio-starter/src/data/project-overrides.ts` (entrada da vitrine, após a publicação)
