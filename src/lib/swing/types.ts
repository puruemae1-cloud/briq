export type SwingView = "faceOn" | "downTheLine";

export type Handedness = "right" | "left";

export type MembershipTier = "trial" | "pro";

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

export const PHASE_LABEL_KO: Record<SwingPhase, string> = {
  address: "어드레스",
  takeaway: "테이크어웨이",
  top: "백스윙 탑",
  transition: "전환",
  impact: "임팩트",
  finish: "피니시",
};

/** 0–100 스케일의 스윙 메트릭. 프로 템플릿과 같은 축으로 비교한다. */
export type SwingMetrics = {
  /** 어깨 회전 (클수록 더 크게 감음) */
  shoulderTurn: number;
  /** 골반 회전 */
  hipTurn: number;
  /** 어깨-골반 분리 (X-Factor) */
  xFactor: number;
  /** 척추 각도 유지 */
  spineTilt: number;
  /** 머리 안정 (높을수록 흔들림 적음) */
  headStability: number;
  /** 체중 이동 — 리드 쪽으로 */
  weightShift: number;
  /** 다운스윙 궤도가 인사이드-아웃에 가까운 정도 */
  clubPath: number;
  /** 캐스팅/얼리 릴리스가 적을수록 높음 */
  lag: number;
  /** 얼리 익스텐션이 적을수록 높음 */
  posture: number;
  /** 템포 (백스윙:다운스윙 비율이 3:1에 가까울수록 높음) */
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

export const METRIC_LABEL_KO: Record<MetricKey, string> = {
  shoulderTurn: "어깨 회전",
  hipTurn: "골반 회전",
  xFactor: "X-팩터",
  spineTilt: "척추 각도",
  headStability: "머리 안정",
  weightShift: "체중 이동",
  clubPath: "클럽 패스",
  lag: "래그 / 릴리스",
  posture: "자세 유지",
  tempo: "템포",
};

export type PhaseMetrics = Record<SwingPhase, SwingMetrics>;

export type Joint3D = {
  id: string;
  x: number;
  y: number;
  z: number;
};

export type SkeletonFrame = {
  t: number;
  joints: Record<string, Joint3D>;
};

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
  /** 미리보기용 프레임 (data URL, 소수만 보관) */
  thumbs: string[];
  skeleton: SkeletonFrame[];
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

export type AnalysisResult = {
  id: string;
  createdAt: string;
  proId: string;
  handedness: Handedness;
  views: SwingView[];
  has3d: boolean;
  overall: number;
  gaps: MetricGap[];
  phaseNotes: { phase: SwingPhase; note: string }[];
  userMetrics: SwingMetrics;
  proMetrics: SwingMetrics;
  trialLimited: boolean;
  coachingFocus: MetricKey;
};

export type SwingSession = {
  id: string;
  createdAt: string;
  proId: string;
  overall: number;
  coachingFocus: MetricKey;
  trialLimited: boolean;
  has3d: boolean;
  views: SwingView[];
  note: string;
};

export type DailyPlan = {
  date: string;
  dayIndex: number;
  title: string;
  focus: MetricKey;
  why: string;
  drills: {
    name: string;
    sets: string;
    how: string;
    feel: string;
  }[];
  checkpoint: string;
};

export type ProSourceClip = {
  id: string;
  title: string;
  angle: "face-on" | "down-the-line" | "both";
  learned: string;
};

export type ProProfile = {
  id: string;
  name: string;
  nameKo: string;
  tour: "PGA" | "LPGA" | "Archive";
  role: string;
  signature: string;
  whyMatch: string;
  instagram?: string;
  metrics: SwingMetrics;
  phaseCues: Record<SwingPhase, string>;
  sources: ProSourceClip[];
};
