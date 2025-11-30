import GarajePage from '@/pages/garajePage'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/garaje')({
  component: GarajePage,
})
