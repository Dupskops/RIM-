let socket: WebSocket | null = null;
let shouldReconnect = true; // controla si debe reconectarse

export const connectNotificationSocket = (
  token: string,
  onMessageCallback?: (data: any) => void
): WebSocket | null => {
  if (!token) {
    console.warn("⚠️ No hay token disponible para conectar al WebSocket");
    return null;
  }

  if (socket && socket.readyState === WebSocket.OPEN) {
    console.log("🔄 WebSocket ya conectado");
    return socket;
  }

  const wsUrl = `ws://127.0.0.1:8000/ws/notifications?token=${token}`;
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("✅ Conectado al servidor de notificaciones WebSocket");
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log("📩 Notificación recibida:", data);
      onMessageCallback?.(data);
    } catch (error) {
      console.error("❌ Error al procesar el mensaje:", error);
    }
  };

  socket.onclose = (event) => {
    console.warn("⚠️ WebSocket cerrado:", event.code, event.reason);

    // Si el backend cerró la conexión (por ejemplo, token inválido)
    if (event.code === 4001 || event.reason.includes("token")) {
      console.error("❌ Token inválido o expirado. No se reconectará.");
      shouldReconnect = false;
      return;
    }

    if (shouldReconnect) {
      console.log("🔁 Reintentando conexión en 3 segundos...");
      setTimeout(() => connectNotificationSocket(token, onMessageCallback), 3000);
    }
  };

  socket.onerror = (err) => {
    console.error("❌ Error en WebSocket:", err);
    socket?.close();
  };

  return socket;
};

export const disconnectNotificationSocket = () => {
  if (socket) {
    console.log("🔌 Desconectando WebSocket manualmente...");
    shouldReconnect = false;
    socket.close();
    socket = null;
  }
};
