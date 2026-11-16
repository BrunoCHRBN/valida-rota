"""Porta de geocodificação e validação de coordenadas.

O MVP usa um provider sintético determinístico. Um adapter Tencent pode
entrar depois sem mudar o gate, desde que implemente o mesmo Protocol.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from app.domain import Aviso


@dataclass(frozen=True)
class ResultadoGeo:
    lat: float
    lon: float
    qualidade: str  # exata | alta | media | baixa | ambigua | fornecida_usuario
    fonte: str  # sintetico | tencent | usuario


class ProvedorGeocodificacao(Protocol):
    def geocodificar(self, consulta: str) -> ResultadoGeo | None: ...


class ProvedorSintetico:
    def __init__(self, base: dict[str, ResultadoGeo]) -> None:
        self._base = {k.strip().lower(): v for k, v in base.items()}

    def geocodificar(self, consulta: str) -> ResultadoGeo | None:
        return self._base.get(consulta.strip().lower())


def distancia_m(a: ResultadoGeo, b: ResultadoGeo) -> float:
    raio = 6371000.0
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * raio * math.asin(math.sqrt(h))


def validar_coordenadas(
    cadastrado: ResultadoGeo,
    obtido: ResultadoGeo | None,
    *,
    raio_max_m: float = 150.0,
    no_id: str | None = None,
) -> list[Aviso]:
    avisos: list[Aviso] = []
    if obtido is None:
        avisos.append(
            Aviso(
                codigo="GEOCODIFICACAO_BAIXA",
                severidade="aviso",
                mensagem="O provider não retornou coordenada para a consulta.",
                detalhe={"motivo": "nao_encontrada"},
                entidade=no_id,
            )
        )
        return avisos

    if obtido.qualidade in {"baixa", "ambigua"}:
        avisos.append(
            Aviso(
                codigo="GEOCODIFICACAO_BAIXA",
                severidade="aviso",
                mensagem=f"Qualidade da geocodificação é '{obtido.qualidade}'.",
                detalhe={"qualidade": obtido.qualidade, "fonte": obtido.fonte},
                entidade=no_id,
            )
        )

    distancia = distancia_m(cadastrado, obtido)
    if distancia > raio_max_m:
        avisos.append(
            Aviso(
                codigo="COORDENADAS_DIVERGENTES",
                severidade="aviso",
                mensagem=(
                    f"Coordenada obtida está a {distancia:.0f} m da cadastrada "
                    f"(limite {raio_max_m:.0f} m)."
                ),
                detalhe={
                    "distancia_m": round(distancia, 1),
                    "raio_max_m": raio_max_m,
                    "lat_cadastrada": cadastrado.lat,
                    "lon_cadastrada": cadastrado.lon,
                    "lat_obtida": obtido.lat,
                    "lon_obtida": obtido.lon,
                },
                entidade=no_id,
            )
        )
    return avisos
