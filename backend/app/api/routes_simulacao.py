"""Simulação: gate antes e depois da otimização, com persistência do resultado."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    carregar_grafo,
    get_conn,
    motorista_de_row,
    perfil_de_row,
    vale_de_row,
    veiculo_de_row,
)
from app.data.sementes import PRECO_DIESEL_RS_L
from app.domain import Parada
from app.schemas import SimulacaoIn
from app.services.custo import calcular
from app.services.otimizador import LIMITE_PARADAS, otimizar
from app.services.supermatrix import SuperMatrix
from app.services.validacao import (
    consolidar,
    validar_cadastro,
    validar_geocodificacao,
    validar_operacao,
    validar_vpo,
)

router = APIRouter(prefix="/api", tags=["simulacao"])


def _erro(status: int, codigo: str, mensagem: str, avisos: list | None = None):
    detalhe = {"codigo": codigo, "mensagem": mensagem}
    if avisos is not None:
        detalhe["avisos"] = avisos
    raise HTTPException(status_code=status, detail=detalhe)


def _simulacao(conn: sqlite3.Connection, sim_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM simulacoes WHERE id = ?", (sim_id,)).fetchone()
    if row is None:
        _erro(404, "DADOS_DIVERGENTES", f"simulação {sim_id} não existe")
    return row


@router.post("/simular")
def simular(payload: SimulacaoIn, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    grafo = carregar_grafo(conn)
    veiculo_row = conn.execute("SELECT * FROM veiculos WHERE id = ?", (payload.veiculo_id,)).fetchone()
    motorista_row = conn.execute("SELECT * FROM motoristas WHERE id = ?", (payload.motorista_id,)).fetchone()
    perfil_row = conn.execute("SELECT * FROM perfis WHERE id = ?", (payload.perfil_id,)).fetchone()
    if veiculo_row is None or motorista_row is None or perfil_row is None:
        _erro(422, "DADOS_DIVERGENTES", "veículo, motorista ou perfil não existe")

    veiculo = veiculo_de_row(veiculo_row)
    motorista = motorista_de_row(motorista_row)
    perfil = perfil_de_row(perfil_row)
    paradas = [
        Parada(
            no_id=p.no_id,
            janela_inicio=p.janela_inicio,
            janela_fim=p.janela_fim,
            peso_kg=p.peso_kg,
            prioridade=p.prioridade,
            minutos_servico=p.minutos_servico,
        )
        for p in payload.paradas
    ]

    avisos = validar_cadastro(payload.origem_id, paradas, grafo)
    if any(a.severidade == "rejeicao" for a in avisos):
        _erro(422, avisos[0].codigo, avisos[0].mensagem, [asdict(a) for a in avisos])

    nos_usados = [grafo.nos[payload.origem_id]] + [grafo.nos[p.no_id] for p in paradas]
    avisos += validar_geocodificacao(nos_usados)

    ids = [payload.origem_id] + [p.no_id for p in paradas]
    matriz = SuperMatrix(
        grafo,
        ids,
        evitar_pedagio=payload.evitar_pedagio,
        lambda_pedagio=1.0,
    )
    faltantes = matriz.faltantes()
    if faltantes:
        _erro(
            422,
            "TRECHO_INALCANCAVEL",
            "Há pares de pontos sem caminho no grafo.",
            [{"codigo": "TRECHO_INALCANCAVEL", "detalhe": {"pares": faltantes[:5]}}],
        )

    try:
        resultado = otimizar(
            payload.origem_id,
            paradas,
            matriz,
            perfil,
            {n.id: n.setor_id for n in grafo.nos.values()},
            partida=payload.partida,
            retornar_origem=payload.retornar_origem,
        )
    except ValueError as exc:
        if str(exc).startswith("LIMITE_PARADAS"):
            _erro(422, "DADOS_DIVERGENTES", f"máximo de {LIMITE_PARADAS} paradas")
        _erro(422, "TRECHO_INALCANCAVEL", "não foi possível montar a rota")

    vpo = None
    if payload.vpo_id:
        vpo_row = conn.execute("SELECT * FROM vales_pedagio WHERE id = ?", (payload.vpo_id,)).fetchone()
        if vpo_row is not None:
            vpo = vale_de_row(vpo_row)

    custo = calcular(
        km=resultado.distancia_km,
        horas=resultado.tempo_total_h or resultado.tempo_h,
        pedagio_rs=resultado.pedagio_rs,
        veiculo=veiculo,
        motorista=motorista,
        receita_rs=payload.receita_rs,
        preco_diesel_rs_l=PRECO_DIESEL_RS_L,
        modo_pedagio=payload.modo_pedagio,
        vpo_consumido_rs=resultado.pedagio_rs if payload.modo_pedagio == "vpo" else 0.0,
    )

    data_viagem = payload.data_viagem or date.today()
    avisos += validar_operacao(
        veiculo=veiculo,
        motorista=motorista,
        perfil=perfil,
        paradas=paradas,
        setores={n.id: n.setor_id for n in grafo.nos.values()},
        resultado=resultado,
        peso_total_kg=sum(p.peso_kg for p in paradas),
    )
    avisos += validar_vpo(
        modo_pedagio=payload.modo_pedagio,
        vpo=vpo,
        placa=payload.placa,
        pedagio_previsto_rs=resultado.pedagio_rs,
        data_viagem=data_viagem,
    )
    status, avisos = consolidar(avisos)

    sim_id = f"sim-{uuid.uuid4().hex[:12]}"
    criado_em = datetime.now(timezone.utc).isoformat()
    resposta = {
        "id": sim_id,
        "created_at": criado_em,
        "status": status,
        "ordem": resultado.ordem,
        "chegadas": resultado.chegadas,
        "distancia_km": resultado.distancia_km,
        "tempo_h": resultado.tempo_h,
        "tempo_total_h": resultado.tempo_total_h,
        "pedagio_rs": resultado.pedagio_rs,
        "pracas": resultado.pracas,
        "custos": asdict(custo),
        "margem_rs": custo.margem_rs,
        "margem_pct": custo.margem_pct,
        "avisos": [asdict(a) for a in avisos],
        "parametros": {
            **payload.model_dump(mode="json"),
            "data_viagem": data_viagem.isoformat(),
            "perfil_nome": perfil.nome,
            "veiculo_nome": veiculo.nome,
            "motorista_nome": motorista.nome,
            "preco_diesel_rs_l": PRECO_DIESEL_RS_L,
        },
    }

    conn.execute(
        "INSERT INTO simulacoes (id, created_at, payload_json, resultado_json) VALUES (?, ?, ?, ?)",
        (
            sim_id,
            criado_em,
            json.dumps(payload.model_dump(mode="json"), ensure_ascii=False),
            json.dumps(resposta, ensure_ascii=False),
        ),
    )
    conn.executemany(
        """INSERT INTO alertas (simulacao_id, codigo, severidade, detalhe_json, criado_em)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (sim_id, a.codigo, a.severidade, json.dumps(a.detalhe, ensure_ascii=False), criado_em)
            for a in avisos
        ],
    )
    conn.commit()
    return resposta


@router.get("/simulacoes")
def listar_simulacoes(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    rows = conn.execute(
        "SELECT id, created_at, resultado_json FROM simulacoes ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    saida = []
    for row in rows:
        resultado = json.loads(row["resultado_json"])
        saida.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "status": resultado.get("status"),
                "distancia_km": resultado.get("distancia_km"),
                "margem_rs": resultado.get("margem_rs"),
            }
        )
    return saida


@router.get("/simulacoes/{sim_id}")
def obter_simulacao(sim_id: str, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    row = _simulacao(conn, sim_id)
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "payload": json.loads(row["payload_json"]),
        "resultado": json.loads(row["resultado_json"]),
    }
