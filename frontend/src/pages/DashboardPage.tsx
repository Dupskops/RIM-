import { useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useAuthStore, useMotoStore } from '@/store';
import { useMotos, useLatestReadings } from '@/hooks';
import toast from 'react-hot-toast';

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { motos, selectedMoto, setSelectedMoto } = useMotoStore();
  const { data: motosData, isLoading: loadingMotos } = useMotos();
  const { data: sensores } = useLatestReadings(selectedMoto?.id || '');

  // Seleccionar primera moto por defecto
  useEffect(() => {
    if (motosData && motosData.length > 0 && !selectedMoto) {
      setSelectedMoto(motosData[0]);
    }
  }, [motosData, selectedMoto, setSelectedMoto]);

  const handleLogout = () => {
    logout();
    toast.success('Sesión cerrada');
    navigate({ to: '/' });
  };

  if (loadingMotos) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-white text-xl">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">🏍️ RIM</h1>
            {selectedMoto && (
              <span className="text-gray-400">
                {selectedMoto.marca} {selectedMoto.modelo} - {selectedMoto.anio}
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">
              Hola, {user?.nombre}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm text-red-400 hover:text-red-300 transition-colors"
              title="Cerrar sesión"
            >
              🚪 Salir
            </button>
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
              {user?.nombre?.charAt(0).toUpperCase()}
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Columna Izquierda - Modelo 3D */}
          <div className="lg:col-span-2">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h2 className="text-xl font-semibold mb-4">Modelo 3D de tu Moto</h2>
              
              {/* ESPACIO RESERVADO PARA MODELO 3D */}
              <div className="w-full h-[500px] bg-slate-900 rounded-lg border-2 border-dashed border-slate-600 flex flex-col items-center justify-center">
                <div className="text-center">
                  <div className="text-6xl mb-4">🏍️</div>
                  <p className="text-gray-400 text-lg mb-2">
                    Espacio reservado para Modelo 3D
                  </p>
                  <p className="text-gray-500 text-sm">
                    Aquí se visualizará tu moto en 3D con Three.js
                  </p>
                  <div className="mt-4 text-xs text-gray-600">
                    {selectedMoto ? (
                      <>
                        <p>{selectedMoto.marca} {selectedMoto.modelo}</p>
                        <p>Año: {selectedMoto.anio} | Color: {selectedMoto.color}</p>
                        <p>Kilometraje: {selectedMoto.kilometraje.toLocaleString()} km</p>
                      </>
                    ) : (
                      <p>Registra una moto para verla aquí</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Controles del modelo (placeholder) */}
              <div className="mt-4 flex gap-2 justify-center">
                <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">
                  🔄 Rotar
                </button>
                <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">
                  🔍 Zoom
                </button>
                <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">
                  🎨 Vista
                </button>
              </div>
            </div>
          </div>

          {/* Columna Derecha - Información */}
          <div className="space-y-6">
            {/* Estado General */}
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-lg font-semibold mb-4">Estado General</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Estado:</span>
                  <span className="px-3 py-1 bg-green-600 rounded-full text-sm">
                    ✅ Excelente
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Motos:</span>
                  <span className="font-semibold">{motos.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Estado Cuenta:</span>
                  <span className={`px-3 py-1 rounded-full text-sm ${user?.activo ? 'bg-green-600' : 'bg-red-600'}`}>
                    {user?.activo ? '✅ Activa' : '❌ Inactiva'}
                  </span>
                </div>
              </div>
            </div>

            {/* Sensores Actuales */}
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-lg font-semibold mb-4">Sensores en Tiempo Real</h3>
              {sensores && sensores.length > 0 ? (
                <div className="space-y-3">
                  {sensores.slice(0, 5).map((sensor) => (
                    <div key={sensor.id} className="flex items-center justify-between">
                      <span className="text-gray-400 text-sm capitalize">
                        {sensor.tipo_sensor.replace('_', ' ')}:
                      </span>
                      <span className={`font-semibold ${sensor.es_anomalia ? 'text-red-500' : 'text-green-500'}`}>
                        {sensor.valor} {sensor.unidad}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No hay lecturas disponibles</p>
              )}
            </div>

            {/* Acciones Rápidas */}
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-lg font-semibold mb-4">Acciones Rápidas</h3>
              <div className="space-y-2">
                <button className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-left">
                  💬 Chatbot IA
                </button>
                <button className="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-left">
                  📊 Ver Sensores
                </button>
                <button className="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-left">
                  🔧 Mantenimientos
                </button>
                <button className="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-left">
                  ⚠️ Fallas Activas
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
