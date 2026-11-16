import { useCallback, useEffect, useState } from 'react'
import { AlertList } from './components/AlertList'
import { AppHeader } from './components/AppHeader'
import { Comparativo } from './components/Comparativo'
import { CostBreakdown } from './components/CostBreakdown'
import { EmptyState } from './components/EmptyState'
import { InlineError } from './components/InlineError'
import { IntegridadePanel } from './components/IntegridadePanel'
import { ResultHeader } from './components/ResultHeader'
import { SimulationForm } from './components/SimulationForm'
import { StopOrderTable } from './components/StopOrderTable'
import { VpoPanel } from './components/VpoPanel'
import { ApiError, api } from './lib/api'
import type { Catalogos, Diagnostico, SimulacaoForm, SimulacaoResultado } from './types'

const FORM_INICIAL: SimulacaoForm = {
  origemId: 'sao-paulo',
  paradas: [
    { noId: 'guarulhos', janelaInicio: '09:00', janelaFim: '12:00', pesoKg: 400, prioridade: 8 },
    { noId: 'osasco', janelaInicio: '10:00', janelaFim: '14:00', pesoKg: 300, prioridade: 5 },
  ],
  veiculoId: 'vuc-01',
  motoristaId: 'mot-01',
  perfilId: 'last-mile-metropolitana',
  placa: 'ABC1D23',
  receitaRs: 1800,
  modoPedagio: 'vpo',
  vpoId: 'vpo-01',
  partida: '08:00',
  evitarPedagio: false,
  retornarOrigem: false,
}

export default function App() {
  const [catalogos, setCatalogos] = useState<Catalogos | null>(null)
  const [form, setForm] = useState<SimulacaoForm>(FORM_INICIAL)
  const [resultado, setResultado] = useState<SimulacaoResultado | null>(null)
  const [erro, setErro] = useState<ApiError | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [diagnostico, setDiagnostico] = useState<Diagnostico | null>(null)
  const [carregandoDiagnostico, setCarregandoDiagnostico] = useState(false)

  const carregarDiagnostico = useCallback(async () => {
    setCarregandoDiagnostico(true)
    try {
      setDiagnostico(await api.diagnostico())
    } catch {
      setDiagnostico(null)
    } finally {
      setCarregandoDiagnostico(false)
    }
  }, [])

  useEffect(() => {
    api
      .catalogos()
      .then(setCatalogos)
      .catch(() =>
        setErro(
          new ApiError(
            'Não foi possível carregar os cadastros. O backend está rodando em localhost:8000?',
            'BACKEND_INDISPONIVEL',
          ),
        ),
      )
    void carregarDiagnostico()
  }, [carregarDiagnostico])

  async function simular() {
    setCarregando(true)
    setErro(null)
    try {
      const resposta = await api.simular(form)
      setResultado(resposta)
      void carregarDiagnostico()
    } catch (falha) {
      setErro(
        falha instanceof ApiError
          ? falha
          : new ApiError('Falha inesperada ao simular a rota.', 'ERRO_INTERNO'),
      )
      setResultado(null)
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="app">
      <AppHeader />

      <main className="layout">
        <div className="coluna-formulario">
          {catalogos ? (
            <SimulationForm
              catalogos={catalogos}
              valor={form}
              onChange={setForm}
              onSubmit={simular}
              carregando={carregando}
            />
          ) : (
            <section className="painel">
              <p className="texto-suave">Carregando cadastros…</p>
            </section>
          )}
        </div>

        <div className="coluna-resultado">
          {erro && <InlineError erro={erro} />}

          {resultado ? (
            <>
              <ResultHeader resultado={resultado} />
              <section className="painel">
                <div className="painel__cabecalho">
                  <h2>Alertas do gate</h2>
                  <p>Cada recusa traz código e evidência. Nada é escondido em tooltip.</p>
                </div>
                <AlertList avisos={resultado.avisos} />
              </section>
              {catalogos && <StopOrderTable resultado={resultado} nos={catalogos.nos} />}
              <CostBreakdown custos={resultado.custos} />
              <VpoPanel resultado={resultado} />
              <Comparativo resultado={resultado} />
            </>
          ) : (
            <section className="painel">
              <EmptyState
                titulo="Nenhuma rota validada ainda"
                texto="Preencha a simulação e clique em Validar rota. O resultado mostra o status do gate, a ordem calculada, o custo e a margem."
              />
            </section>
          )}
        </div>
      </main>

      <section className="faixa-integridade">
        <IntegridadePanel
          diagnostico={diagnostico}
          carregando={carregandoDiagnostico}
          onAtualizar={() => void carregarDiagnostico()}
        />
      </section>

      <footer className="rodape">
        <p>
          Dados sintéticos do corredor Santos–São Paulo–Campinas–Ribeirão Preto. Nenhum mapa
          renderizado, nenhuma chave externa.
        </p>
      </footer>
    </div>
  )
}
