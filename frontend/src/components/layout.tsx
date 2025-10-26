import { Outlet } from "@tanstack/react-router";
import { BarChart2, BellDot, Bot, Clock, Home, User } from "lucide-react";
import { useState } from "react";


export default function Layout() {
  const [activeIndex, setActiveIndex] = useState<number>(0);
  return (
    <div>
      <header className="flex items-center justify-between p-3">
        <h1
          className="text-2xl font-extrabold"
          style={{ color: "var(--accent)" }}
        >
          KTM
        </h1>

        <div className="flex items-center gap-2">
          <button
            className="cursor-pointer p-2 rounded-lg text-[var(--muted)]"
            aria-label="Notificaciones"
          >
            <BellDot />
          </button>
          <button
            className="cursor-pointer p-2 rounded-lg text-[var(--muted)]"
            aria-label="Perfil"
          >
            <User />
          </button>
        </div>
      </header>
      <Outlet />
      <button
        aria-label="Chatbot"
        title="Chatbot"
        onClick={() => { /* placeholder: abrir chat */ }}
        className="fixed right-4 bottom-20 md:bottom-20 z-40 w-14 h-14 rounded-full bg-[var(--accent)] text-[#071218] shadow-lg flex items-center justify-center transform transition-transform duration-150 hover:-translate-y-1 active:scale-95"
      >
        <Bot />
      </button>
      <nav
        className="fixed left-1/2 -translate-x-1/2 bottom-3 w-[min(92%,360px)] bg-[var(--accent)] rounded-lg flex gap-2 px-2"
        role="navigation"
        aria-label="Navegación principal"
      >
        {/* indicator: width 1/4, moves by translateX(0|100%|200%|300%) */}
        <div
          className="nav-indicator absolute left-0 top-0 h-full w-[25%] rounded-md"
          style={{ transform: `translateX(${activeIndex * 100}%)` }}
          aria-hidden
        />

        <button
          onClick={() => setActiveIndex(0)}
          aria-current={activeIndex === 0}
          aria-label="Home"
          className="nav-button relative z-10 flex-1 flex flex-col items-center justify-center py-2 text-[var(--bg)] transition-transform duration-200 ease-in-out hover:-translate-y-1 hover:scale-[1.03]"
        >
          <Home size={18} />
          <span className="text-xs">Home</span>
        </button>

        <button
          onClick={() => setActiveIndex(1)}
          aria-current={activeIndex === 1}
          aria-label="Diagnóstico"
          className="nav-button relative z-10 flex-1 flex flex-col items-center justify-center py-2 text-[var(--bg)] transition-transform duration-200 ease-in-out hover:-translate-y-1 hover:scale-[1.03]"
        >
          <BarChart2 size={18} />
          <span className="text-xs">Diagnóstico</span>
        </button>

        {/* Garaje */}
        <button
          onClick={() => setActiveIndex(2)}
          aria-current={activeIndex === 2}
          aria-label="Garaje"
          className="nav-button relative z-10 flex-1 flex flex-col items-center justify-center py-2 text-[var(--bg)] transition-transform duration-200 ease-in-out hover:-translate-y-1 hover:scale-[1.03]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="lucide lucide-motorbike-icon lucide-motorbike"><path d="m18 14-1-3" /><path d="m3 9 6 2a2 2 0 0 1 2-2h2a2 2 0 0 1 1.99 1.81" /><path d="M8 17h3a1 1 0 0 0 1-1 6 6 0 0 1 6-6 1 1 0 0 0 1-1v-.75A5 5 0 0 0 17 5" /><circle cx="19" cy="17" r="3" /><circle cx="5" cy="17" r="3" /></svg>
          <span className="text-xs">Garaje</span>
        </button>

        <button
          onClick={() => setActiveIndex(3)}
          aria-current={activeIndex === 3}
          aria-label="Historial"
          className="nav-button relative z-10 flex-1 flex flex-col items-center justify-center py-2 text-[var(--bg)] transition-transform duration-200 ease-in-out hover:-translate-y-1 hover:scale-[1.03]"
        >
          <Clock size={18} />
          <span className="text-xs">Historial</span>
        </button>
      </nav>
    </div>
  )
}
