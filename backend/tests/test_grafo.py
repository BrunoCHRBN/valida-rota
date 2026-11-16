from app.domain import Aresta, No
from app.services.grafo import Grafo


def _no(no_id: str) -> No:
    return No(no_id, no_id, "S", "exata", 0.0, 0.0)


def _grafo() -> Grafo:
    nos = [_no("A"), _no("B"), _no("C"), _no("D"), _no("E")]
    arestas = [
        Aresta("A", "B", 10, 25, 60),
        Aresta("B", "D", 10, 0, 60),
        Aresta("A", "C", 20, 0, 60),
        Aresta("C", "D", 20, 0, 60),
    ]
    return Grafo(nos, arestas)


def test_menor_caminho_por_km():
    trecho = _grafo().dijkstra("A", "D")
    assert trecho is not None
    assert trecho.km == 20
    assert trecho.pedagio_rs == 25
    assert trecho.caminho == ("A", "B", "D")
    assert round(trecho.horas, 4) == round(20 / 60, 4)


def test_evitar_pedagio_escolhe_rota_mais_longa_sem_tarifa():
    trecho = _grafo().dijkstra("A", "D", evitar_pedagio=True, lambda_pedagio=1.0)
    assert trecho is not None
    assert trecho.km == 40
    assert trecho.pedagio_rs == 0
    assert trecho.caminho == ("A", "C", "D")


def test_trecho_inalcancavel_retorna_none():
    assert _grafo().dijkstra("A", "E") is None


def test_alcancaveis_nao_inclui_no_isolado():
    assert _grafo().alcancaveis("A") == {"A", "B", "C", "D"}


def test_aresta_com_velocidade_zero_e_incompleta():
    grafo = Grafo([_no("A"), _no("B")], [Aresta("A", "B", 10, 0, 0)])
    assert len(grafo.arestas_incompletas()) == 1


def test_origem_igual_destino_devolve_trecho_vazio():
    trecho = _grafo().dijkstra("A", "A")
    assert trecho is not None
    assert trecho.km == 0
    assert trecho.caminho == ("A",)
