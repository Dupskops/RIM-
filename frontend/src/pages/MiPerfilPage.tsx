import React, { useState, useEffect } from 'react';
import { User, Wrench, Edit2 } from 'lucide-react';
import { useAuthStore } from '@/store';
import { useNavigate } from '@tanstack/react-router';

type Vehicle = {
    id: number;
    marca: string;
    modelo: string;
    anio: number;
    placa: string;
    vin?: string;
    km: number;
    color?: string;
    ultimaRevision?: string;
};

type Diagnostic = {
    id: number;
    fecha: string;
    motivo: string;
    resultado: string;
    componentes: string[];
    desgaste: string; // e.g. '80%'
    reparaciones: string;
    costo?: string;
    tecnico?: string;
};

type Plan = {
    id: number;
    nombre: string;
    precio: string;
    resumen: string;
    incluye: string[];
};

type UserProfile = {
    nombre: string;
    documento: string;
    email: string;
    telefono: string;
    direccion: string;
    usuario: string;
    registro: string;
    foto: string;
    preferencias: { correo: boolean; app: boolean; sms: boolean };
    idioma: string;
    rol: string;
    tarjeta: string;
};

const MiPerfilPage: React.FC = () => {
    // estado local por compatibilidad / valores por defecto
    const [user, setUser] = useState(() => ({
        nombre: 'Jennifer López',
        documento: 'CC 1.234.567.890',
        email: 'jennifer.lopez@example.com',
        telefono: '+57 300 123 4567',
        direccion: 'Calle 45 #12-34, Cali',
        usuario: 'jlopez',
        registro: '15/02/2024',
        foto: '',
        preferencias: { correo: true, app: true, sms: false },
        idioma: 'Español',
        rol: 'cliente',
        tarjeta: '**** **** **** 4242',
    }));

    // datos reales del usuario (persistidos / traídos desde la API)
    const authUser = useAuthStore((s) => s.user);
    const loadUser = useAuthStore((s) => s.loadUser);
    const navigate = useNavigate();

    useEffect(() => {
        if (!authUser) {
            // intentar cargar el usuario desde la API / sesión si no está en el store
            loadUser().catch(() => {
                /* noop */
            });
        }
    }, [authUser, loadUser]);

    const [vehicles, setVehicles] = useState<Vehicle[]>(() => [
        { id: 1, marca: 'KTM', modelo: 'Duke 390', anio: 2021, placa: 'ABC-123', vin: 'VIN123456789', km: 12450, color: 'Naranja', ultimaRevision: '10/09/2025' },
    ]);

    const [diagnostics] = useState<Diagnostic[]>(() => [
        { id: 1, fecha: '10/09/2025', motivo: 'Revisión periódica', resultado: 'Cambio aceite y revisión frenos', componentes: ['Aceite', 'Frenos'], desgaste: '85%', reparaciones: 'Cambio aceite', costo: '$120.000', tecnico: 'Taller MotoService' },
    ]);

    // planes disponibles
    const [plans] = useState<Plan[]>(() => [
        { id: 1, nombre: 'Freemium', precio: 'Gratis', resumen: 'Funciones básicas de monitoreo', incluye: ['Registro de vehículo', 'Historial básico', 'Notificaciones básicas'] },
        { id: 2, nombre: 'Premium', precio: '$9.99/mes', resumen: 'Soporte y mantenimiento ampliado', incluye: ['Recordatorios personalizados', 'Descuentos en talleres', 'Soporte prioritario', 'Reportes avanzados'] },
        { id: 3, nombre: 'Platinum', precio: '$19.99/mes', resumen: 'Cobertura completa y beneficios', incluye: ['Asistencia en carretera', 'Mantenimiento preventivo anual', 'Seguro parcial', 'Consultoría personalizada'] },
    ]);

    const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
    const closePlanModal = () => setSelectedPlan(null);

    // edit modes
    const [editPersonal, setEditPersonal] = useState(false);
    const [editVehicleId, setEditVehicleId] = useState<number | null>(null);
    const [editSettings, setEditSettings] = useState(false);

    // temp states for editing personal data
    const [tempPersonal, setTempPersonal] = useState<UserProfile>({ ...user });

    const startEditPersonal = () => { setTempPersonal({ ...user }); setEditPersonal(true); };
    const savePersonal = () => { setUser(tempPersonal); setEditPersonal(false); };
    const cancelPersonal = () => { setEditPersonal(false); setTempPersonal({ ...user }); };

    // vehicle edit temp
    const [tempVehicle, setTempVehicle] = useState<Vehicle | null>(null);
    const startEditVehicle = (v: Vehicle) => { setTempVehicle({ ...v }); setEditVehicleId(v.id); };
    const saveVehicle = () => { if (!tempVehicle) return; setVehicles((prev) => prev.map((p) => p.id === tempVehicle.id ? tempVehicle : p)); setEditVehicleId(null); setTempVehicle(null); };
    const cancelVehicle = () => { setEditVehicleId(null); setTempVehicle(null); };

    return (
        <div className="bg-[var(--bg)] text-white p-4 mb-18">
            <div className="max-w-5xl mx-auto">
                <header className="flex items-center gap-4 mb-6">
                    <div className="w-20 h-20 rounded-full bg-[var(--card)] flex items-center justify-center text-[var(--accent)] text-3xl">
                        <User />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-[var(--card)]">{authUser?.nombre ?? user.nombre}</h1>
                        <p className="text-sm text-[var(--muted)]">Miembro desde {authUser?.created_at ? new Date(authUser.created_at).toLocaleDateString() : user.registro}</p>
                        <div className="mt-3">
                            <button className="px-4 py-2 rounded-md bg-[var(--accent)] text-[#071218] font-semibold flex items-center gap-2">
                                <Wrench size={16} />
                                Contactar un mecánico
                            </button>
                        </div>
                    </div>
                    {/* Contact button moved below the user name for better visibility */}
                </header>

                <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Personal data */}
                    <div className="lg:col-span-1 bg-[var(--card)] rounded-xl p-5">
                        <div className="flex items-start justify-between mb-4">
                            <h3 className="font-semibold text-[var(--color-2)]">Datos personales</h3>
                            <button onClick={startEditPersonal} className="text-[var(--color-2)] hover:text-[var(--accent)]"><Edit2 /></button>
                        </div>

                        {!editPersonal ? (
                            <div className="space-y-3 text-sm text-[var(--color-2)]">
                                <div><strong>Nombre:</strong> {authUser?.nombre ?? user.nombre}</div>
                                <div><strong>DNI / Documento:</strong> {user.documento}</div>
                                <div><strong>Correo:</strong> {authUser?.email ?? user.email}</div>
                                <div><strong>Teléfono:</strong> {user.telefono}</div>
                                <div><strong>Dirección:</strong> {user.direccion}</div>
                                <div><strong>Fecha registro:</strong> {authUser?.created_at ? new Date(authUser.created_at).toLocaleDateString() : user.registro}</div>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                <label className="text-xs">Nombre completo</label>
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.nombre} onChange={(e) => setTempPersonal(t => ({...t, nombre: e.target.value}))} />
                                <label className="text-xs">DNI / Documento</label>
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.documento} onChange={(e) => setTempPersonal(t => ({...t, documento: e.target.value}))} />
                                <label className="text-xs">Correo electrónico</label>
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.email} onChange={(e) => setTempPersonal(t => ({...t, email: e.target.value}))} />
                                <label className="text-xs">Teléfono</label>
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.telefono} onChange={(e) => setTempPersonal(t => ({...t, telefono: e.target.value}))} />
                                <label className="text-xs">Dirección</label>
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.direccion} onChange={(e) => setTempPersonal(t => ({...t, direccion: e.target.value}))} />
                                <div className="flex gap-2 mt-2">
                                    <button onClick={savePersonal} className="px-3 py-2 rounded bg-[var(--accent)] text-[#071218]">Guardar</button>
                                    <button onClick={cancelPersonal} className="px-3 py-2 rounded bg-white/5">Cancelar</button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Vehicle & Diagnostics */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="bg-[var(--card)] rounded-xl p-5">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-[var(--color-2)]">Datos del vehículo</h3>
                                <div className="text-[var(--color-2)]">Última revisión: {vehicles[0]?.ultimaRevision || '—'}</div>
                            </div>

                            <div className="space-y-3">
                                {vehicles.map((v) => (
                                    <div key={v.id} className="p-3 rounded-lg bg-[rgba(255,255,255,0.02)] flex items-center justify-between">
                                        <div>
                                            <div className="font-medium">{v.marca} {v.modelo} · {v.anio}</div>
                                            <div className="text-xs text-[var(--color-2)]">Placa: {v.placa} · VIN: {v.vin || '—'}</div>
                                            <div className="text-xs text-[var(--color-2)]">KM: {v.km} · Color: {v.color}</div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {editVehicleId === v.id ? (
                                                <>
                                                    <button onClick={saveVehicle} className="px-3 py-1 rounded bg-[var(--accent)] text-[#071218]">Guardar</button>
                                                    <button onClick={cancelVehicle} className="px-3 py-1 rounded bg-white/5">Cancelar</button>
                                                </>
                                            ) : (
                                                <>
                                                    <button onClick={() => startEditVehicle(v)} className="px-3 py-1 rounded bg-white/5">Editar</button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                ))}

                                {editVehicleId && tempVehicle && (
                                    <div className="mt-3 space-y-2">
                                        <label className="text-xs">Marca</label>
                                        <input value={tempVehicle.marca} onChange={(e) => setTempVehicle((t) => t ? { ...t, marca: e.target.value } : t)} className="w-full p-2 rounded bg-[var(--bg)]" />
                                        <label className="text-xs">Modelo</label>
                                        <input value={tempVehicle.modelo} onChange={(e) => setTempVehicle((t) => t ? { ...t, modelo: e.target.value } : t)} className="w-full p-2 rounded bg-[var(--bg)]" />
                                        <label className="text-xs">Año</label>
                                        <input value={tempVehicle.anio} onChange={(e) => setTempVehicle((t) => t ? { ...t, anio: Number(e.target.value) } : t)} className="w-full p-2 rounded bg-[var(--bg)]" />
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="bg-[var(--card)] rounded-xl p-5">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-[var(--color-2)]">Diagnósticos y Mantenimiento</h3>
                                <button 
                                onClick={() => navigate({ to: '/app/historial' })}
                                className="text-[var(--color-2)] hover:text-[var(--accent)]">Ver historial completo</button>
                            </div>

                            <div className="space-y-3">
                                {diagnostics.map((d) => (
                                    <div key={d.id} className="p-3 rounded-lg bg-[rgba(255,255,255,0.02)]">
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <div className="font-medium">{d.fecha} — {d.motivo}</div>
                                                <div className="text-xs text-[var(--color-2)] mt-1">Resultado: {d.resultado}</div>
                                            </div>
                                            <div className="text-sm text-[var(--color-2)]">Técnico: {d.tecnico || '—'}</div>
                                        </div>

                                        <div className="mt-2 text-[var(--color-2)] text-sm">
                                            <div><strong>Componentes revisados:</strong> {d.componentes.join(', ')}</div>
                                            <div><strong>Desgaste / Estado:</strong> {d.desgaste}</div>
                                            <div><strong>Reparaciones:</strong> {d.reparaciones}</div>
                                            <div><strong>Costo:</strong> {d.costo || '—'}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                            <div className="bg-[var(--card)] rounded-xl p-5">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-[var(--color-2)]">Configuraciones</h3>
                                <button onClick={() => setEditSettings((s) => !s)} className="text-[var(--color-2)] hover:text-[var(--accent)]"><Edit2 /></button>
                            </div>

                            {!editSettings ? (
                                <div className="text-sm text-[var(--color-2)] space-y-2">
                                    <div><strong>Notificaciones:</strong> {user.preferencias.app ? 'App' : ''}{user.preferencias.correo ? ' · Correo' : ''}{user.preferencias.sms ? ' · SMS' : ''}</div>
                                    <div><strong>Método de pago:</strong> {user.tarjeta}</div>
                                    <div><strong>Idioma:</strong> {user.idioma}</div>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <label className="flex items-center gap-2"><input type="checkbox" checked={user.preferencias.app} onChange={(e) => setUser(u => ({...u, preferencias: {...u.preferencias, app: e.target.checked}}))} /> Notificaciones en la app</label>
                                    <label className="flex items-center gap-2"><input type="checkbox" checked={user.preferencias.correo} onChange={(e) => setUser(u => ({...u, preferencias: {...u.preferencias, correo: e.target.checked}}))} /> Notificaciones por correo</label>
                                    <label className="flex items-center gap-2"><input type="checkbox" checked={user.preferencias.sms} onChange={(e) => setUser(u => ({...u, preferencias: {...u.preferencias, sms: e.target.checked}}))} /> Notificaciones por SMS</label>
                                    <div className="flex gap-2 mt-2">
                                        <button onClick={() => setEditSettings(false)} className="px-3 py-2 rounded bg-[var(--accent)] text-[#071218]">Guardar</button>
                                    </div>
                                </div>
                            )}
                        </div>
                        
                        {/* Sección de Planes */}
                        <div className="bg-[var(--card)] rounded-xl p-5">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-[var(--color-2)]">Planes</h3>
                                <div className="text-[var(--color-2)]">Elige el plan que más te convenga</div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                {plans.map((p) => (
                                    <div key={p.id} className="p-3 rounded-lg bg-[rgba(255,255,255,0.02)] flex flex-col justify-between">
                                        <div>
                                            <div className="font-medium text-[var(--color-2)]">{p.nombre}</div>
                                            <div className="text-sm text-[var(--color-2)] mt-1">{p.resumen}</div>
                                        </div>
                                        <div className="mt-3 flex items-center justify-between">
                                            <div className="text-[var(--accent)] font-semibold">{p.precio}</div>
                                            <div className="flex gap-2">
                                                <button onClick={() => setSelectedPlan(p)} className="px-3 py-1 rounded bg-white/5 text-sm">Ver detalles</button>
                                                <button className="px-3 py-1 rounded bg-[var(--accent)] text-[#071218] text-sm">Suscribirse</button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>
                {/* Modal / Pop-up para detalles del plan */}
                {selectedPlan && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={closePlanModal}>
                        <div className="bg-[var(--card)] text-[var(--color-2)] rounded-lg p-6 w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-start justify-between">
                                <div>
                                    <h3 className="text-xl font-semibold text-[var(--card)]">{selectedPlan.nombre} <span className="text-sm text-[var(--accent)] ml-2">{selectedPlan.precio}</span></h3>
                                    <p className="text-sm mt-1">{selectedPlan.resumen}</p>
                                </div>
                                <button onClick={closePlanModal} className="text-[var(--color-2)] ml-4">Cerrar</button>
                            </div>

                            <ul className="mt-4 list-disc list-inside text-sm space-y-1">
                                {selectedPlan.incluye.map((inc, i) => (
                                    <li key={i}>{inc}</li>
                                ))}
                            </ul>

                            <div className="mt-6 flex justify-end">
                                <button onClick={closePlanModal} className="px-4 py-2 rounded bg-[var(--accent)] text-[#071218]">Cerrar</button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MiPerfilPage;
