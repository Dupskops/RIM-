import React from "react";
import { Droplet, Gauge, Zap, Wrench, Battery } from "lucide-react";

const DiagnosticoPage: React.FC = () => {
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
            <img
              src="/imagenes/moto-bg.jpeg"
              alt="Moto"
              className="w-full h-[360px] object-cover rounded-md shadow-md"
            />

            {/* Icon badges positioned around the bike */}
            <button
              aria-label="Combustible"
              className="absolute left-12 top-10 w-12 h-12 rounded-full flex items-center justify-center text-black bg-[var(--shadow2)]"
              style={{ boxShadow: 'var(--accent-shadow)' }}
            >
              <Zap size={18} />
            </button>

            <button
              aria-label="Batería"
              className="absolute right-10 top-28 w-12 h-12 rounded-full flex items-center justify-center text-black bg-[var(--shadow2)]"
              style={{ boxShadow: 'var(--accent-shadow)' }}
            >
              <Battery size={18} />
            </button>

            <button
              aria-label="Aceite"
              className="absolute left-28 bottom-20 w-12 h-12 rounded-full flex items-center justify-center text-black bg-[var(--shadow2)]"
              style={{ boxShadow: 'var(--accent-shadow)' }}
            >
              <Droplet size={18} />
            </button>

            <button
              aria-label="Garaje"
              className="absolute right-16 bottom-8 w-12 h-12 rounded-full flex items-center justify-center text-black bg-[var(--shadow2)]"
              style={{ boxShadow: 'var(--accent-shadow)' }}
            >
              <Wrench size={18} />
            </button>
          </div>
        </div>

        {/* CTA */}
        <div>
          <button
            type="button"
            className="w-full py-3 bg-[var(--accent)] text-black font-semibold rounded-lg shadow-[var(--accent-shadow)] hover:brightness-95 transition"
          >
            Generar diagnóstico
          </button>
        </div>

        {/* Status list */}
        <div className="space-y-3">
          <div className="bg-[var(--card)] rounded-lg p-3">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-[rgba(255,255,255,0.04)] flex items-center justify-center text-[var(--accent)]">
                <svg className="w-6 h-6 text-[var(--accent)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9" /><path d="M12 4h9" /><path d="M3 10h18" /></svg>
              </div>
              <div className="flex-1">
                <div className="text-sm text-[var(--color-2)] font-semibold">Sistema de Frenos</div>
                <div className="mt-2 text-xs text-[var(--color-2)] bg-[rgba(255,255,255,0.03)] p-3 rounded-md">Estado: Crítico</div>
              </div>
              <div className="ml-2 flex items-center">
                <span className="w-3 h-3 rounded-full bg-red-500" />
              </div>
            </div>
          </div>

          <div className="bg-[var(--card)] rounded-lg p-3">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-[rgba(255,255,255,0.04)] flex items-center justify-center text-[var(--accent)]">
                <Droplet className="w-5 h-5 text-[var(--accent)]" />
              </div>
              <div className="flex-1">
                <div className="text-sm text-[var(--color-2)] font-semibold">Nivel de Aceite</div>
                <div className="mt-2 text-xs text-[var(--color-2)] bg-[rgba(255,255,255,0.03)] p-3 rounded-md">Estado: Atención</div>
              </div>
              <div className="ml-2 flex items-center">
                <span className="w-3 h-3 rounded-full bg-yellow-400" />
              </div>
            </div>
          </div>

          <div className="bg-[var(--card)] rounded-lg p-3">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-[rgba(255,255,255,0.04)] flex items-center justify-center text-[var(--accent)]">
                <Gauge className="w-5 h-5 text-[var(--accent)]" />
              </div>
              <div className="flex-1">
                <div className="text-sm text-[var(--color-2)] font-semibold">Presión de Neumáticos</div>
                <div className="mt-2 text-xs text-[var(--color-2)] bg-[rgba(255,255,255,0.03)] p-3 rounded-md">Estado: Óptimo</div>
              </div>
              <div className="ml-2 flex items-center">
                <span className="w-3 h-3 rounded-full bg-green-500" />
              </div>
            </div>
          </div>
        </div>

        {/* Question input */}
        <div className="mt-3 relative">
          <input
            type="text"
            placeholder="Haz una pregunta..."
            className="w-full pr-12 px-4 py-3 rounded-full bg-[rgba(255,255,255,0.03)] text-[var(--color-2)] placeholder-[rgba(215,215,215,0.5)] focus:outline-none"
          />
          <button
            type="button"
            aria-label="Enviar pregunta"
            className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-[var(--accent)] flex items-center justify-center text-black shadow-md"
          >
            ▶
          </button>
        </div>
      </main>
    </div>
  );
};

export default DiagnosticoPage;