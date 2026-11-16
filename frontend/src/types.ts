export type Severidade = 'aviso' | 'rejeicao'
export type StatusGate = 'aprovada' | 'aprovada_com_avisos' | 'rejeitada'
export type ModoPedagio = 'vpo' | 'proprio' | 'embutido_no_frete'

export interface Aviso {
  codigo: string
  severidade: Severidade
  mensagem: string
  detalhe: Record<string, unknown>
  entidade: string | null
}

export interface Custo {
  diesel_rs: number
  pedagio_rs: number
  depreciacao_rs: number
  manutencao_rs: number
  motorista_rs: number
  total_rs: number
  pedagio_coberto_rs: number
  margem_rs: number
  margem_pct: number
  custo_logistico_embarcador_rs: number
  extra_revisao_rs: number
}

export interface SimulacaoResultado {
  id: string
  created_at: string
  status: StatusGate
  ordem: string[]
  chegadas: Record<string, string>
  distancia_km: number
  tempo_h: number
  tempo_total_h: number
  pedagio_rs: number
  pracas: Record<string, number>
  custos: Custo
  margem_rs: number
  margem_pct: number
  avisos: Aviso[]
  parametros: Record<string, unknown>
}

export interface No {
  id: string
  nome: string
  setor_id: string
  qualidade_geo: string
  lat: number
  lon: number
}

export interface Veiculo {
  id: string
  nome: string
  perfil: string
  consumo_km_l: number
  capacidade_kg: number
  km_atual: number
  km_proxima_revisao: number
  disponivel: number
}

export interface Motorista {
  id: string
  nome: string
  custo_hora: number
  jornada_max_h: number
}

export interface Perfil {
  id: string
  nome: string
  setor_id: string
  ocupacao_minima_pct: number
  permitir_multiplos_setores: number
}

export interface Vale {
  id: string
  operadora: string
  tag: string
  placa: string
  saldo_rs: number
  validade: string
}

export interface Catalogos {
  nos: No[]
  veiculos: Veiculo[]
  motoristas: Motorista[]
  perfis: Perfil[]
  vales: Vale[]
}

export interface ParadaForm {
  noId: string
  janelaInicio: string
  janelaFim: string
  pesoKg: number
  prioridade: number
}

export interface SimulacaoForm {
  origemId: string
  paradas: ParadaForm[]
  veiculoId: string
  motoristaId: string
  perfilId: string
  placa: string
  receitaRs: number
  modoPedagio: ModoPedagio
  vpoId: string
  partida: string
  evitarPedagio: boolean
  retornarOrigem: boolean
}

export interface Comparativo {
  km_previsto: number
  km_real: number
  desvio_km: number
  desvio_km_pct: number
  custo_previsto_rs: number
  custo_real_rs: number
  desvio_custo_rs: number
  desvio_custo_pct: number
  classificacao: 'dentro' | 'atencao' | 'critico'
}

export interface Diagnostico {
  gerado_em: string
  total: number
  por_codigo: Record<string, number>
  alertas: Aviso[]
}
