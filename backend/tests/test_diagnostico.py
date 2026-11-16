from datetime import date

from app.data import sementes
from app.domain import Aresta, No, ValePedagio
from app.services.diagnostico import diagnosticar
from app.services.grafo import Grafo

HOJE = date(2026, 11, 16)


def _diagnostico(**kwargs):
    base = dict(
        grafo=Grafo(sementes.NOS, sementes.ARESTAS),
        veiculos=sementes.VEICULOS,
        vales=sementes.VALES,
        simulacoes=[],
        execucoes=[],
        hoje=HOJE,
    )
    base.update(kwargs)
    return diagnosticar(**base)


def test_encontra_revisao_vencida_do_seed():
    codigos = [a.codigo for a in _diagnostico()]
    assert "REVISAO_VENCIDA" in codigos


def test_encontra_no_isolado():
    grafo = Grafo(
        [No("A", "A", "S", "exata", 0, 0), No("B", "B", "S", "exata", 0, 0)],
        [Aresta("A", "A", 1, 0, 10)],
    )
    avisos = _diagnostico(grafo=grafo, veiculos=[], vales=[])
    assert any(a.codigo == "TRECHO_INALCANCAVEL" for a in avisos)


def test_encontra_vpo_vencido():
    vale = ValePedagio("v", "Op", "TAG", "ABC1D23", 100, "2026-01-01")
    avisos = _diagnostico(veiculos=[], vales=[vale])
    assert "VPO_VENCIDO" in [a.codigo for a in avisos]


def test_simulacao_antiga_sem_execucao():
    simulacoes = [
        {
            "id": "sim-1",
            "created_at": "2026-11-01T10:00:00+00:00",
            "payload": {"veiculo_id": "vuc-01"},
            "resultado": {"distancia_km": 100},
        }
    ]
    avisos = _diagnostico(veiculos=[], vales=[], simulacoes=simulacoes)
    assert "EXECUCAO_NAO_REGISTRADA" in [a.codigo for a in avisos]


def test_desvio_recorrente_em_duas_execucoes():
    simulacoes = [
        {
            "id": "sim-1",
            "created_at": "2026-11-15T10:00:00+00:00",
            "payload": {"veiculo_id": "vuc-01"},
            "resultado": {"distancia_km": 100},
        },
        {
            "id": "sim-2",
            "created_at": "2026-11-15T11:00:00+00:00",
            "payload": {"veiculo_id": "vuc-01"},
            "resultado": {"distancia_km": 100},
        },
    ]
    execucoes = [
        {"simulacao_id": "sim-1", "km_real": 130},
        {"simulacao_id": "sim-2", "km_real": 125},
    ]
    avisos = _diagnostico(veiculos=[], vales=[], simulacoes=simulacoes, execucoes=execucoes)
    recorrente = [a for a in avisos if a.codigo == "DESVIO_ROTA_RECORRENTE"]
    assert recorrente and recorrente[0].detalhe["execucoes"] == 2
