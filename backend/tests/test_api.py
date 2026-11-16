import pytest
from fastapi.testclient import TestClient

from app.main import criar_app


@pytest.fixture()
def client(tmp_path):
    app = criar_app(str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def _payload(**kwargs):
    base = {
        "origem_id": "sao-paulo",
        "paradas": [
            {
                "no_id": "guarulhos",
                "janela_inicio": "09:00",
                "janela_fim": "12:00",
                "peso_kg": 400,
                "prioridade": 8,
            },
            {
                "no_id": "osasco",
                "janela_inicio": "10:00",
                "janela_fim": "14:00",
                "peso_kg": 300,
                "prioridade": 5,
            },
        ],
        "veiculo_id": "vuc-01",
        "motorista_id": "mot-01",
        "perfil_id": "last-mile-metropolitana",
        "placa": "ABC1D23",
        "receita_rs": 1800,
        "modo_pedagio": "vpo",
        "vpo_id": "vpo-01",
    }
    base.update(kwargs)
    return base


def test_health(client):
    resposta = client.get("/api/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_seed_tem_doze_nos(client):
    assert len(client.get("/api/nos").json()) == 12


def test_simulacao_feliz_calcula_diesel_corretamente(client):
    resposta = client.post("/api/simular", json=_payload())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] in {"aprovada", "aprovada_com_avisos"}
    assert corpo["ordem"] == ["osasco", "guarulhos"]
    assert corpo["distancia_km"] == 60.0
    assert corpo["custos"]["diesel_rs"] == 38.53
    assert corpo["id"].startswith("sim-")


def test_no_inexistente_retorna_422_com_codigo(client):
    resposta = client.post("/api/simular", json=_payload(origem_id="atlantida"))
    assert resposta.status_code == 422
    assert resposta.json()["detail"]["codigo"] == "NO_NAO_EXISTE"


def test_veiculo_com_revisao_vencida_e_rejeitado(client):
    resposta = client.post(
        "/api/simular",
        json=_payload(veiculo_id="carreta-02", motorista_id="mot-02"),
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "rejeitada"
    assert "REVISAO_VENCIDA" in [a["codigo"] for a in corpo["avisos"]]


def test_vpo_sem_saldo_rejeita_rota_com_pedagio_alto(client):
    resposta = client.post(
        "/api/simular",
        json=_payload(
            paradas=[{"no_id": "ribeirao-preto", "peso_kg": 1000}],
            veiculo_id="truck-01",
            motorista_id="mot-02",
            perfil_id="corredor-interior",
            placa="XYZ9K88",
            vpo_id="vpo-02",
        ),
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "rejeitada"
    assert "VPO_SALDO_INSUFICIENTE" in [a["codigo"] for a in corpo["avisos"]]


def test_parada_fora_do_setor_rejeita_perfil_metropolitano(client):
    resposta = client.post(
        "/api/simular",
        json=_payload(paradas=[{"no_id": "campinas", "peso_kg": 1000}]),
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "rejeitada"
    assert "DESVIO_SETOR" in [a["codigo"] for a in corpo["avisos"]]


def test_comparativo_exige_execucao_e_depois_compara(client):
    sim = client.post("/api/simular", json=_payload()).json()
    sim_id = sim["id"]

    sem_execucao = client.get(f"/api/simulacoes/{sim_id}/comparativo")
    assert sem_execucao.status_code == 404
    assert sem_execucao.json()["detail"]["codigo"] == "EXECUCAO_NAO_REGISTRADA"

    execucao = client.post(
        "/api/execucoes",
        json={
            "simulacao_id": sim_id,
            "km_real": 72,
            "diesel_real": 50,
            "pedagio_real": 0,
            "tempo_real_h": 1.8,
            "rota_executada": ["sao-paulo", "osasco", "guarulhos"],
        },
    )
    assert execucao.status_code == 201

    comparativo = client.get(f"/api/simulacoes/{sim_id}/comparativo")
    assert comparativo.status_code == 200
    corpo = comparativo.json()["comparativo"]
    assert corpo["desvio_km"] == 12
    assert corpo["classificacao"] == "critico"


def test_execucao_duplicada_retorna_409(client):
    sim = client.post("/api/simular", json=_payload()).json()
    corpo = {
        "simulacao_id": sim["id"],
        "km_real": 60,
        "diesel_real": 38.53,
        "pedagio_real": 0,
        "tempo_real_h": 1.33,
        "rota_executada": ["sao-paulo", "osasco", "guarulhos"],
    }
    assert client.post("/api/execucoes", json=corpo).status_code == 201
    assert client.post("/api/execucoes", json=corpo).status_code == 409


def test_diagnostico_encontra_revisao_vencida_do_seed(client):
    resposta = client.get("/api/diagnostico")
    assert resposta.status_code == 200
    assert "REVISAO_VENCIDA" in resposta.json()["por_codigo"]


def test_geocodificacao_sem_divergencia(client):
    no = next(n for n in client.get("/api/nos").json() if n["id"] == "sao-paulo")
    resposta = client.post(
        "/api/geocodificacao/validar",
        json={"no_id": "sao-paulo", "lat": no["lat"], "lon": no["lon"]},
    )
    assert resposta.status_code == 200
    assert resposta.json()["avisos"] == []


def test_geocodificacao_com_divergencia(client):
    no = next(n for n in client.get("/api/nos").json() if n["id"] == "sao-paulo")
    resposta = client.post(
        "/api/geocodificacao/validar",
        json={"no_id": "sao-paulo", "lat": no["lat"] + 0.01, "lon": no["lon"]},
    )
    assert resposta.status_code == 200
    assert [a["codigo"] for a in resposta.json()["avisos"]] == ["COORDENADAS_DIVERGENTES"]


def test_conciliacao_de_pedagio_sem_lancamento(client):
    sim = client.post(
        "/api/simular",
        json=_payload(paradas=[{"no_id": "campinas", "peso_kg": 1000}]),
    ).json()
    resposta = client.get(f"/api/simulacoes/{sim['id']}/pedagio")
    assert resposta.status_code == 200
    codigos = [a["codigo"] for a in resposta.json()["avisos"]]
    assert "PEDAGIO_DIVERGENTE" in codigos
