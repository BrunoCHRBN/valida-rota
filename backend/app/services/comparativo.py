"""Comparativo previsto × real, sempre com a mesma fórmula de custo."""

from __future__ import annotations


def _pct(desvio: float, base: float) -> float:
    if base == 0:
        return 0.0
    return round(desvio / base * 100.0, 2)


def comparar(
    *,
    km_previsto: float,
    custo_previsto_rs: float,
    km_real: float,
    custo_real_rs: float,
) -> dict:
    desvio_km = round(km_real - km_previsto, 2)
    desvio_custo = round(custo_real_rs - custo_previsto_rs, 2)
    pior_pct = max(abs(_pct(desvio_km, km_previsto)), abs(_pct(desvio_custo, custo_previsto_rs)))

    if pior_pct <= 5.0:
        classificacao = "dentro"
    elif pior_pct <= 15.0:
        classificacao = "atencao"
    else:
        classificacao = "critico"

    return {
        "km_previsto": round(km_previsto, 2),
        "km_real": round(km_real, 2),
        "desvio_km": desvio_km,
        "desvio_km_pct": _pct(desvio_km, km_previsto),
        "custo_previsto_rs": round(custo_previsto_rs, 2),
        "custo_real_rs": round(custo_real_rs, 2),
        "desvio_custo_rs": desvio_custo,
        "desvio_custo_pct": _pct(desvio_custo, custo_previsto_rs),
        "classificacao": classificacao,
    }
