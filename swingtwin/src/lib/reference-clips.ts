export type ReferenceClip = {
  proId: string;
  src: string;
  label: string;
  /** Official source (not scraped from Instagram). */
  sourceName: string;
  sourceUrl: string;
  /** Where fans usually see the same FO slow-mo reposted. */
  instagramHandles: string[];
};

export const REFERENCE_CLIPS: ReferenceClip[] = [
  {
    proId: "rory-mcilroy",
    src: "/reference/rory-mcilroy-faceon.mp4",
    label: "Rory McIlroy — slow motion (face-on)",
    sourceName: "PGA Tour",
    sourceUrl:
      "https://www.pgatour.com/video/competition/6083133193001/rory-mcilroys-powerful-golf-swing-in-slow-motion-at-wells-fargo",
    instagramHandles: ["@golf_swings", "@pgatour", "@golfdigest"],
  },
];

export function getReferenceClip(proId: string) {
  return REFERENCE_CLIPS.find((c) => c.proId === proId);
}
