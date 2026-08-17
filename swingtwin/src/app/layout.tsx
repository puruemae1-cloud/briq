import type { Metadata, Viewport } from "next";
import { Shell } from "@/components/Shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "TwinSwing — match your swing to the tour player you want",
  description:
    "UK golf app. Upload your swing and the PGA Tour clip you want to copy. Side-by-side compare, 3D from two cameras, daily drills for subscribers.",
  applicationName: "TwinSwing",
  appleWebApp: { capable: true, title: "TwinSwing", statusBarStyle: "black-translucent" },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#07140f",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-GB">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap"
        />
      </head>
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
