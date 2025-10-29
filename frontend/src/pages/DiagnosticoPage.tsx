import React, { useEffect, useRef, useState } from "react";
import { Droplet, Gauge, Zap, Wrench, Battery, LassoSelect } from "lucide-react";
import PopUp from "../components/pop-up";
import type { StatusCard as PopStatusCard } from "../components/pop-up";
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

const DiagnosticoPage: React.FC = () => {
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  // model loading skeleton control
  const [modelLoading, setModelLoading] = useState<boolean>(true);

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
  // Orbit controls ref and helper type
  type ControlsLike = {
    autoRotate?: boolean;
    dollyIn?: (n: number) => void;
    dollyOut?: (n: number) => void;
    update?: () => void;
    object?: { position?: { z?: number } };
  };
  const orbitRef = useRef<ControlsLike | null>(null);

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
              <Canvas className="w-full h-full" camera={{ position: [0, 0, 4] }} onCreated={() => setTimeout(() => setModelLoading(false), 350)}>
                 <ambientLight intensity={0.8} />
                 <directionalLight position={[5, 5, 5]} intensity={0.6} />
                 {/* Simple placeholder model (replace with GLTF model via useGLTF) */}
                 {!modelLoading && (
                   <mesh rotation={[0.4, 0.7, 0]}>
                     <torusKnotGeometry args={[0.8, 0.3, 128, 32]} />
                     <meshStandardMaterial color="#9ca3af" metalness={0.6} roughness={0.2} />
                   </mesh>
                 )}

                {/* OrbitControls: ref will be set to orbitRef so DOM buttons can control it */}
                <OrbitControls ref={(el) => { orbitRef.current = el as unknown as ControlsLike; }} makeDefault enablePan enableZoom enableRotate />
              </Canvas>

                {/* Controls overlay (rotation toggle + zoom) - will be hooked to OrbitControls when present */}
                {!modelLoading && (
                  <div className="absolute right-3 top-3 flex flex-col gap-2 z-20">
                    <LassoSelect className=" bg-[var(--card)] text-[var(--bg)]/80 p-2 rounded-md shadow w-8 h-8" onClick={() => {
                      const controls = orbitRef.current;
                      if (controls) {
                        controls.autoRotate = !controls.autoRotate;
                      }
                    }}/>

                    <div className="flex flex-col bg-[var(--card)] rounded-md p-1 shadow">
                      <button
                        type="button"
                        className="px-2 py-1 text-sm"
                        onClick={() => {
                          const controls = orbitRef.current;
                          if (controls && typeof controls.dollyOut === 'function') {
                            controls.dollyOut(1.1);
                            if (controls.update) controls.update();
                          } else if (controls && controls.object && controls.object.position && typeof controls.object.position.z === 'number') {
                            controls.object.position.z *= 1.1;
                          }
                        }}
                        title="Zoom +"
                      >
                        +
                      </button>
                      <button
                        type="button"
                        className="px-2 py-1 text-sm"
                        onClick={() => {
                          const controls = orbitRef.current;
                          if (controls && typeof controls.dollyIn === 'function') {
                            controls.dollyIn(1.1);
                            if (controls.update) controls.update();
                          } else if (controls && controls.object && controls.object.position && typeof controls.object.position.z === 'number') {
                            controls.object.position.z /= 1.1;
                          }
                        }}
                        title="Zoom -"
                      >
                        -
                      </button>
                    </div>
                  </div>
                )}
                {modelLoading && (
                  <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/40">
                    <div className="w-32 h-20 rounded-lg bg-gray-500/10 animate-pulse" aria-hidden />
                  </div>
                )}
            </div>

            {/* Colored status points positioned around the bike (percent-based for responsiveness) */}
            {[
              { id: 'p1', left: '50%', top: '40%', color: 'green', title: 'Frenos' },
              { id: 'p2', left: '45%', top: '58%', color: 'blue', title: 'Tanque' },
              { id: 'p3', left: '64%', top: '38%', color: 'orange', title: 'Motor' },
              { id: 'p4', left: '18%', top: '60%', color: 'red', title: 'Neumático delantero' },
              { id: 'p5', left: '28%', top: '55%', color: 'green', title: 'Neumático trasero' },
              { id: 'p6', left: '72%', top: '60%', color: 'green', title: 'Batería' },
            ].map((pt, idx) => {
              const colorClass = pt.color === 'green' ? 'bg-green-500' : pt.color === 'blue' ? 'bg-sky-400' : pt.color === 'orange' ? 'bg-orange-400' : 'bg-red-500';
              const linkedCard = statusCards[idx];

              const activate = () => {
                setSelectedId(linkedCard.id);
                if (!started) {
                  handleGenerate();
                } else if (!loading) {
                  scrollToCard(linkedCard.id);
                }
              };

              const onKeyDown = (e: React.KeyboardEvent) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  activate();
                }
              };

              return (
                <div
                  key={pt.id}
                  role="button"
                  tabIndex={0}
                  aria-label={pt.title}
                  onClick={activate}
                  onKeyDown={onKeyDown}
                  className="absolute rounded-full flex items-center justify-center transform -translate-x-1/2 -translate-y-1/2 group cursor-pointer"
                  style={{ left: pt.left, top: pt.top }}
                >
                  <span className={`block w-5 h-5 rounded-full border-2 border-white ${colorClass}`} />
                  <span className="absolute w-9 h-9 rounded-full opacity-20" style={{ background: 'transparent' }} />

                  {/* Tooltip: visible on hover or focus (accessible) */}
                  <div className="pointer-events-none absolute -top-9 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-black/80 text-white text-xs px-2 py-1 opacity-0 scale-95 transform transition-all duration-150 group-hover:opacity-100 group-hover:scale-100 group-focus:opacity-100" role="tooltip">
                    {pt.title}
                  </div>
                </div>
              );
            })}

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