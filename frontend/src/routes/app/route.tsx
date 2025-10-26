import Layout from '@/components/layout'
import { createFileRoute } from '@tanstack/react-router'


export const Route = createFileRoute('/app')({
  component: Layout,
})

