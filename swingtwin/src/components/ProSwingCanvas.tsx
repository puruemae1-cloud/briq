import { useEffect, useRef } from "react";
import { BODY_BONES, FINE_PHASES, TOUR_STYLE } from "@/lib/anatomy";
import { buildPose } from "@/lib/pose";
import type { Handedness, ProProfile } from "@/lib/types";

type Props = {
  pro: ProProfile;
  handedness: Handedness;
  /** 0 = takeaway, 1 = impact */
  phaseNorm: number;
  label?: string;
};

function project(x: number, y: number, w: number, h: number) {
  return { x: w * 0.5 + x * w * 0.72, y: h * 0.1 + y * h * 0.82 };
}

export function ProSwingCanvas({ pro, handedness, phaseNorm, label }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    ctx.fillStyle = "#04110c";
    ctx.fillRect(0, 0, w, h);

    const idx = Math.min(
      FINE_PHASES.length - 1,
      Math.max(0, Math.round(phaseNorm * (FINE_PHASES.length - 1))),
    );
    const phase = FINE_PHASES[idx]!;
    const joints = buildPose({
      style: pro.style ?? TOUR_STYLE,
      phaseT: phase.t,
      handedness,
    });

    ctx.strokeStyle = "#c9b37a";
    ctx.lineWidth = 3.2;
    ctx.lineCap = "round";
    for (const [a, b] of BODY_BONES) {
      const ja = joints[a];
      const jb = joints[b];
      const pa = project(ja.x, ja.y, w, h);
      const pb = project(jb.x, jb.y, w, h);
      ctx.beginPath();
      ctx.moveTo(pa.x, pa.y);
      ctx.lineTo(pb.x, pb.y);
      ctx.stroke();
    }

    for (const j of Object.values(joints)) {
      const p = project(j.x, j.y, w, h);
      ctx.beginPath();
      ctx.fillStyle = j.id === "head" ? "#f2ead2" : "#c9b37a";
      ctx.arc(p.x, p.y, j.id === "head" ? 6 : 3, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.fillStyle = "rgba(201,179,122,0.85)";
    ctx.font = "11px Sora, sans-serif";
    ctx.fillText(`${phase.n}. ${phase.label}`, 10, h - 12);
  }, [pro, handedness, phaseNorm]);

  return (
    <div className="twin-pro-canvas">
      <canvas ref={canvasRef} className="twin-pro-canvas__el" aria-label={label} />
      {label ? <p className="twin-pro-canvas__cap">{label}</p> : null}
    </div>
  );
}
