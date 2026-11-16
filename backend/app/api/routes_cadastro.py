"""Cadastros: nós, arestas, frota, motoristas, perfis, VPO e tarifas."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_conn
from app.schemas import LancamentoIn, PerfilIn, ValeIn, VeiculoIn

router = APIRouter(prefix="/api", tags=["cadastro"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "servico": "valida-rota", "versao": "0.1.0"}


@router.get("/nos")
def listar_nos(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM nos ORDER BY nome")]


@router.get("/arestas")
def listar_arestas(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM arestas ORDER BY de, para")]


@router.get("/veiculos")
def listar_veiculos(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM veiculos ORDER BY nome")]


@router.post("/veiculos", status_code=201)
def criar_veiculo(payload: VeiculoIn, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    try:
        conn.execute(
            """INSERT INTO veiculos
               (id, nome, perfil, consumo_km_l, depreciacao_rs_km, manutencao_rs_km,
                capacidade_kg, km_atual, km_proxima_revisao, disponivel)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                payload.id,
                payload.nome,
                payload.perfil,
                payload.consumo_km_l,
                payload.depreciacao_rs_km,
                payload.manutencao_rs_km,
                payload.capacidade_kg,
                payload.km_atual,
                payload.km_proxima_revisao,
                int(payload.disponivel),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail={"codigo": "DADOS_DIVERGENTES", "mensagem": "veículo já cadastrado"},
        ) from exc
    return payload.model_dump()


@router.get("/motoristas")
def listar_motoristas(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM motoristas ORDER BY nome")]


@router.get("/perfis")
def listar_perfis(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM perfis ORDER BY nome")]


@router.post("/perfis", status_code=201)
def criar_perfil(payload: PerfilIn, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    try:
        conn.execute(
            """INSERT INTO perfis
               (id, nome, setor_id, mu, nu, xi, ocupacao_minima_pct, raio_setor_km,
                consumo_min_km_l, consumo_max_km_l, permitir_multiplos_setores)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                payload.id,
                payload.nome,
                payload.setor_id,
                payload.mu,
                payload.nu,
                payload.xi,
                payload.ocupacao_minima_pct,
                payload.raio_setor_km,
                payload.consumo_min_km_l,
                payload.consumo_max_km_l,
                int(payload.permitir_multiplos_setores),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail={"codigo": "DADOS_DIVERGENTES", "mensagem": "perfil já cadastrado"},
        ) from exc
    return payload.model_dump()


@router.get("/vales-pedagio")
def listar_vales(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM vales_pedagio ORDER BY id")]


@router.post("/vales-pedagio", status_code=201)
def criar_vale(payload: ValeIn, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    try:
        conn.execute(
            """INSERT INTO vales_pedagio (id, operadora, tag, placa, saldo_rs, validade)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                payload.id,
                payload.operadora,
                payload.tag,
                payload.placa,
                payload.saldo_rs,
                payload.validade.isoformat(),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail={"codigo": "DADOS_DIVERGENTES", "mensagem": "vale-pedágio já cadastrado"},
        ) from exc
    return {**payload.model_dump(), "validade": payload.validade.isoformat()}


@router.post("/lancamentos-pedagio", status_code=201)
def criar_lancamento(payload: LancamentoIn, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    existe = conn.execute("SELECT 1 FROM vales_pedagio WHERE id = ?", (payload.vale_id,)).fetchone()
    if existe is None:
        raise HTTPException(
            status_code=422,
            detail={"codigo": "DADOS_DIVERGENTES", "mensagem": "vale-pedágio não existe"},
        )
    try:
        conn.execute(
            """INSERT INTO lancamentos_pedagio (id, vale_id, praca, valor_rs, data, tag)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                payload.id,
                payload.vale_id,
                payload.praca,
                payload.valor_rs,
                payload.data.isoformat(),
                payload.tag,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail={"codigo": "DADOS_DIVERGENTES", "mensagem": "lançamento já cadastrado"},
        ) from exc
    return {**payload.model_dump(), "data": payload.data.isoformat()}


@router.get("/tarifas-pedagio")
def listar_tarifas(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM tarifas_pedagio ORDER BY praca")]
