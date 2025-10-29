import React, { useState, useEffect } from 'react';
import { parse, subDays, isAfter } from 'date-fns';

type Analysis = {
    id: number;
    title: string;
    date: string; // ISO or display
    time: string;
    priority: 'Baja' | 'Media' | 'Alta';
    summary: string;
};

const sample: Analysis[] = [
    {
        id: 1,
        title: 'Análisis General',
        date: '12-05-2026',
        time: '3:30 pm',
        priority: 'Baja',
        summary:
            'En general la motocicleta se encuentra estable solo unas variaciones a la hora de llegar al tope de velocidad pero nada grave.',
    },
    {
        id: 2,
        title: 'Análisis General',
        date: '12-04-2025',
        time: '3:30 pm',
        priority: 'Media',
        summary:
            'En general la motocicleta se encuentra estable solo unas variaciones a la hora de llegar al tope de velocidad pero nada grave.',
    },
    {
        id: 3,
        title: 'Análisis General',
        date: '12-03-2025',
        time: '3:30 pm',
        priority: 'Alta',
        summary:
            'En general la motocicleta se encuentra estable solo unas variaciones a la hora de llegar al tope de velocidad pero nada grave.',
    },
    {
        id: 4,
        title: 'Análisis General',
        date: '12-02-2025',
        time: '3:30 pm',
        priority: 'Baja',
        summary:
            'En general la motocicleta se encuentra estable solo unas variaciones a la hora de llegar al tope de velocidad pero nada grave.',
    },
];

const priorityColor = (p: Analysis['priority']) => {
    switch (p) {
        case 'Baja':
            return 'bg-green-400 text-white';
        case 'Media':
            return 'bg-yellow-400 text-black';
        case 'Alta':
            return 'bg-red-400 text-white';
        default:
            return 'bg-gray-400 text-white';
    }
};

const HistorialPage: React.FC = () => {
    const [open, setOpen] = useState<boolean>(false);
    const [selectedDate, setSelectedDate] = useState<string>('Todas');
    const [selectedPriority, setSelectedPriority] = useState<string>('Todas');
    // simulate loading state for the list (show skeletons)
    const [isLoading, setIsLoading] = useState<boolean>(true);

    useEffect(() => {
        // simulate network/data load
        const t = setTimeout(() => setIsLoading(false), 700);
        return () => clearTimeout(t);
    }, []);
    return (
        <div className="min-h-screen bg-[var(--bg)] text-white p-4">
            <div className="max-w-[420px] mx-auto">
                {/* Filters header + toggle */}
                <div className="flex items-center justify-between mb-2">
                    <h2 className="text-[var(--card)] font-bold">Filtros</h2>
                    {/* Toggle button */}
                    <button
                        aria-controls="filters-panel"
                        aria-expanded={open}
                        onClick={() => setOpen((s: boolean) => !s)}
                        className="flex items-center gap-2 text-[var(--accent)]  px-3 py-1 rounded-md bg-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.06)] transition-colors"
                    >
                        <span className="hidden sm:inline">{open ? 'Ocultar' : 'Mostrar'}</span>
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className={`h-5 w-5 transform transition-transform duration-300 ${open ? 'rotate-180' : 'rotate-0'}`}
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2.5}
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                        </svg>
                    </button>
                </div>

                {/* Filters panel (collapsible with animation) */}
                <div id="filters-panel" className={`filter-panel ${open ? 'filter-panel--open' : 'filter-panel--closed'} rounded-xl p-4 mb-4`} style={{ background: 'var(--accent)', boxShadow: '0 8px 20px rgba(0,0,0,0.45)' }}>
                    <div className="grid grid-cols-1 gap-3">
                        <label className="text-[var(--bg)] text-xs">Fecha</label>
                        <select value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} className="w-full rounded-md p-2 border-2 text-black text-xs">
                            <option value="Todas">Todas</option>
                            <option value="7">Últimos 7 días</option>
                            <option value="30">Últimos 30 días</option>
                        </select>

                        <label className="text-[var(--bg)] text-xs">Prioridad</label>
                        <select value={selectedPriority} onChange={(e) => setSelectedPriority(e.target.value)} className="w-full rounded-md p-2 border-2 text-black text-xs">
                            <option value="Todas">Todas las prioridades</option>
                            <option value="Baja">Baja</option>
                            <option value="Media">Media</option>
                            <option value="Alta">Alta</option>
                        </select>
                    </div>
                </div>

                {/* List */}
                <div className="space-y-5 mb-16">
                    {(() => {
                        if (isLoading) {
                            // show 3 skeleton cards
                            return Array.from({ length: 3 }).map((_, idx) => (
                                <article key={`skeleton-${idx}`} className="rounded-lg overflow-hidden" style={{ background: 'transparent' }}>
                                    <div className="p-4 rounded-lg bg-[var(--card)] animate-pulse">
                                        <div className="flex items-start gap-3">
                                            <div className="flex-1">
                                                <div className="flex items-start justify-between gap-2">
                                                    <div>
                                                        <div className="h-4 bg-gray-400 rounded w-40 mb-2" />
                                                        <div className="h-3 bg-gray-500 rounded w-24" />
                                                    </div>

                                                    <div className="flex items-center gap-2">
                                                        <div className="h-6 w-20 bg-gray-500 rounded-full" />
                                                    </div>
                                                </div>

                                                <div className="mt-3 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)' }}>
                                                    <div className="flex items-start gap-3">
                                                        <div className="w-10 h-10 rounded-md bg-gray-500" />
                                                        <div className="space-y-2 flex-1">
                                                            <div className="h-3 bg-gray-500 rounded w-full" />
                                                            <div className="h-3 bg-gray-500 rounded w-5/6" />
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </article>
                            ));
                        }

                        const now = new Date();
                        const filtered = sample.filter((s) => {
                            if (selectedPriority !== 'Todas' && s.priority !== selectedPriority) return false;
                            if (selectedDate === '7' || selectedDate === '30') {
                                const parsed = parse(s.date, 'dd-MM-yyyy', new Date());
                                const days = selectedDate === '7' ? 7 : 30;
                                const since = subDays(now, days);
                                if (isAfter(since, parsed)) return false;
                            }
                            return true;
                        });

                        if (filtered.length === 0) {
                            return (
                                <div className="p-6 rounded-lg bg-[var(--card)] text-center text-sm text-[var(--color-2)]">No hay diagnósticos en este periodo</div>
                            );
                        }

                        return filtered.map((s) => (
                            <article key={s.id} className="rounded-lg overflow-hidden" style={{ background: 'transparent' }}>
                                <div className="p-4 rounded-lg bg-[var(--card)]">
                                    <div className="flex items-start gap-3">
                                        <div className="flex-1">
                                            <div className="flex items-start justify-between gap-2">
                                                <div>
                                                    <h3 className="font-bold text-white">{s.title}</h3>
                                                    <div className="text-[var(--color-2)] text-sm mt-1 flex items-center gap-2">
                                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-[var(--color-2)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                                            <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3M3 11h18M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                        </svg>
                                                        <span className="text-sm">{s.date}</span>
                                                        <span className="text-[var(--color-2)]">•</span>
                                                        <span className="text-sm">{s.time}</span>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-2">
                                                    <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-bold ${priorityColor(s.priority)}`}>{s.priority}</span>
                                                </div>
                                            </div>

                                            <div className="mt-3 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.06)' }}>
                                                <div className="flex items-start gap-3">
                                                    <div className="rounded-md flex items-center justify-center text-black font-extrabold">RIM</div>
                                                    <div className="text-[var(--color-2)] text-sm">{s.summary}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </article>
                        ));
                    })()}
                </div>
            </div>
        </div>
    );
};

export default HistorialPage;