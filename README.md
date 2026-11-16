# ValidaRota

Gate de aceitação de rotas rodoviárias. A simulação calcula ordem de entrega, custo e margem; antes de emplacar, devolve `aprovada`, `aprovada_com_avisos` ou `rejeitada` com o código e a evidência de cada recusa.

O projeto é um MVP de portfólio: dados sintéticos do corredor Santos–São Paulo–Campinas–Ribeirão Preto, sem mapa renderizado, sem chave externa e sem autenticação.

## Stack

- Backend: Python 3.14, FastAPI, Pydantic, SQLite, pytest.
- Frontend: React 19, TypeScript, Vite.
- Serviços puros: Dijkstra, SuperMatrix pairwise, otimizador por permutações (até 8 paradas), custo, validação, comparativo, diagnóstico, geocodificação e conciliação de VPO.

## Como rodar

```bash
# backend
cd backend
../.venv/bin/uvicorn app.main:app --reload --port 8000

# frontend (outro terminal)
cd frontend
npm install
npm run dev
```

O frontend usa proxy de `/api` para `http://localhost:8000`. Para apontar para outro backend, defina `VITE_API_URL`.

Testes:

```bash
cd backend
../.venv/bin/python -m pytest
```

Build do frontend:

```bash
cd frontend
npm run build
```

## O que o gate verifica

Cadastro e caminho: `NO_NAO_EXISTE`, `ARESTA_INCOMPLETA`, `TRECHO_INALCANCAVEL`, `DADOS_DIVERGENTES`.

Operação: `REVISAO_VENCIDA`, `JORNADA_EXCEDIDA`, `OCUPACAO_BAIXA`, `CONSUMO_FORA_FAIXA`, `DESVIO_SETOR`.

VPO: `VPO_VENCIDO`, `VPO_SALDO_INSUFICIENTE`, `TAG_NAO_VINCULADO_A_PLACA`, `PEDAGIO_EMBUTIDO_NO_FRETE`.

Diagnóstico e conciliação: `GEOCODIFICACAO_BAIXA`, `COORDENADAS_DIVERGENTES`, `PEDAGIO_DIVERGENTE`, `TARIFA_DIVERGENTE`, `PRACA_NAO_PREVISTA`, `DESVIO_ROTA_RECORRENTE`, `EXECUCAO_NAO_REGISTRADA`.

Cada aviso carrega `codigo`, `severidade`, `mensagem`, `detalhe` e `entidade`. A interface não mostra apenas cor: mostra o motivo.

## Decisões que valem registro

- Diesel é `(km / consumo_km_l) * preço`, não `km * consumo * preço`. A segunda fórmula erra a unidade e infla o custo em ordens de grandeza.
- `tempo_h` é direção; `tempo_total_h` é jornada, incluindo espera em janela e tempo de serviço. Custo de motorista e limite de jornada usam o total.
- Origem e destino podem estar em setores diferentes: são hubs logísticos. A restrição de setor vale para as paradas de entrega. Se o perfil não permite múltiplos setores, `DESVIO_SETOR` rejeita; se permite, avisa.
- O comparativo previsto × real usa a mesma `custo.py`, com diesel e pedágio realizados como entradas. Sem isso, mediria diferença de implementação.
- O MVP não tem mapa, tiles ou provider externo. A porta `ProvedorGeocodificacao` existe; o provider é sintético.

## Estrutura

```
backend/
  app/{main.py, db.py, domain.py, schemas.py, api/, services/, data/}
  tests/
frontend/
  src/{App.tsx, components/, lib/, types.ts, styles.css}
docs/
  PLANO_VALIDA_ROTA.md
  PROPOSTA_DESIGN_SYSTEM.md
  PROPOSTA_SYSTEM_DESIGN.md
  AUDITORIA_PRE_EXECUCAO.md
  plano-implementacao.md
```

## Limitações declaradas

- Distâncias, tarifas e velocidades são sintéticas e plausíveis; não foram confrontadas com fonte externa.
- Não há autenticação. Não publicar endpoints de escrita sem reverse proxy ou auth básica.
- A importação de VPO é CSV; não há integração com operadora de TAG.
- A geocodificação com provider real não foi medida em endereço brasileiro.
- O texto da Resolução ANTT 6.024/2023 foi localizado na base oficial; a alegação de exclusividade eletrônica do VPO desde 01/01/2025 não foi confirmada em fonte oficial e não é codificada.
