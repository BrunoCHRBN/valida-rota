# AUDITORIA — ValidaRota: estado antes da execução

**Data**: 16/11/2026, 12:52 (GMT-3) · **Status**: execução local concluída às 13:00; publicação feita às 14:10 em `BrunoCHRBN/valida-rota`, com deploy no Render pendente de conta no provedor · **Escopo original**: revisão de contexto e pendências antes de executar.

Base lida: `PLANO_VALIDA_ROTA.md` (310 linhas), `PROPOSTA_DESIGN_SYSTEM.md` (144), `PROPOSTA_SYSTEM_DESIGN.md` (165), memória do projeto e decisões registradas na conversa.

## 1. Concluído

| Item | Evidência |
| --- | --- |
| Plano reconstruído após duas reversões | 310 linhas, sha256 `8c49e5b0…d774495` antes desta auditoria |
| Cópia canônica no projeto | `docs/PLANO_VALIDA_ROTA.md`, 310 linhas, mesmo hash do plano |
| Oito correções de slop | Ausentes nos quatro documentos; `hors-line` corrigido na linha 141 do design system |
| Nome e slug | ValidaRota / `valida-rota`; consulta à API do GitHub em 16/11 retornou 404 para `valida-rota` e `validarota` |
| Tese e prioridade | Gate de aceitação pós-simulação escolhido como automação nº 1 |
| Domínio | Conceitos do ITB.BRA-M220, modelo de VPO e porta de geocodificação incorporados ao plano |
| Documentos de design | Design system e system design escritos, com contrastes medidos e premissas explícitas |

## 2. Resolvido por medição nesta auditoria

| Pendência antiga | Resultado medido | Destino |
| --- | --- | --- |
| Python sem FastAPI | Python 3.14.9, `fastapi` ausente globalmente, módulo `venv` e pip 26.2.2 disponíveis | Etapa 1 resolve com venv; não é bloqueio |
| React/Vite no Node 26 | React 19.3.1, React DOM 19.3.1, Vite 7.3.7, TypeScript 5.9.3 instalados no portfólio; npm 12.2.1 | Instalação sem conflito observada; build do projeto novo segue pendente |
| Texto da Resolução ANTT | Base legislativa oficial da ANTT contém **Resolução nº 6.024, de 3 de agosto de 2023** | Ano 2024 da publicação de setor estava errado; corrigido no plano e no system design |
| Slug disponível | `BrunoCHRBN/valida-rota` e `BrunoCHRBN/validarota` continuam 404 na API do GitHub | Confirmado em 16/11, 12:52 |
| Estado da vitrine | `bruno-portfolio-starter` sem remote, working tree limpo, `node_modules` presente, nenhum card ValidaRota | Confirma a ordem de publicação do plano |

A resolução oficial de 2023 trata de normas para o Vale-Pedágio obrigatório, habilitação de fornecedoras e infrações, e cita a Lei 10.209/2001. Ela não contém a afirmação de exclusividade eletrônica desde 01/01/2025; essa frase permanece como informação de setor e **não** foi codificada como regra jurídica no projeto.

## 3. Depende de decisão — priorizadas

**P0 — impedem a publicação e definem segurança do deploy**

1. **Deploy do backend**: container com volume persistente ou serverless? Define se o SQLite sobrevive a redeploys e se os endpoints de escrita ficam expostos sem autenticação. Sem essa definição, o plano não pode fechar a seção de segurança.
2. **Publicação do repositório**: criar `BrunoCHRBN/valida-rota` no GitHub é ação externa. Requer autorização. O card da vitrine só entra depois do repo público e do deploy; publicar antes gera link inventado.

**P1 — impedem fechar regras do gate**

3. **Setor de origem e destino**: decidido em 16/11. Origem e destino são hubs e ficam isentos; a restrição vale para as paradas de entrega. `DESVIO_SETOR` rejeita quando o perfil não permite múltiplos setores e avisa quando permite. Implementado e testado.

**P2 — aceitação do recorte, não bloqueiam o início**

4. Distâncias do corredor paulista são sintéticas e plausíveis, não confrontadas com fonte externa. Para portfólio, a decisão é se isso fica declarado como limitação ou se vale medir contra fonte real.

## 4. Depende de validação — não bloqueiam o início, bloqueiam o fechamento

1. **Contraste no navegador**: os valores do design system foram calculados fora do navegador; revalidar após a UI existir.
2. **Build do frontend novo**: a compatibilidade foi observada no projeto de vitrine, não no `valida-rota`.
3. **Cobertura de geocodificação**: endereço brasileiro com provider permitido (Tencent padrão) não medido; exige chave via proxy e teste controlado. O MVP usa provider sintético.
4. **Exclusividade eletrônica do VPO desde 2025**: sem confirmação em fonte oficial. Mantida como referência de setor; não altera a modelagem TAG-based.
5. **Reversão silenciosa do plano**: causa não identificada (sem hook git, sem processo escritor, plano fora de versionamento). Mitigação adotada: backup, escrita em temporário, validação, troca atômica e cópia canônica. Continua como risco, não como pendência resolvida.

## 5. Bloqueios

Não há bloqueio técnico para a implementação local: etapas 1 a 9 foram executadas em 16/11. O item P1 (setor) foi decidido e implementado. Os itens P0 continuam abertos e bloqueiam apenas a etapa 10: sem decisão de deploy e sem autorização do repositório, nada é publicado. A execução local não cria repositório público, não faz deploy e não altera a vitrine.

## 6. Critério de liberação

- Implementação local: liberada e concluída (etapas 1 a 9).
- Publicação: depende de decisão de deploy e autorização explícita para criar o repositório público. Sem esses dois itens, a etapa 10 não começa.
- Fechamento do projeto: os itens da seção 4 precisam estar resolvidos ou declarados como limitação aceita antes de considerar o MVP concluído.
