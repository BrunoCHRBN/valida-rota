"""Execução real, comparativo, conciliação de pedágio, diagnóstico e geocodificação."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import asdict
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    carregar_grafo,
    get_conn,
    motorista_de_row,
    no_de_row,
    veiculo_de_row,
    vale_de_row,
)
from app.data.sementes import PRECO_DIESEL_RS_L
from app.domain import LancamentoPedagio, TarifaPedagio
from app.schemas import ExecucaoIn, GeocodificacaoIn
from app.services.comparativo import comparar
from app.services.custo import calcular
from app.services.diagnostico import diagnosticar
from app.services.geocodificacao import ResultadoGeo as Geo
from app.services.geocodificacao import distancia_m, validar_coordenadas
from app.services.pedagio import conciliar

router = APIRouter(prefix="/api", tags=["analise"])


def _simulacao(conn: sqlite3.Connection, sim_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM simulacoes WHERE id = ?", (sim_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"codigo": "DADOS_DIVERGENTES", "mensagem": f"simulação {sim_id} não existe"},
        )
    return row


@router.post("/execucoes", status_code=201)
def registrar_execucao(payload: ExecucaoIn, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    _simulacao(conn, payload.simulacao_id)
    exec_id = f"exec-{payload.simulacao_id.split('-')[-1]}"
    criado_em = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            """INSERT INTO execucoes
               (id, simulacao_id, km_real, diesel_real, pedagio_real, tempo_real_h,
                rota_executada_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                exec_id,
                payload.simulacao_id,
                payload.km_real,
                payload.diesel_real,
                payload.pedagio_real,
                payload.tempo_real_h,
                json.dumps(payload.rota_executada),
                criado_em,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail={"codigo": "DADOS_DIVERGENTES", "mensagem": "execução já registrada"},
        ) from exc
    return {
        "id": exec_id,
        "simulacao_id": payload.simulacao_id,
        "km_real": payload.km_real,
        "custo_registrado_rs": round(
            payload.diesel_real + payload.pedagio_real, 2
        ),
        "created_at": criado_em,
    }


@router.get("/simulacoes/{sim_id}/comparativo")
def obter_comparativo(sim_id: str, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    sim = _simulacao(conn, sim_id)
    execucao = conn.execute("SELECT * FROM execucoes WHERE simulacao_id = ?", (sim_id,)).fetchone()
    if execucao is None:
        raise HTTPException(
            status_code=404,
            detail={
                "codigo": "EXECUCAO_NAO_REGISTRADA",
                "mensagem": "esta simulação ainda não tem execução registrada",
            },
        )

    resultado = json.loads(sim["resultado_json"])
    payload = json.loads(sim["payload_json"])
    veiculo_row = conn.execute("SELECT * FROM veiculos WHERE id = ?", (payload["veiculo_id"],)).fetchone()
    motorista_row = conn.execute("SELECT * FROM motoristas WHERE id = ?", (payload["motorista_id"],)).fetchone()
    if veiculo_row is None or motorista_row is None:
        raise HTTPException(
            status_code=422,
            detail={"codigo": "DADOS_DIVERGENTES", "mensagem": "veículo ou motorista da simulação não existe"},
        )

    custo_real = calcular(
        km=execucao["km_real"],
        horas=execucao["tempo_real_h"],
        pedagio_rs=execucao["pedagio_real"],
        veiculo=veiculo_de_row(veiculo_row),
        motorista=motorista_de_row(motorista_row),
        receita_rs=payload["receita_rs"],
        preco_diesel_rs_l=PRECO_DIESEL_RS_L,
        modo_pedagio=payload["modo_pedagio"],
        vpo_consumido_rs=execucao["pedagio_real"] if payload["modo_pedagio"] == "vpo" else 0.0,
        diesel_rs=execucao["diesel_real"],
    )
    comparativo = comparar(
        km_previsto=resultado["distancia_km"],
        custo_previsto_rs=resultado["custos"]["total_rs"],
        km_real=execucao["km_real"],
        custo_real_rs=custo_real.total_rs,
    )
    return {
        "simulacao_id": sim_id,
        "execucao_id": execucao["id"],
        "comparativo": comparativo,
        "custo_real": asdict(custo_real),
    }


@router.get("/simulacoes/{sim_id}/pedagio")
def conciliar_pedagio(sim_id: str, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    sim = _simulacao(conn, sim_id)
    resultado = json.loads(sim["resultado_json"])
    payload = json.loads(sim["payload_json"])
    previstos = resultado.get("pracas", {})

    lancamentos = [
        LancamentoPedagio(
            id=r["id"],
            vale_id=r["vale_id"],
            praca=r["praca"],
            valor_rs=r["valor_rs"],
            data=r["data"],
            tag=r["tag"],
        )
        for r in conn.execute("SELECT * FROM lancamentos_pedagio ORDER BY data")
    ]
    tarifas = [
        TarifaPedagio(
            praca=r["praca"],
            valor_rs=r["valor_rs"],
            vigente_de=r["vigente_de"],
            vigente_ate=r["vigente_ate"],
        )
        for r in conn.execute("SELECT * FROM tarifas_pedagio")
    ]
    data_viagem = payload.get("data_viagem") or sim["created_at"][:10]
    avisos = conciliar(
        previstos=previstos,
        lancamentos=lancamentos,
        tarifas=tarifas,
        data_viagem=data_viagem,
    )
    return {
        "simulacao_id": sim_id,
        "previstos": previstos,
        "lancamentos": [
            {
                "id": l.id,
                "praca": l.praca,
                "valor_rs": l.valor_rs,
                "data": l.data,
                "tag": l.tag,
            }
            for l in lancamentos
        ],
        "avisos": [asdict(a) for a in avisos],
    }


@router.get("/diagnostico")
def obter_diagnostico(conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    grafo = carregar_grafo(conn)
    veiculos = [veiculo_de_row(r) for r in conn.execute("SELECT * FROM veiculos")]
    vales = [vale_de_row(r) for r in conn.execute("SELECT * FROM vales_pedagio")]
    simulacoes = [
        {
            "id": r["id"],
            "created_at": r["created_at"],
            "payload": json.loads(r["payload_json"]),
            "resultado": json.loads(r["resultado_json"]),
        }
        for r in conn.execute("SELECT * FROM simulacoes")
    ]
    execucoes = [
        {"simulacao_id": r["simulacao_id"], "km_real": r["km_real"]}
        for r in conn.execute("SELECT * FROM execucoes")
    ]

    avisos = diagnosticar(
        grafo=grafo,
        veiculos=veiculos,
        vales=vales,
        simulacoes=simulacoes,
        execucoes=execucoes,
        hoje=date.today(),
    )
    contagem = Counter(a.codigo for a in avisos)
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "total": len(avisos),
        "por_codigo": dict(sorted(contagem.items())),
        "alertas": [asdict(a) for a in avisos],
    }


@router.post("/geocodificacao/validar")
def validar_geocodificacao_endpoint(
    payload: GeocodificacaoIn, conn: sqlite3.Connection = Depends(get_conn)
) -> dict:
    row = conn.execute("SELECT * FROM nos WHERE id = ?", (payload.no_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=422,
            detail={"codigo": "NO_NAO_EXISTE", "mensagem": f"nó {payload.no_id} não existe"},
        )
    no = no_de_row(row)
    cadastrado = Geo(no.lat, no.lon, no.qualidade_geo, "sintetico")
    obtido = Geo(payload.lat, payload.lon, payload.qualidade, "usuario")
    avisos = validar_coordenadas(
        cadastrado,
        obtido,
        raio_max_m=payload.raio_max_m,
        no_id=no.id,
    )
    return {
        "no_id": no.id,
        "distancia_m": round(distancia_m(cadastrado, obtido), 1),
        "avisos": [asdict(a) for a in avisos],
    }
