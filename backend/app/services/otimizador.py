"""Ordenação de paradas por enumeração de permutações (limite explícito de 8)."""

from __future__ import annotations

from itertools import permutations

from app.domain import Parada, Perfil, ResultadoOtimizacao
from app.services.supermatrix import SuperMatrix

LIMITE_PARADAS = 8


def _para_minutos(hhmm: str) -> int:
    partes = hhmm.split(":")
    if len(partes) != 2:
        raise ValueError(f"horário inválido: {hhmm}")
    hora, minuto = int(partes[0]), int(partes[1])
    if not (0 <= hora <= 23 and 0 <= minuto <= 59):
        raise ValueError(f"horário inválido: {hhmm}")
    return hora * 60 + minuto


def _para_hhmm(minutos: float) -> str:
    total = int(round(minutos)) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


def _janela(parada: Parada) -> tuple[int | None, int | None]:
    inicio = _para_minutos(parada.janela_inicio) if parada.janela_inicio else None
    fim = _para_minutos(parada.janela_fim) if parada.janela_fim else None
    if inicio is not None and fim is not None and fim < inicio:
        fim += 24 * 60
    return inicio, fim


def otimizar(
    origem: str,
    paradas: list[Parada],
    matriz: SuperMatrix,
    perfil: Perfil,
    setores: dict[str, str],
    *,
    partida: str = "08:00",
    retornar_origem: bool = False,
) -> ResultadoOtimizacao:
    if len(paradas) > LIMITE_PARADAS:
        raise ValueError(f"LIMITE_PARADAS:{LIMITE_PARADAS}")
    if not paradas:
        return ResultadoOtimizacao(
            ordem=[],
            chegadas={},
            distancia_km=0.0,
            tempo_h=0.0,
            pedagio_rs=0.0,
            violacao_janela_min=0.0,
            penalidade_prioridade=0.0,
            desvio_setor_km=0.0,
            score=0.0,
            pracas={},
        )

    partida_min = _para_minutos(partida)
    melhor: tuple[float, tuple[str, ...], ResultadoOtimizacao] | None = None

    for perm in permutations(paradas):
        atual = origem
        relogio = float(partida_min)
        km = horas = pedagio = 0.0
        atraso_total = 0.0
        penalidade = 0.0
        desvio = 0.0
        chegadas: dict[str, str] = {}
        pracas: dict[str, float] = {}
        viavel = True

        for parada in perm:
            trecho = matriz.trecho(atual, parada.no_id)
            if trecho is None:
                viavel = False
                break
            km += trecho.km
            horas += trecho.horas
            pedagio += trecho.pedagio_rs
            for praca, valor in trecho.pracas.items():
                pracas[praca] = pracas.get(praca, 0.0) + valor

            relogio += trecho.horas * 60.0
            inicio, fim = _janela(parada)
            if inicio is not None and relogio < inicio:
                relogio = float(inicio)
            chegada = relogio
            if fim is not None and chegada > fim:
                atraso = chegada - fim
                atraso_total += atraso
                penalidade += parada.prioridade * (atraso / 60.0)
            chegadas[parada.no_id] = _para_hhmm(chegada)
            relogio += parada.minutos_servico

            if setores.get(parada.no_id) != perfil.setor_id:
                desvio += trecho.km
            atual = parada.no_id

        if not viavel:
            continue

        if retornar_origem:
            volta = matriz.trecho(atual, origem)
            if volta is None:
                continue
            km += volta.km
            horas += volta.horas
            relogio += volta.horas * 60.0
            pedagio += volta.pedagio_rs
            for praca, valor in volta.pracas.items():
                pracas[praca] = pracas.get(praca, 0.0) + valor

        score = (
            km
            + perfil.mu * atraso_total
            + perfil.nu * penalidade
            + perfil.xi * desvio
        )
        chave = tuple(p.no_id for p in perm)
        resultado = ResultadoOtimizacao(
            ordem=list(chave),
            chegadas=chegadas,
            distancia_km=round(km, 3),
            tempo_h=round(horas, 4),
            pedagio_rs=round(pedagio, 2),
            violacao_janela_min=round(atraso_total, 2),
            penalidade_prioridade=round(penalidade, 4),
            desvio_setor_km=round(desvio, 3),
            score=round(score, 3),
            pracas={k: round(v, 2) for k, v in sorted(pracas.items())},
            tempo_total_h=round((relogio - partida_min) / 60.0, 4),
        )
        if melhor is None or score < melhor[0] - 1e-9 or (
            abs(score - melhor[0]) <= 1e-9 and chave < melhor[1]
        ):
            melhor = (score, chave, resultado)

    if melhor is None:
        raise ValueError("SEM_CAMINHO")
    return melhor[2]
