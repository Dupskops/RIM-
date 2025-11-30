import type { ChatMessage } from '@/types';
import { env } from '@/config/env';
import apiClient from '@/config/api-client';
import { CHATBOT_ENDPOINTS } from '@/config/api-endpoints';

// Tipos para la API REST del chatbot
export interface ChatRequest {
  message: string;
  moto_id: number;
  conversation_id?: string;
  tipo_prompt?: string | null;
  stream?: boolean;
  context?: any | null;
}

export interface ChatResponseData {
  message: string;
  conversation_id: string;
  mensaje_usuario_id: number;
  mensaje_asistente_id: number;
  tipo_prompt: string;
}

export interface ChatResponse {
  success: boolean;
  message: string;
  data: ChatResponseData;
  timestamp: string;
  version: string;
}

export interface ConversacionHistorial {
  id: number;
  conversation_id: string;
  usuario_id: number;
  moto_id: number;
  titulo: string | null;
  activa: boolean;
  total_mensajes: number;
  ultima_actividad: string;
  created_at: string;
}

export interface ConversacionesResponse {
  success: boolean;
  message: string;
  data: ConversacionHistorial[];
  pagination: {
    page: number;
    per_page: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
    next_page: number | null;
    prev_page: number | null;
  };
  timestamp: string;
}

export interface MensajeConversacion {
  id: number;
  conversacion_id: number;
  role: 'user' | 'assistant';
  contenido: string;
  tipo_prompt: string;
  created_at: string;
}

export interface ConversacionConMensajes {
  conversacion: ConversacionHistorial;
  mensajes: MensajeConversacion[];
}

export interface ConversacionResponse {
  success: boolean;
  message: string;
  data: ConversacionConMensajes;
  timestamp: string;
  version: string;
}

export class ChatbotService {
  private ws: WebSocket | null = null;
  private messageHandlers: Array<(message: ChatMessage) => void> = [];
  private connectionHandlers: Array<(connected: boolean) => void> = [];

  /**
   * Enviar mensaje al chatbot vía REST API
   */
  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>(CHATBOT_ENDPOINTS.CHAT, request);
    return response.data;
  }

  /**
   * Obtener conversaciones del usuario
   */
  async getConversaciones(
    usuarioId: number,
    motoId?: number,
    soloActivas: boolean = true,
    page: number = 1,
    perPage: number = 20
  ): Promise<ConversacionesResponse> {
    const params = new URLSearchParams();
    if (motoId) params.append('moto_id', String(motoId));
    params.append('solo_activas', String(soloActivas));
    params.append('page', String(page));
    params.append('per_page', String(perPage));

    const url = `${CHATBOT_ENDPOINTS.BY_USUARIO(usuarioId)}?${params.toString()}`;
    const response = await apiClient.get<ConversacionesResponse>(url);
    return response.data;
  }

  /**
   * Obtener una conversación específica con sus mensajes
   */
  async getConversacionById(
    conversationId: string,
    limit: number = 50
  ): Promise<ConversacionResponse> {
    const url = `${CHATBOT_ENDPOINTS.BY_ID(conversationId)}?limit=${limit}`;
    const response = await apiClient.get<ConversacionResponse>(url);
    return response.data;
  }

  /**
   * Conectar al WebSocket del chatbot
   */
  connect(motoId: string, token: string): void {
    const wsUrl = `${env.WS_URL}/ws/chatbot/${motoId}?token=${token}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('✅ Chatbot WebSocket conectado');
      this.notifyConnection(true);
    };

    this.ws.onmessage = (event) => {
      try {
        const message: ChatMessage = JSON.parse(event.data);
        this.notifyMessage(message);
      } catch (error) {
        console.error('Error al parsear mensaje del chatbot:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('❌ Error en chatbot WebSocket:', error);
    };

    this.ws.onclose = () => {
      console.log('🔌 Chatbot WebSocket desconectado');
      this.notifyConnection(false);
    };
  }

  /**
   * Enviar mensaje al chatbot
   */
  sendMessage(content: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ content }));
    } else {
      console.error('WebSocket no está conectado');
    }
  }

  /**
   * Suscribirse a mensajes
   */
  onMessage(handler: (message: ChatMessage) => void): () => void {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter((h) => h !== handler);
    };
  }

  /**
   * Suscribirse a cambios de conexión
   */
  onConnectionChange(handler: (connected: boolean) => void): () => void {
    this.connectionHandlers.push(handler);
    return () => {
      this.connectionHandlers = this.connectionHandlers.filter((h) => h !== handler);
    };
  }

  /**
   * Desconectar WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private notifyMessage(message: ChatMessage): void {
    this.messageHandlers.forEach((handler) => handler(message));
  }

  private notifyConnection(connected: boolean): void {
    this.connectionHandlers.forEach((handler) => handler(connected));
  }
}

// Exportar instancia singleton
export const chatbotService = new ChatbotService();
