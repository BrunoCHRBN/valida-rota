import { Route } from 'lucide-react'

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="app-header__marca">
        <Route size={22} strokeWidth={1.5} aria-hidden="true" />
        <div>
          <h1>ValidaRota</h1>
          <p>Valide a rota antes de emplacar. O gate devolve o motivo de cada recusa.</p>
        </div>
      </div>
      <span className="badge badge--neutro">MVP local</span>
    </header>
  )
}
