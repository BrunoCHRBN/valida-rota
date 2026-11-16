"""Seed determinístico do corredor sintético Santos–São Paulo–Campinas–Ribeirão Preto.

Distâncias, tarifas e velocidades são plausíveis, não medidas contra fonte
externa. O seed existe para tornar o resultado reproduzível em teste.
"""

from __future__ import annotations

from app.domain import Aresta, Motorista, No, Perfil, TarifaPedagio, ValePedagio, Veiculo

PRECO_DIESEL_RS_L = 6.10
PERFIL_PADRAO = "last-mile-metropolitana"

NOS = [
    No("santos", "Santos", "LITORAL", "exata", -23.9608, -46.3336),
    No("cubatao", "Cubatão", "LITORAL", "exata", -23.8953, -46.4256),
    No("sao-paulo", "São Paulo", "METROPOLITANA", "exata", -23.5505, -46.6333),
    No("guarulhos", "Guarulhos", "METROPOLITANA", "alta", -23.4538, -46.5333),
    No("osasco", "Osasco", "METROPOLITANA", "alta", -23.5325, -46.7917),
    No("jundiai", "Jundiaí", "INTERIOR", "alta", -23.1864, -46.8842),
    No("campinas", "Campinas", "INTERIOR", "exata", -22.9099, -47.0626),
    No("limeira", "Limeira", "INTERIOR", "alta", -22.5647, -47.4017),
    No("piracicaba", "Piracicaba", "INTERIOR", "ambigua", -22.7253, -47.6492),
    No("sorocaba", "Sorocaba", "INTERIOR", "media", -23.5015, -47.4526),
    No("sao-carlos", "São Carlos", "INTERIOR", "alta", -22.0174, -47.8908),
    No("ribeirao-preto", "Ribeirão Preto", "INTERIOR", "exata", -21.1704, -47.8103),
]


def _par(
    de: str,
    para: str,
    km: float,
    pedagio: float,
    velocidade: float,
    praca: str | None = None,
) -> list[Aresta]:
    return [
        Aresta(de, para, km, pedagio, velocidade, praca),
        Aresta(para, de, km, pedagio, velocidade, praca),
    ]


ARESTAS: list[Aresta] = [
    *_par("santos", "cubatao", 24.5, 0.0, 50.0),
    *_par("santos", "sao-paulo", 71.0, 12.40, 70.0, "Imigrantes"),
    *_par("cubatao", "sao-paulo", 58.0, 12.40, 65.0, "Anchieta"),
    *_par("sao-paulo", "guarulhos", 26.0, 0.0, 45.0),
    *_par("sao-paulo", "osasco", 17.0, 0.0, 45.0),
    *_par("sao-paulo", "jundiai", 58.0, 9.80, 80.0, "Anhanguera"),
    *_par("jundiai", "campinas", 44.0, 8.40, 90.0, "Bandeirantes"),
    *_par("sao-paulo", "campinas", 96.0, 18.20, 90.0, "Bandeirantes"),
    *_par("campinas", "limeira", 54.0, 7.60, 90.0, "Anhanguera"),
    *_par("campinas", "piracicaba", 63.0, 7.90, 80.0, "Piracicaba"),
    *_par("limeira", "sao-carlos", 74.0, 9.40, 90.0, "Anhanguera"),
    *_par("sao-carlos", "ribeirao-preto", 99.0, 11.80, 100.0, "Anhanguera"),
    *_par("campinas", "ribeirao-preto", 218.0, 24.60, 100.0, "Anhanguera"),
    *_par("sao-paulo", "sorocaba", 99.0, 11.20, 90.0, "Castelo Branco"),
    *_par("sorocaba", "campinas", 88.0, 9.90, 90.0, "Dom Pedro"),
    *_par("sorocaba", "sao-carlos", 121.0, 10.80, 90.0, "Castelo Branco"),
    *_par("jundiai", "sorocaba", 84.0, 8.10, 80.0, "Dom Pedro"),
    *_par("piracicaba", "sao-carlos", 69.0, 8.20, 90.0, "SP-127"),
]

VEICULOS = [
    Veiculo("vuc-01", "VUC 01", "VUC", 9.5, 0.42, 0.18, 1500, 42000, 45000),
    Veiculo("toco-01", "Toco 01", "Toco", 6.8, 0.55, 0.24, 3500, 88000, 92000),
    Veiculo("truck-01", "Truck 01", "Truck", 4.2, 0.72, 0.31, 8000, 152000, 160000),
    Veiculo("semi-01", "Semi-Leve 01", "Semi-Leve", 3.1, 0.86, 0.38, 14000, 210000, 225000),
    Veiculo("carreta-01", "Carreta 01", "Carreta", 2.6, 1.05, 0.45, 25000, 320000, 340000),
    Veiculo("carreta-02", "Carreta 02 (revisão vencida)", "Carreta", 2.6, 1.05, 0.45, 25000, 341500, 340000),
]

MOTORISTAS = [
    Motorista("mot-01", "Ana Ribeiro", 42.0, 8.0),
    Motorista("mot-02", "Carlos Menezes", 48.0, 10.0),
]

PERFIS = [
    Perfil(
        "last-mile-metropolitana",
        "Last mile metropolitana",
        "METROPOLITANA",
        mu=22.0,
        nu=8.0,
        xi=0.45,
        ocupacao_minima_pct=55.0,
        raio_setor_km=45.0,
        consumo_min_km_l=8.0,
        consumo_max_km_l=12.0,
        permitir_multiplos_setores=False,
    ),
    Perfil(
        "corredor-interior",
        "Corredor interior",
        "INTERIOR",
        mu=16.0,
        nu=5.0,
        xi=0.25,
        ocupacao_minima_pct=40.0,
        raio_setor_km=180.0,
        consumo_min_km_l=2.4,
        consumo_max_km_l=7.5,
        permitir_multiplos_setores=True,
    ),
]

VALES = [
    ValePedagio("vpo-01", "Sem Parar", "TAG-001", "ABC1D23", 480.0, "2027-06-30"),
    ValePedagio("vpo-02", "Veloe", "TAG-002", "XYZ9K88", 35.0, "2026-12-31"),
]

TARIFAS = [
    TarifaPedagio("Imigrantes", 12.40, "2026-01-01", None),
    TarifaPedagio("Anchieta", 12.40, "2026-01-01", None),
    TarifaPedagio("Anhanguera", 9.80, "2026-01-01", None),
    TarifaPedagio("Bandeirantes", 18.20, "2026-01-01", None),
    TarifaPedagio("Piracicaba", 7.90, "2026-01-01", None),
    TarifaPedagio("Castelo Branco", 11.20, "2026-01-01", None),
    TarifaPedagio("Dom Pedro", 9.90, "2026-01-01", None),
    TarifaPedagio("SP-127", 8.20, "2026-01-01", None),
]
