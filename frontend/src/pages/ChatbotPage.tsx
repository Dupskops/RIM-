import { useEffect, useRef, useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Bot, Send, Loader2, Sparkles, RefreshCcw, Trash2, X } from 'lucide-react';

type Msg = {
    id: string;
    from: 'user' | 'bot';
    text: string;
    time?: string;
};

const sampleReplies = [
    'Hola 👋, ¿en qué puedo ayudarte hoy?',
    'Puedo analizar diagnósticos, notificaciones y ayudarte con el mantenimiento.',
    '¿Quieres que revise el último informe de la moto?',
    'Puedes preguntarme por el estado de la batería o cuándo hacer el próximo mantenimiento.'
];

export default function ChatbotPage() {
    const navigate = useNavigate();
    const [msgs, setMsgs] = useState<Msg[]>(() => [
        { id: 'm1', from: 'bot', text: 'Hola, soy RIM. Puedo ayudarte con diagnósticos y dudas sobre tu moto.' },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [connected, setConnected] = useState(true);
    const [showQuickActions, setShowQuickActions] = useState(false);
    const containerRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        // scroll to bottom when msgs change
        const el = containerRef.current;
        if (el) {
            el.scrollTop = el.scrollHeight;
        }
    }, [msgs]);

    function sendMessage(text: string) {
        if (!text.trim()) return;
        const userMsg: Msg = { id: Date.now().toString(), from: 'user', text: text.trim() };
        setMsgs((s) => [...s, userMsg]);
        setInput('');
        setLoading(true);

        // simulate bot reply
        setTimeout(() => {
            const reply = sampleReplies[Math.floor(Math.random() * sampleReplies.length)];
            const botMsg: Msg = { id: 'b' + Date.now().toString(), from: 'bot', text: reply };
            setMsgs((s) => [...s, botMsg]);
            setLoading(false);
        }, 900 + Math.random() * 700);
    }

    return (
        <div className=" bg-[var(--bg)] text-white p-4">
            <div className="max-w-3xl mx-auto">
                <header className="flex items-center justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-[var(--card)] flex items-center justify-center text-[var(--accent)] shadow">
                            <Bot />
                        </div>
                        <div>
                            <h2 className="font-bold text-lg text-[var(--card)]">RIM</h2>
                            <div className="text-xs text-[var(--muted)]">Asistente virtual </div>
                            <div className="border-t border-[rgba(255,255,255,0.03)]">
                                <div className="flex items-center gap-2">
                                    <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
                                    <div className="text-xs text-[var(--muted)]">{connected ? 'Conectado' : 'Desconectado'}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            title="Cerrar"
                            onClick={() => navigate({ to: '/app' })}
                            className="p-2 rounded-md bg-[var(--card)] hover:bg-[var(--accent)]"
                        >
                            <X size={16} />
                        </button>
                        <button
                            title="Reconectar"
                            onClick={() => { setConnected(true); }}
                            className="p-2 rounded-md bg-[var(--card)] hover:bg-[var(--accent)]"
                        >
                            <RefreshCcw size={16} />
                        </button>
                        <button
                            title="Borrar conversación"
                            onClick={() => setMsgs([])}
                            className="p-2 rounded-md bg-[var(--card)] hover:bg-[var(--accent)]"
                        >
                            <Trash2 size={16} />
                        </button>
                    </div>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* conversation column */}
                    <div className="md:col-span-2 flex flex-col bg-[var(--card)] rounded-xl overflow-hidden h-[70vh] md:h-[72vh]">
                        <div ref={containerRef} className="flex-1 p-4 space-y-3 overflow-y-auto">
                            {msgs.map((m) => (
                                <div key={m.id} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`${m.from === 'user' ? 'bg-[var(--accent)] text-[#071218]' : 'bg-[rgba(255,255,255,0.03)] text-[var(--color-2)]'} max-w-[80%] p-3 rounded-lg`}>
                                        <div className="text-sm whitespace-pre-wrap">{m.text}</div>
                                    </div>
                                </div>
                            ))}

                            {loading && (
                                <div className="flex justify-start">
                                    <div className="bg-[rgba(255,255,255,0.03)] p-2 rounded-lg flex items-center gap-2">
                                        <Loader2 className="animate-spin" size={16} />
                                        <span className="text-[var(--color-2)] text-sm">RIM está escribiendo...</span>
                                    </div>
                                </div>
                            )}
                        </div>
                        {/* quick actions toggle above input */}
                        <div className="p-3 border-t border-[rgba(255,255,255,0.03)] bg-[rgba(0,0,0,0.02)] relative">
                            <div className="flex justify-center mb-3">
                                <button
                                    aria-label="Acciones rápidas"
                                    title="Acciones rápidas"
                                    onClick={() => setShowQuickActions((s) => !s)}
                                    className="w-12 h-12 rounded-full bg-[var(--accent)] text-[#071218] flex items-center justify-center shadow-md"
                                >
                                    <Sparkles />
                                </button>
                            </div>

                            {showQuickActions && (
                                <div className="mb-3 mx-auto max-w-xl">
                                    <div className="bg-[var(--card)] rounded-xl p-3 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <h4 className="font-semibold text-[var(--bg)]">Sugerencias</h4>
                                            <span className="text-xs text-[var(--color-2)]">Interacción rápida</span>
                                        </div>

                                        <div className="grid gap-2">
                                            {['Último diagnóstico', 'Estado de batería', 'Próximo mantenimiento', 'Recomendaciones de viaje'].map((s) => (
                                                <button
                                                    key={s}
                                                    onClick={() => { sendMessage(s); setShowQuickActions(false); }}
                                                    className="text-left px-3 py-2 rounded-lg bg-[rgba(255,255,255,0.02)] hover:bg-[rgba(255,255,255,0.04)]"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <Sparkles size={16} className="text-[var(--accent)]" />
                                                        <div className="text-sm">{s}</div>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* input area */}
                            <div className="flex items-center gap-3">
                                <input
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => { if (e.key === 'Enter') sendMessage(input); }}
                                    placeholder="Escribe tu pregunta aquí..."
                                    className="flex-1 rounded-xl p-3 bg-[var(--bg)] border border-[rgba(255,255,255,0.03)] focus:outline-none text-[var(--muted)]"
                                />
                                <button
                                    onClick={() => sendMessage(input)}
                                    disabled={!input.trim()}
                                    className="p-3 rounded-xl bg-[var(--accent)] text-[#071218] disabled:opacity-60"
                                >
                                    <Send />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}