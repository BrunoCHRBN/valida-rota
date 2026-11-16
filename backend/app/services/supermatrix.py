"""Matriz pairwise de km, tempo e pedágio entre os pontos de uma simulação."""

from __future__ import annotations

from app.domain import Trecho
from app.services.grafo import Grafo


class SuperMatrix:
    def __init__(
        self,
        grafo: Grafo,
        nos_ids: list[str],
        *,
        evitar_pedagio: bool = False,
        lambda_pedagio: float = 1.0,
    ) -> None:
        self._ids = list(dict.fromkeys(nos_ids))
        self._trechos: dict[tuple[str, str], Trecho] = {}
        for origem in self._ids:
            for destino in self._ids:
                if origem == destino:
                    trecho = Trecho(0.0, 0.0, 0.0, (origem,))
                else:
                    trecho = grafo.dijkstra(
                        origem,
                        destino,
                        evitar_pedagio=evitar_pedagio,
                        lambda_pedagio=lambda_pedagio,
                    )
                if trecho is not None:
                    self._trechos[(origem, destino)] = trecho

    def trecho(self, origem: str, destino: str) -> Trecho | None:
        return self._trechos.get((origem, destino))

    def faltantes(self) -> list[tuple[str, str]]:
        return [
            (a, b)
            for a in self._ids
            for b in self._ids
            if (a, b) not in self._trechos
        ]
