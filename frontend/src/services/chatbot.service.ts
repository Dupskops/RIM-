import type { ChatMessage } from '@/types';
import { env } from '@/config/env';

export class ChatbotService {
  private ws: WebSocket | null = null;
  private messageHandlers: Array<(message: ChatMessage) => void> = [];
  private connectionHandlers: Array<(connected: boolean) => void> = [];

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
