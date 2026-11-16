import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { brl, numero, percentual } from '../lib/formato'
import type { Comparativo as ComparativoTipo, SimulacaoResultado } from '../types'

const ROTULO = {
  dentro: 'Dentro da faixa',
  atencao: 'Atenção',
  critico: 'Crítico',
} as const

export function Comparativo({ resultado }: { resultado: SimulacaoResultado }) {
  const [km, setKm] = useState(resultado.distancia_km)
  const [diesel, setDiesel] = useState(resultado.custos.diesel_rs)
  const [pedagio, setPedagio] = useState(resultado.pedagio_rs)
  const [tempo, setTempo] = useState(resultado.tempo_total_h)
  const [dados, setDados] = useState<ComparativoTipo | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(false)

  useEffect(() => {
    setKm(resultado.distancia_km)
    setDiesel(resultado.custos.diesel_rs)
    setPedagio(resultado.pedagio_rs)
    setTempo(resultado.tempo_total_h)
    setDados(null)
    setErro(null)
  }, [resultado])

  async function registrar() {
    setCarregando(true)
    setErro(null)
    try {
      const origem = String(resultado.parametros.origem_id ?? '')
      await api.registrarExecucao({
        simulacao_id: resultado.id,
        km_real: km,
        diesel_real: diesel,
        pedagio_real: pedagio,
        tempo_real_h: tempo,
        rota_executada: [origem, ...resultado.ordem].filter(Boolean),
      })
      const resposta = await api.comparativo(resultado.id)
      setDados(resposta.comparativo)
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : 'Falha ao registrar execução')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <section className="painel">
      <div className="painel__cabecalho">
        <h2>Previsto × realizado</h2>
        <p>O desvio é medido contra a mesma fórmula de custo, não contra outra implementação.</p>
      </div>

      <div className="grade-4">
        <label>
          <span>KM real</span>
          <input type="number" min={0} step={1} value={km} onChange={(e) => setKm(Number(e.target.value))} />
        </label>
        <label>
          <span>Diesel real (R$)</span>
          <input type="number" min={0} step={1} value={diesel} onChange={(e) => setDiesel(Number(e.target.value))} />
        </label>
        <label>
          <span>Pedágio real (R$)</span>
          <input type="number" min={0} step={1} value={pedagio} onChange={(e) => setPedagio(Number(e.target.value))} />
        </label>
        <label>
          <span>Tempo real (h)</span>
          <input type="number" min={0} step={0.1} value={tempo} onChange={(e) => setTempo(Number(e.target.value))} />
        </label>
      </div>

      <button type="button" className="botao botao--secundario" onClick={registrar} disabled={carregando}>
        {carregando ? 'Registrando…' : 'Registrar execução'}
      </button>

      {erro && <p className="inline-erro-texto">{erro}</p>}

      {dados && (
        <div className="comparativo-resultado">
          <p className={`status status--${dados.classificacao === 'critico' ? 'rejeitada' : dados.classificacao === 'atencao' ? 'aprovada_com_avisos' : 'aprovada'}`}>
            {ROTULO[dados.classificacao]}
          </p>
          <table>
            <caption className="sr-only">Comparativo entre previsto e realizado</caption>
            <thead>
              <tr>
                <th scope="col">Métrica</th>
                <th scope="col" className="num">Previsto</th>
                <th scope="col" className="num">Real</th>
                <th scope="col" className="num">Desvio</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">Distância</th>
                <td className="num">{numero(dados.km_previsto)} km</td>
                <td className="num">{numero(dados.km_real)} km</td>
                <td className="num">{percentual(dados.desvio_km_pct)}</td>
              </tr>
              <tr>
                <th scope="row">Custo</th>
                <td className="num">{brl(dados.custo_previsto_rs)}</td>
                <td className="num">{brl(dados.custo_real_rs)}</td>
                <td className="num">{percentual(dados.desvio_custo_pct)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
