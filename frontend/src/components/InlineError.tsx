import { AlertOctagon } from 'lucide-react'
import type { ApiError } from '../lib/api'

interface Props {
  erro: ApiError
}

export function InlineError({ erro }: Props) {
  return (
    <div className="inline-error" role="alert">
      <AlertOctagon size={18} strokeWidth={1.5} aria-hidden="true" />
      <div>
        <p>{erro.message}</p>
        <p className="inline-error__codigo">{erro.codigo}</p>
        {erro.avisos.length > 0 && (
          <ul>
            {erro.avisos.map((aviso) => (
              <li key={`${aviso.codigo}-${aviso.entidade ?? ''}`}>
                <code>{aviso.codigo}</code> {aviso.mensagem}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
