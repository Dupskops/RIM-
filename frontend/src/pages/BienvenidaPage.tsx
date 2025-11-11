import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "@tanstack/react-router";

const BienvenidaPage: React.FC = () => {
    const navigate = useNavigate();
    const [mounted, setMounted] = useState(false);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const [isMuted, setIsMuted] = useState(true); // empezar muteado para permitir autoplay
    const [isPlaying, setIsPlaying] = useState(true);
    const [animateEntry, setAnimateEntry] = useState(false);

    useEffect(() => {
        const t = setTimeout(() => setMounted(true), 30);
        return () => clearTimeout(t);
    }, []);

    useEffect(() => {
        // Mostrar animación de entrada tras 2s (se ejecuta cada vez para facilitar pruebas)
        const timer = setTimeout(() => setAnimateEntry(true), 2000);
        return () => clearTimeout(timer);
    }, []);

    return (
        <div
            className="min-h-screen flex items-center justify-center p-6"
            style={{
                background: "linear-gradient(180deg,#ff9a3c,#ff6a00)",
            }}
        >
            <div className={`w-full max-w-5xl mx-auto transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
                <div className="relative rounded-3xl overflow-hidden shadow-2xl" style={{ minHeight: 640 }}>

                    {/* Vídeo de fondo (archivo en public/imagenes) */}
                    <video
                        ref={videoRef}
                        className="absolute inset-0 w-full h-full object-cover hero-video"
                        src="/imagenes/Video_Bienvenida.mp4"
                        autoPlay
                        muted={isMuted}
                        loop
                        playsInline
                        aria-hidden="false"
                        onPlay={() => setIsPlaying(true)}
                        onPause={() => setIsPlaying(false)}
                    />

                    {/* overlay degradado para legibilidad */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />

                    <div className="absolute inset-0 z-10 flex items-center justify-center p-6 md:p-12 pointer-events-none">
                        <div className="w-full max-w-3xl text-center pointer-events-auto flex flex-col h-full py-8">
                            <div className="flex-grow flex flex-col items-center justify-center">
                                <h1 className={`text-4xl md:text-5xl lg:text-6xl font-extrabold text-white drop-shadow-lg leading-tight entry-title ${animateEntry ? 'enter' : ''}`}>Bienvenido a RIM</h1>
                                <p className={`mt-3 text-white/85 mx-auto max-w-2xl entry-sub ${animateEntry ? 'enter' : ''}`}>Tu asistente virtual para el mantenimiento de tu vehículo. Gestiona servicios, historial y más desde un lugar cómodo, ahora con una experiencia visual inmersiva.</p>
                            </div>

                            <div className={`flex flex-col items-center gap-4 mb-8 entry-actions ${animateEntry ? 'enter' : ''}`}>
                                <div className="flex items-center justify-center gap-4">
                                    <button
                                        onClick={() => navigate({ to: "/auth/login" })}
                                        className="relative inline-flex items-center gap-3 py-3 px-8 bg-white/95 text-black font-semibold rounded-full shadow-2xl hover:scale-[1.02] active:scale-95 transition-transform duration-200"
                                    >
                                        <span>Ingresar</span>
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="opacity-90">
                                            <path d="M5 12h14M13 5l7 7-7 7" stroke="#000" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                                        </svg>
                                    </button>
                                </div>

                                <div className="mt-2 flex items-center justify-center gap-3">
                                    <button
                                        aria-label={isPlaying ? 'Pausar vídeo' : 'Reproducir vídeo'}
                                        onClick={async () => {
                                            const v = videoRef.current;
                                            if (!v) return;
                                            if (isPlaying) {
                                                v.pause();
                                            } else {
                                                try { await v.play(); } catch { /* reproducción bloqueada */ }
                                            }
                                        }}
                                        className="flex items-center gap-2 px-3 py-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition"
                                    >
                                        {isPlaying ? (
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M6 4h4v16H6zM14 4h4v16h-4z" fill="white"/></svg>
                                        ) : (
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 3v18l15-9L5 3z" fill="white"/></svg>
                                        )}
                                    </button>

                                    <button
                                        aria-label={isMuted ? 'Activar audio' : 'Silenciar audio'}
                                        onClick={async () => {
                                            const v = videoRef.current;
                                            if (!v) return;
                                            if (isMuted) {
                                                setIsMuted(false);
                                                try { await v.play(); } catch { /* ignore */ }
                                            } else {
                                                setIsMuted(true);
                                            }
                                        }}
                                        className="flex items-center gap-2 px-3 py-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition"
                                    >
                                        {isMuted ? (
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 9v6h4l5 5V4L9 9H5z" fill="white" opacity="0.95"/></svg>
                                        ) : (
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 9v6h4l5 5V4L9 9H5z" fill="white"/><path d="M16 8l4 4m0-4l-4 4" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
                                        )}

                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* estilos locales para animaciones suaves, video y moto en movimiento */}
                    <style>{`
                        .hero-video { transform-origin: center center; animation: hero-zoom 18s linear infinite alternate; filter: brightness(0.75) saturate(1.05); }

                        @keyframes hero-zoom {
                            0% { transform: scale(1); }
                            100% { transform: scale(1.04); }
                        }

                        .bike-track { display: flex; gap: 48px; align-items: center; }
                        /* entrada desde arriba/abajo - título y acciones */
                        .entry-title, .entry-sub, .entry-actions { transition: transform 700ms cubic-bezier(.2,.9,.25,1), opacity 700ms cubic-bezier(.2,.9,.25,1); }
                        .entry-title { transform: translateY(-40px); opacity: 0; }
                        .entry-sub { transform: translateY(-24px); opacity: 0; }
                        .entry-actions { transform: translateY(36px); opacity: 0; }
                        .entry-title.enter, .entry-sub.enter { transform: translateY(0); opacity: 1; }
                        .entry-actions.enter { transform: translateY(0); opacity: 1; }
                        /* pequeño stagger */
                        .entry-sub.enter { transition-delay: 120ms; }
                        .entry-actions.enter { transition-delay: 260ms; }
                        .bike { transform: translateX(-30%); opacity: 0.98; }
                        .bike-1 { animation: bike-move 5.8s cubic-bezier(.2,.8,.2,1) infinite; }
                        .bike-2 { animation: bike-move 5.8s cubic-bezier(.2,.8,.2,1) infinite 2.9s; opacity: 0.9; transform: scale(0.92); }

                        @keyframes bike-move {
                            0% { transform: translateX(-120%); }
                            60% { transform: translateX(-5%); }
                            100% { transform: translateX(0%); }
                        }

                        .animate-fade-up { animation: fade-up 700ms cubic-bezier(.2,.9,.25,1) both; }
                        @keyframes fade-up { from { opacity:0; transform: translateY(8px); } to { opacity:1; transform: translateY(0); } }
                    `}</style>
                </div>
            </div>
        </div>
    );
};

export default BienvenidaPage;