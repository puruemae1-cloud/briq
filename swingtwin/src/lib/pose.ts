import type { Handedness, Joint3D, MotionSample, SkeletonFrame } from "./types";
import {
  AMATEUR_STYLE,
  BODY_PARTS,
  FINE_PHASES,
  type BodyId,
  type PlayerStyle,
} from "./anatomy";

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function j(id: BodyId, x: number, y: number, z: number): Joint3D {
  return { id, x, y, z };
}

export type PoseOpts = {
  style: PlayerStyle;
  phaseT: number;
  handedness?: Handedness;
  motion?: Pick<MotionSample, "cx" | "cy" | "width" | "height">;
};

/**
 * Parametric tour skeleton. Style knobs come from the Instagram-archive
 * models; optional motion (from the subscriber clip) shifts the axis.
 */
export function buildPose(opts: PoseOpts): Record<BodyId, Joint3D> {
  const s = opts.style;
  const t = clamp(opts.phaseT, 0, 1);
  const rh = opts.handedness !== "left";
  const lead = rh ? 1 : -1;
  const trail = -lead;

  const atTop = Math.sin((Math.min(t, 0.42) / 0.42) * Math.PI);
  const down = t <= 0.42 ? 0 : clamp((t - 0.42) / 0.32, 0, 1);
  const through = t <= 0.74 ? 0 : clamp((t - 0.74) / 0.26, 0, 1);

  const m = opts.motion;
  const cx = m ? (m.cx - 0.5) * 1.4 : 0;
  const cy = m ? m.cy - 0.48 : 0;
  const w = (m?.width ?? 0.3) * (0.7 + s.stanceWidth * 0.6);
  const h = m?.height ?? 0.7;

  const headSway = (1 - s.headQuiet) * Math.sin(t * Math.PI) * 0.09;
  const ee = s.earlyExt * down * 0.1;
  const squat = s.squat * atTop * 0.04;
  const turn = s.shoulderTurn * atTop * 0.16;
  const hip = s.hipClear * (down * 0.12 + through * 0.1);
  const armUp = s.backswingLen * atTop * h * 0.38;
  const elbowIn = s.trailElbowIn;
  const wristBow = s.leadWristBow;
  const handsIn = s.handPathIn;
  const tilt = s.spineTilt;

  const baseX = cx + headSway * (1 - s.headQuiet);
  const shoulderY = 0.28 + cy - tilt * 0.02 + ee;
  const hipY = 0.52 + cy + squat - ee * 0.4;
  const zTurn = turn;

  const leadShoulder = {
    x: baseX + lead * w * 0.34 + hip * lead * 0.04,
    y: shoulderY,
    z: zTurn * 0.4,
  };
  const trailShoulder = {
    x: baseX + trail * w * 0.36 - hip * trail * 0.02,
    y: shoulderY + atTop * 0.01,
    z: -zTurn * 0.5,
  };
  const chest = {
    x: (leadShoulder.x + trailShoulder.x) / 2,
    y: shoulderY + 0.05,
    z: zTurn * 0.1,
  };
  const leadHip = {
    x: baseX + lead * w * (0.16 + s.stanceWidth * 0.04) + hip * lead,
    y: hipY,
    z: hip * 0.3,
  };
  const trailHip = {
    x: baseX + trail * w * (0.18 + s.stanceWidth * 0.04) - hip * 0.3 * trail,
    y: hipY + down * 0.01,
    z: -hip * 0.2,
  };
  const pelvis = {
    x: (leadHip.x + trailHip.x) / 2,
    y: hipY,
    z: 0,
  };

  const leadElbow = {
    x: leadShoulder.x + lead * w * 0.12,
    y: shoulderY + h * 0.1 - armUp * 0.35 + down * 0.08,
    z: zTurn * 0.7,
  };
  const trailElbow = {
    x: trailShoulder.x + trail * w * (0.22 - elbowIn * 0.16) + down * trail * -0.04,
    y: shoulderY - armUp * 0.55 + down * 0.14,
    z: -zTurn * (1.1 - elbowIn * 0.3),
  };
  const leadWrist = {
    x: lerp(leadElbow.x, chest.x + lead * 0.04, 0.35) + (0.5 - handsIn) * lead * 0.06,
    y: shoulderY + h * 0.16 - armUp * 0.95 + down * 0.22 + through * -0.08,
    z: zTurn * 1.2 + wristBow * 0.05,
  };
  const trailWrist = {
    x: lerp(trailElbow.x, leadWrist.x, 0.35),
    y: leadWrist.y - 0.02 + (1 - wristBow) * 0.02,
    z: leadWrist.z - 0.08,
  };

  const leadKnee = {
    x: leadHip.x + lead * 0.01 - down * lead * 0.02,
    y: hipY + h * 0.2,
    z: 0.02,
  };
  const trailKnee = {
    x: trailHip.x + trail * 0.02 + down * 0.03 * trail,
    y: hipY + h * 0.2 + atTop * 0.01,
    z: 0.02,
  };
  const leadAnkle = {
    x: baseX + lead * w * (0.2 + s.stanceWidth * 0.08),
    y: hipY + h * 0.4,
    z: 0,
  };
  const trailAnkle = {
    x: baseX + trail * w * (0.22 + s.stanceWidth * 0.08),
    y: hipY + h * 0.4 - through * 0.03,
    z: through * 0.04,
  };

  const head = {
    x: baseX + headSway,
    y: shoulderY - h * 0.16 - ee * 0.3,
    z: zTurn * 0.05,
  };

  const mid = (
    a: { x: number; y: number; z: number },
    b: { x: number; y: number; z: number },
  ) => ({
    x: (a.x + b.x) / 2,
    y: (a.y + b.y) / 2,
    z: (a.z + b.z) / 2,
  });

  const leadHand = {
    x: leadWrist.x + lead * 0.02,
    y: leadWrist.y + 0.015,
    z: leadWrist.z,
  };
  const trailHand = {
    x: trailWrist.x + trail * 0.015,
    y: trailWrist.y + 0.01,
    z: trailWrist.z,
  };

  const pts: Record<BodyId, { x: number; y: number; z: number }> = {
    head,
    forehead: { x: head.x, y: head.y - 0.03, z: head.z },
    chin: { x: head.x, y: head.y + 0.03, z: head.z },
    neck: { x: head.x, y: shoulderY - 0.04, z: head.z },
    leadShoulder,
    trailShoulder,
    leadUpperArm: mid(leadShoulder, leadElbow),
    trailUpperArm: mid(trailShoulder, trailElbow),
    leadElbow,
    trailElbow,
    leadForearm: mid(leadElbow, leadWrist),
    trailForearm: mid(trailElbow, trailWrist),
    leadWrist,
    trailWrist,
    leadHand,
    trailHand,
    chest,
    leadHip,
    trailHip,
    pelvis,
    leadThigh: mid(leadHip, leadKnee),
    trailThigh: mid(trailHip, trailKnee),
    leadKnee,
    trailKnee,
    leadShin: mid(leadKnee, leadAnkle),
    trailShin: mid(trailKnee, trailAnkle),
    leadAnkle,
    trailAnkle,
    leadFoot: { x: leadAnkle.x + lead * 0.02, y: leadAnkle.y + 0.02, z: 0 },
    trailFoot: {
      x: trailAnkle.x + trail * 0.02,
      y: trailAnkle.y + 0.015,
      z: through * 0.05,
    },
  };

  const out = {} as Record<BodyId, Joint3D>;
  for (const part of BODY_PARTS) {
    const p = pts[part.id];
    out[part.id] = j(part.id, p.x, p.y, p.z);
  }
  return out;
}

export function poseToFrame(
  t: number,
  joints: Record<BodyId, Joint3D>,
): SkeletonFrame {
  const mapped: Record<string, Joint3D> = {};
  for (const [id, joint] of Object.entries(joints)) mapped[id] = joint;
  mapped.lShoulder = joints.leadShoulder;
  mapped.rShoulder = joints.trailShoulder;
  mapped.lElbow = joints.leadElbow;
  mapped.rElbow = joints.trailElbow;
  mapped.lWrist = joints.leadWrist;
  mapped.rWrist = joints.trailWrist;
  mapped.lHip = joints.leadHip;
  mapped.rHip = joints.trailHip;
  mapped.lKnee = joints.leadKnee;
  mapped.rKnee = joints.trailKnee;
  mapped.lAnkle = joints.leadAnkle;
  mapped.rAnkle = joints.trailAnkle;
  return { t, joints: mapped };
}

export function framesForStyle(
  style: PlayerStyle,
  handedness: Handedness,
  samples?: MotionSample[],
): SkeletonFrame[] {
  return FINE_PHASES.map((phase, i) => {
    const motion = samples?.[Math.min(i, (samples?.length ?? 1) - 1)];
    return poseToFrame(
      phase.t,
      buildPose({ style, phaseT: phase.t, handedness, motion }),
    );
  });
}

export function userFramesFromMotion(
  samples: MotionSample[],
  handedness: Handedness,
): SkeletonFrame[] {
  if (!samples.length) return framesForStyle(AMATEUR_STYLE, handedness);
  return FINE_PHASES.map((phase) => {
    const idx = Math.min(
      samples.length - 1,
      Math.round(phase.t * (samples.length - 1)),
    );
    return poseToFrame(
      samples[idx]?.t ?? phase.t,
      buildPose({
        style: AMATEUR_STYLE,
        phaseT: phase.t,
        handedness,
        motion: samples[idx],
      }),
    );
  });
}

export type BodyDelta = {
  id: BodyId;
  label: string;
  group: string;
  dist: number;
  dx: number;
  dy: number;
  severity: "ok" | "watch" | "fix";
  note: string;
};

export function comparePoses(
  user: Record<BodyId, Joint3D>,
  pro: Record<BodyId, Joint3D>,
): BodyDelta[] {
  return BODY_PARTS.map((part) => {
    const a = user[part.id];
    const b = pro[part.id];
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    const dist = Math.hypot(dx, dy, a.z - b.z);
    const severity: BodyDelta["severity"] =
      dist < 0.035 ? "ok" : dist < 0.07 ? "watch" : "fix";
    const dir =
      Math.abs(dx) > Math.abs(dy)
        ? dx > 0
          ? "too far toward the lead side"
          : "too far toward the trail side"
        : dy > 0
          ? "too low"
          : "too high";
    return {
      id: part.id,
      label: part.label,
      group: part.group,
      dist,
      dx,
      dy,
      severity,
      note: `${part.label} is ${dir} versus the player (${(dist * 100).toFixed(0)}).`,
    };
  }).sort((a, b) => b.dist - a.dist);
}

export function interpolateJoints(
  frames: SkeletonFrame[],
  phaseIndex: number,
): Record<string, Joint3D> {
  if (!frames.length) return {};
  const i = clamp(Math.round(phaseIndex), 0, frames.length - 1);
  return frames[i].joints;
}

export function jointsAsBody(
  joints: Record<string, Joint3D>,
): Record<BodyId, Joint3D> | null {
  if (!joints.leadShoulder && !joints.lShoulder) return null;
  const pick = (id: BodyId, alias?: string) =>
    joints[id] ?? (alias ? joints[alias] : undefined);
  const out = {} as Record<BodyId, Joint3D>;
  for (const part of BODY_PARTS) {
    const hit = pick(part.id);
    if (!hit) return null;
    out[part.id] = hit;
  }
  return out;
}
