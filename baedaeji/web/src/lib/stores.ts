import type { StoreMode } from "./types";

export type StoreBanner = {
  id: string;
  nameKo: string;
  nameEn: string;
  href: string;
  hosts: string[];
  sort: number;
  enabled: boolean;
  mode: StoreMode;
  bg: string;
  fg: string;
  accent: string;
  blurb: string;
};

export const STORES: StoreBanner[] = [
  {
    id: "asos",
    nameKo: "에이소스",
    nameEn: "ASOS",
    href: "https://www.asos.com/",
    hosts: ["asos.com"],
    sort: 1,
    enabled: true,
    mode: "purchase",
    bg: "#111111",
    fg: "#ffffff",
    accent: "#ffffff",
    blurb: "영국 스트리트 · 트렌드",
  },
  {
    id: "zalando",
    nameKo: "잘란도",
    nameEn: "Zalando",
    href: "https://www.zalando.co.uk",
    hosts: ["zalando.co.uk", "zalando.com"],
    sort: 2,
    enabled: true,
    mode: "purchase",
    bg: "#ff6900",
    fg: "#111111",
    accent: "#111111",
    blurb: "유럽 패션 플랫폼",
  },
  {
    id: "next",
    nameKo: "넥스트",
    nameEn: "Next",
    href: "https://www.next.co.uk",
    hosts: ["next.co.uk"],
    sort: 3,
    enabled: true,
    mode: "purchase",
    bg: "#0b1f3a",
    fg: "#f4f0e8",
    accent: "#d4b483",
    blurb: "영국 대표 패밀리 브랜드",
  },
  {
    id: "very",
    nameKo: "베리",
    nameEn: "Very",
    href: "https://www.very.co.uk",
    hosts: ["very.co.uk"],
    sort: 4,
    enabled: true,
    mode: "purchase",
    bg: "#5b2d8e",
    fg: "#ffffff",
    accent: "#e8d5ff",
    blurb: "UK 홈·패션 몰",
  },
  {
    id: "flannels",
    nameKo: "플래널스",
    nameEn: "Flannels",
    href: "https://www.flannels.com",
    hosts: ["flannels.com"],
    sort: 5,
    enabled: true,
    mode: "purchase",
    bg: "#0a0a0a",
    fg: "#f3e6c4",
    accent: "#c4a574",
    blurb: "디자이너 · 스니커즈",
  },
  {
    id: "endclothing",
    nameKo: "엔드 클로딩",
    nameEn: "END.",
    href: "https://www.endclothing.com",
    hosts: ["endclothing.com"],
    sort: 6,
    enabled: true,
    mode: "purchase",
    bg: "#161616",
    fg: "#f5f5f5",
    accent: "#ffffff",
    blurb: "컨템포러리 · 한정판",
  },
  {
    id: "boohoo",
    nameKo: "부후",
    nameEn: "boohoo",
    href: "https://www.boohoo.com",
    hosts: ["boohoo.com"],
    sort: 7,
    enabled: true,
    mode: "purchase",
    bg: "#e11d48",
    fg: "#ffffff",
    accent: "#ffe4e8",
    blurb: "영 패션",
  },
  {
    id: "selfridges",
    nameKo: "셀프리지스",
    nameEn: "Selfridges",
    href: "https://www.selfridges.com",
    hosts: ["selfridges.com"],
    sort: 8,
    enabled: true,
    mode: "purchase",
    bg: "#ffe100",
    fg: "#111111",
    accent: "#111111",
    blurb: "런던 백화점",
  },
  {
    id: "harrods",
    nameKo: "해로즈",
    nameEn: "Harrods",
    href: "https://www.harrods.com",
    hosts: ["harrods.com"],
    sort: 9,
    enabled: true,
    mode: "purchase",
    bg: "#0b3d2e",
    fg: "#e7d7a3",
    accent: "#e7d7a3",
    blurb: "나이츠브리지 백화점",
  },
  {
    id: "netaporter",
    nameKo: "넷어포터",
    nameEn: "NET-A-PORTER",
    href: "https://www.net-a-porter.com",
    hosts: ["net-a-porter.com"],
    sort: 10,
    enabled: true,
    mode: "purchase",
    bg: "#1a1a1a",
    fg: "#f7f4ee",
    accent: "#c4a574",
    blurb: "럭셔리 우먼즈",
  },
];

export function enabledStores() {
  return STORES.filter((s) => s.enabled).sort((a, b) => a.sort - b.sort);
}

export function storeFromUrl(raw: string): StoreBanner | null {
  try {
    const host = new URL(raw).hostname.toLowerCase().replace(/^www\./, "");
    return (
      STORES.find((s) =>
        s.hosts.some((h) => host === h || host.endsWith(`.${h}`)),
      ) ?? null
    );
  } catch {
    return null;
  }
}

export function isAllowedProductUrl(raw: string): boolean {
  try {
    const u = new URL(raw);
    if (u.protocol !== "https:" && u.protocol !== "http:") return false;
    return storeFromUrl(raw) !== null;
  } catch {
    return false;
  }
}
