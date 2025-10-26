import {
  Battery,
  Zap,
  Droplet,
  Gauge,
  AlertCircle,
  MapPin,
  Calendar,
  Clock,
} from "lucide-react";

const HomePage: React.FC = () => {
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

              <div className="flex items-center justify-center p-2 relative">
                <div className="h-80 w-full max-w-3xl rounded-lg overflow-hidden shadow-2xl">
                  <div
                    className="w-full"
                    role="img"
                    aria-label="Modelo 3D de la moto"
                    style={{
                      height: "clamp(310px,42vw,420px)",
                      background:
                        "linear-gradient(180deg, rgba(2,6,8,0.8), rgba(0,0,0,0.65))",
                    }}
                  />
                </div>

                <div className="absolute left-4 top-4 flex flex-col gap-2">
                  <span
                    className="px-2 py-1 rounded-full font-semibold text-[var(--accent)]"
                    style={{
                      background:
                        "linear-gradient(90deg, rgba(254,119,67,0.12), rgba(254,119,67,0.06))",
                      border: "1px solid rgba(254,119,67,0.12)",
                    }}
                  >
                    Encendido
                  </span>
                  <span
                    className="px-2 py-1 rounded-full font-semibold text-[var(--accent-2)]"
                    style={{
                      background:
                        "linear-gradient(90deg, rgba(68,125,155,0.08), rgba(68,125,155,0.04))",
                      border: "1px solid rgba(68,125,155,0.06)",
                    }}
                  >
                    En línea
                  </span>
                </div>
              </div>
            </div>
          </section>

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
                <div className="mt-2 text-lg font-extrabold text-white">
                  92%
                </div>
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
                <div className="mt-2 text-lg font-extrabold text-white">
                  98%
                </div>
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
                <div className="mt-2 text-lg font-extrabold text-white">
                  16 cSt
                </div>
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
                <div className="mt-2 text-lg font-extrabold text-white">
                  20%
                </div>
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
                <div className="mt-2 text-lg font-extrabold text-white">
                  32 PSI
                </div>
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
                <div className="mt-2 text-lg font-extrabold text-white">
                  Óptimo
                </div>
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
                  <div className="text-lg font-extrabold text-white">
                    200 km
                  </div>
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
                  <div className="text-lg font-extrabold text-white">
                    Hoy
                  </div>
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
                  <div className="text-lg font-extrabold text-white">
                    2h 30m
                  </div>
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
                  <div className="text-lg font-extrabold text-white">
                    80 km/h
                  </div>
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
                className="h-full bg-gradient-to-r from-[var(--accent)] to-[var(--accent-2)]"
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
