import React from 'react';

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
    return (
        <div className="min-h-screen bg-[var(--bg)] text-white p-4">
            <div className="max-w-[420px] mx-auto">
                {/* Filters card */}
                <div className="rounded-xl p-4 mb-4" style={{ background: 'var(--accent)', boxShadow: '0 8px 20px rgba(0,0,0,0.45)' }}>
                    <div className="grid grid-cols-1 gap-3">
                        <label className="text-[var(--muted)] text-xs font-medium">Fecha</label>
                        <select className="w-full rounded-md p-2 border-2 text-black text-xs">
                            <option>Todas</option>
                            <option>Últimos 7 días</option>
                            <option>Últimos 30 días</option>
                        </select>

                        <label className="text-[var(--muted)] text-xs font-medium">Prioridad</label>
                        <select className="w-full rounded-md p-2 border-2 text-black text-xs">
                            <option>Todas las prioridades</option>
                            <option>Baja</option>
                            <option>Media</option>
                            <option>Alta</option>
                        </select>
                    </div>
                </div>

                {/* List */}
                <div className="space-y-5 mb-16">
                    {sample.map((s) => (
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
                    ))}
                </div>
            </div>
        </div>
    );
};

export default HistorialPage;