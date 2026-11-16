from app.domain import Motorista, Veiculo
from app.services.custo import calcular

VEICULO = Veiculo("v", "V", "Toco", 10.0, 0.5, 0.2, 1000, 1000, 5000)
MOTORISTA = Motorista("m", "M", 40.0, 8.0)


def _calcular(**kwargs):
    base = dict(
        km=100.0,
        horas=2.0,
        pedagio_rs=10.0,
        veiculo=VEICULO,
        motorista=MOTORISTA,
        receita_rs=300.0,
        preco_diesel_rs_l=6.0,
        modo_pedagio="proprio",
    )
    base.update(kwargs)
    return calcular(**base)


def test_diesel_usa_divisao_pelo_consumo():
    custo = _calcular()
    assert custo.diesel_rs == 60.0  # 100 km / 10 km/l * 6,00
    assert custo.total_rs == 220.0  # 60 + 10 + 50 + 20 + 80
    assert custo.margem_rs == 80.0
    assert custo.margem_pct == 26.67


def test_vpo_remove_pedagio_do_custo_da_transportadora():
    custo = _calcular(modo_pedagio="vpo", vpo_consumido_rs=10.0)
    assert custo.pedagio_coberto_rs == 10.0
    assert custo.margem_rs == 90.0
    assert custo.custo_logistico_embarcador_rs == 310.0


def test_revisao_ultrapassada_adiciona_extra():
    custo = _calcular(km=4500.0, horas=1.0)
    assert custo.extra_revisao_rs == 450.0
    assert custo.manutencao_rs == 4500 * 0.2 + 450.0


def test_diesel_real_sobrescreve_formula_no_comparativo():
    custo = _calcular(diesel_rs=123.45)
    assert custo.diesel_rs == 123.45
