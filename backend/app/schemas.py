"""Contratos de entrada da API."""

from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class ParadaIn(BaseModel):
    no_id: str = Field(min_length=1)
    janela_inicio: str | None = None
    janela_fim: str | None = None
    peso_kg: float = Field(default=0.0, ge=0)
    prioridade: int = Field(default=0, ge=0, le=9)
    minutos_servico: int = Field(default=15, ge=0, le=240)

    @field_validator("janela_inicio", "janela_fim")
    @classmethod
    def validar_hora(cls, valor: str | None) -> str | None:
        if valor is not None and not HORA.match(valor):
            raise ValueError("horário deve estar no formato HH:MM")
        return valor


class SimulacaoIn(BaseModel):
    origem_id: str = Field(min_length=1)
    paradas: list[ParadaIn] = Field(min_length=1, max_length=8)
    veiculo_id: str
    motorista_id: str
    perfil_id: str
    placa: str = Field(min_length=7, max_length=8)
    receita_rs: float = Field(ge=0)
    modo_pedagio: Literal["vpo", "proprio", "embutido_no_frete"] = "proprio"
    vpo_id: str | None = None
    evitar_pedagio: bool = False
    retornar_origem: bool = False
    partida: str = "08:00"
    data_viagem: date | None = None

    @field_validator("placa")
    @classmethod
    def normalizar_placa(cls, valor: str) -> str:
        return valor.replace("-", "").upper()

    @field_validator("partida")
    @classmethod
    def validar_partida(cls, valor: str) -> str:
        if not HORA.match(valor):
            raise ValueError("partida deve estar no formato HH:MM")
        return valor


class ExecucaoIn(BaseModel):
    simulacao_id: str
    km_real: float = Field(gt=0)
    diesel_real: float = Field(ge=0)
    pedagio_real: float = Field(ge=0)
    tempo_real_h: float = Field(gt=0)
    rota_executada: list[str] = Field(min_length=1)


class VeiculoIn(BaseModel):
    id: str
    nome: str
    perfil: str
    consumo_km_l: float = Field(gt=0)
    depreciacao_rs_km: float = Field(ge=0)
    manutencao_rs_km: float = Field(ge=0)
    capacidade_kg: float = Field(gt=0)
    km_atual: float = Field(ge=0)
    km_proxima_revisao: float = Field(gt=0)
    disponivel: bool = True


class PerfilIn(BaseModel):
    id: str
    nome: str
    setor_id: str
    mu: float = Field(ge=0)
    nu: float = Field(ge=0)
    xi: float = Field(ge=0)
    ocupacao_minima_pct: float = Field(ge=0, le=100)
    raio_setor_km: float = Field(gt=0)
    consumo_min_km_l: float = Field(gt=0)
    consumo_max_km_l: float = Field(gt=0)
    permitir_multiplos_setores: bool = True


class ValeIn(BaseModel):
    id: str
    operadora: str
    tag: str
    placa: str
    saldo_rs: float = Field(ge=0)
    validade: date

    @field_validator("placa")
    @classmethod
    def normalizar_placa(cls, valor: str) -> str:
        return valor.replace("-", "").upper()


class LancamentoIn(BaseModel):
    id: str
    vale_id: str
    praca: str
    valor_rs: float = Field(ge=0)
    data: date
    tag: str


class GeocodificacaoIn(BaseModel):
    no_id: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    qualidade: Literal["exata", "alta", "media", "baixa", "ambigua", "fornecida_usuario"] = "alta"
    raio_max_m: float = Field(default=150.0, gt=0, le=5000)
