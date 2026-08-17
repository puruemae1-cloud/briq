export type ReferenceClip = {
  proId: string;
  src: string;
  label: string;
  /** Official source (not scraped from Instagram). */
  sourceName: string;
  sourceUrl: string;
  /** Where fans usually see the same reposted. */
  instagramHandles: string[];
};

export const REFERENCE_CLIPS: ReferenceClip[] = [
  {
    proId: "rory-mcilroy",
    src: "/reference/rory-mcilroy-dtl.mp4",
    label: "Rory McIlroy — down the line (normal speed)",
    sourceName: "PGA Tour",
    sourceUrl:
      "https://www.pgatour.com/video/competition/6401330997112/rory-mcilroy-crushes-yard-tee-shot-drives-green-for-birdie-at-the-open",
    instagramHandles: ["@golf_swings", "@pgatour", "@golfdigest"],
  },
];

export function getReferenceClip(proId: string) {
  return REFERENCE_CLIPS.find((c) => c.proId === proId);
}
