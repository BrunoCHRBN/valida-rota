import { RefreshCw } from 'lucide-react'
import type { Diagnostico } from '../types'

interface Props {
  diagnostico: Diagnostico | null
  carregando: boolean
  onAtualizar: () => void
}

export function IntegridadePanel({ diagnostico, carregando, onAtualizar }: Props) {
  return (
    <section className="painel">
      <div className="painel__cabecalho painel__cabecalho--linha">
        <div>
          <h2>Integridade do cadastro</h2>
          <p>Varredura dos mesmos códigos que o gate usa na simulação.</p>
        </div>
        <button
          type="button"
          className="botao botao--icone"
          onClick={onAtualizar}
          disabled={carregando}
          aria-label="Atualizar diagnóstico"
        >
          <RefreshCw size={16} strokeWidth={1.5} aria-hidden="true" />
        </button>
      </div>

      {diagnostico === null ? (
        <p className="texto-suave">Carregando diagnóstico…</p>
      ) : diagnostico.total === 0 ? (
        <p className="texto-suave">Nenhuma inconsistência encontrada no cadastro atual.</p>
      ) : (
        <>
          <p className="texto-suave">
            {diagnostico.total} ocorrência(s) em {Object.keys(diagnostico.por_codigo).length}{' '}
            código(s).
          </p>
          <ul className="chips">
            {Object.entries(diagnostico.por_codigo).map(([codigo, quantidade]) => (
              <li key={codigo}>
                <code>{codigo}</code>
                <span>{quantidade}</span>
              </li>
            ))}
          </ul>
          <ul className="lista-compacta">
            {diagnostico.alertas.slice(0, 8).map((alerta, indice) => (
              <li key={`${alerta.codigo}-${alerta.entidade ?? indice}`}>
                <span
                  className={`marcador ${alerta.severidade === 'rejeicao' ? 'is-rejeicao' : 'is-aviso'}`}
                  aria-hidden="true"
                />
                <div>
                  <code>{alerta.codigo}</code>
                  <p>{alerta.mensagem}</p>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
