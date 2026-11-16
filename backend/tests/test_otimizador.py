import pytest

from app.data import sementes
from app.domain import Parada
from app.services.grafo import Grafo
from app.services.otimizador import LIMITE_PARADAS, otimizar
from app.services.supermatrix import SuperMatrix


def _contexto():
    grafo = Grafo(sementes.NOS, sementes.ARESTAS)
    paradas = [
        Parada("guarulhos", "09:00", "12:00", 400, 8, 15),
        Parada("osasco", "10:00", "14:00", 300, 5, 15),
    ]
    matriz = SuperMatrix(grafo, ["sao-paulo", "guarulhos", "osasco"])
    perfil = sementes.PERFIS[0]
    setores = {n.id: n.setor_id for n in sementes.NOS}
    return grafo, paradas, matriz, perfil, setores


def test_escolhe_ordem_de_menor_distancia_respeitando_janelas():
    _, paradas, matriz, perfil, setores = _contexto()
    resultado = otimizar("sao-paulo", paradas, matriz, perfil, setores)
    assert resultado.ordem == ["osasco", "guarulhos"]
    assert resultado.distancia_km == 60.0
    assert resultado.tempo_h == pytest.approx(60 / 45, abs=1e-4)
    assert resultado.tempo_total_h == pytest.approx(207.333 / 60, abs=1e-3)
    assert resultado.violacao_janela_min == 0


def test_prioridade_alta_aceita_km_maior_para_nao_perder_janela():
    _, _, matriz, perfil, setores = _contexto()
    paradas = [
        Parada("guarulhos", "08:00", "08:10", 400, 9, 15),
        Parada("osasco", "10:00", "14:00", 300, 5, 15),
    ]
    resultado = otimizar("sao-paulo", paradas, matriz, perfil, setores)
    assert resultado.ordem[0] == "guarulhos"
    assert resultado.violacao_janela_min > 0


def test_limite_de_oito_paradas_e_erro_explicito():
    _, _, matriz, perfil, setores = _contexto()
    paradas = [Parada("osasco", peso_kg=1) for _ in range(LIMITE_PARADAS + 1)]
    with pytest.raises(ValueError, match="LIMITE_PARADAS"):
        otimizar("sao-paulo", paradas, matriz, perfil, setores)


def test_retorno_a_origem_soma_km():
    _, paradas, matriz, perfil, setores = _contexto()
    sem_volta = otimizar("sao-paulo", paradas, matriz, perfil, setores)
    com_volta = otimizar("sao-paulo", paradas, matriz, perfil, setores, retornar_origem=True)
    assert com_volta.distancia_km > sem_volta.distancia_km
