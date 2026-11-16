from datetime import date

from app.data import sementes
from app.domain import Aresta, Motorista, No, Parada, ResultadoOtimizacao, Veiculo
from app.services.grafo import Grafo
from app.services.validacao import (
    consolidar,
    validar_cadastro,
    validar_geocodificacao,
    validar_operacao,
    validar_vpo,
)

VEICULO = Veiculo("vuc-01", "VUC 01", "VUC", 9.5, 0.42, 0.18, 1500, 42000, 45000)
MOTORISTA = Motorista("mot-01", "Ana", 42.0, 8.0)
PERFIL = sementes.PERFIS[0]
SETORES = {n.id: n.setor_id for n in sementes.NOS}


def _resultado(**kwargs) -> ResultadoOtimizacao:
    base = dict(
        ordem=["guarulhos"],
        chegadas={"guarulhos": "09:00"},
        distancia_km=60.0,
        tempo_h=1.5,
        pedagio_rs=10.0,
        violacao_janela_min=0.0,
        penalidade_prioridade=0.0,
        desvio_setor_km=0.0,
        score=60.0,
        pracas={},
    )
    base.update(kwargs)
    return ResultadoOtimizacao(**base)


def test_origem_inexistente_gera_no_nao_existe():
    grafo = Grafo(sementes.NOS, sementes.ARESTAS)
    avisos = validar_cadastro("atlantida", [Parada("guarulhos")], grafo)
    assert [a.codigo for a in avisos] == ["NO_NAO_EXISTE"]


def test_aresta_incompleta_gera_alerta_de_rejeicao():
    grafo = Grafo(
        [No("A", "A", "S", "exata", 0, 0), No("B", "B", "S", "exata", 0, 0)],
        [Aresta("A", "B", 10, 0, 0)],
    )
    avisos = validar_cadastro("A", [Parada("B")], grafo)
    assert avisos[0].codigo == "ARESTA_INCOMPLETA"
    assert avisos[0].severidade == "rejeicao"


def test_no_sem_aresta_gera_trecho_inalcancavel():
    grafo = Grafo(
        [No("A", "A", "S", "exata", 0, 0), No("B", "B", "S", "exata", 0, 0)],
        [],
    )
    avisos = validar_cadastro("A", [Parada("B")], grafo)
    assert avisos[0].codigo == "TRECHO_INALCANCAVEL"


def test_parada_repetida_gera_dados_divergentes():
    grafo = Grafo(sementes.NOS, sementes.ARESTAS)
    avisos = validar_cadastro(
        "sao-paulo",
        [Parada("guarulhos"), Parada("guarulhos")],
        grafo,
    )
    assert [a.codigo for a in avisos] == ["DADOS_DIVERGENTES"]


def test_qualidade_ambigua_gera_geocodificacao_baixa():
    no = No("x", "X", "S", "ambigua", 0, 0)
    avisos = validar_geocodificacao([no])
    assert avisos[0].codigo == "GEOCODIFICACAO_BAIXA"
    assert avisos[0].severidade == "aviso"


def test_revisao_vencida_considera_km_da_rota():
    veiculo = Veiculo("v", "V", "VUC", 9.5, 0.42, 0.18, 1500, 44950, 45000)
    avisos = validar_operacao(
        veiculo=veiculo,
        motorista=MOTORISTA,
        perfil=PERFIL,
        paradas=[Parada("guarulhos", peso_kg=1000)],
        setores=SETORES,
        resultado=_resultado(distancia_km=100),
        peso_total_kg=1000,
    )
    assert "REVISAO_VENCIDA" in [a.codigo for a in avisos]


def test_jornada_excedida():
    avisos = validar_operacao(
        veiculo=VEICULO,
        motorista=MOTORISTA,
        perfil=PERFIL,
        paradas=[Parada("guarulhos", peso_kg=1000)],
        setores=SETORES,
        resultado=_resultado(tempo_h=8.5),
        peso_total_kg=1000,
    )
    assert "JORNADA_EXCEDIDA" in [a.codigo for a in avisos]


def test_ocupacao_baixa_e_aviso_nao_rejeicao():
    avisos = validar_operacao(
        veiculo=VEICULO,
        motorista=MOTORISTA,
        perfil=PERFIL,
        paradas=[Parada("guarulhos", peso_kg=100)],
        setores=SETORES,
        resultado=_resultado(),
        peso_total_kg=100,
    )
    ocupacao = [a for a in avisos if a.codigo == "OCUPACAO_BAIXA"]
    assert ocupacao and ocupacao[0].severidade == "aviso"


def test_desvio_de_setor_rejeita_quando_perfil_nao_permite():
    avisos = validar_operacao(
        veiculo=VEICULO,
        motorista=MOTORISTA,
        perfil=PERFIL,
        paradas=[Parada("campinas", peso_kg=1000)],
        setores=SETORES,
        resultado=_resultado(),
        peso_total_kg=1000,
    )
    desvio = [a for a in avisos if a.codigo == "DESVIO_SETOR"]
    assert desvio and desvio[0].severidade == "rejeicao"


def test_desvio_de_setor_e_aviso_quando_perfil_permite():
    perfil = sementes.PERFIS[1]
    avisos = validar_operacao(
        veiculo=VEICULO,
        motorista=MOTORISTA,
        perfil=perfil,
        paradas=[Parada("guarulhos", peso_kg=1000)],
        setores=SETORES,
        resultado=_resultado(),
        peso_total_kg=1000,
    )
    desvio = [a for a in avisos if a.codigo == "DESVIO_SETOR"]
    assert desvio and desvio[0].severidade == "aviso"


def test_vpo_com_saldo_insuficiente():
    vale = sementes.VALES[1]  # saldo 35
    avisos = validar_vpo(
        modo_pedagio="vpo",
        vpo=vale,
        placa="XYZ9K88",
        pedagio_previsto_rs=50.0,
        data_viagem=date(2026, 11, 16),
    )
    assert [a.codigo for a in avisos] == ["VPO_SALDO_INSUFICIENTE"]


def test_vpo_vencido():
    vale = sementes.VALES[0]
    avisos = validar_vpo(
        modo_pedagio="vpo",
        vpo=vale,
        placa="ABC1D23",
        pedagio_previsto_rs=10.0,
        data_viagem=date(2028, 1, 1),
    )
    assert "VPO_VENCIDO" in [a.codigo for a in avisos]


def test_tag_de_outra_placa():
    vale = sementes.VALES[0]
    avisos = validar_vpo(
        modo_pedagio="vpo",
        vpo=vale,
        placa="ZZZ9Z99",
        pedagio_previsto_rs=10.0,
        data_viagem=date(2026, 11, 16),
    )
    assert [a.codigo for a in avisos] == ["TAG_NAO_VINCULADO_A_PLACA"]


def test_pedagio_embutido_no_frete():
    avisos = validar_vpo(
        modo_pedagio="embutido_no_frete",
        vpo=None,
        placa="ABC1D23",
        pedagio_previsto_rs=10.0,
        data_viagem=date(2026, 11, 16),
    )
    assert [a.codigo for a in avisos] == ["PEDAGIO_EMBUTIDO_NO_FRETE"]


def test_consolidar_deduplica_e_define_status():
    aviso = validar_geocodificacao([No("x", "X", "S", "ambigua", 0, 0)])[0]
    status, avisos = consolidar([aviso, aviso])
    assert status == "aprovada_com_avisos"
    assert len(avisos) == 1
