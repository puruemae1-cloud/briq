import { useEffect, useRef } from "react";
import type { SkeletonFrame } from "@/lib/types";

const BONES: [string, string][] = [
  ["head", "neck"],
  ["neck", "lShoulder"],
  ["neck", "rShoulder"],
  ["lShoulder", "lElbow"],
  ["lElbow", "lWrist"],
  ["rShoulder", "rElbow"],
  ["rElbow", "rWrist"],
  ["lShoulder", "lHip"],
  ["rShoulder", "rHip"],
  ["lHip", "rHip"],
  ["lHip", "lKnee"],
  ["lKnee", "lAnkle"],
  ["rHip", "rKnee"],
  ["rKnee", "rAnkle"],
];

type Props = {
  frames: SkeletonFrame[];
  playing?: boolean;
  label?: string;
};

export function Swing3D({ frames, playing = true, label }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rot = useRef({ yaw: 0.55, pitch: 0.18 });
  const frameI = useRef(0);
  const drag = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let last = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const project = (x: number, y: number, z: number, w: number, h: number) => {
      const cy = Math.cos(rot.current.yaw);
      const sy = Math.sin(rot.current.yaw);
      const cp = Math.cos(rot.current.pitch);
      const sp = Math.sin(rot.current.pitch);
      const x1 = x * cy - z * sy;
      const z1 = x * sy + z * cy;
      const y1 = y * cp - z1 * sp;
      const z2 = y * sp + z1 * cp;
      const scale = 220 / (2.2 + z2);
      return { x: w / 2 + x1 * scale, y: h * 0.22 + y1 * scale * 1.15 };
    };

    const draw = (now: number) => {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      ctx.clearRect(0, 0, w, h);

      ctx.fillStyle = "rgba(255,255,255,0.04)";
      ctx.strokeStyle = "rgba(183,161,106,0.25)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.ellipse(w / 2, h * 0.82, 90, 22, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      if (frames.length) {
        if (playing && now - last > 70) {
          frameI.current = (frameI.current + 1) % frames.length;
          last = now;
        }
        const frame = frames[frameI.current] ?? frames[0];
        const joints = frame.joints;

        ctx.lineCap = "round";
        ctx.lineWidth = 3.5;
        ctx.strokeStyle = "#c9b37a";
        for (const [a, b] of BONES) {
          const ja = joints[a];
          const jb = joints[b];
          if (!ja || !jb) continue;
          const pa = project(ja.x, ja.y, ja.z, w, h);
          const pb = project(jb.x, jb.y, jb.z, w, h);
          ctx.beginPath();
          ctx.moveTo(pa.x, pa.y);
          ctx.lineTo(pb.x, pb.y);
          ctx.stroke();
        }

        for (const j of Object.values(joints)) {
          const p = project(j.x, j.y, j.z, w, h);
          ctx.beginPath();
          ctx.fillStyle = j.id === "head" ? "#f2ead2" : "#7dcea0";
          ctx.arc(p.x, p.y, j.id === "head" ? 7 : 3.4, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);

    const onDown = (e: PointerEvent) => {
      drag.current = { x: e.clientX, y: e.clientY };
      canvas.setPointerCapture(e.pointerId);
    };
    const onMove = (e: PointerEvent) => {
      if (!drag.current) return;
      rot.current.yaw += (e.clientX - drag.current.x) * 0.01;
      rot.current.pitch = Math.max(
        -0.7,
        Math.min(0.7, rot.current.pitch + (e.clientY - drag.current.y) * 0.008),
      );
      drag.current = { x: e.clientX, y: e.clientY };
    };
    const onUp = () => {
      drag.current = null;
    };
    canvas.addEventListener("pointerdown", onDown);
    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerup", onUp);
    canvas.addEventListener("pointercancel", onUp);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      canvas.removeEventListener("pointerdown", onDown);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerup", onUp);
      canvas.removeEventListener("pointercancel", onUp);
    };
  }, [frames, playing]);

  return (
    <div className="twin-3d">
      <canvas ref={canvasRef} className="twin-3d__canvas" aria-label="3D swing" />
      <p className="twin-3d__hint">
        {label ?? "Drag to rotate"} · face-on + down-the-line adds depth
      </p>
    </div>
  );
}
