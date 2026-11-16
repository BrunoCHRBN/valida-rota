# Plano de implementação — estado em 16/11/2026

**Status**: MVP publicado em `BrunoCHRBN/valida-rota`; deploy no Render pronto para aplicar, pendente de conta no provedor.

## Etapas do plano

| Etapa | Estado | Evidência |
| --- | --- | --- |
| 1. Ambiente e dependências | concluída | venv com FastAPI 0.163.1, Pydantic 2.14.3, pytest 9.2.0; versões fixadas no `pyproject.toml` |
| 2. Serviços puros | concluída | `grafo`, `supermatrix`, `otimizador`, `custo` com testes de valor esperado |
| 3. Gate de mutação | concluída | 5 mutações executadas; uma delas revelou teste fraco, corrigido antes de restaurar |
| 4. Gate e módulos de domínio | concluída | `validacao`, `comparativo`, `diagnostico`, `geocodificacao`, `pedagio` |
| 5. API e SQLite | concluída | 17 caminhos / 20 operações no `openapi.json`, seed determinístico, testes com `TestClient` |
| 6. Geocodificação e VPO | concluída | provider sintético, validação de coordenadas, conciliação CSV |
| 7. Frontend | concluída | React 19 + TS + Vite; build de produção passa |
| 8. Verificação no navegador | concluída | layout desktop e mobile conferidos; contraste medido; varredura de teclado e reflow a 200% executada e dois defeitos corrigidos |
| 9. Documentação | concluída | README, docs de design, auditoria e este plano |
| 10. Publicação | concluída | repositório público com 7 commits, descrição e 8 topics; card na vitrine renderizado e conferido no navegador |
| 11. Verificação ao vivo | bloqueada | depende de conta no Render: não há host nesta máquina nem credencial de PaaS |

## Decisões tomadas durante a implementação

1. **Fórmula do diesel corrigida.** O plano original dizia `km · consumo_km_l · preço`; a unidade correta é `(km / consumo_km_l) · preço`. O erro foi encontrado no primeiro smoke test, não por leitura.
2. **Tempo separado em dois campos.** `tempo_h` é direção; `tempo_total_h` inclui espera e serviço. Jornada e custo de motorista usam o total. Sem essa separação, o custo subestimava o turno.
3. **Setor.** Origem e destino são isentos; a restrição vale para paradas de entrega. `DESVIO_SETOR` rejeita quando o perfil não permite múltiplos setores e avisa quando permite. Decisão registrada porque a pergunta estava em aberto na auditoria.
4. **Duplicidade de parada.** A mesma parada duas vezes na requisição gera `DADOS_DIVERGENTES`, em vez de produzir uma ordem com chegada sobrescrita.
5. **Fontes do sistema.** O app usa `system-ui`/`ui-monospace` como fallback, sem requisição ao Google Fonts. A dependência externa fica fora do MVP.
6. **Comparativo.** A execução real entra com km, diesel, pedágio e tempo realizados; a fórmula é a mesma, com os valores realizados como entrada.

## Verificação executada

- `pytest`: 55 testes verdes.
- `npm run build`: `tsc --noEmit` e Vite sem erro; bundle de 245 kB (76 kB gzip).
- Navegador: simulação aprovada com aviso renderizada; rejeição por `REVISAO_VENCIDA` renderizada; comparativo “dentro da faixa” após registrar execução; console sem erro.
- Contraste medido no navegador: texto principal 13,75:1; secundário 5,51:1; status de rejeição 7,02:1. Todos acima de AA para texto normal.
- Layout: 1440 px e 390 px conferidos por captura; a primeira versão da linha de parada tinha seis colunas em 440 px e foi refeita em duas linhas.

## Verificação do container

`docker build` concluído; container rodando em `:8099` com volume nomeado. Medido, não deduzido:

| Verificação | Resultado |
| --- | --- |
| `GET /api/health` no container | 200, `{"status":"ok"}` |
| `GET /` no container | 200, `text/html`, `<title>ValidaRota</title>` |
| asset do bundle (`/assets/index-*.js`) | 200, `text/javascript` |
| `POST /api/simular` no container | `aprovada_com_avisos`, 60 km, `tempo_total_h` 3,4556 |
| persistência | simulação sobreviveu a `docker restart`; `valida_rota.db` em `/data`, dono `valida` |
| porta injetada | com `PORT=10000` (padrão do Render), `/api/health` e `/` respondem 200; healthcheck do container em `healthy` |
| porta padrão | sem `PORT`, escuta 8000; compose inalterado |


## Varredura de acessibilidade

Executada com Chromium via Playwright, não por inspeção do CSS: `Tab` real, comparação de pixel antes e depois do foco, e leitura das pseudo-classes que casam em cada parada.

| Medida | Antes | Depois |
| --- | --- | --- |
| Paradas de foco na página inteira | 45 | 45 |
| Paradas **sem anel visível** | 5 | 0 |
| Reflow 640×512 (200% de zoom) | sem rolagem horizontal | sem rolagem horizontal |
| Reflow 320 CSS px | sem rolagem horizontal; tabela estoura e rola no próprio contêiner | idem |

**Defeito 1 — o anel sumia no meio do campo de hora.** O `input[type=time]` do Chromium tem subcampos internos (hora, minuto, seletor). No terceiro, `:focus` e `:focus-visible` deixam de casar e o anel desaparecia com o campo ainda ativo. Medido: `focus:false`, `visivel:false`, `dentro:true`. A primeira tentativa (`input[type='time']:focus`) **não corrigiu** — o teste continuou acusando o passo 3. Só `:focus-within` cobre o campo inteiro.

**Defeito 2 — a tabela rolava sem teclado.** Em tela estreita a tabela de ordem de entrega rola na horizontal dentro de `.tabela-scroll`; sem `tabindex` o teclado não alcança a rolagem e as colunas da direita ficam inacessíveis. Corrigido com `tabindex={0}`, `role="region"` e `aria-label`.

**Limitação declarada:** cada campo de hora custa três paradas de foco no Chromium (hora, minuto, seletor), contra uma no Firefox. São 5 campos, 15 paradas onde poderiam ser 5. Não troquei por campo de texto porque perderia o seletor nativo e a validação de formato; fica registrado como escolha, não como desconhecimento.

## Mutação executada

| Defeito reintroduzido | Testes que falharam | Restauração |
| --- | --- | --- |
| diesel voltou a `km · consumo · preço` | `test_diesel_usa_divisao_pelo_consumo`, `test_vpo_remove_pedagio_do_custo_da_transportadora` | `git checkout -- custo.py`; testes verdes |
| regra de revisão desligada | `test_revisao_vencida_considera_km_da_rota`, `test_veiculo_com_revisao_vencida_e_rejeitado` | `git checkout -- validacao.py`; testes verdes |
| penalidade de prioridade zerada | **passou na primeira execução** — a ordem era explicada só pelo atraso. A asserção foi reforçada para exigir `penalidade_prioridade == 3,7`; com a asserção nova, falhou | `git checkout -- otimizador.py`; testes verdes |
| saldo de VPO deixou de ser checado | `test_vpo_com_saldo_insuficiente`, `test_vpo_sem_saldo_rejeita_rota_com_pedagio_alto` | `git checkout -- validacao.py`; testes verdes |
| duplicidade de parada deixou de ser checada | `test_parada_repetida_gera_dados_divergentes` | `git checkout -- validacao.py`; testes verdes |
| montagem do bundle passou a ser incondicional | `test_sem_bundle_a_raiz_nao_e_montada` falhou com `RuntimeError: Directory ... does not exist` | `git checkout -- main.py`; testes verdes |
| montagem do bundle movida para antes das rotas `/api` | 9 testes falharam com 404/405 e `assert 1 == 12` — o catch-all engoliu a API | `git checkout -- main.py`; testes verdes |
| regra `:focus-within` do campo de hora removida | `npm run a11y` acusou 5 paradas sem anel, saída 1 | restaurado do backup; saída 0 |
| `tabIndex` do contêiner da tabela removido | `npm run a11y` acusou "contêiner da tabela alcançável: false", saída 1 | restaurado; saída 0 |

O terceiro caso é o registro mais importante: um teste verde que passava pelo motivo errado. Sem a mutação, ele teria sido aceito como prova de uma regra que não estava sendo exercitada.

## Pendências

- Deploy no Render: `render.yaml` escrito e validado; imagem verificada com `PORT=10000`, que é o padrão do provedor. Falta apenas aplicar o Blueprint, o que exige conta no Render — não há credencial de PaaS nesta máquina.
- Persistência em produção: no plano free o SQLite é descartado a cada spin-down. Decidir se fica assim (demonstração sempre limpa) ou se sobe para plano pago com disco.
- Exposição sem autenticação: os endpoints de escrita ficam abertos na URL pública. Se o deploy for adiante com disco pago, avaliar guarda de escrita antes.
- Cobertura de geocodificação com provider permitido em endereço brasileiro: não medida.
- Acessibilidade: teclado e reflow medidos e corrigidos. Falta leitor de tela (NVDA/Orca) e alto contraste do sistema, não exercitados.
- Distâncias do corredor: sintéticas; decisão de manter como limitação declarada ou medir contra fonte real.
- Vitrine: o card foi commitado localmente (`29faf42`), mas o projeto do portfólio não tem remote configurado — publicar a vitrine é decisão separada.
