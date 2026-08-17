import type { ProProfile, SwingMetrics } from "./types";

/**
 * Tour models used when a subscriber has not uploaded their own
 * reference clip. Patterns follow public slow-motion face-on / DTL
 * archives such as https://www.instagram.com/purego1f
 *
 * We do not scrape Instagram. Subscribers should upload the exact
 * player clip they want to copy (saved from IG, Tour footage, etc.).
 */
const tourBlend: SwingMetrics = {
  shoulderTurn: 88,
  hipTurn: 48,
  xFactor: 42,
  spineTilt: 86,
  headStability: 90,
  weightShift: 84,
  clubPath: 82,
  lag: 86,
  posture: 88,
  tempo: 85,
};

export const PROS: ProProfile[] = [
  {
    id: "custom-clip",
    name: "My tour clip",
    tour: "Model",
    role: "Whatever player clip you upload",
    signature:
      "Your reference video is the model. We compare motion, tempo and posture against that clip — not a generic average.",
    whyMatch: "Use this when you have a specific slow-mo of the player you want to look like.",
    metrics: tourBlend,
    phaseCues: {
      address: "Match their ball position and knee flex before anything else.",
      takeaway: "Club, hands and chest move together; the head stays quiet.",
      top: "Width in the lead arm, less hip turn than shoulders.",
      transition: "Lower body starts; the hands do not throw the club.",
      impact: "Handle ahead of the ball, pelvis open, chest still covering.",
      finish: "Belt buckle to target, weight on the lead heel, spine not flipped.",
    },
  },
  {
    id: "puregolf-tour",
    name: "Tour blend",
    tour: "Model",
    role: "Common lines from FO + DTL slow-mo archives",
    signature:
      "Quiet head, width at the top, handle forward at impact. Distilled from public tour slow-mo pairs.",
    whyMatch: "When you want tour standards rather than one player’s quirks.",
    instagram: "https://www.instagram.com/purego1f",
    metrics: tourBlend,
    phaseCues: {
      address: "Ball under the lead ear, body square rather than pre-opened.",
      takeaway: "Low and wide. The head must not beat the hands inside.",
      top: "Lead arm stays long; hips trail the shoulders.",
      transition: "Pressure to the lead side before the arms drop.",
      impact: "Handle forward, hips open, chest still looking at the ball.",
      finish: "Full rotation, lead-side balance, spine angle held.",
    },
  },
  {
    id: "rory-mcilroy",
    name: "Rory McIlroy",
    tour: "PGA Tour",
    country: "Northern Ireland",
    role: "Wide arc, aggressive hip clearance",
    signature:
      "Wide stance, huge shoulder turn, hips clear early, slight bow in the lead wrist.",
    whyMatch: "If you want speed and a big arc.",
    metrics: {
      shoulderTurn: 94,
      hipTurn: 52,
      xFactor: 46,
      spineTilt: 84,
      headStability: 86,
      weightShift: 90,
      clubPath: 80,
      lag: 88,
      posture: 82,
      tempo: 78,
    },
    phaseCues: {
      address: "Wide stance, trail foot slightly open, pressure gathered.",
      takeaway: "Head stays low and long; hands do not roll inside early.",
      top: "Shoulders under the chin; lead arm long.",
      transition: "Lead hip clears hard toward the target.",
      impact: "Hips already open, handle ahead, trail heel up.",
      finish: "High finish, all the weight on the lead foot.",
    },
  },
  {
    id: "scottie-scheffler",
    name: "Scottie Scheffler",
    tour: "PGA Tour",
    country: "USA",
    role: "Athletic footwork, deep left-side shift",
    signature:
      "The feet stay alive. On the way down the body drives left while the face stays square.",
    whyMatch: "If you time the swing with the ground more than with a textbook pose.",
    metrics: {
      shoulderTurn: 86,
      hipTurn: 50,
      xFactor: 40,
      spineTilt: 80,
      headStability: 78,
      weightShift: 92,
      clubPath: 84,
      lag: 84,
      posture: 76,
      tempo: 80,
    },
    phaseCues: {
      address: "Trail heel is light; the set-up is not static.",
      takeaway: "The club is not shut early.",
      top: "The lower body is already easing toward the target.",
      transition: "Feet first, hands second. The angles stay.",
      impact: "Deep into the lead side, face square.",
      finish: "Trail foot almost dragged; balance over the lead side.",
    },
  },
  {
    id: "collin-morikawa",
    name: "Collin Morikawa",
    tour: "PGA Tour",
    country: "USA",
    role: "Compact irons, quiet body",
    signature: "Shorter backswing, quiet lower body, high hands through impact.",
    whyMatch: "If iron control and face control matter more than raw speed.",
    metrics: {
      shoulderTurn: 78,
      hipTurn: 42,
      xFactor: 38,
      spineTilt: 90,
      headStability: 94,
      weightShift: 80,
      clubPath: 88,
      lag: 90,
      posture: 92,
      tempo: 90,
    },
    phaseCues: {
      address: "Narrow, tidy stance. Hands slightly ahead.",
      takeaway: "One-piece; the head does not hinge early.",
      top: "Short. Lead arm does not collapse.",
      transition: "Quiet lower body; no cast.",
      impact: "Clear handle-forward, chest still over the ball.",
      finish: "Controlled, lower finish.",
    },
  },
  {
    id: "xander-schauffele",
    name: "Xander Schauffele",
    tour: "PGA Tour",
    country: "USA",
    role: "Stacked impact, textbook sequence",
    signature:
      "Full backswing, then hips–torso–arms in order, body stacked on the ball.",
    whyMatch: "If you want a clean tour pattern without a signature quirk.",
    metrics: {
      shoulderTurn: 90,
      hipTurn: 46,
      xFactor: 44,
      spineTilt: 88,
      headStability: 92,
      weightShift: 86,
      clubPath: 86,
      lag: 87,
      posture: 90,
      tempo: 88,
    },
    phaseCues: {
      address: "Neutral grip, square stance.",
      takeaway: "The club does not drop inside too soon.",
      top: "Full shoulder turn, head behind the ball.",
      transition: "Hips, then torso, then arms.",
      impact: "Stacked — pelvis and ribs over the ball.",
      finish: "Balanced high finish.",
    },
  },
  {
    id: "jon-rahm",
    name: "Jon Rahm",
    tour: "PGA Tour",
    country: "Spain",
    role: "Strong grip, short backswing, fast transition",
    signature: "Short swing, strong grip, lower body leads hard.",
    whyMatch: "If a long backswing feels awkward and you want speed from a short move.",
    metrics: {
      shoulderTurn: 72,
      hipTurn: 44,
      xFactor: 36,
      spineTilt: 82,
      headStability: 88,
      weightShift: 88,
      clubPath: 78,
      lag: 82,
      posture: 84,
      tempo: 74,
    },
    phaseCues: {
      address: "Strong grip; do not play the ball too far back.",
      takeaway: "Early wrist hinge, compact arc.",
      top: "Short — already ready to come down.",
      transition: "Lower body explodes; hands follow.",
      impact: "Strong cover, face square to a touch closed.",
      finish: "Full rotation, balance left.",
    },
  },
  {
    id: "nelly-korda",
    name: "Nelly Korda",
    tour: "LPGA",
    country: "USA",
    role: "Even tempo, long square face",
    signature: "Unhurried tempo, quiet lower-body lead, face stays square through the ball.",
    whyMatch: "If you want timing and face control more than force.",
    metrics: {
      shoulderTurn: 84,
      hipTurn: 46,
      xFactor: 40,
      spineTilt: 88,
      headStability: 93,
      weightShift: 83,
      clubPath: 90,
      lag: 85,
      posture: 90,
      tempo: 94,
    },
    phaseCues: {
      address: "Soft knee flex, light grip pressure.",
      takeaway: "Smooth one-piece.",
      top: "Width held; no rush.",
      transition: "A pause you can feel.",
      impact: "The face stays on the ball for longer.",
      finish: "Hold the high finish.",
    },
  },
];

export function getPro(id: string): ProProfile | undefined {
  return PROS.find((p) => p.id === id);
}

export function defaultProId() {
  return "custom-clip";
}
