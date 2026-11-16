import { brl } from '../lib/formato'
import type { SimulacaoResultado } from '../types'

export function VpoPanel({ resultado }: { resultado: SimulacaoResultado }) {
  const pracas = Object.entries(resultado.pracas)
  const vpoId = String(resultado.parametros.vpo_id ?? '')
  if (pracas.length === 0 && resultado.custos.pedagio_coberto_rs === 0) {
    return null
  }

  return (
    <section className="painel">
      <div className="painel__cabecalho">
        <h2>Pedágio e VPO</h2>
        <p>Praças previstas na rota e o que o vale-pedágio cobre.</p>
      </div>
      {pracas.length > 0 ? (
        <table>
          <caption className="sr-only">Praças de pedágio previstas</caption>
          <thead>
            <tr>
              <th scope="col">Praça</th>
              <th scope="col" className="num">
                Valor previsto
              </th>
            </tr>
          </thead>
          <tbody>
            {pracas.map(([praca, valor]) => (
              <tr key={praca}>
                <th scope="row">{praca}</th>
                <td className="num">{brl(valor)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="texto-suave">A rota não passa por praça com tarifa cadastrada.</p>
      )}
      <p className="texto-suave texto-pequeno">
        {vpoId ? `VPO ${vpoId} · ` : ''}
        coberto: {brl(resultado.custos.pedagio_coberto_rs)} de {brl(resultado.pedagio_rs)}.
      </p>
    </section>
  )
}
