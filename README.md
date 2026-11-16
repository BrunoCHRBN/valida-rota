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

### Com Docker (um processo só)

```bash
docker compose up --build
# interface em http://localhost:8000, API no mesmo host
```

A imagem compila o bundle do Vite e o entrega pelo próprio FastAPI (`StaticFiles` montado depois das rotas `/api`). Isso elimina CORS em produção e faz do deploy um artefato único. O banco fica em `/data/valida_rota.db`, em volume nomeado: sobrevive a `docker compose down` e a restart do container.

O processo escuta `${PORT:-8000}`. Localmente, 8000; em PaaS que injeta `PORT` (o Render usa 10000 por padrão), ele acompanha sem alteração de imagem.

Sem `index.html` no diretório do bundle, o processo sobe como API pura — é o modo que os testes exercitam.

### Deploy no Render

O repositório traz `render.yaml`. No painel do Render: **New → Blueprint**, apontar para este repositório, aplicar.

O plano escolhido é o **free**, e isso tem consequência declarada — verificada na documentação do Render em 16/11/2026:

- instância free **não aceita disco persistente**; só plano pago;
- o filesystem é efêmero: o SQLite volta ao seed determinístico a cada redeploy, restart ou spin-down (15 min sem tráfego);
- o primeiro acesso depois do spin-down leva cerca de um minuto.

Para persistência real, troque `plan: free` por `plan: 0.5c-512mb` e descomente o bloco `disk` do blueprint (mount em `/data`).

**Antes de apontar uma URL pública:** não há autenticação. `POST /api/simular`, `/api/execucoes`, `/api/veiculos` e `/api/vales-pedagio` ficam abertos para quem tiver o endereço. No plano free o estrago é limitado porque o banco é descartado no spin-down; com disco pago, não é.

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

Acessibilidade de foco (com o frontend no ar):

```bash
cd frontend
npm install --no-save playwright
npm run a11y
```

O script percorre a página por `Tab`, exige anel visível em toda parada de foco e verifica se o contêiner da tabela recebe foco. Sai com código 1 quando algo falha — foi assim que os dois defeitos de foco foram encontrados.

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
Dockerfile
docker-compose.yml
render.yaml
```

## Limitações declaradas

- Distâncias, tarifas e velocidades são sintéticas e plausíveis; não foram confrontadas com fonte externa.
- Não há autenticação. Não publicar endpoints de escrita sem reverse proxy ou auth básica.
- A importação de VPO é CSV; não há integração com operadora de TAG.
- A geocodificação com provider real não foi medida em endereço brasileiro.
- Acessibilidade medida em Chromium: 45 paradas de foco, todas com anel visível; sem rolagem horizontal a 200% de zoom e a 320 CSS px. Não exercitado com leitor de tela. Cada campo de hora custa três paradas de foco no Chromium (hora, minuto, seletor) contra uma no Firefox — escolha declarada, para manter o seletor nativo.
- O texto da Resolução ANTT 6.024/2023 foi localizado na base oficial; a alegação de exclusividade eletrônica do VPO desde 01/01/2025 não foi confirmada em fonte oficial e não é codificada.
