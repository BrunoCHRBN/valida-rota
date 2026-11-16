# Plano de implementação — estado em 16/11/2026

**Status**: MVP local implementado e verificado; publicação externa não iniciada.

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
| 8. Verificação no navegador | parcial | layout desktop e mobile conferidos; contraste medido; falta varredura completa de teclado |
| 9. Documentação | concluída | README, docs de design, auditoria e este plano |
| 10. Publicação | não iniciada | depende de decisão de deploy e autorização do repositório |
| 11. Verificação ao vivo | não iniciada | depende da etapa 10 |

## Decisões tomadas durante a implementação

1. **Fórmula do diesel corrigida.** O plano original dizia `km · consumo_km_l · preço`; a unidade correta é `(km / consumo_km_l) · preço`. O erro foi encontrado no primeiro smoke test, não por leitura.
2. **Tempo separado em dois campos.** `tempo_h` é direção; `tempo_total_h` inclui espera e serviço. Jornada e custo de motorista usam o total. Sem essa separação, o custo subestimava o turno.
3. **Setor.** Origem e destino são isentos; a restrição vale para paradas de entrega. `DESVIO_SETOR` rejeita quando o perfil não permite múltiplos setores e avisa quando permite. Decisão registrada porque a pergunta estava em aberto na auditoria.
4. **Duplicidade de parada.** A mesma parada duas vezes na requisição gera `DADOS_DIVERGENTES`, em vez de produzir uma ordem com chegada sobrescrita.
5. **Fontes do sistema.** O app usa `system-ui`/`ui-monospace` como fallback, sem requisição ao Google Fonts. A dependência externa fica fora do MVP.
6. **Comparativo.** A execução real entra com km, diesel, pedágio e tempo realizados; a fórmula é a mesma, com os valores realizados como entrada.

## Verificação executada

- `pytest`: 53 testes verdes.
- `npm run build`: `tsc --noEmit` e Vite sem erro; bundle de 245 kB (76 kB gzip).
- Navegador: simulação aprovada com aviso renderizada; rejeição por `REVISAO_VENCIDA` renderizada; comparativo “dentro da faixa” após registrar execução; console sem erro.
- Contraste medido no navegador: texto principal 13,75:1; secundário 5,51:1; status de rejeição 7,02:1. Todos acima de AA para texto normal.
- Layout: 1440 px e 390 px conferidos por captura; a primeira versão da linha de parada tinha seis colunas em 440 px e foi refeita em duas linhas.

## Mutação executada

| Defeito reintroduzido | Testes que falharam | Restauração |
| --- | --- | --- |
| diesel voltou a `km · consumo · preço` | `test_diesel_usa_divisao_pelo_consumo`, `test_vpo_remove_pedagio_do_custo_da_transportadora` | `git checkout -- custo.py`; testes verdes |
| regra de revisão desligada | `test_revisao_vencida_considera_km_da_rota`, `test_veiculo_com_revisao_vencida_e_rejeitado` | `git checkout -- validacao.py`; testes verdes |
| penalidade de prioridade zerada | **passou na primeira execução** — a ordem era explicada só pelo atraso. A asserção foi reforçada para exigir `penalidade_prioridade == 3,7`; com a asserção nova, falhou | `git checkout -- otimizador.py`; testes verdes |
| saldo de VPO deixou de ser checado | `test_vpo_com_saldo_insuficiente`, `test_vpo_sem_saldo_rejeita_rota_com_pedagio_alto` | `git checkout -- validacao.py`; testes verdes |
| duplicidade de parada deixou de ser checada | `test_parada_repetida_gera_dados_divergentes` | `git checkout -- validacao.py`; testes verdes |

O terceiro caso é o registro mais importante: um teste verde que passava pelo motivo errado. Sem a mutação, ele teria sido aceito como prova de uma regra que não estava sendo exercitada.

## Pendências

- Deploy do backend: container com volume persistente ou serverless. Define sobrevivência do SQLite e exposição de escrita.
- Publicação do repositório `BrunoCHRBN/valida-rota`: ação externa, depende de autorização.
- Cobertura de geocodificação com provider permitido em endereço brasileiro: não medida.
- Varredura completa de teclado e zoom a 200%: parcialmente coberta pelos estilos, falta exercitar.
- Distâncias do corredor: sintéticas; decisão de manter como limitação declarada ou medir contra fonte real.
- Mutação das regras críticas: próxima etapa, depois do commit.
