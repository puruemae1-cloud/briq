export type ReferenceClip = {
  proId: string;
  src: string;
  label: string;
  /** Official source (not scraped from Instagram). */
  sourceName: string;
  sourceUrl: string;
  /** Where fans usually see the same reposted. */
  instagramHandles: string[];
  sourceW?: number;
  sourceH?: number;
  poster?: string;
};

export const REFERENCE_CLIPS: ReferenceClip[] = [
  {
    proId: "rory-mcilroy",
    src: "/reference/rory-mcilroy-dtl.mp4",
    label: "Rory McIlroy — driver DTL (portrait)",
    sourceName: "PGA Tour — Swing Theory",
    sourceUrl:
      "https://www.pgatour.com/video/features/6314012785112/rory-mcilroy-swing-theory-driver-iron-wedge",
    instagramHandles: ["@golf_swings", "@pgatour", "@golfdigest"],
    sourceW: 540,
    sourceH: 720,
    poster: "/reference/rory-mcilroy-dtl.jpg",
  },
];

export function getReferenceClip(proId: string) {
  return REFERENCE_CLIPS.find((c) => c.proId === proId);
}
