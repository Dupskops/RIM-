import MiPerfilPage from '@/pages/MiPerfilPage'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/miPerfil')({
  component: MiPerfilPage,
})
