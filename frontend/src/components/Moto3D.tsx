import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import { useRef, useState, useEffect } from "react";
import * as THREE from "three";
import Marker from "./Marker.tsx";

// Componente que carga el modelo
function MotoModel() {
  const group = useRef<THREE.Group>(null!);
  const { scene } = useGLTF("/models/moto.glb"); // Ruta de tu modelo

  return (
    <primitive
      ref={group}
      object={scene}
      scale={5} // Aumentado para que la moto se vea más grande
      position={[0, -1.1, 0]} // Ajuste leve de posicionamiento
      rotation={[0, Math.PI, 0]}
    />
  );
}

export default function Moto3D({ onMarkerSelect, markers }: { onMarkerSelect?: (label: string) => void; markers?: Array<{ position: [number, number, number]; label: string; status: "excelente" | "bueno" | "atencion" | "critico" }> }) {
  // marcadores estratégicos iniciales (posiciones aproximadas — ajústalas a tu modelo)
  type MarkerItem = { position: [number, number, number]; label: string; status: "excelente" | "bueno" | "atencion" | "critico" };
  
  const defaultMarkers: MarkerItem[] = [
    { position: [0.35, -1.85, -1.74], label: "Sistema de frenos trasero", status: "critico" },
    { position: [0.35, -1.85, 1.85], label: "Sistema de frenos delantero", status: "critico" },
    { position: [0.35, -1.85, 2.4], label: "Neumáticos y ruedas delantero", status: "atencion" },
    { position: [0.35, -1.85, -2.30], label: "Neumáticos y ruedas trasero", status: "atencion" },
    { position: [0.5, -1.2, 1.1], label: "Sistema de dirección y chasis", status: "bueno" },
    { position: [0, -0.2, 0], label: "Motor y transmisión", status: "critico" },
    { position: [0, -0.7, 1.74], label: "Sistema eléctrico", status: "atencion" },
    { position: [0.7, -1.7, -1], label: "Escape", status: "bueno" },
    { position: [0, 0.2, 1], label: "Controles y mandos", status: "bueno" },
  ];
  
  const [markersState, setMarkersState] = useState<MarkerItem[]>(markers || defaultMarkers);

  // Actualizar marcadores cuando cambia la prop (para diagnósticos dinámicos)
  useEffect(() => {
    if (markers && markers.length > 0) {
      setMarkersState(markers);
    }
  }, [markers]);

  // Añadir un marcador donde el usuario haga click (si intersecta algo)
  const handleCanvasPointerDown = (e: any) => {
    if ((e as any).point) {
      const p = e.point as THREE.Vector3;
      setMarkersState((m) => [...m, { position: [p.x, p.y, p.z], label: "Marcador", status: "atencion" }]);
    }
  };

  return (
  // The card parent provides the background, we keep the canvas filling the container
  <div className="w-full h-full rounded-2xl overflow-hidden">
      <Canvas
        className="w-full h-full"
        camera={{ position: [3, 2.5, 6], fov: 45 }}
        onPointerDown={(e) => handleCanvasPointerDown(e)}
      >
        {/* Luces básicas */}
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 5, 5]} intensity={1.2} />

        {/* Modelo */}
        <MotoModel />

        {/* Marcadores: se renderizan sobre la moto */}
        {markersState.map((m, i) => (
          <Marker key={i} position={m.position} label={m.label} status={m.status} onSelect={onMarkerSelect} />
        ))}

        {/* Control con el mouse */}
        <OrbitControls enableZoom={false} />
      </Canvas>
    </div>
  );
}
