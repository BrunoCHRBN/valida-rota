"""Varredura de integridade do cadastro e do histórico.

Devolve os mesmos códigos do gate, para que a UI use uma única função de
severidade e o operador não aprenda dois vocabulários.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from app.domain import Aviso, Veiculo, ValePedagio
from app.services.grafo import Grafo

DIAS_SEM_EXECUCAO = 7
LIMITE_DESVIO_PCT = 15.0


def _aviso(codigo: str, severidade: str, mensagem: str, entidade: str | None = None, **detalhe) -> Aviso:
    return Aviso(
        codigo=codigo,
        severidade=severidade,  # type: ignore[arg-type]
        mensagem=mensagem,
        detalhe=detalhe,
        entidade=entidade,
    )


def diagnosticar(
    *,
    grafo: Grafo,
    veiculos: list[Veiculo],
    vales: list[ValePedagio],
    simulacoes: list[dict],
    execucoes: list[dict],
    hoje: date,
) -> list[Aviso]:
    avisos: list[Aviso] = []

    for aresta in grafo.arestas_incompletas():
        avisos.append(
            _aviso(
                "ARESTA_INCOMPLETA",
                "rejeicao",
                f"Aresta {aresta.de} → {aresta.para} sem dados completos.",
                f"{aresta.de}->{aresta.para}",
                de=aresta.de,
                para=aresta.para,
            )
        )

    total_nos = len(grafo.nos)
    for no_id in grafo.nos:
        alcancaveis = grafo.alcancaveis(no_id)
        if len(alcancaveis) < total_nos:
            faltantes = sorted(set(grafo.nos) - alcancaveis)
            avisos.append(
                _aviso(
                    "TRECHO_INALCANCAVEL",
                    "rejeicao",
                    f"{no_id} não alcança {len(faltantes)} nó(s) do grafo.",
                    no_id,
                    origem=no_id,
                    destinos=faltantes[:5],
                    total_faltantes=len(faltantes),
                )
            )

    for veiculo in veiculos:
        if veiculo.km_atual >= veiculo.km_proxima_revisao:
            avisos.append(
                _aviso(
                    "REVISAO_VENCIDA",
                    "rejeicao",
                    f"{veiculo.nome} já está com a revisão vencida.",
                    veiculo.id,
                    veiculo_id=veiculo.id,
                    km_atual=veiculo.km_atual,
                    km_proxima_revisao=veiculo.km_proxima_revisao,
                )
            )

    tags = Counter(v.tag for v in vales)
    for tag, quantidade in tags.items():
        if quantidade > 1:
            avisos.append(
                _aviso(
                    "DADOS_DIVERGENTES",
                    "rejeicao",
                    f"TAG {tag} aparece em {quantidade} vales-pedágio.",
                    tag,
                    campo="tag",
                    tag=tag,
                    ocorrencias=quantidade,
                )
            )

    for vale in vales:
        if date.fromisoformat(vale.validade) < hoje:
            avisos.append(
                _aviso(
                    "VPO_VENCIDO",
                    "rejeicao",
                    f"VPO {vale.id} venceu em {vale.validade}.",
                    vale.id,
                    vale_id=vale.id,
                    validade=vale.validade,
                )
            )
        if vale.saldo_rs <= 0:
            avisos.append(
                _aviso(
                    "VPO_SALDO_INSUFICIENTE",
                    "rejeicao",
                    f"VPO {vale.id} está sem saldo.",
                    vale.id,
                    vale_id=vale.id,
                    saldo_rs=vale.saldo_rs,
                )
            )

    executadas = {e["simulacao_id"] for e in execucoes}
    for sim in simulacoes:
        if sim["id"] in executadas:
            continue
        try:
            criada = date.fromisoformat(str(sim["created_at"])[:10])
        except ValueError:
            continue
        idade = (hoje - criada).days
        if idade > DIAS_SEM_EXECUCAO:
            avisos.append(
                _aviso(
                    "EXECUCAO_NAO_REGISTRADA",
                    "aviso",
                    f"Simulação {sim['id']} tem {idade} dias e não tem execução registrada.",
                    sim["id"],
                    simulacao_id=sim["id"],
                    idade_dias=idade,
                )
            )

    desvios_por_veiculo: Counter[str] = Counter()
    for execucao in execucoes:
        sim = next((s for s in simulacoes if s["id"] == execucao["simulacao_id"]), None)
        if sim is None:
            continue
        km_previsto = float(sim["resultado"].get("distancia_km", 0.0))
        if km_previsto <= 0:
            continue
        desvio_pct = abs(execucao["km_real"] - km_previsto) / km_previsto * 100.0
        if desvio_pct > LIMITE_DESVIO_PCT:
            veiculo_id = str(sim["payload"].get("veiculo_id", "desconhecido"))
            desvios_por_veiculo[veiculo_id] += 1

    for veiculo_id, quantidade in desvios_por_veiculo.items():
        if quantidade >= 2:
            avisos.append(
                _aviso(
                    "DESVIO_ROTA_RECORRENTE",
                    "aviso",
                    f"{quantidade} execuções do veículo {veiculo_id} passaram de {LIMITE_DESVIO_PCT:.0f}% de desvio.",
                    veiculo_id,
                    veiculo_id=veiculo_id,
                    execucoes=quantidade,
                    limite_pct=LIMITE_DESVIO_PCT,
                )
            )

    avisos.sort(key=lambda a: (0 if a.severidade == "rejeicao" else 1, a.codigo, str(a.entidade)))
    return avisos
