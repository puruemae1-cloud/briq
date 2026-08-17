import { useEffect, useMemo, useRef, useState } from "react";
import { BODY_BONES, FINE_PHASES, TOUR_STYLE, type BodyId } from "@/lib/anatomy";
import { buildPose, comparePoses, jointsAsBody, type BodyDelta } from "@/lib/pose";
import type { Handedness, ProProfile, SkeletonFrame } from "@/lib/types";

type Props = {
  userFrames: SkeletonFrame[];
  proFrames?: SkeletonFrame[];
  pro: ProProfile;
  handedness: Handedness;
  trialLimited?: boolean;
  onPhase?: (index: number, t: number) => void;
};

function project(x: number, y: number, w: number, h: number) {
  return { x: w * 0.5 + x * w * 0.72, y: h * 0.12 + y * h * 0.78 };
}

export function PhaseOverlay({
  userFrames,
  proFrames,
  pro,
  handedness,
  trialLimited,
  onPhase,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const onPhaseRef = useRef(onPhase);
  onPhaseRef.current = onPhase;
  const [phase, setPhase] = useState(17);
  const [focus, setFocus] = useState<BodyId | null>(null);

  const userBody = useMemo(() => {
    const joints = userFrames[Math.min(phase, Math.max(userFrames.length - 1, 0))]?.joints ?? {};
    return jointsAsBody(joints);
  }, [userFrames, phase]);
  const proBody = useMemo(() => {
    if (proFrames?.length) {
      const joints = proFrames[Math.min(phase, proFrames.length - 1)]?.joints ?? {};
      const fromClip = jointsAsBody(joints);
      if (fromClip) return fromClip;
    }
    return buildPose({
      style: pro.style ?? TOUR_STYLE,
      phaseT: FINE_PHASES[phase]?.t ?? 0.74,
      handedness,
    });
  }, [pro, proFrames, phase, handedness]);
  const deltas: BodyDelta[] = useMemo(() => {
    if (!userBody) return [];
    return comparePoses(userBody, proBody);
  }, [userBody, proBody]);

  const shown = trialLimited ? deltas.slice(0, 6) : deltas;
  const current = FINE_PHASES[phase];

  useEffect(() => {
    onPhaseRef.current?.(phase, current?.t ?? 0);
  }, [phase, current?.t]);

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

    ctx.fillStyle = "rgba(255,255,255,0.03)";
    ctx.fillRect(0, 0, w, h);

    const drawBones = (
      joints: Record<string, { x: number; y: number }>,
      color: string,
      width: number,
    ) => {
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.lineCap = "round";
      for (const [a, b] of BODY_BONES) {
        const ja = joints[a];
        const jb = joints[b];
        if (!ja || !jb) continue;
        const pa = project(ja.x, ja.y, w, h);
        const pb = project(jb.x, jb.y, w, h);
        ctx.beginPath();
        ctx.moveTo(pa.x, pa.y);
        ctx.lineTo(pb.x, pb.y);
        ctx.stroke();
      }
    };

    drawBones(proBody, "#c9b37a", 3.2);
    if (userBody) drawBones(userBody, "#7dcea0", 2.4);

    if (userBody) {
      for (const d of shown) {
        const a = userBody[d.id];
        const b = proBody[d.id];
        if (!a || !b) continue;
        const pa = project(a.x, a.y, w, h);
        const pb = project(b.x, b.y, w, h);
        const active = !focus || focus === d.id;
        ctx.strokeStyle =
          d.severity === "fix"
            ? `rgba(255,140,120,${active ? 0.95 : 0.2})`
            : d.severity === "watch"
              ? `rgba(240,200,90,${active ? 0.85 : 0.15})`
              : `rgba(125,206,160,${active ? 0.45 : 0.08})`;
        ctx.lineWidth = focus === d.id ? 3 : 1.4;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(pa.x, pa.y);
        ctx.lineTo(pb.x, pb.y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = "#7dcea0";
        ctx.beginPath();
        ctx.arc(pa.x, pa.y, focus === d.id ? 5 : 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#c9b37a";
        ctx.beginPath();
        ctx.arc(pb.x, pb.y, focus === d.id ? 5 : 3, 0, Math.PI * 2);
        ctx.fill();
        if (focus === d.id || d.severity === "fix") {
          ctx.fillStyle = "#f2ead2";
          ctx.font = "11px Sora, sans-serif";
          ctx.fillText(d.label, (pa.x + pb.x) / 2 + 6, (pa.y + pb.y) / 2);
        }
      }
    }
  }, [userBody, proBody, shown, focus]);

  return (
    <section className="twin-overlay">
      <header className="twin-overlay__head">
        <p className="twin-kicker">
          Phase {current?.n} / 30 · {current?.code}
        </p>
        <h2>
          {current?.label} — you vs {pro.name}
        </h2>
        <p>{current?.cue} Gold = player. Mint = you. Dashed line = the gap.</p>
      </header>
      <canvas ref={canvasRef} className="twin-overlay__canvas" />
      <label className="twin-overlay__slider">
        <span>
          {current?.n}. {current?.label}
        </span>
        <input
          type="range"
          min={0}
          max={FINE_PHASES.length - 1}
          value={phase}
          onChange={(e) => setPhase(Number(e.target.value))}
        />
      </label>
      <div className="twin-overlay__phases">
        {FINE_PHASES.map((p, i) => (
          <button
            key={p.id}
            type="button"
            className={i === phase ? "is-on" : undefined}
            onClick={() => setPhase(i)}
          >
            {p.n}
          </button>
        ))}
      </div>
      <ul className="twin-body">
        {shown.map((d) => (
          <li key={d.id} className={`is-${d.severity}${focus === d.id ? " is-focus" : ""}`}>
            <button type="button" onClick={() => setFocus(focus === d.id ? null : d.id)}>
              <strong>{d.label}</strong>
              <span>{d.group}</span>
              <p>{d.note}</p>
            </button>
          </li>
        ))}
      </ul>
      {trialLimited ? (
        <p className="twin-note">Trial shows six body lines. Subscribe for all 30 parts at every phase.</p>
      ) : null}
    </section>
  );
}
