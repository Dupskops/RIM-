import { useRef, useState } from "react";
import { Html } from "@react-three/drei";
import * as THREE from "three";

type Props = {
  position: [number, number, number];
  label?: string;
  status?: "excelente" | "bueno" | "atencion" | "critico";
  onSelect?: (label: string) => void;
};

export default function Marker({ position, label = "Punto", status = "critico", onSelect }: Props) {
  const ref = useRef<THREE.Mesh | null>(null);
  const [open, setOpen] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const colorMap: Record<string, string> = {
    excelente: "#10b981", // green
    bueno: "#06b6d4", // cyan
    atencion: "#f59e0b", // orange
    critico: "#ef4444", // red
  };
  const markerColor = colorMap[status] ?? "#ef4444";
  

  return (
    <group position={position}>
      <mesh
        ref={ref}
        onClick={(e: any) => {
          e.stopPropagation();
          // If parent provided an onSelect handler, delegate selection to it
          if (onSelect && typeof onSelect === "function") {
            onSelect(label);
            return;
          }
          // fallback: toggle local tooltip
          setOpen((v) => !v);
        }}
      >
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color={markerColor} emissive={markerColor} />
      </mesh>

      <Html center style={{ pointerEvents: open || showDetails ? "auto" : "none" }}>
        {open && (
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "white",
              color: "#000",
              padding: 8,
              borderRadius: 6,
              boxShadow: "0 6px 18px rgba(0,0,0,0.2)",
              minWidth: 160,
              textAlign: "left",
            }}
          >
            <div style={{ fontWeight: 700 }}>{label}</div>
            <div style={{ fontSize: 12, marginTop: 6 }}>Estado: revisión recomendada</div>
              <div style={{ marginTop: 8, display: "flex", justifyContent: "flex-end" }}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  // Delegate to parent if available
                  if (onSelect && typeof onSelect === "function") {
                    onSelect(label);
                    setOpen(false);
                    return;
                  }
                  // fallback to local details
                  setOpen(false);
                  setShowDetails(true);
                }}
                style={{ padding: "6px 10px", background: "#2563eb", color: "white", border: "none", borderRadius: 4 }}
              >
                Ver diagnóstico
              </button>
            </div>
          </div>
        )}

        {/* Card de diagnóstico más grande anclada (se puede cerrar) */}
        {showDetails && (
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "white",
              color: "#000",
              padding: 14,
              borderRadius: 8,
              boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
              minWidth: 260,
              maxWidth: 360,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontWeight: 800 }}>Diagnóstico del vehículo</div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDetails(false);
                }}
                style={{ background: "transparent", border: "none", fontSize: 16, cursor: "pointer" }}
                aria-label="Cerrar diagnóstico"
              >
                ✕
              </button>
            </div>

            <div style={{ marginTop: 8, fontSize: 13 }}>
              <div><strong>Componente:</strong> {label}</div>
              <div style={{ marginTop: 6 }}><strong>Estado:</strong> Requiere revisión</div>
              <div style={{ marginTop: 8 }}><strong>Recomendación:</strong> Revisar sistema de frenos y conexiones.</div>
            </div>

            <div style={{ marginTop: 12, display: "flex", justifyContent: "flex-end", gap: 8 }}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  // Aquí podrías abrir una vista detallada o enviar a backend
                  alert("Abrir más detalles (a implementar)");
                }}
                style={{ padding: "6px 10px", background: "#10b981", color: "white", border: "none", borderRadius: 4 }}
              >
                Acción
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDetails(false);
                }}
                style={{ padding: "6px 10px", background: "#ef4444", color: "white", border: "none", borderRadius: 4 }}
              >
                Cerrar
              </button>
            </div>
          </div>
        )}
      </Html>
    </group>
  );
}
