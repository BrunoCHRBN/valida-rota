"""Custo operacional e margem, com tratamento explícito de VPO."""

from __future__ import annotations

from app.domain import Motorista, Perfil, ResultadoCusto, Veiculo

EXTRA_REVISAO_RS = 450.0


def calcular(
    *,
    km: float,
    horas: float,
    pedagio_rs: float,
    veiculo: Veiculo,
    motorista: Motorista,
    receita_rs: float,
    preco_diesel_rs_l: float,
    modo_pedagio: str,
    vpo_consumido_rs: float = 0.0,
    diesel_rs: float | None = None,
) -> ResultadoCusto:
    # consumo é km/l: litros = km / (km/l). Multiplicar por consumo inverteria a unidade.
    diesel = diesel_rs if diesel_rs is not None else (km / veiculo.consumo_km_l) * preco_diesel_rs_l
    depreciacao = km * veiculo.depreciacao_rs_km
    extra_revisao = (
        EXTRA_REVISAO_RS
        if veiculo.km_atual + km > veiculo.km_proxima_revisao
        else 0.0
    )
    manutencao = km * veiculo.manutencao_rs_km + extra_revisao
    motorista_rs = horas * motorista.custo_hora
    total = diesel + pedagio_rs + depreciacao + manutencao + motorista_rs

    coberto = pedagio_rs if modo_pedagio == "vpo" else 0.0
    margem = receita_rs - (total - coberto)
    margem_pct = (margem / receita_rs * 100.0) if receita_rs > 0 else 0.0
    custo_logistico = receita_rs + (vpo_consumido_rs if modo_pedagio == "vpo" else 0.0)

    return ResultadoCusto(
        diesel_rs=round(diesel, 2),
        pedagio_rs=round(pedagio_rs, 2),
        depreciacao_rs=round(depreciacao, 2),
        manutencao_rs=round(manutencao, 2),
        motorista_rs=round(motorista_rs, 2),
        total_rs=round(total, 2),
        pedagio_coberto_rs=round(coberto, 2),
        margem_rs=round(margem, 2),
        margem_pct=round(margem_pct, 2),
        custo_logistico_embarcador_rs=round(custo_logistico, 2),
        extra_revisao_rs=round(extra_revisao, 2),
    )


def consumo_em_faixa(veiculo: Veiculo, perfil: Perfil) -> bool:
    return perfil.consumo_min_km_l <= veiculo.consumo_km_l <= perfil.consumo_max_km_l
