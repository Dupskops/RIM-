import DiagnosticoPage from '@/pages/DiagnosticoPage'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/diagnostico')({
  component: DiagnosticoPage,
})

