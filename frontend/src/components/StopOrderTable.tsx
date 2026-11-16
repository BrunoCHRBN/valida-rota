import { numero } from '../lib/formato'
import type { No, SimulacaoResultado } from '../types'

interface Props {
  resultado: SimulacaoResultado
  nos: No[]
}

interface ParadaParametro {
  no_id: string
  janela_inicio: string | null
  janela_fim: string | null
  peso_kg: number
  prioridade: number
}

export function StopOrderTable({ resultado, nos }: Props) {
  const porId = new Map(nos.map((no) => [no.id, no]))
  const parametros = (resultado.parametros.paradas ?? []) as ParadaParametro[]
  const porNo = new Map(parametros.map((p) => [p.no_id, p]))

  return (
    <section className="painel">
      <div className="painel__cabecalho">
        <h2>Ordem de entrega</h2>
        <p>Sequência calculada pelo menor score, não pela ordem de digitação.</p>
      </div>
      <div className="tabela-scroll">
        <table>
          <caption className="sr-only">Ordem de entrega calculada</caption>
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Ponto</th>
              <th scope="col">Setor</th>
              <th scope="col">Chegada</th>
              <th scope="col">Janela</th>
              <th scope="col" className="num">
                Peso
              </th>
              <th scope="col" className="num">
                Prioridade
              </th>
            </tr>
          </thead>
          <tbody>
            {resultado.ordem.map((noId, indice) => {
              const no = porId.get(noId)
              const parada = porNo.get(noId)
              const janela =
                parada?.janela_inicio && parada?.janela_fim
                  ? `${parada.janela_inicio}–${parada.janela_fim}`
                  : 'livre'
              return (
                <tr key={noId}>
                  <td className="num">{indice + 1}</td>
                  <td>{no?.nome ?? noId}</td>
                  <td>{no?.setor_id ?? '—'}</td>
                  <td>{resultado.chegadas[noId] ?? '—'}</td>
                  <td>{janela}</td>
                  <td className="num">{numero(parada?.peso_kg ?? 0, 0)} kg</td>
                  <td className="num">{parada?.prioridade ?? 0}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
