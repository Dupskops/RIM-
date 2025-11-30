import FormularioNewMoto from '@/components/formulario';
import { Plus, Edit, Trash, CheckCircle } from 'lucide-react';
import React, { useRef, useState, useEffect } from 'react';
import apiClient from '@/config/api-client';
import { MOTOS_ENDPOINTS } from '@/config/api-endpoints';
import { useMotoStore } from '@/store';
import toast from 'react-hot-toast';

type Bike = {
    id: number;
    usuario_id: number;
    modelo_moto_id: number;
    vin: string;
    placa: string | null;
    color: string | null;
    kilometraje_actual: string;
    observaciones: string | null;
    created_at: string;
    updated_at: string;
    // Campos para mostrar (por ahora usamos modelo_moto_id)
    title?: string;  // Se construirá del modelo
    subtitle?: string; // Se construirá del estado
    img?: string; // Imagen por defecto
};

const GarajePage: React.FC = () => {
    const { selectedMoto, setSelectedMoto } = useMotoStore();
    const carouselRef = useRef<HTMLDivElement | null>(null);
    const [active, setActive] = useState(0);
    const [bikes, setBikes] = useState<Bike[]>([]);
    const [loading, setLoading] = useState(true);

    // Track image load state per bike id
    const [imgLoaded, setImgLoaded] = useState<Record<number, boolean>>({});

    // Fetch motos from API
    useEffect(() => {
        fetchMotos();
    }, []);

    const fetchMotos = async () => {
        setLoading(true);
        try {
            const response = await apiClient.get(MOTOS_ENDPOINTS.BASE);
            if (response.data && response.data.data) {
                const motosData = response.data.data.map((moto: Bike) => ({
                    ...moto,
                    title: `Modelo ID: ${moto.modelo_moto_id}`, // Temporal hasta tener modelo_moto
                    subtitle: `VIN: ${moto.vin.slice(-6)} • ${moto.kilometraje_actual} km`,
                    img: 'https://s7g10.scene7.com/is/image/ktm/KTM-naked-bikes-segment-1390-super-duke-revo-left-side?fmt=png-alpha&wid=1000&dpr=off'
                }));
                setBikes(motosData);

                // Initialize image loaded state
                const imgState: Record<number, boolean> = {};
                motosData.forEach((b: Bike) => { imgState[b.id] = false; });
                setImgLoaded(imgState);
            }
        } catch (error: any) {
            console.error('Error al cargar motos:', error);
            toast.error('Error al cargar las motos');
        } finally {
            setLoading(false);
        }
    };

    // Auto-center the active card when bikes load
    useEffect(() => {
        if (loading || bikes.length === 0) return;
        const el = carouselRef.current;
        if (!el) return;
        // small timeout to ensure layout is ready
        const t = setTimeout(() => {
            const card = el.children[active] as HTMLElement | undefined;
            if (!card) return;
            el.scrollTo({ left: card.offsetLeft - (el.clientWidth - card.clientWidth) / 2, behavior: 'smooth' });
        }, 80);
        return () => clearTimeout(t);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, bikes]);

    // cleanup for fab timeout
    useEffect(() => {
        return () => {
            if (fabTimeoutRef.current) window.clearTimeout(fabTimeoutRef.current);
        };
    }, []);

    const scrollTo = (index: number) => {
        const el = carouselRef.current;
        if (!el) return;
        const card = el.children[index] as HTMLElement | undefined;
        if (!card) return;
        el.scrollTo({ left: card.offsetLeft - 8, behavior: 'smooth' });
        setActive(index);
    };

    const [showForm, setShowForm] = useState(false);
    const [fabAnimating, setFabAnimating] = useState(false);
    const fabTimeoutRef = useRef<number | null>(null);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deleteCandidate, setDeleteCandidate] = useState<number | null>(null);

    return (

        <div className=" bg-[var(--bg)] text-white">
            {/* Header centered */}
            <header className="relative px-4 py-4">
                <h2 className="text-center text-lg font-bold text-[var(--card)]">Garaje KTM</h2>
            </header>

            <main className="content mx-auto px-4 flex flex-col items-center justify-center flex-1 w-full">
                {/* Hero / carousel area */}
                <section className="animate-in flex items-center justify-center min-h-[60vh] w-full">
                    <div className="relative w-full flex justify-center">
                        <div className="overflow-hidden rounded-xl max-w-[920px] w-full mx-auto">
                            <div
                                ref={carouselRef}
                                className="max-w-[900px] w-full mx-auto flex gap-4 overflow-x-auto snap-x snap-mandatory py-6 px-6"
                                onScroll={() => {
                                    const el = carouselRef.current;
                                    if (!el) return;
                                    const children = Array.from(el.children) as HTMLElement[];
                                    const center = el.scrollLeft + el.clientWidth / 2;
                                    const index = children.findIndex((c) => center >= c.offsetLeft && center <= c.offsetLeft + c.clientWidth);
                                    if (index !== -1 && index !== active) setActive(index);
                                }}
                            >
                                {loading ? (
                                    <article className={`min-w-[280px] max-w-[320px] snap-center card relative rounded-lg p-3  bg-[var(--card)] border-3`}>
                                        <div className="rounded-md overflow-hidden shadow-md flex items-center justify-center bg-[rgba(255,255,255,0.03)]" style={{ height: 160 }}>
                                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--accent)]"></div>
                                        </div>
                                        <div className="mt-3 text-center">
                                            <div className="text-white font-extrabold text-lg">Cargando motos...</div>
                                            <div className="text-[var(--color-2)] text-sm mt-1">Por favor espera</div>
                                        </div>
                                    </article>
                                ) : bikes.length === 0 ? (
                                    <article className={`min-w-[280px] max-w-[320px] snap-center card relative rounded-lg p-3  bg-[var(--card)] border-3`}>
                                        <div className="rounded-md overflow-hidden shadow-md" style={{ height: 160 }}>
                                            <img src="/imagenes/moto-bg.jpeg" alt="Sin motos" className="w-full h-full object-cover" />
                                        </div>
                                        <div className="mt-3 text-center">
                                            <div className="text-white font-extrabold text-lg">Aún no tienes motos registradas</div>
                                            <div className="text-[var(--color-2)] text-sm mt-1">Agrega tu primera moto para empezar</div>
                                        </div>
                                    </article>
                                ) : (
                                    bikes.map((b, i) => (
                                        <article
                                            key={b.id}
                                            className={`min-w-[280px] max-w-[320px] snap-center card relative rounded-lg p-3 mb-9 bg-[var(--card)] border-3`}
                                            style={{ borderColor: i === active ? 'var(--accent)' : 'rgba(255,255,255,0.03)', boxShadow: i === active ? 'var(--bg2)' : undefined }}
                                        >
                                            <div className="rounded-md overflow-hidden shadow-md" style={{ height: 160 }}>
                                                {/* show provided image or fallback to public image; also handle broken urls via onError */}
                                                <div className="relative w-full h-full">
                                                    {/* skeleton while image loads */}
                                                    {!imgLoaded[b.id] && (
                                                        <div className="absolute inset-0 z-20 flex items-center justify-center bg-[rgba(0,0,0,0.35)]">
                                                            <div className="w-28 h-14 rounded-md bg-gray-500/20 animate-pulse" aria-hidden />
                                                        </div>
                                                    )}

                                                    <img
                                                        src={b.img || '/imagenes/moto-bg.jpeg'}
                                                        alt={b.title}
                                                        className={`w-full h-full object-cover transition-opacity duration-300 ${imgLoaded[b.id] ? 'opacity-100' : 'opacity-0'}`}
                                                        onLoad={() => setImgLoaded((p) => ({ ...p, [b.id]: true }))}
                                                        onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/imagenes/moto-bg.jpeg'; setImgLoaded((p) => ({ ...p, [b.id]: true })); }}
                                                    />
                                                </div>
                                            </div>
                                            <div className="mt-3">
                                                <div className="text-white font-extrabold text-lg">{b.title}</div>
                                                <div className="text-[var(--color-2)] text-sm mt-1">{b.subtitle}</div>

                                                {/* Acción: Usar / Editar / Eliminar */}
                                                <div className="mt-4 flex items-left justify-between gap-3">
                                                    <button
                                                        onClick={() => {
                                                            setSelectedMoto(b as any);
                                                            toast.success(`Moto ${b.title} seleccionada`);
                                                        }}
                                                        title={selectedMoto?.id === b.id ? 'Moto activa' : 'Usar esta moto'}
                                                        className={`flex items-center gap-2 px-4 py-2 rounded-full font-semibold hover:scale-105 transition-transform ${
                                                            selectedMoto?.id === b.id
                                                                ? 'bg-[var(--accent)] text-[var(--muted)]'
                                                                : 'bg-[rgba(255,255,255,0.06)] text-white border border-white/5'
                                                        }`}
                                                    >
                                                        {selectedMoto?.id === b.id ? (
                                                            <><CheckCircle size={14} /> Activa</>
                                                        ) : (
                                                            'Usar'
                                                        )}
                                                    </button>

                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => setShowForm(true)}
                                                            title="Editar"
                                                            className="flex items-center gap-2 px-4 py-2 rounded-full bg-[rgba(255,255,255,0.06)] text-white border border-white/5 hover:scale-105 transition-transform"
                                                        >
                                                            <Edit size={14} />
                                                        </button>

                                                        <button
                                                            onClick={() => { setDeleteCandidate(b.id); setShowDeleteConfirm(true); }}
                                                            title="Eliminar"
                                                            className="flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/80 text-white font-semibold hover:scale-105 transition-transform"
                                                        >
                                                            <Trash size={14} />
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </article>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                    {/* dots: absolute, centered at the bottom of the carousel container */}
                    <div className="absolute left-1/2 -translate-x-1/2 bottom-10 flex items-center gap-3 z-10">
                        <div className="flex items-center gap-3 bg-[rgba(255,255,255,0.81)] px-3 py-1 rounded-full">
                            {bikes.map((_, i) => (
                                <button
                                    key={i}
                                    onClick={() => scrollTo(i)}
                                    aria-label={`go-to-${i}`}
                                    aria-current={i === active}
                                    className={`transition-transform transform flex items-center justify-center focus:outline-none focus:ring-2 rounded-full ${i === active ? 'w-3.5 h-3.5 md:w-3.5 md:h-3.5 bg-[var(--accent)]  scale-110' : 'w-2.5 h-2.5 md:w-2.5 md:h-2.5 bg-[var(--card)]'}`}
                                />
                            ))}
                        </div>
                    </div>
                </section>

                {/* FAB centered bottom */}
                <button
                    onClick={() => {
                        // animate FAB then open form
                        setFabAnimating(true);
                        if (fabTimeoutRef.current) window.clearTimeout(fabTimeoutRef.current);
                        fabTimeoutRef.current = window.setTimeout(() => {
                            setFabAnimating(false);
                            setShowForm(true);
                        }, 140);
                    }}
                    aria-label="añadir-moto"
                    className={`fixed bottom-20 left-1/2 -translate-x-1/2 bg-[var(--accent)] w-14 h-14 rounded-full flex items-center justify-center shadow-md transform transition-transform duration-150 ${fabAnimating ? 'scale-110' : 'scale-100'} transition-transform duration-200 ease-in-out hover:-translate-y-1 hover:scale-[1.03]`}
                    style={{ color: 'var(--muted)' }}
                >
                    <Plus />
                </button>
                <FormularioNewMoto
                    showForm={showForm}
                    onClose={() => {
                        setShowForm(false);
                        fetchMotos(); // Recargar motos después de cerrar el formulario
                    }}
                />
                {/* Confirmación personalizada para eliminar moto */}
                {showDeleteConfirm && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center">
                        <div className="absolute inset-0 bg-black/60" onClick={() => { setShowDeleteConfirm(false); setDeleteCandidate(null); }} />
                        <div className="relative z-50 w-full max-w-xs bg-[var(--card)] rounded-lg p-6 text-center shadow-2xl">
                            <h4 className="font-bold text-white mb-2">¿Desea eliminar esta moto?</h4>
                            <p className="text-[var(--color-2)] mb-4">Esta acción no se puede deshacer.</p>
                            <div className="flex justify-center gap-3">
                                <button onClick={() => { setShowDeleteConfirm(false); setDeleteCandidate(null); }} className="px-4 py-2 rounded-md bg-white/5 text-[var(--color-2)]">No</button>
                                <button onClick={() => { console.log('eliminar', deleteCandidate); setShowDeleteConfirm(false); setDeleteCandidate(null); }} className="px-4 py-2 rounded-md bg-[var(--accent)] text-[var(--bg)] font-bold">Sí</button>
                            </div>
                        </div>
                    </div>
                )}
            </main>

        </div>
    );
};

export default GarajePage;
