"""Grafo viário abstrato e menor caminho por Dijkstra."""

from __future__ import annotations

import heapq
from collections import defaultdict

from app.domain import Aresta, No, Trecho


class Grafo:
    def __init__(self, nos: list[No], arestas: list[Aresta]) -> None:
        self.nos: dict[str, No] = {n.id: n for n in nos}
        self.arestas: list[Aresta] = list(arestas)
        self._adj: dict[str, list[Aresta]] = defaultdict(list)
        for aresta in self.arestas:
            self._adj[aresta.de].append(aresta)

    def vizinhos(self, no_id: str) -> list[Aresta]:
        return list(self._adj.get(no_id, []))

    def arestas_incompletas(self) -> list[Aresta]:
        """Arestas que não permitem calcular km ou tempo com segurança."""
        return [
            a
            for a in self.arestas
            if a.de not in self.nos
            or a.para not in self.nos
            or a.km <= 0
            or a.velocidade_media_km_h <= 0
            or a.pedagio_rs < 0
        ]

    def alcancaveis(self, origem: str) -> set[str]:
        if origem not in self.nos:
            return set()
        vistos = {origem}
        fila = [origem]
        while fila:
            atual = fila.pop()
            for aresta in self._adj.get(atual, []):
                if aresta.para not in vistos:
                    vistos.add(aresta.para)
                    fila.append(aresta.para)
        return vistos

    def dijkstra(
        self,
        origem: str,
        destino: str,
        *,
        evitar_pedagio: bool = False,
        lambda_pedagio: float = 1.0,
    ) -> Trecho | None:
        if origem not in self.nos or destino not in self.nos:
            return None
        if origem == destino:
            return Trecho(km=0.0, horas=0.0, pedagio_rs=0.0, caminho=(origem,))

        melhor: dict[str, float] = {origem: 0.0}
        anterior: dict[str, tuple[str, Aresta]] = {}
        contador = 0
        fila: list[tuple[float, int, str]] = [(0.0, contador, origem)]

        while fila:
            custo, _, atual = heapq.heappop(fila)
            if custo > melhor.get(atual, float("inf")):
                continue
            if atual == destino:
                break
            for aresta in self._adj.get(atual, []):
                peso = aresta.km
                if evitar_pedagio:
                    peso += lambda_pedagio * aresta.pedagio_rs
                novo = custo + peso
                if novo < melhor.get(aresta.para, float("inf")):
                    melhor[aresta.para] = novo
                    anterior[aresta.para] = (atual, aresta)
                    contador += 1
                    heapq.heappush(fila, (novo, contador, aresta.para))

        if destino not in melhor:
            return None

        caminho = [destino]
        arestas: list[Aresta] = []
        atual = destino
        while atual != origem:
            pai, aresta = anterior[atual]
            arestas.append(aresta)
            caminho.append(pai)
            atual = pai
        caminho.reverse()
        arestas.reverse()

        km = sum(a.km for a in arestas)
        horas = sum(a.km / a.velocidade_media_km_h for a in arestas)
        pedagio = sum(a.pedagio_rs for a in arestas)
        pracas: dict[str, float] = defaultdict(float)
        for a in arestas:
            if a.praca:
                pracas[a.praca] += a.pedagio_rs

        return Trecho(
            km=km,
            horas=horas,
            pedagio_rs=pedagio,
            caminho=tuple(caminho),
            pracas=dict(pracas),
        )
