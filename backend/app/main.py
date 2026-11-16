"""Aplicação FastAPI do ValidaRota."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import db
from app.api import routes_analise, routes_cadastro, routes_simulacao


def _diretorio_do_bundle() -> Path:
    """Bundle do frontend, quando existir.

    Em desenvolvimento o Vite serve na 5173 e esta pasta pode não existir; em
    produção o mesmo processo entrega API e interface, o que dispensa CORS e
    transforma o deploy em um artefato só.
    """
    if override := os.environ.get("VALIDA_ROTA_DIST"):
        return Path(override).resolve()
    return Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def criar_app(db_path: str | None = None) -> FastAPI:
    caminho = (
        db_path
        or os.environ.get("VALIDA_ROTA_DB")
        or str(Path(__file__).resolve().parent.parent / "valida_rota.db")
    )
    db.inicializar(caminho)

    app = FastAPI(
        title="ValidaRota",
        description="Gate de aceitação de rotas rodoviárias: valida antes de emplacar.",
        version="0.1.0",
    )
    app.state.db_path = str(caminho)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(routes_cadastro.router)
    app.include_router(routes_simulacao.router)
    app.include_router(routes_analise.router)

    # Montado por último: as rotas /api e /docs, registradas antes, continuam
    # tendo precedência sobre o catch-all do bundle.
    bundle = _diretorio_do_bundle()
    if (bundle / "index.html").is_file():
        app.mount("/", StaticFiles(directory=bundle, html=True), name="interface")

    return app


app = criar_app()
