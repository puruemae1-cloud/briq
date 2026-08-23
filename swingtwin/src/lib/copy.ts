import type { MetricKey, ProProfile } from "./types";

type Copy = { summary: string; drill: string; feel: string };

const COPY: Record<MetricKey, { low: Copy; high: Copy }> = {
  shoulderTurn: {
    low: {
      summary: "Your shoulder turn is shorter than the model, so speed is coming from the hands.",
      drill: "Alignment stick across the shoulders. Turn to 90° in a mirror, 10 slow reps.",
      feel: "Lead shoulder under the chin. Do not lift the arms.",
    },
    high: {
      summary: "You are over-rotating and the head is likely swaying off the ball.",
      drill: "Chair outside the trail hip. Turn the shoulders without bumping it.",
      feel: "Keep pressure in the trail inner thigh.",
    },
  },
  hipTurn: {
    low: {
      summary: "Hips are quiet while the chest turns, so the arms tend to come over the top.",
      drill: "Club across the belt. Rotate the pelvis 45° each way, 12 reps.",
      feel: "Belt buckle moves first; chest waits.",
    },
    high: {
      summary: "Hips are opening too soon — early extension and a slice often follow.",
      drill: "Pause at the top, bump the lead hip 10 cm toward the target, stop.",
      feel: "Shift first. Turn second.",
    },
  },
  xFactor: {
    low: {
      summary: "Shoulders and hips turn together. There is no coil, so distance and face control drop.",
      drill: "Feet quiet, hips small, shoulders more — slow-mo separation, 8 reps.",
      feel: "Hold the stretch in the trail side for one second at the top.",
    },
    high: {
      summary: "Too much separation. Backs up and timing usually go together.",
      drill: "Half swings at a 3:1 tempo so hips and shoulders unwind in order.",
      feel: "Let the lower body unwind the coil. Do not brace against it.",
    },
  },
  spineTilt: {
    low: {
      summary: "The spine stands up on the way down. Thin, slice and fat shots share this.",
      drill: "Chair behind the glutes. Keep pushing it away through the half swing, 15 balls.",
      feel: "Head stays behind the ball; hips stay back.",
    },
    high: {
      summary: "You are bent over too far, so the flight is low and the face wants to close.",
      drill: "Keep a fist of space between chin and chest through a pump drill.",
      feel: "Cover the ball; do not crush down on it.",
    },
  },
  headStability: {
    low: {
      summary: "The head is moving more than the tour clip. That is usually the biggest visible gap.",
      drill: "Stick in the ground behind the ball. Keep the gap to your head through slow-mo swings.",
      feel: "Nose stays behind the ball for longer.",
    },
    high: {
      summary: "Head is quiet — good. Unlock the chin slightly so the chest can still turn.",
      drill: "Finish with the chin sitting on the lead shoulder, 10 swings.",
      feel: "Stable axis, not a frozen neck.",
    },
  },
  weightShift: {
    low: {
      summary: "Weight is hanging on the trail foot (hang-back). The strike gets thin or the ball fades.",
      drill: "Step-through: plant the lead heel before you swing down, 8 reps.",
      feel: "Lead inner thigh is already firm before impact.",
    },
    high: {
      summary: "You are sliding to the target rather than turning. That is sway.",
      drill: "Towel under the trail instep. Keep it pinned in the backswing.",
      feel: "Move to the lead side, not up onto it.",
    },
  },
  clubPath: {
    low: {
      summary: "Out-to-in path — over the top. On a DTL clip the hands drop outside the head.",
      drill: "Headcover outside the head. Miss it coming from the inside, 12 swings.",
      feel: "Hands drop toward the trail pocket.",
    },
    high: {
      summary: "Too far in-to-out. Push and hook both live here.",
      drill: "Stick on the target line. Keep the head parallel to it in the downswing.",
      feel: "Open the body less; keep the chest on the ball.",
    },
  },
  lag: {
    low: {
      summary: "The wrists are throwing from the top (cast). Tour slow-mo holds the angle into the ball.",
      drill: "9-to-3: trail middle and ring fingers keep the angle until the ball is gone.",
      feel: "Hands ahead, head still trailing.",
    },
    high: {
      summary: "Too much lag — blocked shots to the right. Allow a release.",
      drill: "Let the club wrap the back in the finish, 10 swings.",
      feel: "Trail palm looks at the ground just after impact.",
    },
  },
  posture: {
    low: {
      summary: "Hips thrust toward the ball (early extension). Two-camera 3D shows this immediately.",
      drill: "Stand a hand off a wall. Keep the glutes on the wall through half swings, 15 reps.",
      feel: "Belt points down-forward, not at the target.",
    },
    high: {
      summary: "You are sitting too deep, so rotation stalls. Soften the knee flex a little.",
      drill: "Stand 5° taller at address and keep that height.",
      feel: "Tilt and turn. Do not squat.",
    },
  },
  tempo: {
    low: {
      summary: "The downswing is rushed. Tour clips sit near 3:1 backswing to downswing.",
      drill: "Count 1-2-3 / 1. Stick swings, 20 reps.",
      feel: "Do not hurry the top. Start the lower body first.",
    },
    high: {
      summary: "Tempo is slow enough that the change of direction loses speed. Sharpen the transition only.",
      drill: "Short backswing, gentle acceleration through 9-to-3.",
      feel: "Slow back, smooth speed — not a lunge.",
    },
  },
};

export function gapCopy(key: MetricKey, user: number, pro: number): Copy {
  return COPY[key][user < pro ? "low" : "high"];
}

export function phaseNote(
  pro: ProProfile,
  phase: keyof ProProfile["phaseCues"],
  userHint: string,
) {
  return `${pro.phaseCues[phase]} ${userHint}`.trim();
}
