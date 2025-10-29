import {
  Battery,
  Zap,
  Droplet,
  Gauge,
  AlertCircle,
  MapPin,
  Calendar,
  Clock,
  RotateCw,
  ZoomIn,
} from "lucide-react";
import { useMotos } from '@/hooks/useMotos';
import { useMotoStore } from '@/store';
import { useState } from 'react';
import FormularioNewMoto from "@/components/formulario";
const HomePage: React.FC = () => {
  const motosQuery = useMotos();
  const motos = useMotoStore((s) => s.motos);

  const hasMoto = Array.isArray(motos) && motos.length > 0;
  // botones del visor 3D (placeholders — conectar con API del visor si existe)
  const handleRotate = () => {
    // Si tienes un controlador 3D, llama aquí: e.g. modelViewer.rotate(90)
    // por ahora solo log
    console.log('3D: rotate requested');
  };

  const handleZoomIn = () => {
    console.log('3D: zoom in requested');
  };
  // Modal state (el formulario maneja su propio estado interno)
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="min-h-screen pb-20 bg-[var(--bg)]">

      {/* Content: render only the active view (no page sliding). Hover transitions are applied to interactive elements. */}
      <div className="max-w-5xl mx-auto px-4">
        {/* HOME */}
        <div className="flex flex-col gap-4">
          <section
            className="h-85 rounded-lg shadow-xl p-2 mb-4 transform transition-transform duration-200 hover:-translate-y-1"
            style={{ background: "var(--card)" }}
          >
            <div className="flex flex-col gap-2">
              <div
                className="flex items-center gap-2"
                aria-hidden
              >
                {/* badges placeholder */}
              </div>

            {/* Modelo 3D */}
              <div className="flex items-center justify-center p-2 relative">
                <div className="h-80 w-full max-w-3xl rounded-lg overflow-hidden shadow-2xl flex items-center justify-center bg-[rgba(255,255,255,0.02)] relative">
                  {/* Loading state */}
                  {motosQuery.isLoading ? (
                    <div className="w-full h-full animate-pulse" />
                  ) : hasMoto ? (
                    // Mostrar modelo 3D (placeholder actual, aquí iría el canvas/visor 3D)
                    <div
                      className="w-full"
                      role="img"
                      aria-label="Modelo 3D de la moto"
                      style={{
                        height: 'clamp(310px,42vw,420px)',
                        background:
                          'linear-gradient(180deg, rgba(2,6,8,0.8), rgba(0,0,0,0.65))',
                      }}
                    />
                  ) : (
                    // No tiene moto: mostrar botón para agregar
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3">
                      <div className="text-[var(--color-2)]">No tienes una moto registrada</div>
                      <button
                        onClick={() => setShowForm(true)}
                        className="px-5 py-2 rounded-md font-bold bg-[var(--accent)] text-[var(--bg)] shadow-md transition-transform duration-200 ease-in-out hover:-translate-y-1 hover:scale-[1.03]"
                        aria-label="Agregar moto"
                      >
                        + Agregar moto
                      </button>
                    </div>
                  )}
                  {/* Overlay buttons (rotate / zoom) — sólo cuando hay moto */}
                  {hasMoto && (
                    <div className="absolute right-4 bottom-4 flex gap-3">
                      <button
                        onClick={handleRotate}
                        aria-label="rotar-modelo"
                        title="Rotar modelo"
                        className="w-10 h-10 rounded-full bg-[rgba(0,0,0,0.6)] border border-white/10 flex items-center justify-center text-white hover:scale-105 transition-transform shadow-md"
                      >
                        <RotateCw size={18} />
                      </button>

                      <button
                        onClick={handleZoomIn}
                        aria-label="acercar-modelo"
                        title="Acercar modelo"
                        className="w-10 h-10 rounded-full bg-[rgba(0,0,0,0.6)] border border-white/10 flex items-center justify-center text-white hover:scale-105 transition-transform shadow-md"
                      >
                        <ZoomIn size={18} />
                      </button>
                    </div>
                  )}
                </div>

                {/* Badges: sólo mostrar si hay una moto */}
                {hasMoto && (
                  <div className="absolute left-4 top-4 flex flex-col gap-2">
                    <span
                      className="px-2 py-1 rounded-full font-semibold text-[var(--accent)]"
                      style={{
                        background:
                          'linear-gradient(90deg, rgba(254,119,67,0.12), rgba(254,119,67,0.06))',
                        border: '1px solid rgba(254,119,67,0.12)',
                      }}
                    >
                      Encendido
                    </span>
                    <span
                      className="px-2 py-1 rounded-full font-semibold text-[var(--accent-2)]"
                      style={{
                        background:
                          'linear-gradient(90deg, rgba(68,125,155,0.08), rgba(68,125,155,0.04))',
                        border: '1px solid rgba(68,125,155,0.06)',
                      }}
                    >
                      En línea
                    </span>
                  </div>
                )}
              </div>
            </div>
          </section>

          <FormularioNewMoto showForm={showForm} onClose={() => setShowForm(false)} />

          <section
            className="rounded-lg p-6"
            style={{ background: "var(--card)" }}
            aria-label="Resumen rápido del vehículo"
          >
            <h3 className="text-lg font-bold text-[var(--color-2)] mb-3">
              Estado Actual
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div
                className="flex flex-col items-center text-center p-3 rounded-md transform transition-transform duration-200 hover:-translate-y-1"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(255,255,255,0.01), transparent)",
                  border: "1px solid rgba(255,255,255,0.02)",
                }}
              >
                <div className="w-9 h-9 rounded-md bg-gradient-to-b from-[var(--accent)] to-[var(--accent-2)] flex items-center justify-center text-white">
                  <Zap size={18} />
                </div>
                {motosQuery.isLoading ? (
                  <div className="mt-2 h-6 w-14 rounded bg-gray-500/20 animate-pulse" />
                ) : (
                  <div className="mt-2 text-lg font-extrabold text-white">92%</div>
                )}
                <div className="text-xs text-[var(--color-2)]">
                  Combustible
                </div>
              </div>

              <div
                className="flex flex-col items-center text-center p-3 rounded-md transform transition-transform duration-200 hover:-translate-y-1"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(255,255,255,0.01), transparent)",
                  border: "1px solid rgba(255,255,255,0.02)",
                }}
              >
                <div className="w-9 h-9 rounded-md bg-gradient-to-b from-[var(--accent)] to-[var(--accent-2)] flex items-center justify-center text-white">
                  <Battery size={18} />
                </div>
                {motosQuery.isLoading ? (
                  <div className="mt-2 h-6 w-14 rounded bg-gray-500/20 animate-pulse" />
                ) : (
                  <div className="mt-2 text-lg font-extrabold text-white">98%</div>
                )}
                <div className="text-xs text-[var(--color-2)]">
                  Batería
                </div>
              </div>

              <div
                className="flex flex-col items-center text-center p-3 rounded-md transform transition-transform duration-200 hover:-translate-y-1"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(255,255,255,0.01), transparent)",
                  border: "1px solid rgba(255,255,255,0.02)",
                }}
              >
                <div className="w-9 h-9 rounded-md bg-gradient-to-b from-[var(--accent)] to-[var(--accent-2)] flex items-center justify-center text-white">
                  <Droplet size={18} />
                </div>
                {motosQuery.isLoading ? (
                  <div className="mt-2 h-6 w-20 rounded bg-gray-500/20 animate-pulse" />
                ) : (
                  <div className="mt-2 text-lg font-extrabold text-white">16 cSt</div>
                )}
                <div className="text-xs text-[var(--color-2)]">
                  Viscosidad
                </div>
              </div>

              <div
                className="flex flex-col items-center text-center p-3 rounded-md transform transition-transform duration-200 hover:-translate-y-1"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(255,255,255,0.01), transparent)",
                  border: "1px solid rgba(255,255,255,0.02)",
                }}
              >
                <div className="w-9 h-9 rounded-md bg-gradient-to-b from-[var(--accent)] to-[var(--accent-2)] flex items-center justify-center text-white">
                  <AlertCircle size={18} />
                </div>
                {motosQuery.isLoading ? (
                  <div className="mt-2 h-6 w-14 rounded bg-gray-500/20 animate-pulse" />
                ) : (
                  <div className="mt-2 text-lg font-extrabold text-white">20%</div>
                )}
                <div className="text-xs text-[var(--color-2)]">
                  Frenos
                </div>
              </div>

              <div
                className="flex flex-col items-center text-center p-3 rounded-md transform transition-transform duration-200 hover:-translate-y-1"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(255,255,255,0.01), transparent)",
                  border: "1px solid rgba(255,255,255,0.02)",
                }}
              >
                <div className="w-9 h-9 rounded-md bg-gradient-to-b from-[var(--accent)] to-[var(--accent-2)] flex items-center justify-center text-white">
                  <Gauge size={18} />
                </div>
                {motosQuery.isLoading ? (
                  <div className="mt-2 h-6 w-20 rounded bg-gray-500/20 animate-pulse" />
                ) : (
                  <div className="mt-2 text-lg font-extrabold text-white">32 PSI</div>
                )}
                <div className="text-xs text-[var(--color-2)]">
                  Neumáticos
                </div>
              </div>

              <div
                className="flex flex-col items-center text-center p-3 rounded-md transform transition-transform duration-200 hover:-translate-y-1"
                style={{
                  background:
                    "linear-gradient(180deg, rgba(255,255,255,0.01), transparent)",
                  border: "1px solid rgba(255,255,255,0.02)",
                }}
              >
                <div className="w-9 h-9 rounded-md bg-gradient-to-b from-[var(--accent)] to-[var(--accent-2)] flex items-center justify-center text-white">
                  <Droplet size={18} />
                </div>
                {motosQuery.isLoading ? (
                  <div className="mt-2 h-6 w-20 rounded bg-gray-500/20 animate-pulse" />
                ) : (
                  <div className="mt-2 text-lg font-extrabold text-white">Óptimo</div>
                )}
                <div className="text-xs text-[var(--color-2)]">
                  Aceite
                </div>
              </div>
            </div>
          </section>

          <section
            className="rounded-lg p-6"
            style={{ background: "var(--card)" }}
          >
            <div className="text-lg font-bold text-[var(--color-2)] mb-3">
              Último viaje
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center gap-3 p-3 transform transition-transform duration-200 hover:-translate-y-1">
                <div className="w-11 h-11 rounded-md bg-white/5 flex items-center justify-center text-[var(--accent)]">
                  <MapPin size={18} />
                </div>
                <div>
                  <div className="text-xs text-[var(--color-2)] font-bold">
                    Distancia
                  </div>
                  {motosQuery.isLoading ? (
                    <div className="h-6 w-20 mt-2 rounded bg-gray-500/20 animate-pulse" />
                  ) : (
                    <div className="text-lg font-extrabold text-white">200 km</div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 transform transition-transform duration-200 hover:-translate-y-1">
                <div className="w-11 h-11 rounded-md bg-white/5 flex items-center justify-center text-[var(--accent)]">
                  <Calendar size={18} />
                </div>
                <div>
                  <div className="text-xs text-[var(--color-2)] font-bold">
                    Fecha
                  </div>
                  {motosQuery.isLoading ? (
                    <div className="h-6 w-12 mt-2 rounded bg-gray-500/20 animate-pulse" />
                  ) : (
                    <div className="text-lg font-extrabold text-white">Hoy</div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 transform transition-transform duration-200 hover:-translate-y-1">
                <div className="w-11 h-11 rounded-md bg-white/5 flex items-center justify-center text-[var(--accent)]">
                  <Clock size={18} />
                </div>
                <div>
                  <div className="text-xs text-[var(--color-2)] font-bold">
                    Tiempo
                  </div>
                  {motosQuery.isLoading ? (
                    <div className="h-6 w-20 mt-2 rounded bg-gray-500/20 animate-pulse" />
                  ) : (
                    <div className="text-lg font-extrabold text-white">2h 30m</div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 transform transition-transform duration-200 hover:-translate-y-1">
                <div className="w-11 h-11 rounded-md bg-white/5 flex items-center justify-center text-[var(--accent)]">
                  <Gauge size={18} />
                </div>
                <div>
                  <div className="text-xs text-[var(--color-2)] font-bold">
                    Velocidad media
                  </div>
                  {motosQuery.isLoading ? (
                    <div className="h-6 w-20 mt-2 rounded bg-gray-500/20 animate-pulse" />
                  ) : (
                    <div className="text-lg font-extrabold text-white">80 km/h</div>
                  )}
                </div>
              </div>
            </div>
          </section>

          <section
            className="rounded-lg p-6"
            style={{ background: "var(--card)" }}
          >
            <div className="flex justify-between items-center mb-3">
              <div>
                <div className="text-lg font-bold text-[var(--color-2)] mb-3">
                  Próximo Mantenimiento
                </div>
                <div className="text-lg font-extrabold text-white">
                  Cambio de Aceite
                </div>
              </div>
              <div className="text-sm text-[var(--bg)] font-bold">
                En 850 km
              </div>
            </div>
            <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[var(--accent)] to-[var(--bg)]"
                style={{ width: "35%" }}
              />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default HomePage;

{/* Iconos de estado para modelo 3D */}
            // <button
            //   aria-label="Combustible"
            //   className="absolute left-6 top-6 w-10 h-10 rounded-full flex items-center justify-center text-black bg-[var(--shadow2)]"
            //   style={{ boxShadow: 'var(--accent-shadow)' }}
            // >
            //   <Zap size={16} />
            // </button>

            // <button
            //   aria-label="Batería"
            //   className="absolute right-6 top-28 w-10 h-10 rounded-full flex items-center justify-center text-black bg-[var(--shadow2)]"
            //   style={{ boxShadow: 'var(--accent-shadow)' }}
            // >
            //   <Battery size={16} />
            // </button>

            // <button
            //   aria-label="Aceite"
            //   className="absolute left-28 bottom-20 w-10 h-10 rounded-full flex items-center justify-center text-black bg-[var(--shadow2)]"
            //   style={{ boxShadow: 'var(--accent-shadow)' }}
            // >
            //   <Droplet size={16} />
            // </button>

            // <button
            //   aria-label="Garaje"
            //   className="absolute right-16 bottom-8 w-10 h-10 rounded-full flex items-center justify-center text-black bg-[var(--shadow2)]"
            //   style={{ boxShadow: 'var(--accent-shadow)' }}
            // >
            //   <Wrench size={16} />
            // </button>
        
