export type BodyId =
  | "head"
  | "forehead"
  | "chin"
  | "neck"
  | "leadShoulder"
  | "trailShoulder"
  | "leadUpperArm"
  | "trailUpperArm"
  | "leadElbow"
  | "trailElbow"
  | "leadForearm"
  | "trailForearm"
  | "leadWrist"
  | "trailWrist"
  | "leadHand"
  | "trailHand"
  | "chest"
  | "leadHip"
  | "trailHip"
  | "pelvis"
  | "leadThigh"
  | "trailThigh"
  | "leadKnee"
  | "trailKnee"
  | "leadShin"
  | "trailShin"
  | "leadAnkle"
  | "trailAnkle"
  | "leadFoot"
  | "trailFoot";

export const BODY_PARTS: { id: BodyId; label: string; group: string }[] = [
  { id: "head", label: "Head", group: "Head" },
  { id: "forehead", label: "Forehead", group: "Head" },
  { id: "chin", label: "Chin", group: "Head" },
  { id: "neck", label: "Neck", group: "Head" },
  { id: "leadShoulder", label: "Lead shoulder", group: "Torso" },
  { id: "trailShoulder", label: "Trail shoulder", group: "Torso" },
  { id: "chest", label: "Chest", group: "Torso" },
  { id: "leadUpperArm", label: "Lead upper arm", group: "Arms" },
  { id: "trailUpperArm", label: "Trail upper arm", group: "Arms" },
  { id: "leadElbow", label: "Lead elbow", group: "Arms" },
  { id: "trailElbow", label: "Trail elbow", group: "Arms" },
  { id: "leadForearm", label: "Lead forearm", group: "Arms" },
  { id: "trailForearm", label: "Trail forearm", group: "Arms" },
  { id: "leadWrist", label: "Lead wrist", group: "Hands" },
  { id: "trailWrist", label: "Trail wrist", group: "Hands" },
  { id: "leadHand", label: "Lead hand", group: "Hands" },
  { id: "trailHand", label: "Trail hand", group: "Hands" },
  { id: "pelvis", label: "Pelvis", group: "Hips" },
  { id: "leadHip", label: "Lead hip", group: "Hips" },
  { id: "trailHip", label: "Trail hip", group: "Hips" },
  { id: "leadThigh", label: "Lead thigh", group: "Legs" },
  { id: "trailThigh", label: "Trail thigh", group: "Legs" },
  { id: "leadKnee", label: "Lead knee", group: "Legs" },
  { id: "trailKnee", label: "Trail knee", group: "Legs" },
  { id: "leadShin", label: "Lead shin", group: "Legs" },
  { id: "trailShin", label: "Trail shin", group: "Legs" },
  { id: "leadAnkle", label: "Lead ankle", group: "Feet" },
  { id: "trailAnkle", label: "Trail ankle", group: "Feet" },
  { id: "leadFoot", label: "Lead foot", group: "Feet" },
  { id: "trailFoot", label: "Trail foot", group: "Feet" },
];

export const BODY_BONES: [BodyId, BodyId][] = [
  ["forehead", "head"],
  ["head", "chin"],
  ["head", "neck"],
  ["neck", "leadShoulder"],
  ["neck", "trailShoulder"],
  ["neck", "chest"],
  ["leadShoulder", "leadUpperArm"],
  ["leadUpperArm", "leadElbow"],
  ["leadElbow", "leadForearm"],
  ["leadForearm", "leadWrist"],
  ["leadWrist", "leadHand"],
  ["trailShoulder", "trailUpperArm"],
  ["trailUpperArm", "trailElbow"],
  ["trailElbow", "trailForearm"],
  ["trailForearm", "trailWrist"],
  ["trailWrist", "trailHand"],
  ["chest", "pelvis"],
  ["leadShoulder", "leadHip"],
  ["trailShoulder", "trailHip"],
  ["leadHip", "pelvis"],
  ["trailHip", "pelvis"],
  ["leadHip", "leadThigh"],
  ["leadThigh", "leadKnee"],
  ["leadKnee", "leadShin"],
  ["leadShin", "leadAnkle"],
  ["leadAnkle", "leadFoot"],
  ["trailHip", "trailThigh"],
  ["trailThigh", "trailKnee"],
  ["trailKnee", "trailShin"],
  ["trailShin", "trailAnkle"],
  ["trailAnkle", "trailFoot"],
];

export type FinePhase = {
  id: string;
  n: number;
  code: string;
  label: string;
  t: number;
  cue: string;
};

/** 30 synced checkpoints through a full swing (P-system, subdivided). */
export const FINE_PHASES: FinePhase[] = [
  { id: "p1-setup", n: 1, code: "P1", label: "Setup", t: 0.00, cue: "Stance, ball, spine." },
  { id: "p1-ball", n: 2, code: "P1", label: "Ball position", t: 0.02, cue: "Lead heel vs ball." },
  { id: "p1-trigger", n: 3, code: "P1.5", label: "Trigger", t: 0.05, cue: "Pressure starts." },
  { id: "p2-takeaway", n: 4, code: "P2", label: "Takeaway", t: 0.09, cue: "Club, hands, chest." },
  { id: "p2-shaft", n: 5, code: "P2", label: "Shaft parallel", t: 0.14, cue: "Shaft to target line." },
  { id: "p2-hands", n: 6, code: "P2.5", label: "Hands past thigh", t: 0.18, cue: "Hands inside trail thigh." },
  { id: "p3-arm", n: 7, code: "P3", label: "Lead arm parallel", t: 0.24, cue: "Width, no early roll." },
  { id: "p3-wrist", n: 8, code: "P3.5", label: "Wrist set", t: 0.30, cue: "Trail wrist hinges." },
  { id: "p4-late", n: 9, code: "P4", label: "Late backswing", t: 0.36, cue: "Shoulders finish the turn." },
  { id: "p4-top", n: 10, code: "P4", label: "Top", t: 0.42, cue: "Lead arm long, hips less." },
  { id: "p4-trans", n: 11, code: "P4.2", label: "Transition", t: 0.46, cue: "Lower body first." },
  { id: "p4-first", n: 12, code: "P4.5", label: "First move down", t: 0.50, cue: "Pressure to lead side." },
  { id: "p5-slot", n: 13, code: "P5", label: "Slot", t: 0.54, cue: "Trail elbow in front of hip." },
  { id: "p5-shallow", n: 14, code: "P5", label: "Shaft shallow", t: 0.58, cue: "Shaft lays down." },
  { id: "p5-arm-down", n: 15, code: "P5.5", label: "Lead arm down", t: 0.62, cue: "Lead arm still long." },
  { id: "p6-delivery", n: 16, code: "P6", label: "Delivery", t: 0.66, cue: "Hands in, club behind." },
  { id: "p6-pre", n: 17, code: "P6.5", label: "Pre-impact", t: 0.70, cue: "Handle ahead." },
  { id: "p7-impact", n: 18, code: "P7", label: "Impact", t: 0.74, cue: "Hips open, chest covering." },
  { id: "p7-ext", n: 19, code: "P7.2", label: "Extension", t: 0.78, cue: "Arms extend down the line." },
  { id: "p7-rel", n: 20, code: "P7.5", label: "Release", t: 0.81, cue: "Trail palm down." },
  { id: "p8-shaft", n: 21, code: "P8", label: "Shaft parallel through", t: 0.84, cue: "Club left of hands." },
  { id: "p8-hands", n: 22, code: "P8.5", label: "Hands high", t: 0.87, cue: "Hands over lead shoulder." },
  { id: "p9-follow", n: 23, code: "P9", label: "Follow-through", t: 0.90, cue: "Chest to target." },
  { id: "p9-rot", n: 24, code: "P9.5", label: "Full rotation", t: 0.93, cue: "Belt buckle faces target." },
  { id: "p10-finish", n: 25, code: "P10", label: "Finish", t: 0.95, cue: "Weight on lead heel." },
  { id: "p10-hold", n: 26, code: "P10", label: "Hold", t: 0.97, cue: "Three-second balance." },
  { id: "chk-head", n: 27, code: "CHK", label: "Head check", t: 0.74, cue: "Head still behind the ball at impact." },
  { id: "chk-trail-foot", n: 28, code: "CHK", label: "Trail foot", t: 0.78, cue: "Trail heel can rise." },
  { id: "chk-lead-side", n: 29, code: "CHK", label: "Lead side", t: 0.74, cue: "Lead leg posts." },
  { id: "chk-recoil", n: 30, code: "CHK", label: "Recoil / pose", t: 1.00, cue: "Finish does not fall back." },
];

export type PlayerStyle = {
  headQuiet: number;
  stanceWidth: number;
  shoulderTurn: number;
  hipClear: number;
  trailElbowIn: number;
  leadWristBow: number;
  earlyExt: number;
  backswingLen: number;
  tempo: number;
  squat: number;
  handPathIn: number;
  spineTilt: number;
};

export const TOUR_STYLE: PlayerStyle = {
  headQuiet: 0.88,
  stanceWidth: 0.72,
  shoulderTurn: 0.86,
  hipClear: 0.78,
  trailElbowIn: 0.82,
  leadWristBow: 0.55,
  earlyExt: 0.12,
  backswingLen: 0.8,
  tempo: 0.72,
  squat: 0.45,
  handPathIn: 0.7,
  spineTilt: 0.8,
};

export const AMATEUR_STYLE: PlayerStyle = {
  headQuiet: 0.42,
  stanceWidth: 0.62,
  shoulderTurn: 0.58,
  hipClear: 0.4,
  trailElbowIn: 0.38,
  leadWristBow: 0.35,
  earlyExt: 0.62,
  backswingLen: 0.7,
  tempo: 0.38,
  squat: 0.55,
  handPathIn: 0.35,
  spineTilt: 0.48,
};
