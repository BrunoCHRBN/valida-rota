"""SQLite: schema, seed determinístico e conexão por request."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.data import sementes

SCHEMA = """
CREATE TABLE IF NOT EXISTS nos (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    setor_id TEXT NOT NULL,
    qualidade_geo TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS arestas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    de TEXT NOT NULL,
    para TEXT NOT NULL,
    km REAL NOT NULL,
    pedagio_rs REAL NOT NULL,
    velocidade_media_km_h REAL NOT NULL,
    praca TEXT,
    UNIQUE (de, para)
);

CREATE TABLE IF NOT EXISTS veiculos (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    perfil TEXT NOT NULL,
    consumo_km_l REAL NOT NULL,
    depreciacao_rs_km REAL NOT NULL,
    manutencao_rs_km REAL NOT NULL,
    capacidade_kg REAL NOT NULL,
    km_atual REAL NOT NULL,
    km_proxima_revisao REAL NOT NULL,
    disponivel INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS motoristas (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    custo_hora REAL NOT NULL,
    jornada_max_h REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS perfis (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    setor_id TEXT NOT NULL,
    mu REAL NOT NULL,
    nu REAL NOT NULL,
    xi REAL NOT NULL,
    ocupacao_minima_pct REAL NOT NULL,
    raio_setor_km REAL NOT NULL,
    consumo_min_km_l REAL NOT NULL,
    consumo_max_km_l REAL NOT NULL,
    permitir_multiplos_setores INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS simulacoes (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    resultado_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS execucoes (
    id TEXT PRIMARY KEY,
    simulacao_id TEXT NOT NULL UNIQUE,
    km_real REAL NOT NULL,
    diesel_real REAL NOT NULL,
    pedagio_real REAL NOT NULL,
    tempo_real_h REAL NOT NULL,
    rota_executada_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vales_pedagio (
    id TEXT PRIMARY KEY,
    operadora TEXT NOT NULL,
    tag TEXT NOT NULL,
    placa TEXT NOT NULL,
    saldo_rs REAL NOT NULL,
    validade TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lancamentos_pedagio (
    id TEXT PRIMARY KEY,
    vale_id TEXT NOT NULL,
    praca TEXT NOT NULL,
    valor_rs REAL NOT NULL,
    data TEXT NOT NULL,
    tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tarifas_pedagio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    praca TEXT NOT NULL,
    valor_rs REAL NOT NULL,
    vigente_de TEXT NOT NULL,
    vigente_ate TEXT,
    UNIQUE (praca, vigente_de)
);

CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacao_id TEXT,
    codigo TEXT NOT NULL,
    severidade TEXT NOT NULL,
    detalhe_json TEXT NOT NULL,
    criado_em TEXT NOT NULL
);
"""


def conectar(caminho: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(caminho), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar(caminho: str | Path) -> None:
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conn = conectar(caminho)
    try:
        conn.executescript(SCHEMA)
        _seed(conn)
        conn.commit()
    finally:
        conn.close()


def _seed(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO nos (id, nome, setor_id, qualidade_geo, lat, lon) VALUES (?, ?, ?, ?, ?, ?)",
        [(n.id, n.nome, n.setor_id, n.qualidade_geo, n.lat, n.lon) for n in sementes.NOS],
    )
    conn.executemany(
        """INSERT OR IGNORE INTO arestas
           (de, para, km, pedagio_rs, velocidade_media_km_h, praca)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (a.de, a.para, a.km, a.pedagio_rs, a.velocidade_media_km_h, a.praca)
            for a in sementes.ARESTAS
        ],
    )
    conn.executemany(
        """INSERT OR IGNORE INTO veiculos
           (id, nome, perfil, consumo_km_l, depreciacao_rs_km, manutencao_rs_km,
            capacidade_kg, km_atual, km_proxima_revisao, disponivel)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                v.id,
                v.nome,
                v.perfil,
                v.consumo_km_l,
                v.depreciacao_rs_km,
                v.manutencao_rs_km,
                v.capacidade_kg,
                v.km_atual,
                v.km_proxima_revisao,
                int(v.disponivel),
            )
            for v in sementes.VEICULOS
        ],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO motoristas (id, nome, custo_hora, jornada_max_h) VALUES (?, ?, ?, ?)",
        [(m.id, m.nome, m.custo_hora, m.jornada_max_h) for m in sementes.MOTORISTAS],
    )
    conn.executemany(
        """INSERT OR IGNORE INTO perfis
           (id, nome, setor_id, mu, nu, xi, ocupacao_minima_pct, raio_setor_km,
            consumo_min_km_l, consumo_max_km_l, permitir_multiplos_setores)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                p.id,
                p.nome,
                p.setor_id,
                p.mu,
                p.nu,
                p.xi,
                p.ocupacao_minima_pct,
                p.raio_setor_km,
                p.consumo_min_km_l,
                p.consumo_max_km_l,
                int(p.permitir_multiplos_setores),
            )
            for p in sementes.PERFIS
        ],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO vales_pedagio (id, operadora, tag, placa, saldo_rs, validade) VALUES (?, ?, ?, ?, ?, ?)",
        [(v.id, v.operadora, v.tag, v.placa, v.saldo_rs, v.validade) for v in sementes.VALES],
    )
    conn.executemany(
        """INSERT OR IGNORE INTO tarifas_pedagio
           (praca, valor_rs, vigente_de, vigente_ate) VALUES (?, ?, ?, ?)""",
        [(t.praca, t.valor_rs, t.vigente_de, t.vigente_ate) for t in sementes.TARIFAS],
    )
