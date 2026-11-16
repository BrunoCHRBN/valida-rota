from app.domain import LancamentoPedagio, TarifaPedagio
from app.services.comparativo import comparar
from app.services.pedagio import conciliar


def test_comparativo_dentro_da_faixa():
    resultado = comparar(
        km_previsto=100,
        custo_previsto_rs=1000,
        km_real=102,
        custo_real_rs=1030,
    )
    assert resultado["desvio_km"] == 2
    assert resultado["desvio_km_pct"] == 2.0
    assert resultado["classificacao"] == "dentro"


def test_comparativo_critico_acima_de_quinze_por_cento():
    resultado = comparar(
        km_previsto=100,
        custo_previsto_rs=1000,
        km_real=120,
        custo_real_rs=1100,
    )
    assert resultado["classificacao"] == "critico"


def test_comparativo_com_base_zero_nao_divide_por_zero():
    resultado = comparar(km_previsto=0, custo_previsto_rs=0, km_real=10, custo_real_rs=20)
    assert resultado["desvio_km_pct"] == 0.0
    assert resultado["desvio_custo_pct"] == 0.0


def test_pedagio_divergente():
    avisos = conciliar(
        previstos={"Anhanguera": 9.80},
        lancamentos=[
            LancamentoPedagio("l1", "v1", "Anhanguera", 12.00, "2026-11-16", "TAG-1")
        ],
        tarifas=[TarifaPedagio("Anhanguera", 9.80, "2026-01-01", None)],
        data_viagem="2026-11-16",
    )
    assert [a.codigo for a in avisos] == ["PEDAGIO_DIVERGENTE"]
    assert avisos[0].detalhe["diferenca_rs"] == 2.2


def test_praca_cobrada_fora_da_rota():
    avisos = conciliar(
        previstos={"Anhanguera": 9.80},
        lancamentos=[
            LancamentoPedagio("l1", "v1", "Anhanguera", 9.80, "2026-11-16", "TAG-1"),
            LancamentoPedagio("l2", "v1", "Imigrantes", 12.40, "2026-11-16", "TAG-1"),
        ],
        tarifas=[],
        data_viagem="2026-11-16",
    )
    assert [a.codigo for a in avisos] == ["PRACA_NAO_PREVISTA"]


def test_tarifa_vigente_divergente_do_grafo():
    avisos = conciliar(
        previstos={"Bandeirantes": 18.20},
        lancamentos=[
            LancamentoPedagio("l1", "v1", "Bandeirantes", 18.20, "2026-11-16", "TAG-1")
        ],
        tarifas=[TarifaPedagio("Bandeirantes", 19.90, "2026-01-01", None)],
        data_viagem="2026-11-16",
    )
    assert [a.codigo for a in avisos] == ["TARIFA_DIVERGENTE"]
