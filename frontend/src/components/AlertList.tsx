import { AlertTriangle, XCircle } from 'lucide-react'
import type { Aviso } from '../types'

interface Props {
  avisos: Aviso[]
}

export function AlertList({ avisos }: Props) {
  if (avisos.length === 0) {
    return <p className="texto-suave">Nenhum alerta. A rota passou por todas as regras do gate.</p>
  }

  return (
    <ul className="alert-list" aria-live="polite">
      {avisos.map((aviso, indice) => {
        const rejeicao = aviso.severidade === 'rejeicao'
        const Icone = rejeicao ? XCircle : AlertTriangle
        return (
          <li
            key={`${aviso.codigo}-${aviso.entidade ?? indice}`}
            className={`alert-list__item ${rejeicao ? 'is-rejeicao' : 'is-aviso'}`}
          >
            <Icone size={18} strokeWidth={1.5} aria-hidden="true" />
            <div className="alert-list__corpo">
              <div className="alert-list__cabecalho">
                <code>{aviso.codigo}</code>
                <span className="texto-suave">{rejeicao ? 'Rejeição' : 'Aviso'}</span>
              </div>
              <p>{aviso.mensagem}</p>
              <details>
                <summary>Evidência</summary>
                <pre>{JSON.stringify(aviso.detalhe, null, 2)}</pre>
              </details>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
