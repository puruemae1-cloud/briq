import type { Metadata, Viewport } from "next";
import { Fraunces, Nanum_Myeongjo, Outfit } from "next/font/google";
import { JsonLd } from "@/components/JsonLd";
import { NaverWcsScript } from "@/components/NaverWcsScript";
import { PretendardStylesheet } from "@/components/PretendardStylesheet";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { getCartCount } from "@/lib/cart-server";
import { rootMetadata } from "@/lib/seo-metadata";
import { DEFAULT_DESCRIPTION, SITE_NAME, getSiteUrl } from "@/lib/site";
import "./globals.css";

const display = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

const classic = Nanum_Myeongjo({
  variable: "--font-classic",
  subsets: ["latin"],
  weight: ["400", "700", "800"],
  display: "swap",
});

const body = Outfit({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = rootMetadata;

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cartCount = await getCartCount();
  const site = getSiteUrl();

  const orgLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: SITE_NAME,
    alternateName: ["브릭", "Briq 브릭"],
    url: site,
    logo: `${site}/icon-512.png`,
    description: DEFAULT_DESCRIPTION,
    email: "support@hjstoryltd.com",
    telephone: "+44-7897-535888",
    address: {
      "@type": "PostalAddress",
      streetAddress: "경기도 김포시 고촌읍 은행영사정로23번길 46",
      addressCountry: "KR",
    },
    sameAs: [site],
  };

  const websiteLd = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: `${SITE_NAME} 브릭`,
    url: site,
    description: DEFAULT_DESCRIPTION,
    inLanguage: "ko-KR",
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: `${site}/shop?q={search_term_string}`,
      },
      "query-input": "required name=search_term_string",
    },
  };

  const storeLd = {
    "@context": "https://schema.org",
    "@type": "OnlineStore",
    name: `${SITE_NAME} 브릭`,
    url: site,
    description:
      "영국 명품의류·명품직구·명품구매대행 셀렉트숍. 샤넬·구찌·버버리 등.",
    priceRange: "₩₩₩₩",
    currenciesAccepted: "KRW",
    paymentAccepted: "Naver Pay, Credit Card",
  };

  return (
    <html lang="ko">
      <body
        className={`${display.variable} ${classic.variable} ${body.variable} antialiased`}
      >
        <JsonLd data={[orgLd, websiteLd, storeLd]} />
        <PretendardStylesheet />
        <div id="top" className="shell">
          <SiteHeader cartCount={cartCount} />
          <main className="shell__main">{children}</main>
          <SiteFooter />
        </div>
        <a href="#top" className="back-to-top" aria-label="맨 위로">
          <span aria-hidden="true">↑</span>
        </a>
        <NaverWcsScript />
      </body>
    </html>
  );
}
