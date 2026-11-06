import { isAllowedProductUrl, storeFromUrl } from "./stores";
import { extractGbpFromHtml, extractImageFromHtml, extractTitleFromHtml } from "./gbp";

export type UrlPreview = {
  url: string;
  title: string;
  image: string;
  gbpPrice: number | null;
  storeId: string;
  storeName: string;
};

export async function previewProductUrl(raw: string): Promise<UrlPreview> {
  const url = raw.trim();
  if (!isAllowedProductUrl(url)) {
    throw new Error("목록에 있는 영국 스토어 상품 링크만 담을 수 있습니다.");
  }
  const store = storeFromUrl(url)!;
  const titleFallback = store.nameEn;
  const empty: UrlPreview = {
    url,
    title: titleFallback,
    image: "",
    gbpPrice: null,
    storeId: store.id,
    storeName: store.nameEn,
  };
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 4500);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      redirect: "follow",
      headers: {
        "user-agent":
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        accept: "text/html,application/xhtml+xml",
      },
    });
    const html = (await res.text()).slice(0, 280_000);
    return {
      url,
      title: extractTitleFromHtml(html, titleFallback),
      image: extractImageFromHtml(html),
      gbpPrice: extractGbpFromHtml(html),
      storeId: store.id,
      storeName: store.nameEn,
    };
  } catch {
    return empty;
  } finally {
    clearTimeout(timer);
  }
}
