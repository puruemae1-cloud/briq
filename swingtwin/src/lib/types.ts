export type SwingView = "faceOn" | "downTheLine";
export type Handedness = "right" | "left";
export type MembershipTier = "trial" | "subscriber";

export type SwingPhase =
  | "address"
  | "takeaway"
  | "top"
  | "transition"
  | "impact"
  | "finish";

export const SWING_PHASES: SwingPhase[] = [
  "address",
  "takeaway",
  "top",
  "transition",
  "impact",
  "finish",
];

export const PHASE_LABEL: Record<SwingPhase, string> = {
  address: "Address",
  takeaway: "Takeaway",
  top: "Top",
  transition: "Transition",
  impact: "Impact",
  finish: "Finish",
};

export type SwingMetrics = {
  shoulderTurn: number;
  hipTurn: number;
  xFactor: number;
  spineTilt: number;
  headStability: number;
  weightShift: number;
  clubPath: number;
  lag: number;
  posture: number;
  tempo: number;
};

export const METRIC_KEYS = [
  "shoulderTurn",
  "hipTurn",
  "xFactor",
  "spineTilt",
  "headStability",
  "weightShift",
  "clubPath",
  "lag",
  "posture",
  "tempo",
] as const;

export type MetricKey = (typeof METRIC_KEYS)[number];

export const METRIC_LABEL: Record<MetricKey, string> = {
  shoulderTurn: "Shoulder turn",
  hipTurn: "Hip turn",
  xFactor: "X-factor",
  spineTilt: "Spine angle",
  headStability: "Head stability",
  weightShift: "Weight shift",
  clubPath: "Club path",
  lag: "Lag / release",
  posture: "Posture",
  tempo: "Tempo",
};

export type Joint3D = { id: string; x: number; y: number; z: number };
export type SkeletonFrame = { t: number; joints: Record<string, Joint3D> };

export type MotionSample = {
  t: number;
  energy: number;
  cx: number;
  cy: number;
  height: number;
  width: number;
};

export type ViewCapture = {
  view: SwingView;
  fileName: string;
  duration: number;
  samples: MotionSample[];
  thumbs: string[];
  skeleton: SkeletonFrame[];
  /** Local object URL for side-by-side playback */
  objectUrl?: string;
};

export type MetricGap = {
  key: MetricKey;
  label: string;
  user: number;
  pro: number;
  delta: number;
  severity: "ok" | "watch" | "fix";
  summary: string;
  drill: string;
  feel: string;
};

export type SwingSyncMarkers = {
  /** Arms start up — start of side-by-side playback */
  takeawayT: number;
  topT: number;
  impactT: number;
  endT: number;
};

export type AnalysisResult = {
  id: string;
  createdAt: string;
  proId: string;
  proName: string;
  comparedAgainstClip: boolean;
  handedness: Handedness;
  views: SwingView[];
  has3d: boolean;
  overall: number;
  gaps: MetricGap[];
  phaseNotes: { phase: SwingPhase; note: string }[];
  finePhaseNotes: { n: number; code: string; label: string; cue: string; note: string }[];
  userMetrics: SwingMetrics;
  proMetrics: SwingMetrics;
  trialLimited: boolean;
  coachingFocus: MetricKey;
  userPeakT: number;
  tourPeakT: number;
  userSync: SwingSyncMarkers;
  tourSync: SwingSyncMarkers;
};

export type SwingSession = {
  id: string;
  createdAt: string;
  proId: string;
  proName: string;
  overall: number;
  coachingFocus: MetricKey;
  trialLimited: boolean;
  has3d: boolean;
  comparedAgainstClip: boolean;
  note: string;
};

export type DailyPlan = {
  date: string;
  dayIndex: number;
  title: string;
  focus: MetricKey;
  why: string;
  drills: { name: string; sets: string; how: string; feel: string }[];
  checkpoint: string;
};

export type ProProfile = {
  id: string;
  name: string;
  tour: "PGA Tour" | "LPGA" | "Model";
  country?: string;
  role: string;
  signature: string;
  whyMatch: string;
  instagram?: string;
  sources?: string[];
  style?: import("./anatomy").PlayerStyle;
  metrics: SwingMetrics;
  phaseCues: Record<SwingPhase, string>;
};
