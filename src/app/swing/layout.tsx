import type { Metadata } from "next";
import { SwingShell } from "@/components/swing/SwingShell";
import "./swing.css";

export const metadata: Metadata = {
  title: "Briq Swing | 스윙 영상 프로 비교 코칭",
  description:
    "스윙 동영상을 올리면 원하는 PGA 선수와 다른 점을 분석합니다. 앞·뒤 영상은 3D로, 트라이얼은 요약, 유료는 데일리 코칭과 교정 자료를 배포합니다.",
};

export default function SwingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <SwingShell>{children}</SwingShell>;
}
