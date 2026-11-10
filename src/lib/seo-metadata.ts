import type { Metadata } from "next";
import { mediaUrl } from "@/lib/product-image";
import {
  DEFAULT_DESCRIPTION,
  DEFAULT_TITLE,
  SEO_KEYWORDS,
  SITE_NAME,
  getSiteUrl,
} from "@/lib/site";

const site = getSiteUrl();

/** Prefer absolute CDN URL — relative /banners/* 404s on Vercel (media is on product-images). */
const OG_IMAGE_PATH = "/banners/rot-luxury-1.jpg";
export const OG_IMAGE_URL = mediaUrl(OG_IMAGE_PATH) || OG_IMAGE_PATH;

export const DEFAULT_OG_IMAGE = {
  url: OG_IMAGE_URL,
  width: 2400,
  height: 1600,
  alt: "Briq 명품의류 · 명품직구 셀렉션",
} as const;

export const rootMetadata: Metadata = {
  metadataBase: new URL(site),
  title: {
    default: DEFAULT_TITLE,
    // Bare child titles get one brand suffix. Pages that already name Briq
    // must use seoTitle() → { absolute } so Naver never sees "Briq · Briq".
    template: `%s | ${SITE_NAME}`,
  },
  description: DEFAULT_DESCRIPTION,
  applicationName: SITE_NAME,
  keywords: [...SEO_KEYWORDS],
  authors: [{ name: "Briq", url: site }],
  creator: "Briq",
  publisher: "(주)리치몬드인터내셔널 / HJ STORY LIMITED",
  category: "shopping",
  alternates: {
    // Do not set a site-wide canonical here — private/legal pages were
    // inheriting https://www.briq.kr and looking like soft duplicates.
    types: {
      "application/rss+xml": `${site}/feed.xml`,
    },
  },
  openGraph: {
    type: "website",
    locale: "ko_KR",
    url: site,
    siteName: `${SITE_NAME} 브릭`,
    title: DEFAULT_TITLE,
    description: DEFAULT_DESCRIPTION,
    images: [DEFAULT_OG_IMAGE],
  },
  twitter: {
    card: "summary_large_image",
    title: DEFAULT_TITLE,
    description: DEFAULT_DESCRIPTION,
    images: [OG_IMAGE_URL],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  verification: {
    ...(process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION
      ? { google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION }
      : {}),
    other: {
      // Naver Search Advisor ownership for https://www.briq.kr
      "naver-site-verification":
        process.env.NEXT_PUBLIC_NAVER_SITE_VERIFICATION ||
        "f415445cd59da5434295472fba2c82d8dc9c635a",
    },
  },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/apple-icon.png", sizes: "180x180", type: "image/png" }],
  },
  appleWebApp: {
    capable: true,
    title: SITE_NAME,
    statusBarStyle: "black-translucent",
  },
};
