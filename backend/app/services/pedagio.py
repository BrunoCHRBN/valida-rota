"""Conciliação entre pedágio previsto no grafo e extrato da operadora."""

from __future__ import annotations

from app.domain import Aviso, LancamentoPedagio, TarifaPedagio

TOLERANCIA_RS = 0.01


def _tarifa_vigente(
    tarifas: list[TarifaPedagio], praca: str, data: str
) -> TarifaPedagio | None:
    candidatas = [
        t
        for t in tarifas
        if t.praca == praca
        and t.vigente_de <= data
        and (t.vigente_ate is None or data <= t.vigente_ate)
    ]
    if not candidatas:
        return None
    return max(candidatas, key=lambda t: t.vigente_de)


def conciliar(
    *,
    previstos: dict[str, float],
    lancamentos: list[LancamentoPedagio],
    tarifas: list[TarifaPedagio],
    data_viagem: str,
) -> list[Aviso]:
    avisos: list[Aviso] = []
    por_praca = {l.praca: l for l in lancamentos}

    for praca, valor_previsto in previstos.items():
        tarifa = _tarifa_vigente(tarifas, praca, data_viagem)
        if tarifa is not None and abs(tarifa.valor_rs - valor_previsto) > TOLERANCIA_RS:
            avisos.append(
                Aviso(
                    codigo="TARIFA_DIVERGENTE",
                    severidade="aviso",
                    mensagem=(
                        f"Tarifa vigente de {praca} é R$ {tarifa.valor_rs:.2f}, "
                        f"mas o grafo usa R$ {valor_previsto:.2f}."
                    ),
                    detalhe={
                        "praca": praca,
                        "tarifa_vigente_rs": tarifa.valor_rs,
                        "valor_no_grafo_rs": valor_previsto,
                    },
                    entidade=praca,
                )
            )

        lancamento = por_praca.get(praca)
        if lancamento is None:
            avisos.append(
                Aviso(
                    codigo="PEDAGIO_DIVERGENTE",
                    severidade="aviso",
                    mensagem=f"Praça {praca} prevista sem lançamento correspondente.",
                    detalhe={"praca": praca, "motivo": "sem_lancamento", "previsto_rs": valor_previsto},
                    entidade=praca,
                )
            )
        elif abs(lancamento.valor_rs - valor_previsto) > TOLERANCIA_RS:
            avisos.append(
                Aviso(
                    codigo="PEDAGIO_DIVERGENTE",
                    severidade="aviso",
                    mensagem=(
                        f"Pedágio de {praca}: previsto R$ {valor_previsto:.2f}, "
                        f"cobrado R$ {lancamento.valor_rs:.2f}."
                    ),
                    detalhe={
                        "praca": praca,
                        "motivo": "valor",
                        "previsto_rs": valor_previsto,
                        "cobrado_rs": lancamento.valor_rs,
                        "diferenca_rs": round(lancamento.valor_rs - valor_previsto, 2),
                    },
                    entidade=praca,
                )
            )

    for lancamento in lancamentos:
        if lancamento.praca not in previstos:
            avisos.append(
                Aviso(
                    codigo="PRACA_NAO_PREVISTA",
                    severidade="aviso",
                    mensagem=f"Praça {lancamento.praca} foi cobrada e não está na rota prevista.",
                    detalhe={
                        "praca": lancamento.praca,
                        "valor_rs": lancamento.valor_rs,
                        "data": lancamento.data,
                    },
                    entidade=lancamento.praca,
                )
            )

    return avisos
