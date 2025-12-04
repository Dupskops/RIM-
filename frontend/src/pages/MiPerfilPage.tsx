import React, { useState, useEffect } from 'react';
import { User, Wrench, Edit2, LogOut } from 'lucide-react';
import { useAuthStore, useSuscripcionStore } from '@/store';
import { useNavigate } from '@tanstack/react-router';
import { suscripcionesService, type Plan as ApiPlan } from '@/services';
import Swal from 'sweetalert2';

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

type PlanDisplay = Plan;

type UserProfile = {
    nombre: string;
    documento: string;
    email: string;
    telefono: string;
    direccion: string;
    registro: string;
    foto: string;
    preferencias: { correo: boolean; app: boolean; sms: boolean };
    idioma: string;
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

    // Suscripción del usuario
    const suscripcion = useSuscripcionStore((s) => s.suscripcion);
    const loadSuscripcion = useSuscripcionStore((s) => s.loadSuscripcion);
    const cambiarPlan = useSuscripcionStore((s) => s.cambiarPlan);

    useEffect(() => {
        if (!authUser) {
            // intentar cargar el usuario desde la API / sesión si no está en el store
            loadUser().catch(() => {
                /* noop */
            });
        }
    }, [authUser, loadUser]);

    // Cargar suscripción del usuario
    useEffect(() => {
        loadSuscripcion();
    }, [loadSuscripcion]);

    const [vehicles, setVehicles] = useState<Vehicle[]>(() => [
        { id: 1, marca: 'KTM', modelo: 'Duke 390', anio: 2021, placa: 'ABC-123', vin: 'VIN123456789', km: 12450, color: 'Naranja', ultimaRevision: '10/09/2025' },
    ]);

    const [diagnostics] = useState<Diagnostic[]>(() => [
        { id: 1, fecha: '10/09/2025', motivo: 'Revisión periódica', resultado: 'Cambio aceite y revisión frenos', componentes: ['Aceite', 'Frenos'], desgaste: '85%', reparaciones: 'Cambio aceite', costo: '$120.000', tecnico: 'Taller MotoService' },
    ]);

    // planes disponibles desde la API
    const [plans, setPlans] = useState<PlanDisplay[]>([]);
    const [loadingPlans, setLoadingPlans] = useState(true);
    const [errorPlans, setErrorPlans] = useState<string | null>(null);

    // Cargar planes desde la API
    useEffect(() => {
        const fetchPlanes = async () => {
            try {
                setLoadingPlans(true);
                setErrorPlans(null);
                const planesData = await suscripcionesService.getPlanes();
                
                // Transformar los datos de la API al formato de visualización
                const planesDisplay: PlanDisplay[] = planesData.map((plan) => ({
                    id: plan.id,
                    nombre: plan.nombre_plan.charAt(0).toUpperCase() + plan.nombre_plan.slice(1),
                    precio: plan.precio === '0.00' ? 'Gratis' : `$${plan.precio}/${plan.periodo_facturacion}`,
                    resumen: `Plan ${plan.nombre_plan} - ${plan.caracteristicas.length} características`,
                    incluye: plan.caracteristicas.map((c) => {
                        if (c.limite_free !== null || c.limite_pro !== null) {
                            const limite = plan.nombre_plan === 'free' ? c.limite_free : c.limite_pro;
                            return `${c.descripcion} ${limite ? `(${limite})` : ''}`;
                        }
                        return c.descripcion;
                    }),
                }));
                
                setPlans(planesDisplay);
            } catch (error) {
                console.error('Error al cargar planes:', error);
                setErrorPlans('No se pudieron cargar los planes. Intenta nuevamente.');
            } finally {
                setLoadingPlans(false);
            }
        };

        fetchPlanes();
    }, []);

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

    // Manejar cambio de plan
    const handleCambiarPlan = async (planId: number, planNombre: string) => {
        // Verificar si es el plan actual
        if (suscripcion && suscripcion.plan.id === planId) {
            await Swal.fire({
                title: 'Plan actual',
                text: `Ya tienes el plan ${planNombre}`,
                icon: 'info',
                confirmButtonColor: '#00D9FF',
            });
            return;
        }

        // Determinar si es upgrade o downgrade
        const isUpgrade = suscripcion && planId > suscripcion.plan.id;
        const actionText = isUpgrade ? 'mejorar' : 'cambiar';

        const result = await Swal.fire({
            title: `¿${isUpgrade ? 'Mejorar' : 'Cambiar'} plan?`,
            text: `¿Deseas ${actionText} al plan ${planNombre}?`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#00D9FF',
            cancelButtonColor: '#d33',
            confirmButtonText: `Sí, ${actionText}`,
            cancelButtonText: 'Cancelar',
        });

        if (result.isConfirmed) {
            try {
                await cambiarPlan(planId);
                await Swal.fire({
                    title: '¡Éxito!',
                    text: `Plan cambiado a ${planNombre} exitosamente`,
                    icon: 'success',
                    confirmButtonColor: '#00D9FF',
                });
            } catch (error) {
                await Swal.fire({
                    title: 'Error',
                    text: 'No se pudo cambiar el plan. Intenta nuevamente.',
                    icon: 'error',
                    confirmButtonColor: '#00D9FF',
                });
            }
        }
    };

    // Determinar el texto y estilo del botón según el plan
    const getPlanButtonInfo = (planId: number) => {
        if (!suscripcion) {
            return {
                text: 'Suscribirse',
                className: 'bg-[var(--accent)] text-[#071218] hover:bg-[var(--accent)]/80',
                disabled: false,
            };
        }

        const currentPlanId = suscripcion.plan.id;

        if (currentPlanId === planId) {
            return {
                text: 'Plan actual',
                className: 'bg-green-500/20 text-green-400 cursor-default',
                disabled: true,
            };
        }

        if (planId > currentPlanId) {
            return {
                text: 'Mejorar plan',
                className: 'bg-gradient-to-r from-[var(--accent)] to-blue-500 text-[#071218] hover:opacity-90',
                disabled: false,
            };
        }

        return {
            text: 'Cambiar plan',
            className: 'bg-orange-500/80 text-white hover:bg-orange-500',
            disabled: false,
        };
    };

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
                        {suscripcion && (
                            <p className="text-sm text-[var(--accent)] font-semibold mt-1">
                                Plan {suscripcion.plan.nombre_plan.charAt(0).toUpperCase() + suscripcion.plan.nombre_plan.slice(1)} - {suscripcion.estado_suscripcion}
                            </p>
                        )}
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
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.nombre} onChange={(e) => setTempPersonal(t => ({ ...t, nombre: e.target.value }))} />
                                <label className="text-xs">DNI / Documento</label>
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.documento} onChange={(e) => setTempPersonal(t => ({ ...t, documento: e.target.value }))} />
                                <label className="text-xs">Correo electrónico</label>
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.email} onChange={(e) => setTempPersonal(t => ({ ...t, email: e.target.value }))} />
                                <label className="text-xs">Teléfono</label>
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.telefono} onChange={(e) => setTempPersonal(t => ({ ...t, telefono: e.target.value }))} />
                                <label className="text-xs">Dirección</label>
                                <input className="w-full p-2 rounded bg-[var(--bg)] text-white" value={tempPersonal.direccion} onChange={(e) => setTempPersonal(t => ({ ...t, direccion: e.target.value }))} />
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
                                    <label className="flex items-center gap-2"><input type="checkbox" checked={user.preferencias.app} onChange={(e) => setUser(u => ({ ...u, preferencias: { ...u.preferencias, app: e.target.checked } }))} /> Notificaciones en la app</label>
                                    <label className="flex items-center gap-2"><input type="checkbox" checked={user.preferencias.correo} onChange={(e) => setUser(u => ({ ...u, preferencias: { ...u.preferencias, correo: e.target.checked } }))} /> Notificaciones por correo</label>
                                    <label className="flex items-center gap-2"><input type="checkbox" checked={user.preferencias.sms} onChange={(e) => setUser(u => ({ ...u, preferencias: { ...u.preferencias, sms: e.target.checked } }))} /> Notificaciones por SMS</label>
                                    <div className="flex gap-2 mt-2">
                                        <button onClick={() => setEditSettings(false)} className="px-3 py-2 rounded bg-[var(--accent)] text-[#071218]">Guardar</button>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Sección de Mi Suscripción */}
                        {suscripcion && (
                            <div className="bg-[var(--card)] rounded-xl p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="font-semibold text-[var(--color-2)]">Mi Suscripción</h3>
                                    <div className="text-[var(--accent)] font-semibold">
                                        {suscripcion.plan.nombre_plan.charAt(0).toUpperCase() + suscripcion.plan.nombre_plan.slice(1)}
                                    </div>
                                </div>

                                <div className="space-y-3 text-sm text-[var(--color-2)]">
                                    <div className="flex justify-between">
                                        <strong>Estado:</strong>
                                        <span className="capitalize">{suscripcion.estado_suscripcion}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <strong>Precio:</strong>
                                        <span>${suscripcion.plan.precio}/{suscripcion.plan.periodo_facturacion}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <strong>Fecha inicio:</strong>
                                        <span>{new Date(suscripcion.fecha_inicio).toLocaleDateString()}</span>
                                    </div>
                                    {suscripcion.fecha_fin && (
                                        <div className="flex justify-between">
                                            <strong>Fecha fin:</strong>
                                            <span>{new Date(suscripcion.fecha_fin).toLocaleDateString()}</span>
                                        </div>
                                    )}
                                </div>

                                <div className="mt-4">
                                    <h4 className="font-semibold text-[var(--color-2)] mb-2">Uso de Características</h4>
                                    <div className="space-y-2 max-h-60 overflow-y-auto">
                                        {suscripcion.features_status
                                            .filter((f) => f.limite_actual !== null)
                                            .map((feature) => {
                                                const limiteActual = feature.limite_actual ?? 0;
                                                const porcentaje = limiteActual > 0 
                                                    ? Math.round((feature.uso_actual / limiteActual) * 100) 
                                                    : 0;
                                                
                                                return (
                                                    <div key={feature.caracteristica} className="p-2 rounded bg-[rgba(255,255,255,0.02)]">
                                                        <div className="flex justify-between items-start">
                                                            <div className="flex-1">
                                                                <div className="text-xs font-medium text-[var(--color-2)]">
                                                                    {feature.descripcion}
                                                                </div>
                                                                {limiteActual === 0 ? (
                                                                    <div className="text-xs text-orange-400 mt-1">
                                                                        {feature.upsell_message}
                                                                    </div>
                                                                ) : (
                                                                    <div className="text-xs text-[var(--muted)] mt-1">
                                                                        Uso: {feature.uso_actual} / {limiteActual}
                                                                    </div>
                                                                )}
                                                            </div>
                                                            {limiteActual > 0 && (
                                                                <div className="ml-2 text-xs font-semibold text-[var(--accent)]">
                                                                    {porcentaje}%
                                                                </div>
                                                            )}
                                                        </div>
                                                        {limiteActual > 0 && (
                                                            <div className="mt-2 w-full bg-[rgba(255,255,255,0.1)] rounded-full h-1.5">
                                                                <div
                                                                    className="bg-[var(--accent)] h-1.5 rounded-full transition-all"
                                                                    style={{ width: `${Math.min(porcentaje, 100)}%` }}
                                                                />
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Sección de Planes */}
                        <div className="bg-[var(--card)] rounded-xl p-5">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-[var(--color-2)]">Planes</h3>
                                <div className="text-[var(--color-2)]">Escoge el plan ideal</div>
                            </div>

                            {loadingPlans ? (
                                <div className="text-center py-8 text-[var(--color-2)]">
                                    Cargando planes...
                                </div>
                            ) : errorPlans ? (
                                <div className="text-center py-8 text-red-400">
                                    {errorPlans}
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {plans.map((p) => {
                                        const buttonInfo = getPlanButtonInfo(p.id);
                                        const isCurrentPlan = suscripcion && suscripcion.plan.id === p.id;
                                        
                                        return (
                                            <div 
                                                key={p.id} 
                                                className={`p-3 rounded-lg bg-[rgba(255,255,255,0.02)] flex flex-col justify-between transition-all ${
                                                    isCurrentPlan ? 'ring-2 ring-[var(--accent)]' : ''
                                                }`}
                                            >
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <div className="font-medium text-[var(--color-2)]">{p.nombre}</div>
                                                        {isCurrentPlan && (
                                                            <span className="text-xs bg-[var(--accent)]/20 text-[var(--accent)] px-2 py-0.5 rounded-full">
                                                                Actual
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="text-sm text-[var(--color-2)] mt-1">{p.resumen}</div>
                                                </div>
                                                <div className="mt-3 flex items-center justify-between">
                                                    <div className="text-[var(--accent)] font-semibold">{p.precio}</div>
                                                    <div className="flex gap-2">
                                                        <button 
                                                            onClick={() => setSelectedPlan(p)} 
                                                            className="px-3 py-1 rounded bg-white/5 text-sm hover:bg-white/10 transition-colors"
                                                        >
                                                            Ver detalles
                                                        </button>
                                                        <button 
                                                            onClick={() => handleCambiarPlan(p.id, p.nombre)}
                                                            className={`px-3 py-1 rounded text-sm transition-all ${buttonInfo.className}`}
                                                            disabled={buttonInfo.disabled}
                                                        >
                                                            {buttonInfo.text}
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    </div>
                </section>

                {/* Botón de cerrar sesión */}
                <div className="mt-8 flex justify-center">
                    <button
                        onClick={() => {
                            const logout = useAuthStore.getState().logout;
                            logout();
                            navigate({ to: '/auth/login' });
                        }}
                        className="px-6 py-3 rounded-lg bg-red-500/80 hover:bg-red-500 text-white font-semibold flex items-center gap-2 transition-all"
                    >
                        <LogOut size={20} />
                        Cerrar sesión
                    </button>
                </div>

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
