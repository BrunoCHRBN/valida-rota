"""Dependências e conversores entre SQLite e tipos de domínio."""

from __future__ import annotations

import sqlite3

from fastapi import Request

from app import db
from app.domain import Aresta, Motorista, No, Perfil, ValePedagio, Veiculo
from app.services.grafo import Grafo


def get_conn(request: Request):
    conn = db.conectar(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


def no_de_row(row: sqlite3.Row) -> No:
    return No(
        id=row["id"],
        nome=row["nome"],
        setor_id=row["setor_id"],
        qualidade_geo=row["qualidade_geo"],
        lat=row["lat"],
        lon=row["lon"],
    )


def veiculo_de_row(row: sqlite3.Row) -> Veiculo:
    return Veiculo(
        id=row["id"],
        nome=row["nome"],
        perfil=row["perfil"],
        consumo_km_l=row["consumo_km_l"],
        depreciacao_rs_km=row["depreciacao_rs_km"],
        manutencao_rs_km=row["manutencao_rs_km"],
        capacidade_kg=row["capacidade_kg"],
        km_atual=row["km_atual"],
        km_proxima_revisao=row["km_proxima_revisao"],
        disponivel=bool(row["disponivel"]),
    )


def motorista_de_row(row: sqlite3.Row) -> Motorista:
    return Motorista(
        id=row["id"],
        nome=row["nome"],
        custo_hora=row["custo_hora"],
        jornada_max_h=row["jornada_max_h"],
    )


def perfil_de_row(row: sqlite3.Row) -> Perfil:
    return Perfil(
        id=row["id"],
        nome=row["nome"],
        setor_id=row["setor_id"],
        mu=row["mu"],
        nu=row["nu"],
        xi=row["xi"],
        ocupacao_minima_pct=row["ocupacao_minima_pct"],
        raio_setor_km=row["raio_setor_km"],
        consumo_min_km_l=row["consumo_min_km_l"],
        consumo_max_km_l=row["consumo_max_km_l"],
        permitir_multiplos_setores=bool(row["permitir_multiplos_setores"]),
    )


def vale_de_row(row: sqlite3.Row) -> ValePedagio:
    return ValePedagio(
        id=row["id"],
        operadora=row["operadora"],
        tag=row["tag"],
        placa=row["placa"],
        saldo_rs=row["saldo_rs"],
        validade=row["validade"],
    )


def carregar_grafo(conn: sqlite3.Connection) -> Grafo:
    nos = [no_de_row(r) for r in conn.execute("SELECT * FROM nos ORDER BY id")]
    arestas = [
        Aresta(
            de=r["de"],
            para=r["para"],
            km=r["km"],
            pedagio_rs=r["pedagio_rs"],
            velocidade_media_km_h=r["velocidade_media_km_h"],
            praca=r["praca"],
        )
        for r in conn.execute("SELECT * FROM arestas ORDER BY id")
    ]
    return Grafo(nos, arestas)
