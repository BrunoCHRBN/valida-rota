import { Plus, Trash2 } from 'lucide-react'
import type { Catalogos, ParadaForm, SimulacaoForm } from '../types'

interface Props {
  catalogos: Catalogos
  valor: SimulacaoForm
  onChange: (valor: SimulacaoForm) => void
  onSubmit: () => void
  carregando: boolean
}

function StopList({
  catalogos,
  paradas,
  onChange,
}: {
  catalogos: Catalogos
  paradas: ParadaForm[]
  onChange: (paradas: ParadaForm[]) => void
}) {
  const usados = new Set(paradas.map((p) => p.noId))
  const proximo = catalogos.nos.find((n) => !usados.has(n.id))?.id ?? catalogos.nos[0]?.id ?? ''

  function alterar(indice: number, campo: keyof ParadaForm, valor: string | number) {
    const copia = paradas.map((parada, i) =>
      i === indice ? { ...parada, [campo]: valor } : parada,
    )
    onChange(copia)
  }

  return (
    <div className="stop-list">
      {paradas.map((parada, indice) => (
        <div className="stop-list__linha" key={`${indice}-${parada.noId}`}>
          <div className="stop-list__topo">
            <label>
              <span>Parada {indice + 1}</span>
              <select
                value={parada.noId}
                onChange={(e) => alterar(indice, 'noId', e.target.value)}
              >
                {catalogos.nos.map((no) => (
                  <option key={no.id} value={no.id}>
                    {no.nome}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="botao botao--icone"
              onClick={() => onChange(paradas.filter((_, i) => i !== indice))}
              aria-label={`Remover parada ${indice + 1}`}
              disabled={paradas.length === 1}
            >
              <Trash2 size={16} strokeWidth={1.5} aria-hidden="true" />
            </button>
          </div>
          <div className="stop-list__campos">
            <label>
              <span>Janela de</span>
              <input
                type="time"
                value={parada.janelaInicio}
                onChange={(e) => alterar(indice, 'janelaInicio', e.target.value)}
              />
            </label>
            <label>
              <span>até</span>
              <input
                type="time"
                value={parada.janelaFim}
                onChange={(e) => alterar(indice, 'janelaFim', e.target.value)}
              />
            </label>
            <label>
              <span>Peso (kg)</span>
              <input
                type="number"
                min={0}
                step={10}
                value={parada.pesoKg}
                onChange={(e) => alterar(indice, 'pesoKg', Number(e.target.value))}
              />
            </label>
            <label>
              <span>Prioridade</span>
              <input
                type="number"
                min={0}
                max={9}
                value={parada.prioridade}
                onChange={(e) => alterar(indice, 'prioridade', Number(e.target.value))}
              />
            </label>
          </div>
        </div>
      ))}

      <button
        type="button"
        className="botao botao--secundario"
        onClick={() =>
          onChange([
            ...paradas,
            { noId: proximo, janelaInicio: '', janelaFim: '', pesoKg: 0, prioridade: 0 },
          ])
        }
        disabled={paradas.length >= 8}
      >
        <Plus size={16} strokeWidth={1.5} aria-hidden="true" />
        Adicionar parada
      </button>
      <p className="texto-suave texto-pequeno">
        Até 8 paradas. O limite existe porque a ordem é calculada por enumeração completa.
      </p>
    </div>
  )
}

export function SimulationForm({ catalogos, valor, onChange, onSubmit, carregando }: Props) {
  function campo<K extends keyof SimulacaoForm>(chave: K, novo: SimulacaoForm[K]) {
    onChange({ ...valor, [chave]: novo })
  }

  const vpoSelecionado = catalogos.vales.find((v) => v.id === valor.vpoId)

  return (
    <form
      className="painel formulario"
      onSubmit={(evento) => {
        evento.preventDefault()
        onSubmit()
      }}
    >
      <div className="painel__cabecalho">
        <h2>Simulação</h2>
        <p>Origem, paradas e restrições. O gate roda antes de qualquer emplacamento.</p>
      </div>

      <fieldset>
        <legend>Rota</legend>
        <label>
          <span>Origem</span>
          <select value={valor.origemId} onChange={(e) => campo('origemId', e.target.value)}>
            {catalogos.nos.map((no) => (
              <option key={no.id} value={no.id}>
                {no.nome}
              </option>
            ))}
          </select>
        </label>

        <StopList
          catalogos={catalogos}
          paradas={valor.paradas}
          onChange={(paradas) => campo('paradas', paradas)}
        />
      </fieldset>

      <fieldset>
        <legend>Veículo e jornada</legend>
        <div className="grade-2">
          <label>
            <span>Veículo</span>
            <select value={valor.veiculoId} onChange={(e) => campo('veiculoId', e.target.value)}>
              {catalogos.veiculos.map((veiculo) => (
                <option key={veiculo.id} value={veiculo.id}>
                  {veiculo.nome}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Motorista</span>
            <select
              value={valor.motoristaId}
              onChange={(e) => campo('motoristaId', e.target.value)}
            >
              {catalogos.motoristas.map((motorista) => (
                <option key={motorista.id} value={motorista.id}>
                  {motorista.nome} · {motorista.jornada_max_h} h
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="grade-2">
          <label>
            <span>Perfil de roteirização</span>
            <select value={valor.perfilId} onChange={(e) => campo('perfilId', e.target.value)}>
              {catalogos.perfis.map((perfil) => (
                <option key={perfil.id} value={perfil.id}>
                  {perfil.nome}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Partida</span>
            <input
              type="time"
              value={valor.partida}
              onChange={(e) => campo('partida', e.target.value)}
            />
          </label>
        </div>
      </fieldset>

      <fieldset>
        <legend>Custo e pedágio</legend>
        <div className="grade-2">
          <label>
            <span>Placa</span>
            <input
              value={valor.placa}
              onChange={(e) => campo('placa', e.target.value.toUpperCase())}
              maxLength={8}
            />
          </label>
          <label>
            <span>Receita do frete (R$)</span>
            <input
              type="number"
              min={0}
              step={50}
              value={valor.receitaRs}
              onChange={(e) => campo('receitaRs', Number(e.target.value))}
            />
          </label>
        </div>
        <div className="grade-2">
          <label>
            <span>Modo de pedágio</span>
            <select
              value={valor.modoPedagio}
              onChange={(e) =>
                campo('modoPedagio', e.target.value as SimulacaoForm['modoPedagio'])
              }
            >
              <option value="vpo">Vale-pedágio (VPO)</option>
              <option value="proprio">Pedágio próprio</option>
              <option value="embutido_no_frete">Embutido no frete</option>
            </select>
          </label>
          <label>
            <span>VPO</span>
            <select
              value={valor.vpoId}
              onChange={(e) => campo('vpoId', e.target.value)}
              disabled={valor.modoPedagio !== 'vpo'}
            >
              {catalogos.vales.map((vale) => (
                <option key={vale.id} value={vale.id}>
                  {vale.operadora} · {vale.placa}
                </option>
              ))}
            </select>
          </label>
        </div>
        {valor.modoPedagio === 'vpo' && vpoSelecionado && (
          <p className="texto-suave texto-pequeno">
            TAG {vpoSelecionado.tag} · saldo R$ {vpoSelecionado.saldo_rs.toFixed(2)} · validade{' '}
            {vpoSelecionado.validade}
          </p>
        )}
        <div className="checks">
          <label className="check">
            <input
              type="checkbox"
              checked={valor.evitarPedagio}
              onChange={(e) => campo('evitarPedagio', e.target.checked)}
            />
            <span>Evitar pedágio</span>
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={valor.retornarOrigem}
              onChange={(e) => campo('retornarOrigem', e.target.checked)}
            />
            <span>Retornar à origem</span>
          </label>
        </div>
      </fieldset>

      <button type="submit" className="botao botao--primario" disabled={carregando}>
        {carregando ? 'Validando…' : 'Validar rota'}
      </button>
    </form>
  )
}
