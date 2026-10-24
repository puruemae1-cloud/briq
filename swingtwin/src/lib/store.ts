import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  AnalysisResult,
  MembershipTier,
  SkeletonFrame,
  SwingSession,
} from "./types";

type SwingState = {
  tier: MembershipTier;
  trialUsed: boolean;
  lastResult: AnalysisResult | null;
  lastSkeleton: SkeletonFrame[] | null;
  lastThumbs: string[];
  sessions: SwingSession[];
  preferredProId: string;
  handedness: "right" | "left";
  setPreferredPro: (id: string) => void;
  setHandedness: (h: "right" | "left") => void;
  activateSubscriber: () => void;
  saveAnalysis: (
    result: AnalysisResult,
    skeleton: SkeletonFrame[],
    thumbs: string[],
  ) => { ok: true } | { ok: false; message: string };
};

export const useTwinStore = create<SwingState>()(
  persist(
    (set, get) => ({
      tier: "trial",
      trialUsed: false,
      lastResult: null,
      lastSkeleton: null,
      lastThumbs: [],
      sessions: [],
      preferredProId: "rory-mcilroy",
      handedness: "right",
      setPreferredPro: (id) => set({ preferredProId: id }),
      setHandedness: (h) => set({ handedness: h }),
      activateSubscriber: () => set({ tier: "subscriber" }),
      saveAnalysis: (result, skeleton, thumbs) => {
        const session: SwingSession = {
          id: result.id,
          createdAt: result.createdAt,
          proId: result.proId,
          proName: result.proName,
          overall: result.overall,
          coachingFocus: result.coachingFocus,
          trialLimited: result.trialLimited,
          has3d: result.has3d,
          comparedAgainstClip: result.comparedAgainstClip,
          note: result.gaps[0]?.summary ?? "",
        };
        set({
          lastResult: result,
          lastSkeleton: skeleton,
          lastThumbs: thumbs.slice(0, 6),
          sessions: [session, ...get().sessions].slice(0, 40),
        });
        return { ok: true };
      },
    }),
    {
      name: "swingtwin-uk-v1",
      partialize: (s) => ({
        tier: s.tier,
        trialUsed: s.trialUsed,
        lastResult: s.lastResult,
        lastThumbs: s.lastThumbs,
        lastSkeleton: s.lastSkeleton,
        sessions: s.sessions,
        preferredProId: s.preferredProId,
        handedness: s.handedness,
      }),
    },
  ),
);

export function todayKey(d = new Date()) {
  return d.toISOString().slice(0, 10);
}
