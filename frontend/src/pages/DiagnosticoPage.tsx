import React, { useEffect, useRef, useState } from "react";
import { Droplet, Gauge, Zap, Wrench, Battery } from "lucide-react";
import PopUp from "../components/pop-up";
import type { StatusCard as PopStatusCard } from "../components/pop-up";
import Moto3D from "../components/Moto3D.tsx";

const DiagnosticoPage: React.FC = () => {
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  // (now using external Moto3D component)

  type StatusCard = { id: string; title: string; state: string; colorClass: string; icon: React.ComponentType<{ className?: string }> };

  const statusCards: StatusCard[] = [
    // Correspond to the 6 points shown around the bike
    { id: 's1', title: 'Sistema de Frenos', state: 'Excelente', colorClass: 'bg-green-500', icon: Zap },
    { id: 's2', title: 'Tanque', state: 'Bueno', colorClass: 'bg-sky-400', icon: Droplet },
    { id: 's3', title: 'Motor', state: 'Atención', colorClass: 'bg-orange-400', icon: Wrench },
    { id: 's4', title: 'Neumático delantero', state: 'Crítico', colorClass: 'bg-red-500', icon: Gauge },
    { id: 's5', title: 'Neumático trasero', state: 'Excelente', colorClass: 'bg-green-500', icon: Gauge },
    { id: 's6', title: 'Batería', state: 'Excelente', colorClass: 'bg-green-500', icon: Battery },
  ];

  const handleGenerate = () => {
    // Si ya se inició, reiniciamos la carga para simular re-ejecución
    setStarted(true);
    setLoading(true);
    // Simula llamada asíncrona (reemplazar por llamada real si aplica)
    setTimeout(() => {
      setLoading(false);
    }, 1100);
  };

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});
  // Orbit controls ref (not used here but kept for future control hooks)
  // If unused, keep commented to avoid lint warnings.

  const scrollToCard = (id: string | null) => {
    if (!id) return;
    const el = cardRefs.current[id];
    if (el && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // When loading finishes (or when a selection is changed and we're not loading), scroll to the card
  useEffect(() => {
    if (!loading && selectedId) {
      // small timeout to ensure DOM has rendered the list
      setTimeout(() => scrollToCard(selectedId), 80);
    }
  }, [loading, selectedId]);

  // Modal for detalle (no backend, use created data)
  const [modalOpen, setModalOpen] = useState(false);
  const [modalCard, setModalCard] = useState<StatusCard | PopStatusCard | null>(null);

  // When a 3D marker is selected, try to find the matching status card and open it
  const handleMarkerSelect = (label: string) => {
    if (!label) return;
    // try to find a card that matches the label (case-insensitive, partial match)
    const found = statusCards.find((c) => {
      const a = c.title.toLowerCase();
      const b = label.toLowerCase();
      return a.includes(b) || b.includes(a) || b.includes(a.split(' ')[0]);
    });

    if (found) {
      setSelectedId(found.id);
      setModalCard(found as StatusCard);
      setModalOpen(true);
      if (!started) {
        handleGenerate();
      } else if (!loading) {
        scrollToCard(found.id);
      }
    } else {
      // fallback: just open generic modal
      setModalCard({ id: 'unknown', title: label, state: 'Desconocido', colorClass: 'bg-gray-400', icon: Zap });
      setModalOpen(true);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] px-4 pb-3">
      {/* Header (no back arrow) */}
      <header className="py-3 ">
        <h2 className="text-center text-lg font-bold text-[var(--card)]">Diagnóstico Avanzado</h2>
      </header>

      <main className="max-w-md mx-auto space-y-4">
        {/* Image with overlay icons */}
        <div className="bg-[var(--card)] rounded-lg p-4 flex justify-center h-100">
          <div className="relative w-full max-w-xl">
            {/* 3D canvas: keep same container size so overlay points map correctly */}
              <div className="w-full h-[360px] rounded-md shadow-md bg-black relative overflow-hidden">
              {/* Moto3D component (loads /models/moto.glb from public/models) */}
              <Moto3D onMarkerSelect={handleMarkerSelect} />
            </div>

            {/* Legend overlay (bottom-left of image) */}
            <div className="absolute left-4 bottom-4 bg-[rgba(0,0,0,0.5)] text-[var(--color-2)] rounded-md p-3 text-sm">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-green-500" />
                  <span>Excelente</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-sky-400" />
                  <span>Bueno</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-orange-400" />
                  <span>Atención</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-red-500" />
                  <span>Crítico</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading}
            className="w-full py-3 bg-[var(--accent)] text-[var(--bg)] font-semibold rounded-lg shadow-[var(--accent-shadow)] hover:brightness-95 transition disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-3 "
          >
            {loading ? (
              <>
                <svg className="w-5 h-5 animate-spin text-black" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeOpacity="0.25" />
                  <path d="M22 12a10 10 0 00-10-10" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
                </svg>
                <span>Analizando...</span>
              </>
            ) : (
              'Generar diagnóstico'
            )}
          </button>
        </div>
        {/* Status list: hidden until started. Appear with nice animation when loading finishes. */}
        <div className="space-y-3">
          {!started ? (
            <div className="text-center text-sm text-[var(--muted)]">Presiona "Generar diagnóstico" para iniciar el análisis.</div>
          ) : (
            <div className="space-y-3" aria-live="polite">
              {loading ? (
                <div className="bg-[var(--card)] rounded-lg p-5 flex items-center justify-center">
                  <svg className="w-10 h-10 animate-spin text-[var(--accent)]" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.2" />
                    <path d="M22 12a10 10 0 00-10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                  </svg>
                </div>
              ) : (
                // Resultado: lista con animación y stagger
                <div className="grid grid-cols-1 gap-3 mb-20">
                  {statusCards.map((card, idx) => {
                    const Icon = card.icon;
                    const selected = selectedId === card.id;
                    return (
                      <div
                        key={card.id}
                        ref={(el) => { cardRefs.current[card.id] = el; }}
                        onClick={() => { setSelectedId(card.id); setModalCard(card as StatusCard); setModalOpen(true); }}
                        className={`bg-[var(--card)] rounded-lg p-3 transform transition-all duration-500 ease-out cursor-pointer ${selected ? 'ring-2 ring-[var(--accent)]' : ''}`}
                        style={{ transitionDelay: `${idx * 80}ms`, opacity: 1, transform: 'translateY(0)' }}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-full bg-[rgba(255,255,255,0.04)] flex items-center justify-center text-[var(--accent)]">
                            <Icon className="w-5 h-5 text-[var(--accent)]" />
                          </div>
                          <div className="flex-1">
                            <div className="text-sm text-[var(--color-2)] font-semibold">{card.title}</div>
                            <div className="mt-2 text-xs text-[var(--color-2)] bg-[rgba(255,255,255,0.03)] p-3 rounded-md">Estado: {card.state}</div>
                          </div>
                          <div className="ml-2 flex items-center">
                            <span className={`w-3 h-3 rounded-full ${card.colorClass}`} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Reusable PopUp component */}
        <PopUp open={modalOpen} card={modalCard as PopStatusCard | null} onClose={() => setModalOpen(false)} />
      </main>
    </div>
  );
};

export default DiagnosticoPage;