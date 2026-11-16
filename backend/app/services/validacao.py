"""Gate único de aceitação: cadastro, operação, setor e VPO.

A mesma função é usada por `/api/simular` e pelos diagnósticos. Cada regra
devolve um `Aviso` com código estável, severidade, mensagem e evidência.
"""

from __future__ import annotations

import json
from datetime import date

from app.domain import (
    Aviso,
    Motorista,
    Parada,
    Perfil,
    ResultadoOtimizacao,
    ValePedagio,
    Veiculo,
)
from app.services.custo import consumo_em_faixa
from app.services.grafo import Grafo

QUALIDADES_FRAGEIS = {"baixa", "ambigua"}


def _aviso(
    codigo: str,
    severidade: str,
    mensagem: str,
    entidade: str | None = None,
    **detalhe: object,
) -> Aviso:
    return Aviso(
        codigo=codigo,
        severidade=severidade,  # type: ignore[arg-type]
        mensagem=mensagem,
        detalhe=detalhe,
        entidade=entidade,
    )


def validar_cadastro(origem: str, paradas: list[Parada], grafo: Grafo) -> list[Aviso]:
    avisos: list[Aviso] = []
    if origem not in grafo.nos:
        avisos.append(
            _aviso(
                "NO_NAO_EXISTE",
                "rejeicao",
                f"Origem '{origem}' não existe no cadastro de nós.",
                origem,
                campo="origem",
                no_id=origem,
            )
        )
    for parada in paradas:
        if parada.no_id not in grafo.nos:
            avisos.append(
                _aviso(
                    "NO_NAO_EXISTE",
                    "rejeicao",
                    f"Parada '{parada.no_id}' não existe no cadastro de nós.",
                    parada.no_id,
                    campo="parada",
                    no_id=parada.no_id,
                )
            )

    ids = [p.no_id for p in paradas]
    duplicadas = sorted({no_id for no_id in ids if ids.count(no_id) > 1})
    if duplicadas:
        avisos.append(
            _aviso(
                "DADOS_DIVERGENTES",
                "rejeicao",
                f"Há paradas repetidas na mesma rota: {', '.join(duplicadas)}.",
                campo="paradas",
                duplicadas=duplicadas,
            )
        )

    incompletas = grafo.arestas_incompletas()
    for aresta in incompletas:
        avisos.append(
            _aviso(
                "ARESTA_INCOMPLETA",
                "rejeicao",
                f"Aresta {aresta.de} → {aresta.para} sem km, velocidade ou pedágio válido.",
                f"{aresta.de}->{aresta.para}",
                de=aresta.de,
                para=aresta.para,
                km=aresta.km,
                velocidade_media_km_h=aresta.velocidade_media_km_h,
                pedagio_rs=aresta.pedagio_rs,
            )
        )

    if origem in grafo.nos and not avisos:
        alcancaveis = grafo.alcancaveis(origem)
        for parada in paradas:
            if parada.no_id not in alcancaveis:
                avisos.append(
                    _aviso(
                        "TRECHO_INALCANCAVEL",
                        "rejeicao",
                        f"Não há caminho de {origem} até {parada.no_id}.",
                        parada.no_id,
                        origem=origem,
                        destino=parada.no_id,
                    )
                )
    return avisos


def validar_geocodificacao(nos: list) -> list[Aviso]:
    avisos: list[Aviso] = []
    for no in nos:
        if no.qualidade_geo in QUALIDADES_FRAGEIS:
            avisos.append(
                _aviso(
                    "GEOCODIFICACAO_BAIXA",
                    "aviso",
                    f"Coordenada de {no.nome} tem qualidade '{no.qualidade_geo}'.",
                    no.id,
                    no_id=no.id,
                    qualidade=no.qualidade_geo,
                    fonte="sintetico",
                )
            )
    return avisos


def validar_operacao(
    *,
    veiculo: Veiculo,
    motorista: Motorista,
    perfil: Perfil,
    paradas: list[Parada],
    setores: dict[str, str],
    resultado: ResultadoOtimizacao,
    peso_total_kg: float,
) -> list[Aviso]:
    avisos: list[Aviso] = []

    if not veiculo.disponivel:
        avisos.append(
            _aviso(
                "DADOS_DIVERGENTES",
                "rejeicao",
                f"Veículo {veiculo.nome} está marcado como indisponível.",
                veiculo.id,
                campo="disponivel",
                veiculo_id=veiculo.id,
            )
        )

    if not consumo_em_faixa(veiculo, perfil):
        avisos.append(
            _aviso(
                "CONSUMO_FORA_FAIXA",
                "aviso",
                f"Consumo de {veiculo.consumo_km_l} km/l está fora da faixa do perfil {perfil.nome}.",
                veiculo.id,
                veiculo_id=veiculo.id,
                consumo_km_l=veiculo.consumo_km_l,
                faixa=[perfil.consumo_min_km_l, perfil.consumo_max_km_l],
            )
        )

    km_final = veiculo.km_atual + resultado.distancia_km
    if km_final > veiculo.km_proxima_revisao:
        avisos.append(
            _aviso(
                "REVISAO_VENCIDA",
                "rejeicao",
                f"A rota levaria {veiculo.nome} a {km_final:.0f} km, acima da revisão em {veiculo.km_proxima_revisao:.0f} km.",
                veiculo.id,
                veiculo_id=veiculo.id,
                km_atual=veiculo.km_atual,
                km_previsto=round(km_final, 1),
                km_proxima_revisao=veiculo.km_proxima_revisao,
            )
        )

    tempo_jornada = resultado.tempo_total_h or resultado.tempo_h
    if tempo_jornada > motorista.jornada_max_h:
        avisos.append(
            _aviso(
                "JORNADA_EXCEDIDA",
                "rejeicao",
                f"Jornada prevista de {tempo_jornada:.1f} h excede o limite de {motorista.jornada_max_h:.1f} h.",
                motorista.id,
                motorista_id=motorista.id,
                tempo_total_h=tempo_jornada,
                tempo_direcao_h=resultado.tempo_h,
                jornada_max_h=motorista.jornada_max_h,
            )
        )

    if veiculo.capacidade_kg > 0:
        ocupacao = peso_total_kg / veiculo.capacidade_kg * 100.0
        if ocupacao < perfil.ocupacao_minima_pct:
            avisos.append(
                _aviso(
                    "OCUPACAO_BAIXA",
                    "aviso",
                    f"Ocupação de {ocupacao:.1f}% abaixo do mínimo de {perfil.ocupacao_minima_pct:.1f}%.",
                    veiculo.id,
                    veiculo_id=veiculo.id,
                    ocupacao_pct=round(ocupacao, 1),
                    minimo_pct=perfil.ocupacao_minima_pct,
                )
            )

    for parada in paradas:
        setor_parada = setores.get(parada.no_id)
        if setor_parada and setor_parada != perfil.setor_id:
            severidade = "aviso" if perfil.permitir_multiplos_setores else "rejeicao"
            avisos.append(
                _aviso(
                    "DESVIO_SETOR",
                    severidade,
                    f"Parada {parada.no_id} está no setor {setor_parada}, fora de {perfil.setor_id}.",
                    parada.no_id,
                    no_id=parada.no_id,
                    setor_esperado=perfil.setor_id,
                    setor_parada=setor_parada,
                    multiplos_setores_permitidos=perfil.permitir_multiplos_setores,
                )
            )

    return avisos


def validar_vpo(
    *,
    modo_pedagio: str,
    vpo: ValePedagio | None,
    placa: str,
    pedagio_previsto_rs: float,
    data_viagem: date,
) -> list[Aviso]:
    avisos: list[Aviso] = []

    if modo_pedagio == "embutido_no_frete":
        avisos.append(
            _aviso(
                "PEDAGIO_EMBUTIDO_NO_FRETE",
                "aviso",
                "Frete com pedágio embutido: o custo não aparece separado do VPO.",
                detalhe={"modo_pedagio": modo_pedagio, "pedagio_rs": pedagio_previsto_rs},
            )
        )
        return avisos

    if modo_pedagio != "vpo":
        return avisos

    if vpo is None:
        avisos.append(
            _aviso(
                "DADOS_DIVERGENTES",
                "rejeicao",
                "Modo VPO selecionado sem vale-pedágio informado.",
                campo="vpo_id",
            )
        )
        return avisos

    if vpo.placa != placa:
        avisos.append(
            _aviso(
                "TAG_NAO_VINCULADO_A_PLACA",
                "rejeicao",
                f"TAG {vpo.tag} está vinculada à placa {vpo.placa}, não à placa {placa}.",
                vpo.id,
                vale_id=vpo.id,
                tag=vpo.tag,
                placa_informada=placa,
                placa_do_vale=vpo.placa,
            )
        )

    validade = date.fromisoformat(vpo.validade)
    if validade < data_viagem:
        avisos.append(
            _aviso(
                "VPO_VENCIDO",
                "rejeicao",
                f"VPO {vpo.id} venceu em {vpo.validade}.",
                vpo.id,
                vale_id=vpo.id,
                validade=vpo.validade,
                data_viagem=data_viagem.isoformat(),
            )
        )

    if vpo.saldo_rs < pedagio_previsto_rs:
        avisos.append(
            _aviso(
                "VPO_SALDO_INSUFICIENTE",
                "rejeicao",
                f"Saldo de R$ {vpo.saldo_rs:.2f} não cobre o pedágio previsto de R$ {pedagio_previsto_rs:.2f}.",
                vpo.id,
                vale_id=vpo.id,
                saldo_rs=vpo.saldo_rs,
                pedagio_previsto_rs=pedagio_previsto_rs,
                falta_rs=round(pedagio_previsto_rs - vpo.saldo_rs, 2),
            )
        )

    return avisos


def consolidar(avisos: list[Aviso]) -> tuple[str, list[Aviso]]:
    vistos: set[tuple[str, str]] = set()
    unicos: list[Aviso] = []
    for aviso in avisos:
        chave = (aviso.codigo, json.dumps(aviso.detalhe, sort_keys=True, ensure_ascii=False))
        if chave in vistos:
            continue
        vistos.add(chave)
        unicos.append(aviso)

    if any(a.severidade == "rejeicao" for a in unicos):
        status = "rejeitada"
    elif unicos:
        status = "aprovada_com_avisos"
    else:
        status = "aprovada"
    return status, unicos
