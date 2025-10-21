import { useState, useEffect, useCallback } from 'react';
import { chatbotService } from '@/services';
import type { ChatMessage } from '@/types';
import { getAccessToken } from '@/lib/auth-guard';

export const useChatbot = (motoId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!motoId) return;

    const token = getAccessToken();
    if (!token) return;

    // Conectar al WebSocket
    chatbotService.connect(motoId, token);

    // Suscribirse a mensajes
    const unsubscribeMessages = chatbotService.onMessage((message: ChatMessage) => {
      setMessages((prev) => [...prev, message]);
      setIsLoading(false);
    });

    // Suscribirse a cambios de conexión
    const unsubscribeConnection = chatbotService.onConnectionChange((connected: boolean) => {
      setIsConnected(connected);
    });

    return () => {
      unsubscribeMessages();
      unsubscribeConnection();
      chatbotService.disconnect();
    };
  }, [motoId]);

  const sendMessage = useCallback((content: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    chatbotService.sendMessage(content);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isConnected,
    isLoading,
    sendMessage,
    clearMessages,
  };
};
