import { enabledStores, storeById, storeFromUrl, isAllowedProductUrl } from "./stores";
import type { StoreBanner } from "./stores";

export function isHttpUrl(raw: string) {
  try {
    const u = new URL(raw.trim());
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

export function searchUrlForStore(storeId: string, query: string) {
  const q = encodeURIComponent(query.trim());
  switch (storeId) {
    case "asos":
      return `https://www.asos.com/search/?q=${q}`;
    case "zalando":
      return `https://www.zalando.co.uk/catalog/?q=${q}`;
    case "next":
      return `https://www.next.co.uk/search?w=${q}`;
    case "very":
      return `https://www.very.co.uk/search?q=${q}`;
    case "flannels":
      return `https://www.flannels.com/search?q=${q}`;
    case "endclothing":
      return `https://www.endclothing.com/gb/catalogsearch/result/?q=${q}`;
    case "boohoo":
      return `https://www.boohoo.com/search?q=${q}`;
    case "selfridges":
      return `https://www.selfridges.com/GB/en/search/?query=${q}`;
    case "harrods":
      return `https://www.harrods.com/en-gb/search?q=${q}`;
    case "netaporter":
      return `https://www.net-a-porter.com/en-gb/shop/search?q=${q}`;
    default:
      return `https://www.asos.com/search/?q=${q}`;
  }
}

export function isStoreSearchUrl(url: string) {
  try {
    const path = new URL(url).pathname.toLowerCase();
    return (
      path.includes("/search") ||
      path.includes("/catalogsearch/") ||
      path === "/catalog" ||
      path.endsWith("/catalog/")
    );
  } catch {
    return false;
  }
}

function cleanQuery(raw: string) {
  return raw
    .trim()
    .replace(/^["'“”]+|["'“”]+$/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function cartLinkLabel(
  url: string,
  storeName: string,
  source?: "url" | "search",
) {
  if (source === "search" || (!source && isStoreSearchUrl(url))) {
    return `${storeName}에서 검색`;
  }
  return "원본 페이지";
}

export type ResolvedProduct = {
  kind: "url" | "search";
  url: string;
  title: string;
  store: StoreBanner;
};

export function resolveProductInput(raw: string, storeId = "asos"): ResolvedProduct {
  const text = cleanQuery(raw);
  if (!text) {
    throw new Error("상품 이름 또는 링크를 넣어 주세요.");
  }
  if (isHttpUrl(text)) {
    if (!isAllowedProductUrl(text)) {
      throw new Error("목록에 있는 영국 스토어 링크만 담을 수 있습니다.");
    }
    return { kind: "url", url: text, title: "", store: storeFromUrl(text)! };
  }
  if (text.length < 2) {
    throw new Error("상품 이름이 너무 짧습니다.");
  }
  const store = storeById(storeId) ?? storeById("asos") ?? enabledStores()[0];
  return {
    kind: "search",
    url: searchUrlForStore(store.id, text),
    title: text,
    store,
  };
}
