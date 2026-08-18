import type { CropRect } from "./swing-framing";

export type ReferenceClip = {
  proId: string;
  src: string;
  label: string;
  /** Official source (not scraped from Instagram). */
  sourceName: string;
  sourceUrl: string;
  /** Where fans usually see the same reposted. */
  instagramHandles: string[];
  /** Pixel crop of the bundled file — skip motion detect (clouds look like swing). */
  displayCrop?: CropRect;
  sourceW?: number;
  sourceH?: number;
};

export const REFERENCE_CLIPS: ReferenceClip[] = [
  {
    proId: "rory-mcilroy",
    src: "/reference/rory-mcilroy-dtl.mp4",
    label: "Rory McIlroy — driver DTL (normal speed)",
    sourceName: "PGA Tour — Swing Theory",
    sourceUrl:
      "https://www.pgatour.com/video/features/6314012785112/rory-mcilroy-swing-theory-driver-iron-wedge",
    instagramHandles: ["@golf_swings", "@pgatour", "@golfdigest", "@JonathanYarwood"],
    sourceW: 1280,
    sourceH: 720,
    // Golfer sits lower-left on the 16:9 Swing Theory plate. Tight 3:4 around body + club.
    displayCrop: { x: 270, y: 240, w: 360, h: 480 },
  },
];

export function getReferenceClip(proId: string) {
  return REFERENCE_CLIPS.find((c) => c.proId === proId);
}
