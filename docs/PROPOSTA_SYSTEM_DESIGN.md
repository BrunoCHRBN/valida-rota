# PROPOSTA — System Design: ValidaRota

**Data**: 16/11/2026 · **Status**: proposta para decisão · **Base**: decisões do plano `cosmic-beacon-darwin-mglD_umX.md` e do ITB.BRA-M220

## 1. Objetivo e premissas

O projeto prova uma tese: validação baseada em dados substitui revisão manual de rotas. O ciclo é *simular → validar → executar → comparar → alertar*.

Premissas já decididas com o Bruno:

| Premissa | Origem |
|---|---|
| Python + FastAPI + React | resposta direta |
| MVP focado, uma ideia bem executada | resposta direta |
| Gate pós-simulação é a prioridade 1 | decisão de "uso real" em 16/11 |
| Dados sintéticos, sem mapa renderizado | plano original, mantido |
| Teste validado contra defeito é gate, não opcional | regra operacional do usuário |
| Nome em discussão: ValidaRota, slug `valida-rota` | sugestão do Bruno em 16/11; slug livre na API do GitHub |

Premissas não confirmadas, que mudariam o desenho se caírem: deploy do backend (container ou serverless), publicação do repo e da vitrine, instalação das dependências Python no ambiente atual.

## 2. Arquitetura geral

```
React (Vite/TS)
   │  POST /api/simular · GET /api/simulacoes/{id}/comparativo
   ▼
FastAPI  ──▶  validacao.py  (gate único: antes e depois)
   │              │
   │              ├─▶ grafo.py / supermatrix.py  (Dijkstra + matriz pairwise)
   │              ├─▶ otimizador.py             (permutações ≤ 8)
   │              ├─▶ custo.py                  (fórmula + VPO)
   │              ├─▶ geocodificacao.py         (porta + provider sintético)
   │              └─▶ pedagio.py                (conciliação previsto × TAG)
   ▼
SQLite  ◀──  models.py / schemas.py  ──▶  JSON  ──▶ React
```

Decisão recomendada: monosserviço em duas frentes (backend + frontend). Não há serviços externos no MVP. A simulação roda em `TestClient` e o deploy se verifica com `curl`.

O gate `validacao.py` é a única fonte de regras. `/api/simular` e `/api/diagnostico` chamam a mesma função.

## 3. Módulos

### 3.1 Backend

| Módulo | Responsabilidade | Entrada → saída |
|---|---|---|
| `grafo.py` | construir grafo a partir de `No`/`Aresta`; validar arcos e alcançabilidade | nós/arestas → matriz de adjacência |
| `supermatrix.py` | distância e tempo pairwise por Dijkstra | grafo → matriz `km` e `horas` |
| `otimizador.py` | ordenar até 8 paradas minimizando score configurável | matriz + paradas + perfil → ordem |
| `custo.py` | calcular diesel, pedágio, depreciação, manutenção, motorista e margens | ordem + veículo + VPO → custos |
| `validacao.py` | **gate**: regras de existência, jornada, ocupação, geocodificação, setor | payload + resultado → `avisos[]` |
| `comparativo.py` | previsto × real: desvio de km, custo e rota | `Simulacao` + `ExecucaoReal` → métricas |
| `diagnostico.py` | varredura de integridade do cadastro e do histórico | banco → `Alerta[]` |
| `geocodificacao.py` | porta `ProvedorGeocodificacao` + regras de divergência | endereço/coordenadas → alertas |
| `pedagio.py` | conciliar grafo × extrato TAG × saldo do VPO | previstos + lançamentos + VPO → desvio |

### 3.2 Frontend

| Módulo | Responsabilidade |
|---|---|
| `lib/api.ts` | único ponto de acesso HTTP; tipa request/response; transforma erro em `InlineError` |
| `types.ts` | contratos espelho dos `schemas.py`, gerados à mão e mantidos sincronizados |
| `components/SimulationForm.tsx` | coleta de parâmetros e perfil |
| `components/Resultado.tsx` | status do gate + ordem + quebra de custos |
| `components/Comparativo.tsx` | previsto × real |
| `components/PainelIntegridade.tsx` | alertas e contadores |
| `App.tsx` | composição das etapas; sem estado de negócio |

**Decisão**: sem gerenciador de estado global. Estado local + React Query não é necessário para 4 telas; `fetch` em `lib/api.ts` resolve.

## 4. Modelo de dados

Entidades do plano, com duas correções da auditoria de 16/11:

- `Aresta(de, para, km, pedagio_rs, velocidade_media_km_h)` — velocidade adicionada para tornar `tempo_h` calculável.
- `Parada(no_id, janela_inicio, janela_fim, peso_kg, prioridade, minutos_servico)` — tempo de serviço adicionado pelo mesmo motivo.
- `No(id, nome, setor_id, qualidade_geo, lat, lon)` — coordenadas sintéticas apenas para validação de geocodificação; sem renderização de mapa.
- `ValePedagio`, `LancamentoPedagio`, `TarifaPedagio` (versionada no tempo).
- `Simulacao` (previsto), `ExecucaoReal` (fato), `Alerta` (evidência).
- `PerfilRoteirizacao` — a "dinâmica" do Roadnet: parâmetros salvos e clonáveis, incluindo `μ`, `ν`, `ξ`.

**Relacionamento crítico**: `ExecucaoReal.simulacao_id` é 1:1 com `Simulacao`. O sistema nunca sobrescreve o previsto com o real.

Persistência: SQLite com SQLModel (ou `sqlite3` puro + Pydantic). Sem Alembic no MVP: `CREATE TABLE IF NOT EXISTS` e seed determinístico bastam, e o banco pode ser recriado do zero em teste.

## 5. Fluxos de dados

### 5.1 Simulação com gate (fluxo principal)

1. React envia `POST /api/simular` com origem, paradas, veículo, motorista, perfil, placa, receita, VPO e `modo_pedagio`.
2. `validacao.py` roda **antes**: existência de nós/arestas, alcançabilidade, geocodificação, revisão do veículo, jornada estimada. Falha → `409/422` com `codigo`.
3. `supermatrix.py` calcula distância/tempo; `otimizador.py` escolhe a ordem; `custo.py` calcula custos e margens.
4. `validacao.py` roda **depois**: ocupação mínima do perfil, desvio de setor, coerência da ordem com janelas.
5. `Simulacao` é gravada com payload e resultado.
6. React recebe status do gate + avisos + custos.

### 5.2 Modo sombra (previsto × real)

1. Operador registra `POST /api/execucoes` com km real, diesel real, pedágio real e rota executada.
2. `comparativo.py` recalcula o custo da rota executada com a **mesma** fórmula do previsto.
3. Desvio vira métrica; desvio recorrente vira alerta de processo (`DESVIO_ROTA_RECORRENTE`), nunca de pessoa.

### 5.3 Vale-pedágio

1. `POST /api/vales-pedagio` cadastra operadora, TAG, placa, saldo e validade.
2. `POST /api/lancamentos-pedagio` importa extrato CSV da operadora (sem integração com API de tag no MVP).
3. `GET /api/simulacoes/{id}/pedagio` cruza praças previstas × cobradas × cobertura do VPO.

### 5.4 Geocodificação

1. Cliente novo entra com qualidade `ambigua`/`baixa`.
2. `validar()` compara coordenada cadastrada com a do provider sintético (raio padrão 150m).
3. Divergência gera alerta → fila de exceção → confirmação humana muda qualidade para `fornecida_usuario` com auditoria.

## 6. Integrações

| Integração | Status | Decisão |
|---|---|---|
| GitHub API (vitrine) | existente, fora do app | card `valida-rota` só aparece "live" se repo público existir |
| Provider de geocodificação | porta prevista, sintético no MVP | Google Maps **proibido** pela diretriz de compliance; permitidos Tencent/AMap/Baidu/Tianditu; cobertura em endereço brasileiro **não medida** |
| Operadora de pedágio | CSV manual no MVP | sem API, sem credencial, sem segredo no repositório |
| CIOT / CT-e / free flow | fora do MVP | registrado como evolução no `docs/` |

## 7. Escalabilidade

Limites conhecidos do MVP:

- Permutações: `8! = 40.320`. Acima disso o tempo cresce sem ganho didático.
- SuperMatrix: `n²` execuções de Dijkstra; com ~10 nós do corredor sintético, irrelevante.
- SQLite: suficiente para centenas de simulações; concorrência de escrita é serial.
- Sem paginação em `/api/simulacoes` no início; adicionar `limit/offset` quando o histórico passar de ~200 registros.

Se virar produto real: trocar SQLite por Postgres, mover SuperMatrix para cache com invalidação por versionamento de tarifa, colocar cálculo pesado em worker, paginar endpoints, adicionar auth. A separação em serviços puros permite essa migração sem reescrever regras.

## 8. Segurança

- **Entrada**: Pydantic valida tipos e intervalos; URLs de API são internas; nenhum dado do usuário vai para shell ou query SQL concatenada.
- SQL: queries parametrizadas via SQLModel/ORM, nunca f-string com input do usuário.
- **Segredos**: nenhuma chave de mapa, nenhum token de operadora, nenhuma credencial no repositório. Provider sintético não usa chave.
- **CORS**: explicitamente limitado à origem do frontend; sem `*` em produção.
- Exposição: MVP sem auth. Não publicar write endpoints em ambiente público sem reverse proxy ou auth básica. A decisão de deploy define isso; ver pendências.
- **PII**: endereços e coordenadas são sintéticos. Se virar real, aplicar minimização e retenção; não publicar localização de terceiros.
- **Compliance de mapas**: nenhum provider de mapa em runtime nesta versão; se adicionado, seguir a diretriz (Tencent padrão, chave via proxy, nunca embutida).

## 9. Decisões recomendadas (resumo)

1. Monosserviço FastAPI + React, sem fila nem cache.
2. `validacao.py` como única fonte de regras, chamada nos caminhos de simular e diagnosticar.
3. Gate pós-simulação entregue primeiro; VPO e geocodificação como fase 2 declarada.
4. SQLite com seed determinístico; banco recriável em teste.
5. Contrastes do design system ajustados para AA — tokens originais do portfólio falham para texto.
6. Nenhuma integração externa com chave no MVP.

## 10. Pontos que precisam ser validados antes de implementar

1. Deploy do backend: container com volume persistente ou serverless. Define se SQLite sobrevive e se write endpoints ficam expostos.
2. Publicação: criar `BrunoCHRBN/valida-rota` (slug livre confirmado) é ação externa e precisa de OK. A vitrine não tem remote configurado.
3. **Ambiente Python**: medido em 16/11 — `fastapi` ausente em Python 3.14.9, `venv` e `pip 26.2.2` disponíveis. Resolver na etapa 1 com venv e versões fixadas no `pyproject.toml`.
4. **Dependências do frontend**: medido em 16/11 no portfólio existente, sob Node 26.13.0 — React 19.3.1, React DOM 19.3.1, Vite 7.3.7 e TypeScript 5.9.3 instalados sem conflito observado. Build do projeto novo ainda não exercitado.
5. **Tempo de rota**: velocidade por aresta e minutos de serviço por parada precisam de valores no seed — estão no desenho, ainda não no banco.
6. **Resolução ANTT 6.024**: texto oficial recuperado em 16/11 na base legislativa da ANTT; a data correta é 3 de agosto de **2023**, não 2024 como citava a publicação de setor. A alegação de exclusividade eletrônica desde 01/01/2025 segue sem confirmação oficial e não é codificada no MVP.
7. **Cobertura de geocodificação** em endereço brasileiro com provider permitido: não medida.
8. **Distâncias do corredor paulista**: sintéticas e plausíveis, não validadas contra fonte externa.
