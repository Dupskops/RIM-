import { Outlet, useLocation, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from 'react';
import { BellDot, Bot, User } from "lucide-react";
import Navbar from "./navbar";
import { useAuthStore } from "@/store";

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  // local state to hide UI immediately when opening chatbot
  const [chatOpen, setChatOpen] = useState(false);

  // hide navbar on certain routes (notificaciones and chatbot) or while chatOpen is true
  const hideNavbar = chatOpen || location?.pathname.startsWith('/app/notificaciones') || location?.pathname.startsWith('/app/chatbot');

  // keep chatOpen in sync with the URL: if we navigate away from chatbot, reset chatOpen
  useEffect(() => {
    if (!location?.pathname.startsWith('/app/chatbot')) setChatOpen(false);
  }, [location]);

  return (
    <div>
      <header className="flex items-center justify-between p-3">
        <button
          onClick={() => navigate({ to: '/app' })}
          className="text-2xl font-extrabold"
          style={{ color: "var(--accent)" }}
        >
        KTM
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate({ to: '/app/notificaciones' })}
            className="p-2 rounded-lg text-[var(--muted)] hover:text-[var(--accent)]"
            aria-label="Notificaciones"
          >
            <BellDot />
          </button>
          
          <button
            onClick={() => navigate({ to: '/app/miPerfil' })}
            className="cursor-pointer pl-1 rounded-lg text-[var(--muted)] hover:text-[var(--accent)]"
            aria-label="Perfil"
          >
            <User />
          </button>
          <h5 className="text-[var(--card)]">{useAuthStore((s) => s.user?.nombre)}</h5>
        </div>
      </header>
      <Outlet />
      {location && !location.pathname.startsWith('/app/diagnostico') && !location.pathname.startsWith('/app/chatbot') && !chatOpen && (
        <button
          aria-label="Chatbot"
          title="Chatbot"
          onClick={() => { setChatOpen(true); navigate({ to: '/app/chatbot' }); }}
          className="fixed right-4 bottom-20 md:bottom-20 z-40 w-14 h-14 rounded-full bg-[var(--accent)] text-[#071218] shadow-lg flex items-center justify-center transform transition-transform duration-150 hover:-translate-y-1 active:scale-95"
        >
          <Bot />
        </button>
      )}
      {!hideNavbar && <Navbar />}
    </div>
  )
}
