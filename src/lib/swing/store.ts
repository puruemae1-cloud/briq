"use client";

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
  activatePro: () => void;
  saveAnalysis: (
    result: AnalysisResult,
    skeleton: SkeletonFrame[],
    thumbs: string[],
  ) => { ok: true } | { ok: false; message: string };
};

export const useSwingStore = create<SwingState>()(
  persist(
    (set, get) => ({
      tier: "trial",
      trialUsed: false,
      lastResult: null,
      lastSkeleton: null,
      lastThumbs: [],
      sessions: [],
      preferredProId: "puregolf-tour",
      handedness: "right",
      setPreferredPro: (id) => set({ preferredProId: id }),
      setHandedness: (h) => set({ handedness: h }),
      activatePro: () => set({ tier: "pro" }),
      saveAnalysis: (result, skeleton, thumbs) => {
        const { tier, trialUsed } = get();
        if (tier === "trial" && trialUsed) {
          return {
            ok: false,
            message:
              "트라이얼은 영상 분석 1회입니다. 유료 회원은 계속 올려 교정 추이를 볼 수 있습니다.",
          };
        }
        const session: SwingSession = {
          id: result.id,
          createdAt: result.createdAt,
          proId: result.proId,
          overall: result.overall,
          coachingFocus: result.coachingFocus,
          trialLimited: result.trialLimited,
          has3d: result.has3d,
          views: result.views,
          note: result.gaps[0]?.summary ?? "",
        };
        set({
          lastResult: result,
          lastSkeleton: skeleton,
          lastThumbs: thumbs.slice(0, 6),
          trialUsed: true,
          sessions: [session, ...get().sessions].slice(0, 40),
        });
        return { ok: true };
      },
    }),
    {
      name: "briq-swing-v1",
      partialize: (s) => ({
        tier: s.tier,
        trialUsed: s.trialUsed,
        lastResult: s.lastResult,
        lastThumbs: s.lastThumbs,
        lastSkeleton: s.lastSkeleton,
        sessions: s.sessions,
        preferredProId: s.preferredProId,
        handedness: s.handedness,
        // skeleton can be large; keep last only in memory after rehydrate skip
      }),
    },
  ),
);

export function todayKey(d = new Date()) {
  return d.toISOString().slice(0, 10);
}
