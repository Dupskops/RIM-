import ChatbotPage from '@/pages/ChatbotPage'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/chatbot')({
  component: ChatbotPage,
})