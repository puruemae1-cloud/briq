import type { Metadata } from "next";
import { Libre_Baskerville, Noto_Sans_KR } from "next/font/google";
import { Footer, Header } from "@/components/Header";
import { getCurrentUser } from "@/lib/auth";
import "./globals.css";

const display = Libre_Baskerville({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-display",
});

const body = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-body",
});

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "배대지 — 영국 구매대행",
  description:
    "ASOS, Zalando, Next, Selfridges, Harrods, NET-A-PORTER 등 영국 쇼핑몰 구매·배송 대행",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  return (
    <html lang="ko">
      <body className={`${display.variable} ${body.variable} antialiased`}>
        <Header user={user} />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
