import { useEffect, useRef, useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Bot, Send, Loader2, Sparkles, RefreshCcw, Trash2, X, MoreVertical, Plus, Clock } from 'lucide-react';

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

const initialMsgs: Msg[] = [
    { id: 'm1', from: 'bot', text: 'Hola, soy RIM. Puedo ayudarte con diagnósticos y dudas sobre tu moto.' },
];

export default function ChatbotPage() {
    const navigate = useNavigate();
    type Conversation = { id: string; title?: string; msgs: Msg[]; createdAt: number; updatedAt: number };

    const firstConvId = Date.now().toString();
    const now = Date.now();
    const [conversations, setConversations] = useState<Conversation[]>(() => [
        { id: firstConvId, title: undefined, msgs: initialMsgs, createdAt: now, updatedAt: now },
    ]);
    const [currentConvId, setCurrentConvId] = useState<string>(firstConvId);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [connected, setConnected] = useState(true);
    const [showQuickActions, setShowQuickActions] = useState(false);
    const [showMenu, setShowMenu] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const containerRef = useRef<HTMLDivElement | null>(null);
    const menuRef = useRef<HTMLDivElement | null>(null);
    const historyRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        // scroll to bottom when msgs change
        const el = containerRef.current;
        if (el) {
            el.scrollTop = el.scrollHeight;
        }
    }, [conversations, currentConvId]);

    // close history modal with Escape
    useEffect(() => {
        if (!showHistory) return;
        const onKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') setShowHistory(false);
        };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [showHistory]);

    function sendMessage(text: string) {
        if (!text.trim()) return;
        const userMsg: Msg = { id: Date.now().toString(), from: 'user', text: text.trim() };
    setConversations((prev) => prev.map((c) => c.id === currentConvId ? { ...c, msgs: [...c.msgs, userMsg], updatedAt: Date.now() } : c));
        setInput('');
        setLoading(true);

        // simulate bot reply
        setTimeout(() => {
            const reply = sampleReplies[Math.floor(Math.random() * sampleReplies.length)];
            const botMsg: Msg = { id: 'b' + Date.now().toString(), from: 'bot', text: reply };
            setConversations((prev) => prev.map((c) => c.id === currentConvId ? { ...c, msgs: [...c.msgs, botMsg], updatedAt: Date.now() } : c));
            setLoading(false);
        }, 900 + Math.random() * 700);
    }

    const currentConv = conversations.find((c) => c.id === currentConvId) as Conversation;

    function generateTitle(conv: Conversation) {
        // If conversation already has an explicit title, use it
        if (conv.title) return conv.title;

        // Try to find the first user message to summarize
        const firstUser = conv.msgs.find((m) => m.from === 'user') || conv.msgs[0];
        const text = (firstUser?.text || '').toLowerCase();

        // simple keyword mapping to nicer titles
        const mappings: [RegExp, string][] = [
            [/bater[ií]a|bateria/, 'Diagnóstico de batería'],
            [/diagn[oó]stic|diagnostico/, 'Diagnóstico'],
            [/mantenim|mantenimiento/, 'Próximo mantenimiento'],
            [/viaje|ruta|itinerario/, 'Recomendaciones de viaje'],
            [/informe|reporte/, 'Informe de la moto'],
            [/estado/, 'Estado de la moto'],
            [/sensor|sensores/, 'Revisión de sensores'],
        ];

        for (const [re, title] of mappings) {
            if (re.test(text)) return title;
        }

        // fallback: use a short snippet of the first user message, capitalized
        const snippet = (firstUser?.text || 'Nueva conversación').trim();
        const short = snippet.length > 40 ? snippet.slice(0, 37) + '...' : snippet;
        return short.charAt(0).toUpperCase() + short.slice(1);
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

                        <div className="relative" ref={menuRef}>
                            <button
                                aria-label="Más opciones"
                                title="Más opciones"
                                onClick={() => setShowMenu((s) => !s)}
                                className="p-2 rounded-md bg-[var(--card)] hover:bg-[var(--accent)]"
                            >
                                <MoreVertical size={16} />
                            </button>

                            {showMenu && (
                                <div className="absolute right-0 mt-2 w-56 bg-[var(--card)] rounded-md shadow-md p-2 z-20">
                                    <button className="w-full text-left px-3 py-2 rounded hover:bg-[var(--accent)]" onClick={() => { setShowMenu(false); setConnected(true); }}>
                                        <div className="flex items-center gap-2"><RefreshCcw size={14} /><span>Reconectar</span></div>
                                    </button>

                                    <button className="w-full text-left px-3 py-2 rounded hover:bg-[var(--accent)]" onClick={() => { setShowMenu(false); setShowHistory(true); }}>
                                        <div className="flex items-center gap-2"><Clock size={14} /><span>Historial de mensajes</span></div>
                                    </button>

                                    <button className="w-full text-left px-3 py-2 rounded hover:bg-[var(--accent)]" onClick={() => { setShowMenu(false); setConversations((prev) => prev.map((c) => c.id === currentConvId ? { ...c, msgs: [], updatedAt: Date.now() } : c)); }}>
                                        <div className="flex items-center gap-2"><Trash2 size={14} /><span>Borrar conversación</span></div>
                                    </button>
                                </div>
                            )}
                        </div>

                        <button
                            title="Nueva conversación"
                            onClick={() => {
                                const id = Date.now().toString();
                                const now = Date.now();
                                const newConv = { id, title: undefined, msgs: initialMsgs, createdAt: now, updatedAt: now };
                                setConversations((prev) => [...prev, newConv]);
                                setCurrentConvId(id);
                            }}
                            className="p-2 rounded-md bg-[var(--card)] hover:bg-[var(--accent)]"
                        >
                            <Plus size={16} />
                        </button>
                    </div>
                </header>

                {showHistory && (
                    <div className="fixed inset-0 z-30 flex items-center justify-center">
                        <div className="absolute inset-0 bg-black/50" onClick={() => setShowHistory(false)} />

                        <div ref={historyRef} className="relative w-full max-w-2xl mx-4 bg-[var(--card)] rounded-lg p-4 text-[var(--muted)] z-40">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-[var(--bg)]">Historial de mensajes</h3>
                                <button
                                    aria-label="Cerrar historial"
                                    onClick={() => setShowHistory(false)}
                                    className="p-2 rounded-md bg-[var(--card)] hover:bg-[var(--accent)]"
                                >
                                    <X size={16} />
                                </button>
                            </div>

                            <div className="max-h-80 overflow-y-auto divide-y divide-[rgba(255,255,255,0.03)]">
                                {conversations.length > 0 ? (
                                    conversations.map((conv) => (
                                        <button
                                            key={conv.id}
                                            onClick={() => { setCurrentConvId(conv.id); setShowHistory(false); }}
                                            aria-label={`Abrir ${generateTitle(conv)}`}
                                            className={`w-full text-left px-3 py-3 flex items-start gap-3 transition-all duration-150 focus:outline-none ${currentConvId === conv.id ? 'bg-[rgba(255,255,255,0.03)] ring-1 ring-[var(--accent)]' : 'hover:bg-[rgba(255,255,255,0.02)]'}`}
                                        >
                                            <div className="flex-shrink-0 w-10 h-10 rounded-md bg-[rgba(255,255,255,0.02)] flex items-center justify-center text-[var(--accent)] font-semibold">{generateTitle(conv).split(' ')[0]?.slice(0,2).toUpperCase()}</div>

                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-semibold text-[var(--bg)] truncate">{generateTitle(conv)}</div>
                                                <div className="text-xs text-[var(--muted)] truncate">Último: {conv.msgs.length ? (conv.msgs[conv.msgs.length - 1].text.length > 60 ? conv.msgs[conv.msgs.length - 1].text.slice(0,57) + '...' : conv.msgs[conv.msgs.length - 1].text) : 'Sin mensajes'}</div>
                                            </div>

                                            <div className="ml-3 flex-shrink-0 flex flex-col items-end gap-1 text-right">
                                                <div className="bg-[var(--accent)] text-[#071218] px-2 py-1 rounded-full text-xs font-medium">{conv.msgs.length}</div>
                                                <div className="text-[var(--muted)] text-[11px]">{new Date(conv.updatedAt).toLocaleString()}</div>
                                            </div>
                                        </button>
                                    ))
                                ) : (
                                    <div className="p-3 text-sm text-[var(--muted)]">No hay conversaciones.</div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* conversation column */}
                    <div className="md:col-span-2 flex flex-col bg-[var(--card)] rounded-xl overflow-hidden h-[70vh] md:h-[72vh]">
                        <div ref={containerRef} className="flex-1 p-4 space-y-3 overflow-y-auto">
                            {(currentConv?.msgs || []).map((m: Msg) => (
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