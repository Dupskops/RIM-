import React, { useMemo, useState, useEffect } from 'react';
import { ArrowLeft, Check } from 'lucide-react';
import { useNavigate } from '@tanstack/react-router';
import { connectNotificationSocket, disconnectNotificationSocket } from '@/services/notificationSocket';
import { getAccessToken } from "@/lib/auth-guard";

type NotificationType = 'mantenimiento' | 'diagnostico' | 'otro';

interface NotificationItem {
    id: string;
    title: string;
    body: string;
    date: string; // ISO
    type: NotificationType 
    read?: boolean;
}

const sampleNotifications: NotificationItem[] = [
    {
        id: '1',
        title: 'Cambio de aceite programado',
        body: 'Tu moto tiene una programación de mantenimiento el 05/11/2025. Reserva tu cita.',
        date: '2025-11-05T09:30:00.000Z',
        type: 'mantenimiento',
        read: false,
    },
    {
        id: '2',
        title: 'Diagnóstico remoto disponible',
        body: 'Se ha completado el diagnóstico remoto. Revisa los resultados y recomendaciones.',
        date: '2025-10-20T14:15:00.000Z',
        type: 'diagnostico',
        read: true,
    },
    {
        id: '3',
        title: 'Recordatorio de revisión',
        body: 'Haz una revisión general cada 6 meses para mantener la garantía.',
        date: '2025-09-01T08:00:00.000Z',
        type: 'mantenimiento',
        read: false,
    },
];

const FILTERS: Array<{ key: 'todas' | NotificationType; label: string }> = [
    { key: 'todas', label: 'Todas' },
    { key: 'mantenimiento', label: 'Mantenimiento' },
    { key: 'diagnostico', label: 'Diagnóstico' },
];

const badgeColor = (type: NotificationType) => {
    switch (type) {
        case 'mantenimiento':
            return 'bg-yellow-100 text-yellow-800';
        case 'diagnostico':
            return 'bg-blue-100 text-blue-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
};

const NotificacionesPage: React.FC = () => {
    const [filter, setFilter] = useState<'todas' | NotificationType>('todas');
    const navigate = useNavigate();
    const [items, setItems] = useState<NotificationItem[]>(sampleNotifications);
    const [loading, setLoading] = useState<boolean>(false);

useEffect(() => {
  const token = getAccessToken(); //Obtener el token desde el auth-guard

  if (!token) {
    console.warn('⚠️ No hay token disponible para conectar al WebSocket');
    return;
  }

  const handleNewNotification = (msg: any) => {
    if (msg.type === 'nueva_notificacion' && msg.data) {
      const nueva = msg.data;
      const formateada: NotificationItem = {
        id: String(nueva.id),
        title: nueva.titulo,
        body: nueva.mensaje,
        date: new Date().toISOString(),
        type: (nueva.tipo as NotificationType) || 'otro',
        read: false,
      };

      setItems((prev) => [formateada, ...prev]); // Añade arriba
    }
  };

  const socket = connectNotificationSocket(token, handleNewNotification);

  return () => {
    disconnectNotificationSocket();
  };
}, []);



    const filtered = useMemo(() => {
        if (filter === 'todas') return items;
        return items.filter((i) => i.type === filter);
    }, [filter, items]);

    const toggleRead = (id: string) => {
        setItems((prev) => prev.map((it) => (it.id === id ? { ...it, read: !it.read } : it)));
    };

    const clearRead = () => {
        setItems((prev) => prev.filter((it) => !it.read));
    };

    const markAllRead = () => {
        setItems((prev) => prev.map((it) => ({ ...it, read: true })));
    };

    const unreadCount = items.filter((it) => !it.read).length;

        return (
            <div className="p-6 max-w-5xl mx-auto">
                <header className="mb-6 flex items-center gap-3">
                    <button
                        onClick={() => navigate({ to: '/app' })}
                        className="p-2 rounded-md text-[var(--accent)] hover:bg-gray-100"
                        aria-label="Volver al inicio"
                    >
                        <ArrowLeft />
                    </button>

                    <div>
                        <h1 className="text-2xl font-semibold text-[var(--text)]">Notificaciones</h1>
                        <p className="text-sm text-gray-500">Aquí verás avisos importantes sobre tu(s) moto(s) y mantenimientos.</p>
                    </div>
                </header>

            <section className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                <div className="flex items-center gap-2 bg-[var(--card)] p-1 rounded-full shadow-sm">
                                {FILTERS.map((f) => {
                                    const active = filter === f.key;
                                    return (
                                        <button
                                            key={f.key}
                                            onClick={() => setFilter(f.key)}
                                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors focus:outline-none ${
                                    active ? 'bg-[var(--accent)] text-white' : 'text-[var(--bg)]'
                                }`}
                                aria-pressed={active}
                            >
                                {f.label}
                            </button>
                        );
                    })}
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={markAllRead}
                        disabled={unreadCount === 0}
                        aria-disabled={unreadCount === 0}
                        className={`text-sm px-3 py-1 rounded-md shadow-sm flex items-center gap-2 bg-[var(--accent)] text-white hover:opacity-95 disabled:opacity-50 disabled:cursor-not-allowed`}
                        title="Marcar todas como leídas"
                    >
                        <Check className="h-4 w-4" />
                        Marcar todo como leído
                    </button>

                    <button
                        onClick={clearRead}
                        className="text-sm text-gray-600 hover:text-[var(--accent)]"
                        title="Eliminar leídas"
                    >
                        Limpiar leídas
                    </button>
                </div>
            </section>

            <main>
                {loading ? (
                    // Skeleton while loading
                    <ul className="space-y-3">
                        {Array.from({ length: 3 }).map((_, i) => (
                            <li key={i} className="flex items-start gap-4 p-4 rounded-lg shadow-sm bg-[var(--card)]">
                                <div className="w-10 h-10 rounded-full bg-gray-500/20 animate-pulse" />
                                <div className="flex-1">
                                    <div className="h-4 bg-gray-500/20 rounded w-1/3 mb-2 animate-pulse" />
                                    <div className="h-3 bg-gray-500/20 rounded w-1/4 mb-3 animate-pulse" />
                                    <div className="h-3 bg-gray-500/20 rounded w-full animate-pulse" />
                                </div>
                            </li>
                        ))}
                    </ul>
                ) : items.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">No tienes notificaciones nuevas.</div>
                ) : filtered.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">No hay notificaciones en esta categoría.</div>
                ) : (
                    <ul className="space-y-3">
                        {filtered.map((n) => (
                            <li
                                key={n.id}
                                className={`flex items-start gap-4 p-4 rounded-lg shadow-sm ${n.read ? 'opacity-75' : 'opacity-100'} bg-[var(--card)]`}
                            >
                                <div className="flex-shrink-0">
                                    <div
                                        className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold ${badgeColor(n.type)} ${n.read ? 'filter grayscale contrast-90' : ''}`}
                                        aria-hidden
                                    >
                                        {n.read ? (
                                            <Check className="h-4 w-4 text-current" />
                                        ) : n.type === 'mantenimiento' ? (
                                            'M'
                                        ) : n.type === 'diagnostico' ? (
                                            'D'
                                        ) : (
                                            '•'
                                        )}
                                    </div>
                                </div>

                                <div className="flex-1">
                                    <div className="flex items-center justify-between gap-4">
                                        <div>
                                            <h3 className={`text-sm font-medium ${n.read ? 'text-gray-400' : 'text-[var(--bg)]'}`}>{n.title}</h3>
                                            <p className={`${n.read ? 'text-gray-400' : 'text-xs text-[var(--accent-2)]'}`}>{new Date(n.date).toLocaleString()}</p>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => toggleRead(n.id)}
                                                className="text-xs text-[var(--accent)] hover:text-[var(--color-2)]"
                                            >
                                                {n.read ? 'Marcar como no leída' : 'Marcar como leída'}
                                            </button>
                                        </div>
                                    </div>

                                    <p className={`mt-2 text-sm ${n.read ? 'text-gray-400' : 'text-[var(--bg)]'}`}>{n.body}</p>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </main>
        </div>
    );
};

export default NotificacionesPage;
