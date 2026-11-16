import { brl } from '../lib/formato'
import type { Custo } from '../types'

export function CostBreakdown({ custos }: { custos: Custo }) {
  const linhas = [
    ['Diesel', custos.diesel_rs],
    ['Pedágio', custos.pedagio_rs],
    ['Depreciação', custos.depreciacao_rs],
    ['Manutenção', custos.manutencao_rs],
    ['Motorista', custos.motorista_rs],
  ] as const

  return (
    <section className="painel">
      <div className="painel__cabecalho">
        <h2>Composição do custo</h2>
        <p>Mesma fórmula no previsto e no realizado.</p>
      </div>
      <table className="tabela-custo">
        <caption className="sr-only">Composição do custo da viagem</caption>
        <tbody>
          {linhas.map(([rotulo, valor]) => (
            <tr key={rotulo}>
              <th scope="row">{rotulo}</th>
              <td className="num">{brl(valor)}</td>
            </tr>
          ))}
          <tr className="tabela-custo__total">
            <th scope="row">Total operacional</th>
            <td className="num">{brl(custos.total_rs)}</td>
          </tr>
          {custos.pedagio_coberto_rs > 0 && (
            <tr>
              <th scope="row">Pedágio coberto pelo VPO</th>
              <td className="num">− {brl(custos.pedagio_coberto_rs)}</td>
            </tr>
          )}
          <tr className="tabela-custo__margem">
            <th scope="row">Margem da transportadora</th>
            <td className={`num ${custos.margem_rs < 0 ? 'negativo' : ''}`}>
              {brl(custos.margem_rs)}
            </td>
          </tr>
        </tbody>
      </table>
      {custos.extra_revisao_rs > 0 && (
        <p className="texto-suave texto-pequeno">
          Inclui {brl(custos.extra_revisao_rs)} de extra por revisão ultrapassada.
        </p>
      )}
    </section>
  )
}
