import type {
  Aviso,
  Catalogos,
  Comparativo,
  Diagnostico,
  SimulacaoForm,
  SimulacaoResultado,
} from '../types'

const BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  codigo: string
  avisos: Aviso[]

  constructor(mensagem: string, codigo = 'ERRO_DESCONHECIDO', avisos: Aviso[] = []) {
    super(mensagem)
    this.name = 'ApiError'
    this.codigo = codigo
    this.avisos = avisos
  }
}

async function req<T>(caminho: string, init?: RequestInit): Promise<T> {
  const resposta = await fetch(`${BASE}${caminho}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  const corpo = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const detalhe = corpo?.detail
    if (detalhe && typeof detalhe === 'object' && !Array.isArray(detalhe)) {
      throw new ApiError(detalhe.mensagem ?? 'Falha na requisição', detalhe.codigo, detalhe.avisos ?? [])
    }
    throw new ApiError('Falha na requisição', 'ERRO_HTTP')
  }
  return corpo as T
}

function paraPayload(form: SimulacaoForm) {
  return {
    origem_id: form.origemId,
    paradas: form.paradas.map((p) => ({
      no_id: p.noId,
      janela_inicio: p.janelaInicio || null,
      janela_fim: p.janelaFim || null,
      peso_kg: p.pesoKg,
      prioridade: p.prioridade,
    })),
    veiculo_id: form.veiculoId,
    motorista_id: form.motoristaId,
    perfil_id: form.perfilId,
    placa: form.placa,
    receita_rs: form.receitaRs,
    modo_pedagio: form.modoPedagio,
    vpo_id: form.modoPedagio === 'vpo' ? form.vpoId : null,
    partida: form.partida,
    evitar_pedagio: form.evitarPedagio,
    retornar_origem: form.retornarOrigem,
  }
}

export const api = {
  async catalogos(): Promise<Catalogos> {
    const [nos, veiculos, motoristas, perfis, vales] = await Promise.all([
      req<Catalogos['nos']>('/api/nos'),
      req<Catalogos['veiculos']>('/api/veiculos'),
      req<Catalogos['motoristas']>('/api/motoristas'),
      req<Catalogos['perfis']>('/api/perfis'),
      req<Catalogos['vales']>('/api/vales-pedagio'),
    ])
    return { nos, veiculos, motoristas, perfis, vales }
  },

  simular(form: SimulacaoForm): Promise<SimulacaoResultado> {
    return req('/api/simular', { method: 'POST', body: JSON.stringify(paraPayload(form)) })
  },

  registrarExecucao(corpo: {
    simulacao_id: string
    km_real: number
    diesel_real: number
    pedagio_real: number
    tempo_real_h: number
    rota_executada: string[]
  }) {
    return req('/api/execucoes', { method: 'POST', body: JSON.stringify(corpo) })
  },

  comparativo(simulacaoId: string): Promise<{ comparativo: Comparativo }> {
    return req(`/api/simulacoes/${simulacaoId}/comparativo`)
  },

  diagnostico(): Promise<Diagnostico> {
    return req('/api/diagnostico')
  },
}
