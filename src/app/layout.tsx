import type { Metadata, Viewport } from "next";
import { Fraunces, Nanum_Myeongjo, Outfit } from "next/font/google";
import { NaverWcsScript } from "@/components/NaverWcsScript";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { getCartCount } from "@/lib/cart-server";
import "./globals.css";

const display = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const classic = Nanum_Myeongjo({
  variable: "--font-classic",
  subsets: ["latin"],
  weight: ["400", "700", "800"],
});

const body = Outfit({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: {
    default: "Briq — British Boutique",
    template: "%s · Briq",
  },
  description:
    "Briq (브릭) — British + Boutique / Unique. 스포츠, 패션의류, 가방, 악세서리를 큐레이션한 셀렉트 숍.",
  applicationName: "Briq",
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
    title: "Briq",
    statusBarStyle: "black-translucent",
  },
};

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

  return (
    <html lang="ko">
      <head>
        <link
          rel="stylesheet"
          as="style"
          crossOrigin="anonymous"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"
        />
      </head>
      <body
        className={`${display.variable} ${classic.variable} ${body.variable} antialiased`}
      >
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
