import HistorialPage from '@/pages/HistorialPage'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/historial')({
  component: HistorialPage,
})

