import React from "react";
import { ArrowLeft, Bot, CheckCircle } from "lucide-react";

// Define the minimal card shape this modal expects
export interface StatusCard {
    id: string;
    title: string;
    state: string;
    colorClass?: string;
    // icon omitted for modal content
}

interface PopUpProps {
    open: boolean;
    card: StatusCard | null;
    onClose: () => void;
}

const PopUp: React.FC<PopUpProps> = ({ open, card, onClose }) => {
    if (!open || !card) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/50" onClick={onClose} />
            <div className="relative max-w-md w-full mx-4">
                <div className="bg-[var(--card)] text-white rounded-2xl p-4 shadow-lg max-h-[93vh] overflow-auto">
                    {/* Header */}
                    <div className="flex items-center gap-3">
                        <button onClick={onClose} aria-label="Volver" className="p-2 rounded-md">
                            <ArrowLeft className="w-5 h-5 text-[var(--accent)]" />
                        </button>
                        <h3 className="flex-1 text-center text-lg font-semibold">Estado del Motor</h3>
                    </div>

                    {/* Estado Actual */}
                    <div className="mt-4 bg-[var(--glass,#392a20)] p-3 rounded-lg">
                        <h4 className="text-sm font-semibold text-[var(--color-2,#f0c36b)]">Estado Actual</h4>
                        <p className="mt-2 text-sm text-[var(--bg,#e6d8c6)]">Se ha detectado una presión de aceite por debajo del rango óptimo. Es crucial revisarlo para evitar daños graves en el motor.</p>
                    </div>

                    {/* Métricas */}
                    <div className="mt-4 grid grid-cols-2 gap-3">
                        <div className="bg-[var(--glass,#392a20)] p-3 rounded-lg">
                            <div className="text-xs text-[var(--color-2,#e6d8c6)]">Presión de Aceite</div>
                            <div className="mt-2 text-2xl font-bold text-white">15 PSI</div>
                        </div>
                        <div className="bg-[var(--glass,#392a20)] p-3 rounded-lg">
                            <div className="text-xs text-[var(--color-2,#e6d8c6)]">Nivel de Aceite</div>
                            <div className="mt-2 text-2xl font-bold text-white">Bajo</div>
                        </div>
                    </div>

                    {/* Info adicional: último cambio y kilometraje */}
                    <div className="mt-3 grid grid-cols-2 gap-3">
                        <div className="bg-[var(--glass,#392a20)] p-3 rounded-lg">
                            <div className="text-xs text-[var(--color-2,#e6d8c6)]">Último cambio de aceite</div>
                            <div className="mt-2 text-sm font-semibold text-white">15/03/2024</div>
                        </div>
                        <div className="bg-[var(--glass,#392a20)] p-3 rounded-lg">
                            <div className="text-xs text-[var(--color-2,#e6d8c6)]">Kilometraje</div>
                            <div className="mt-2 text-sm font-semibold text-white">25,120 km</div>
                        </div>
                    </div>

                    {/* Recomendaciones */}
                    <div className="mt-4 p-0">
                        <h4 className="text-sm font-semibold text-[var(--color-2,#f0c36b)]">Recomendaciones</h4>
                        <ul className="mt-2 space-y-3">
                            <li className="flex items-start gap-3">
                                <div className="mt-1"><CheckCircle className="w-5 h-5 text-[var(--accent,#f59e0b)]" /></div>
                                <div>
                                    <div className="font-semibold text-sm text-white">Verificar Nivel de Aceite</div>
                                    <div className="text-xs text-[var(--color-2,#e6d8c6)]">Con el motor frío y en una superficie plana, revisa la varilla medidora. Rellena si es necesario.</div>
                                </div>
                            </li>
                            <li className="flex items-start gap-3">
                                <div className="mt-1"><CheckCircle className="w-5 h-5 text-[var(--accent,#f59e0b)]" /></div>
                                <div>
                                    <div className="font-semibold text-sm text-white">Inspeccionar Posibles Fugas</div>
                                    <div className="text-xs text-[var(--color-2,#e6d8c6)]">Busca manchas de aceite debajo de la motocicleta después de haber estado estacionada.</div>
                                </div>
                            </li>
                        </ul>
                    </div>

                    {/* CTA */}
                    <div className="mt-6 pb-4">
                        <button
                            aria-label="Consultar a RIM"
                            className="w-full bg-[var(--accent,#f59e0b)] text-[var(--bg,#000)] font-semibold py-3 rounded-full shadow-sm hover:brightness-95 transition flex items-center justify-center gap-3 duration-200 ease-in-out hover:-translate-y-1 hover:scale-[1.03]"
                        >
                            <Bot className="w-5 h-5 text-[var(--bg,#000)]" />
                            <span>Consultar a RIM</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PopUp;