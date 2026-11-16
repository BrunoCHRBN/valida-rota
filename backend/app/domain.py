"""Tipos de domínio compartilhados pelos serviços puros.

Nada aqui importa FastAPI ou sqlite: os serviços recebem estes objetos e
devolvem resultados determinísticos, o que permite testar regra por regra.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severidade = Literal["aviso", "rejeicao"]
StatusGate = Literal["aprovada", "aprovada_com_avisos", "rejeitada"]
ModoPedagio = Literal["vpo", "proprio", "embutido_no_frete"]


@dataclass(frozen=True)
class No:
    id: str
    nome: str
    setor_id: str
    qualidade_geo: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Aresta:
    de: str
    para: str
    km: float
    pedagio_rs: float
    velocidade_media_km_h: float
    praca: str | None = None


@dataclass(frozen=True)
class Veiculo:
    id: str
    nome: str
    perfil: str
    consumo_km_l: float
    depreciacao_rs_km: float
    manutencao_rs_km: float
    capacidade_kg: float
    km_atual: float
    km_proxima_revisao: float
    disponivel: bool = True


@dataclass(frozen=True)
class Motorista:
    id: str
    nome: str
    custo_hora: float
    jornada_max_h: float


@dataclass(frozen=True)
class Perfil:
    id: str
    nome: str
    setor_id: str
    mu: float
    nu: float
    xi: float
    ocupacao_minima_pct: float
    raio_setor_km: float
    consumo_min_km_l: float
    consumo_max_km_l: float
    permitir_multiplos_setores: bool


@dataclass(frozen=True)
class Parada:
    no_id: str
    janela_inicio: str | None = None
    janela_fim: str | None = None
    peso_kg: float = 0.0
    prioridade: int = 0
    minutos_servico: int = 15


@dataclass(frozen=True)
class ValePedagio:
    id: str
    operadora: str
    tag: str
    placa: str
    saldo_rs: float
    validade: str  # ISO date


@dataclass(frozen=True)
class LancamentoPedagio:
    id: str
    vale_id: str
    praca: str
    valor_rs: float
    data: str
    tag: str


@dataclass(frozen=True)
class TarifaPedagio:
    praca: str
    valor_rs: float
    vigente_de: str
    vigente_ate: str | None


@dataclass(frozen=True)
class Trecho:
    km: float
    horas: float
    pedagio_rs: float
    caminho: tuple[str, ...]
    pracas: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Aviso:
    codigo: str
    severidade: Severidade
    mensagem: str
    detalhe: dict = field(default_factory=dict)
    entidade: str | None = None


@dataclass(frozen=True)
class ResultadoOtimizacao:
    ordem: list[str]
    chegadas: dict[str, str]
    distancia_km: float
    tempo_h: float
    pedagio_rs: float
    violacao_janela_min: float
    penalidade_prioridade: float
    desvio_setor_km: float
    score: float
    pracas: dict[str, float]
    tempo_total_h: float = 0.0


@dataclass(frozen=True)
class ResultadoCusto:
    diesel_rs: float
    pedagio_rs: float
    depreciacao_rs: float
    manutencao_rs: float
    motorista_rs: float
    total_rs: float
    pedagio_coberto_rs: float
    margem_rs: float
    margem_pct: float
    custo_logistico_embarcador_rs: float
    extra_revisao_rs: float
