import React, { useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import apiClient from '@/config/api-client';
import { API_ENDPOINTS } from '@/config/api-endpoints';
import { useMotoStore } from '@/store';

interface NewMoto {
    vin: string;
    modelo: string;
    anio: number;
    placa?: string | null;
    color?: string | null;
    kilometraje: number;
    observaciones?: string | null;
}

type Props = {
    showForm: boolean;
    onClose: () => void;
};

const FormularioNewMoto: React.FC<Props> = ({ showForm, onClose }) => {
    const addMoto = useMotoStore((s) => s.addMoto);
    const navigate = useNavigate();

    const [vin, setVin] = useState('');
    const [modelo, setModelo] = useState('');
    const [anio, setAnio] = useState<number>(new Date().getFullYear());
    const [placa, setPlaca] = useState('');
    const [color, setColor] = useState('');
    const [kilometraje, setKilometraje] = useState<number>(0);
    const [observaciones, setObservaciones] = useState('');

    const [formError, setFormError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showSuccess, setShowSuccess] = useState(false);

    const resetForm = () => {
        setVin('');
        setModelo('');
        setAnio(new Date().getFullYear());
        setPlaca('');
        setColor('');
        setKilometraje(0);
        setObservaciones('');
        setFormError(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setFormError(null);

        if (!vin || vin.trim().length !== 17) {
            setFormError('El VIN debe tener 17 caracteres');
            return;
        }
        if (!modelo || modelo.trim().length < 2) {
            setFormError('Ingrese el modelo');
            return;
        }
        const yearNum = Number(anio);
        const current = new Date().getFullYear();
        if (isNaN(yearNum) || yearNum < 1990 || yearNum > current + 1) {
            setFormError(`Año inválido (1990 - ${current + 1})`);
            return;
        }

        const payload: NewMoto = {
            vin: vin.trim(),
            modelo: modelo.trim(),
            anio: yearNum,
            placa: placa?.trim() || null,
            color: color?.trim() || null,
            kilometraje: kilometraje || 0,
            observaciones: observaciones?.trim() || null,
        };

        setIsSubmitting(true);
        try {
            const resp = await apiClient.post(API_ENDPOINTS.MOTOS.BASE, payload);
            const newMoto = resp.data;
            addMoto(newMoto);
            setShowSuccess(true);
            resetForm();
            onClose();
            // Redirigir al Garaje después del registro
            navigate({ to: '/app/garaje' });
        } catch (err) {
            let msg = 'Error al registrar moto';
            if (err instanceof Error) msg = err.message;
            else {
                try {
                    msg = JSON.stringify(err);
                } catch {
                    // ignore
                }
            }
            setFormError(msg);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!showForm && !showSuccess) return null;

    return (
        <>
            {showForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center ">
                    <div className="absolute inset-0 bg-black/60" onClick={onClose}  />
                    <form onSubmit={handleSubmit} className="relative z-50 w-full max-w-lg bg-[var(--card)] rounded-lg p-6 m-4 shadow-2xl">
                        <h3 className="text-lg font-bold mb-3 text-white">Añadir moto</h3>
                        <div className="grid grid-cols-1 gap-3">
                            <label className="text-xs text-[var(--color-2)]">VIN (17 caracteres)</label>
                            <input value={vin} onChange={(e) => setVin(e.target.value.toUpperCase())} maxLength={17} className="w-full p-2 rounded-md bg-[rgba(255,255,255,0.03)] text-white" />

                            <label className="text-xs text-[var(--color-2)]">Modelo</label>
                            <input value={modelo} onChange={(e) => setModelo(e.target.value)} className="w-full p-2 rounded-md bg-[rgba(255,255,255,0.03)] text-white" />

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-[var(--color-2)]">Año</label>
                                    <input value={anio} onChange={(e) => setAnio(Number(e.target.value))} type="number" className="w-full p-2 rounded-md bg-[rgba(255,255,255,0.03)] text-white" />
                                </div>
                                <div>
                                    <label className="text-xs text-[var(--color-2)]">Placa (opcional)</label>
                                    <input value={placa} onChange={(e) => setPlaca(e.target.value.toUpperCase())} className="w-full p-2 rounded-md bg-[rgba(255,255,255,0.03)] text-white" />
                                </div>
                            </div>

                            <label className="text-xs text-[var(--color-2)]">Color (opcional)</label>
                            <input value={color} onChange={(e) => setColor(e.target.value)} className="w-full p-2 rounded-md bg-[rgba(255,255,255,0.03)] text-white" />

                            <label className="text-xs text-[var(--color-2)]">Kilometraje</label>
                            <input value={kilometraje} onChange={(e) => setKilometraje(Number(e.target.value))} type="number" min={0} className="w-full p-2 rounded-md bg-[rgba(255,255,255,0.03)] text-white" />

                            <label className="text-xs text-[var(--color-2)]">Observaciones (opcional)</label>
                            <textarea value={observaciones} onChange={(e) => setObservaciones(e.target.value)} className="w-full p-2 rounded-md bg-[rgba(255,255,255,0.03)] text-white" rows={3} />

                            {formError && <div className="text-sm text-red-300">{formError}</div>}

                            <div className="flex justify-end gap-2">
                                <button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-white/5 text-[var(--color-2)]">Cancelar</button>
                                <button type="submit" disabled={isSubmitting} className="px-4 py-2 rounded-md bg-[var(--accent)] text-[var(--bg)] font-bold">{isSubmitting ? 'Registrando...' : 'Registrar moto'}</button>
                            </div>
                        </div>
                    </form>
                </div>
            )}

            {showSuccess && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    <div className="absolute inset-0 bg-black/60" onClick={() => setShowSuccess(false)} />
                    <div className="relative z-50 w-full max-w-xs bg-[var(--card)] rounded-lg p-6 text-center shadow-2xl">
                        <h4 className="font-bold text-white mb-2">Moto registrada</h4>
                        <p className="text-[var(--color-2)] mb-4">La moto fue registrada correctamente.</p>
                        <button onClick={() => setShowSuccess(false)} className="px-4 py-2 rounded-md bg-[var(--accent)] text-[var(--bg)] font-bold">Cerrar</button>
                    </div>
                </div>
            )}
        </>
    );
};

export default FormularioNewMoto;