import { useState, useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useAuthStore } from '@/store';
import { RegisterSchemaWithConfirm, getPasswordRequirements } from '@/lib/validators';
import * as v from 'valibot';
import toast from 'react-hot-toast';
import { Eye, EyeOff } from 'lucide-react';


const RegisterPage = () => {
  const navigate = useNavigate();
  const { register, isLoading } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    nombre: '',
    apellido: '',
    telefono: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  // Obtener requisitos de contraseña en tiempo real
  const passwordReqs = getPasswordRequirements(formData.password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validar con Valibot
    try {
      const validatedData = v.parse(RegisterSchemaWithConfirm, formData);

      // Si la validación pasa, registrar usuario
      await register({
        email: validatedData.email,
        password: validatedData.password,
        nombre: validatedData.nombre,
        apellido: validatedData.apellido,
        telefono: validatedData.telefono,
      });

      toast.success('¡Cuenta creada exitosamente!');
      navigate({ to: '/app' });
    } catch (error) {
      // Manejar errores de validación de Valibot
      if (error instanceof v.ValiError) {
        const newErrors: Record<string, string> = {};
        error.issues.forEach((issue) => {
          const path = issue.path?.[0]?.key as string;
          if (path && !newErrors[path]) {
            newErrors[path] = issue.message;
          }
        });
        setErrors(newErrors);

        // Mostrar el primer error
        const firstError = Object.values(newErrors)[0];
        if (firstError) {
          toast.error(firstError);
        }
        return;
      }

      // Manejar errores del backend
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: unknown } } };
        const detail = axiosError.response?.data?.detail;
        if (detail) {
          // Si es un array de errores de validación (FastAPI)
          if (Array.isArray(detail)) {
            (detail as Array<Record<string, unknown>>).forEach((err) => {
              const maybeErr = err as Record<string, unknown>;
              const msg = maybeErr && typeof maybeErr === 'object' && 'msg' in maybeErr ? (maybeErr.msg as string | undefined) : undefined;
              toast.error(msg || 'Error de validación');
            });
          } else if (typeof detail === 'string') {
            toast.error(detail);
          } else {
            toast.error('Error al crear la cuenta');
          }
        } else {
          toast.error('Error al crear la cuenta');
        }
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 80);
    return () => clearTimeout(t);
  }, []);

  return (
    <div
      className="min-h-screen flex items-center justify-center "
      style={{ background: "var(--card)" }}
    >
      <div className="w-full max-w-md mx-4">
        <div
          className={`rounded-2xl overflow-hidden transform transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-6 scale-95'}`}
          style={{ background: "var(--card)" }}
        >
          <div className="p-6 sm:p-8">
            <div className="mb-6 text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512"><path fill="#fe7743" d="M280 16c-13.3 0-24 10.7-24 24s10.7 24 24 24l56.6 0 22.5 48.7-95.1 71.3c-33.4-25.1-75-40-120-40l-56 0c-13.3 0-24 10.7-24 24s10.7 24 24 24l56 0c78.5 0 143.2 59.6 151.2 136l-25.4 0c-11.2-59.2-63.3-104-125.8-104-70.7 0-128 57.3-128 128S73.3 480 144 480c62.5 0 114.5-44.8 125.8-104l50.2 0c13.3 0 24-10.7 24-24l0-22.5c0-45.1 25.7-85.4 65.5-107.7l12.1 26.1c-32.4 23.2-53.5 61.2-53.5 104.1 0 70.7 57.3 128 128 128s128-57.3 128-128-57.3-128-128-128c-10.7 0-21 1.3-30.9 3.8L433.8 160 488 160c13.3 0 24-10.7 24-24l0-48c0-13.3-10.7-24-24-24l-53.3 0c-6.9 0-13.7 2.2-19.2 6.4l-17.1 12.8-24.6-53.3C369.9 21.4 361.4 16 352 16l-72 0zM445.8 300.4l28.4 61.6c5.6 12 19.8 17.3 31.8 11.7s17.3-19.8 11.7-31.8l-28.5-61.6c2.2-.2 4.4-.3 6.7-.3 39.8 0 72 32.2 72 72s-32.2 72-72 72-72-32.2-72-72c0-20.2 8.3-38.5 21.8-51.6zM144 424c-39.8 0-72-32.2-72-72s32.2 72 72 72c31.3 0 58 20 67.9 48L144 328c-13.3 0-24 10.7-24 24s10.7 24 24 24l67.9 0c-9.9 28-36.6 48-67.9 48z" /></svg>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white transition-all duration-700" style={{ transform: mounted ? 'translateY(0)' : 'translateY(-8px)', opacity: mounted ? 1 : 0, transitionDelay: '120ms' }}>Crea tu Cuenta</h1>
              <p className="mt-2 text-sm text-[var(--color-2)] transition-all duration-700" style={{ transform: mounted ? 'translateY(0)' : 'translateY(-6px)', opacity: mounted ? 1 : 0, transitionDelay: '200ms' }}>Empieza a proteger y gestionar tu moto</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="nombre" className="block text-sm font-medium text-gray-200 mb-2">
                  Nombre
                </label>
                <input
                  id="nombre"
                  name="nombre"
                  type="text"
                  required
                  value={formData.nombre}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg bg-white/5 border ${errors.nombre ? 'border-red-500' : 'border-white/10'
                    } text-white placeholder-[rgba(215,215,215,0.6)] focus:outline-none focus:ring-2 ${errors.nombre ? 'focus:ring-red-500' : 'focus:ring-[var(--bg2)]'
                    }`}
                  placeholder="Juan"
                />
                {errors.nombre && (
                  <p className="mt-1 text-xs text-red-400">{errors.nombre}</p>
                )}
              </div>

              <div>
                <label htmlFor="apellido" className="block text-sm font-medium text-gray-200 mb-2">
                  Apellido
                </label>
                <input
                  id="apellido"
                  name="apellido"
                  type="text"
                  required
                  value={formData.apellido}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg bg-white/5 border ${errors.apellido ? 'border-red-500' : 'border-white/10'
                    } text-white placeholder-[rgba(215,215,215,0.6)] focus:outline-none focus:ring-2 ${errors.apellido ? 'focus:ring-red-500' : 'focus:ring-[var(--bg2)]'
                    }`}
                  placeholder="Pérez"
                />
                {errors.apellido && (
                  <p className="mt-1 text-xs text-red-400">{errors.apellido}</p>
                )}
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-200 mb-2">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg bg-white/10 border ${errors.email ? 'border-red-500' : 'border-white/20'
                    } text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${errors.email ? 'focus:ring-red-500' : 'focus:ring-blue-500'
                    }`}
                  placeholder="juanPerez@email.com"
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-red-400">{errors.email}</p>
                )}
              </div>

              <div>
                <label htmlFor="telefono" className="block text-sm font-medium text-gray-200 mb-2">
                  Teléfono <span className="text-gray-400 text-xs">(opcional)</span>
                </label>
                <input
                  id="telefono"
                  name="telefono"
                  type="tel"
                  value={formData.telefono}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg bg-white/10 border ${errors.telefono ? 'border-red-500' : 'border-white/20'
                    } text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${errors.telefono ? 'focus:ring-red-500' : 'focus:ring-blue-500'
                    }`}
                  placeholder="+57 300 123 4567"
                />
                {errors.telefono && (
                  <p className="mt-1 text-xs text-red-400">{errors.telefono}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-200 mb-2">
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className={`w-full px-4 pr-12 py-3 rounded-lg bg-white/10 border ${errors.password ? 'border-red-500' : 'border-white/20'
                      } text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${errors.password ? 'focus:ring-red-500' : 'focus:ring-blue-500'
                      }`}
                    placeholder="••••••••"
                  />

                  <button
                    type="button"
                    onClick={() => setShowPassword((s) => !s)}
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    className="absolute inset-y-0 right-0 flex items-center px-3 text-white/70 hover:text-white"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-xs text-red-400">{errors.password}</p>
                )}
                {formData.password && (
                  <div className="mt-2 text-xs space-y-1">
                    <p className={passwordReqs.minLength ? 'text-green-400' : 'text-gray-400'}>
                      {passwordReqs.minLength ? '✓' : '○'} Mínimo 8 caracteres
                    </p>
                    <p className={passwordReqs.hasUppercase ? 'text-green-400' : 'text-gray-400'}>
                      {passwordReqs.hasUppercase ? '✓' : '○'} Una mayúscula
                    </p>
                    <p className={passwordReqs.hasLowercase ? 'text-green-400' : 'text-gray-400'}>
                      {passwordReqs.hasLowercase ? '✓' : '○'} Una minúscula
                    </p>
                    <p className={passwordReqs.hasNumber ? 'text-green-400' : 'text-gray-400'}>
                      {passwordReqs.hasNumber ? '✓' : '○'} Un número
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-200 mb-2">
                  Confirmar Contraseña
                </label>
                <div className="relative">
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    required
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={`w-full px-4 pr-12 py-3 rounded-lg bg-white/10 border ${errors.confirmPassword ? 'border-red-500' : 'border-white/20'
                      } text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${errors.confirmPassword ? 'focus:ring-red-500' : 'focus:ring-blue-500'
                      }`}
                    placeholder="••••••••"
                  />

                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword((s) => !s)}
                    aria-label={showConfirmPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    className="absolute inset-y-0 right-0 flex items-center px-3 text-white/70 hover:text-white"
                  >
                    {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="mt-1 text-xs text-red-400">{errors.confirmPassword}</p>
                )}

                
              </div>


              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 bg-[var(--accent)] text-black font-semibold rounded-lg shadow-[var(--accent-shadow)] hover:brightness-95 disabled:opacity-60 transition-all duration-150 mt-4"
              >
                {isLoading ? 'Creando cuenta...' : 'Registrarse'}
              </button>
            </form>

            <div className="mt-4 text-center text-sm">
              <p className="text-[var(--color-2)]">
                ¿Ya tienes cuenta?{' '}
                <button
                  onClick={() => navigate({ to: '/auth/login' })}
                  type="button"
                  className="text-[var(--accent)] font-semibold"
                >
                  Inicia sesión
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
