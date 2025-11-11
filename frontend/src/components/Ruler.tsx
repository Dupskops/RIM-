// @ts-nocheck
import { Html } from "@react-three/drei";
import * as THREE from "three";

type RulerProps = {
  axis: "x" | "y" | "z";
  length?: number;
  divisions?: number;
  color?: string;
};

export default function Ruler({ axis, length = 2, divisions = 8, color = "#ffffff" }: RulerProps) {
  const half = length / 2;
  const ticks: JSX.Element[] = [];

  for (let i = 0; i <= divisions; i++) {
    const t = -half + (i * length) / divisions;
    let pos: [number, number, number] = [0, 0, 0];
    if (axis === "x") pos = [t, 0, 0];
    if (axis === "y") pos = [0, t, 0];
    if (axis === "z") pos = [0, 0, t];

    ticks.push(
      <group key={i} position={pos}>
        <mesh>
          <boxGeometry args={[0.02, 0.02, 0.02]} />
          <meshBasicMaterial color={color} />
        </mesh>
        <Html center distanceFactor={8} style={{ pointerEvents: "none", color: "white", fontSize: 10 }}>
          <div style={{ transform: "translateY(-6px)", whiteSpace: "nowrap", fontSize: 12, color }}>
            {parseFloat(t.toFixed(2))}
          </div>
        </Html>
      </group>
    );
  }

  // line points
  const p1 = new THREE.Vector3();
  const p2 = new THREE.Vector3();
  if (axis === "x") {
    p1.set(-half, 0, 0);
    p2.set(half, 0, 0);
  } else if (axis === "y") {
    p1.set(0, -half, 0);
    p2.set(0, half, 0);
  } else {
    p1.set(0, 0, -half);
    p2.set(0, 0, half);
  }

  const points = [p1, p2];

  return (
    <group>
      {/* main line */}
      <line>
        <bufferGeometry attach="geometry">
          <bufferAttribute
            attach="attributes-position"
            array={new Float32Array(points.flatMap((v) => [v.x, v.y, v.z]))}
            count={points.length}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial attach="material" color={color} linewidth={2} />
      </line>

      {/* ticks and labels */}
      {ticks}
    </group>
  );
}
