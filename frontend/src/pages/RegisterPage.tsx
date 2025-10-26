import { useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useAuthStore } from '@/store';
import { RegisterSchemaWithConfirm, getPasswordRequirements } from '@/lib/validators';
import * as v from 'valibot';
import toast from 'react-hot-toast';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register, isLoading } = useAuthStore();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    nombre: '',
    telefono: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

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
        telefono: validatedData.telefono,
      });
      
      toast.success('¡Cuenta creada exitosamente!');
      navigate({ to: '/home' });
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
        const axiosError = error as any;
        if (axiosError.response?.data?.detail) {
          const detail = axiosError.response.data.detail;
          
          // Si es un array de errores de validación (FastAPI)
          if (Array.isArray(detail)) {
            detail.forEach((err: any) => {
              toast.error(err.msg || 'Error de validación');
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 py-12 px-4">
      <div className="bg-white/10 backdrop-blur-lg p-8 rounded-2xl shadow-2xl w-full max-w-md border border-white/20">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🏍️ RIM</h1>
          <p className="text-gray-300">Crea tu cuenta</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="nombre" className="block text-sm font-medium text-gray-200 mb-2">
              Nombre completo
            </label>
            <input
              id="nombre"
              name="nombre"
              type="text"
              required
              value={formData.nombre}
              onChange={handleChange}
              className={`w-full px-4 py-3 rounded-lg bg-white/10 border ${
                errors.nombre ? 'border-red-500' : 'border-white/20'
              } text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${
                errors.nombre ? 'focus:ring-red-500' : 'focus:ring-blue-500'
              }`}
              placeholder="Juan Pérez"
            />
            {errors.nombre && (
              <p className="mt-1 text-xs text-red-400">{errors.nombre}</p>
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
              className={`w-full px-4 py-3 rounded-lg bg-white/10 border ${
                errors.email ? 'border-red-500' : 'border-white/20'
              } text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${
                errors.email ? 'focus:ring-red-500' : 'focus:ring-blue-500'
              }`}
              placeholder="tu@email.com"
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
              className={`w-full px-4 py-3 rounded-lg bg-white/10 border ${
                errors.telefono ? 'border-red-500' : 'border-white/20'
              } text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${
                errors.telefono ? 'focus:ring-red-500' : 'focus:ring-blue-500'
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
            <input
              id="password"
              name="password"
              type="password"
              required
              value={formData.password}
              onChange={handleChange}
              className={`w-full px-4 py-3 rounded-lg bg-white/10 border ${
                errors.password ? 'border-red-500' : 'border-white/20'
              } text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${
                errors.password ? 'focus:ring-red-500' : 'focus:ring-blue-500'
              }`}
              placeholder="••••••••"
            />
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
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              required
              value={formData.confirmPassword}
              onChange={handleChange}
              className={`w-full px-4 py-3 rounded-lg bg-white/10 border ${
                errors.confirmPassword ? 'border-red-500' : 'border-white/20'
              } text-white placeholder-gray-400 focus:outline-none focus:ring-2 ${
                errors.confirmPassword ? 'focus:ring-red-500' : 'focus:ring-blue-500'
              }`}
              placeholder="••••••••"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-xs text-red-400">{errors.confirmPassword}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors duration-200 mt-6"
          >
            {isLoading ? 'Creando cuenta...' : 'Registrarse'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-300">
            ¿Ya tienes cuenta?{' '}
            <button
              onClick={() => navigate({ to: '/' })}
              type="button"
              className="text-blue-400 hover:text-blue-300 font-semibold"
            >
              Inicia sesión aquí
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
