import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'
import { brl, numero, percentual } from '../lib/formato'
import type { SimulacaoResultado } from '../types'

const ROTULO = {
  aprovada: 'Aprovada',
  aprovada_com_avisos: 'Aprovada com avisos',
  rejeitada: 'Rejeitada',
} as const

export function ResultHeader({ resultado }: { resultado: SimulacaoResultado }) {
  const Icone =
    resultado.status === 'aprovada'
      ? CheckCircle2
      : resultado.status === 'aprovada_com_avisos'
        ? AlertTriangle
        : XCircle

  return (
    <section className="painel resultado-cabecalho" aria-live="polite">
      <div className={`status status--${resultado.status}`}>
        <Icone size={20} strokeWidth={1.5} aria-hidden="true" />
        <span>{ROTULO[resultado.status]}</span>
        <code>{resultado.id}</code>
      </div>

      <dl className="metricas">
        <div>
          <dt>Distância</dt>
          <dd>{numero(resultado.distancia_km)} km</dd>
        </div>
        <div>
          <dt>Jornada</dt>
          <dd>{numero(resultado.tempo_total_h)} h</dd>
        </div>
        <div>
          <dt>Pedágio</dt>
          <dd>{brl(resultado.pedagio_rs)}</dd>
        </div>
        <div>
          <dt>Margem</dt>
          <dd className={resultado.margem_rs < 0 ? 'negativo' : ''}>
            {brl(resultado.margem_rs)}
            <span className="texto-suave"> · {percentual(resultado.margem_pct)}</span>
          </dd>
        </div>
      </dl>

      <p className="texto-suave texto-pequeno">
        Direção: {numero(resultado.tempo_h)} h. A jornada inclui espera em janela e tempo de
        serviço.
      </p>
    </section>
  )
}
