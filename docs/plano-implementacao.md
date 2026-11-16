# Plano de implementação — estado em 16/11/2026

**Status**: MVP local implementado e verificado; publicação externa não iniciada.

## Etapas do plano

| Etapa | Estado | Evidência |
| --- | --- | --- |
| 1. Ambiente e dependências | concluída | venv com FastAPI 0.163.1, Pydantic 2.14.3, pytest 9.2.0; versões fixadas no `pyproject.toml` |
| 2. Serviços puros | concluída | `grafo`, `supermatrix`, `otimizador`, `custo` com testes de valor esperado |
| 3. Gate de mutação | pendente | suíte verde; mutações serão executadas após o commit local |
| 4. Gate e módulos de domínio | concluída | `validacao`, `comparativo`, `diagnostico`, `geocodificacao`, `pedagio` |
| 5. API e SQLite | concluída | 17 rotas, seed determinístico, testes com `TestClient` |
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

## Pendências

- Deploy do backend: container com volume persistente ou serverless. Define sobrevivência do SQLite e exposição de escrita.
- Publicação do repositório `BrunoCHRBN/valida-rota`: ação externa, depende de autorização.
- Cobertura de geocodificação com provider permitido em endereço brasileiro: não medida.
- Varredura completa de teclado e zoom a 200%: parcialmente coberta pelos estilos, falta exercitar.
- Distâncias do corredor: sintéticas; decisão de manter como limitação declarada ou medir contra fonte real.
- Mutação das regras críticas: próxima etapa, depois do commit.
