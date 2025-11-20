import NotificacionesPage from '@/pages/NotificacionesPage'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/notificaciones')({
  component: NotificacionesPage,
})


