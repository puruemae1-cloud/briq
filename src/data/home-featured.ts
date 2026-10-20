/**
 * Products that lead their homepage rail after a manual add / restock / update
 * request, ahead of the rail's normal rule (e.g. watches = CW New Releases).
 *
 * Brand syncs regenerate the catalogues but never touch this file, so an entry
 * survives weekly syncs. It drops off automatically after HOME_FEATURED_DAYS
 * or as soon as the product is sold out.
 */
export type HomeFeaturedEntry = {
  id: string;
  /** ISO time of the manual update; newer entries come first. */
  featuredAt: string;
  note?: string;
};

export const HOME_FEATURED_DAYS = 30;

export const HOME_FEATURED: HomeFeaturedEntry[] = [
  {
    id: "cw-c60-41c3h31t0kk0-b0",
    featuredAt: "2026-10-14T21:50:42Z",
    note: "C60 Trident Lumière black bracelet restock",
  },
  {
    id: "ms-m-s-tour-army-dark-brown",
    featuredAt: "2026-10-20T22:40:03Z",
    note: "Mismo weekend bag",
  },
  {
    id: "ms-aspire-leather-black-black",
    featuredAt: "2026-10-20T22:40:02Z",
    note: "Mismo briefcase",
  },
  {
    id: "ms-m-s-mega-tote-tall-army-canvas-tote-bag-for-men-danish-design",
    featuredAt: "2026-10-20T22:40:01Z",
    note: "Mismo tote",
  },
  {
    id: "ms-backpack-into-the-deep-black",
    featuredAt: "2026-10-20T22:40:00Z",
    note: "Mismo backpack",
  },
];
