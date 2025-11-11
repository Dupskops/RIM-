import { useState, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useAuthStore } from "@/store";
import { LoginSchema } from "@/lib/validators";
import * as v from "valibot";
import toast from "react-hot-toast";
import { Eye, EyeOff } from "lucide-react";

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validar con Valibot
    try {
      const validatedData = v.parse(LoginSchema, formData);

      // Si la validación pasa, hacer login
      await login(validatedData.email, validatedData.password);
      toast.success("¡Bienvenido a RIM!");
      navigate({ to: "/app" });
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
        const axiosError = error as { response?: { data?: { detail?: string } } };
        const message = axiosError.response?.data?.detail || "Error al iniciar sesión";
        toast.error(message);
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
      className="min-h-screen flex items-center justify-center"
      style={{
        backgroundImage:
          "linear-gradient(180deg, rgba(2,6,8,0.48), rgba(2,6,8,0.64)), url('/imagenes/moto-bg.jpeg')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      <div className="w-full max-w-md mx-4">
        <div
          className={`rounded-2xl overflow-hidden shadow-2xl border border-white/10 transform transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-6 scale-95'}`}
          style={{ background: "linear-gradient(180deg, rgba(2,6,8,0.72), rgba(39,63,79,0.85))" }}
        >
          <div className="p-6 sm:p-8">
            <div className="mb-6">
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white transition-all duration-700" style={{ transform: mounted ? 'translateY(0)' : 'translateY(-8px)', opacity: mounted ? 1 : 0, transitionDelay: '120ms' }}>Iniciar Sesión</h1>
              <p className="mt-2 text-sm text-[var(--color-2)] transition-all duration-700" style={{ transform: mounted ? 'translateY(0)' : 'translateY(-6px)', opacity: mounted ? 1 : 0, transitionDelay: '200ms' }}>Bienvenido de nuevo, te echábamos de menos.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-[var(--color-2)] mb-2">
                  Correo electrónico
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg bg-white/5 border ${errors.email ? 'border-red-500' : 'border-white/10'
                    } text-white placeholder-[rgba(215,215,215,0.6)] focus:outline-none focus:ring-2 ${errors.email ? 'focus:ring-red-500' : 'focus:ring-[var(--bg2)]'
                    }`}
                  placeholder="ayelen@gmail.com"
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-red-400">{errors.email}</p>
                )}
              </div>

              <div className="relative">
                <label htmlFor="password" className="block text-sm font-semibold text-[var(--color-2)] mb-2">
                  Contraseña
                </label>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg bg-white/5 border ${errors.password ? 'border-red-500' : 'border-white/10'
                    } pr-12 text-white placeholder-[rgba(215,215,215,0.6)] focus:outline-none focus:ring-2 ${errors.password ? 'focus:ring-red-500' : 'focus:ring-[var(--bg2)]'
                    }`}
                  placeholder="●●●●●●●●"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-white/70 hover:text-white"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
                {errors.password && (
                  <p className="mt-1 text-xs text-red-400">{errors.password}</p>
                )}
                <button type="button" className="text-[var(--accent)] font-semibold mt-2">
                  ¿Olvidé mi contraseña?
                </button>
              </div>

              <div className="flex items-center justify-between">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 py-3 px-4 bg-[var(--accent)] text-black font-semibold rounded-lg shadow-[var(--accent-shadow)] hover:brightness-95 disabled:opacity-60 transition-all duration-150"
                >
                  {isLoading ? "Iniciando sesión..." : "Iniciar Sesión"}
                </button>
              </div>
            </form>

            <div className="mt-4 flex items-center justify-between text-sm transition-all duration-700" style={{ transform: mounted ? 'translateY(0)' : 'translateY(6px)', opacity: mounted ? 1 : 0, transitionDelay: '260ms' }}>
              <div className="text-[var(--color-2)]">
                ¿No tienes una cuenta?{' '}
                <button
                  onClick={() => navigate({ to: "/auth/register" })}
                  type="button"
                  className="text-[var(--accent)] font-semibold"
                >
                  Crear cuenta
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
