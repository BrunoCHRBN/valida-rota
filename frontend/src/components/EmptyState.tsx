interface Props {
  titulo: string
  texto: string
}

export function EmptyState({ titulo, texto }: Props) {
  return (
    <div className="empty-state">
      <p className="empty-state__titulo">{titulo}</p>
      <p>{texto}</p>
    </div>
  )
}
