import { isAllowedProductUrl, storeFromUrl } from "./stores";

function meta(html: string, keys: string[]) {
  for (const key of keys) {
    const re = new RegExp(
      `<meta[^>]+(?:property|name)=["']${key}["'][^>]+content=["']([^"']+)["']`,
      "i",
    );
    const re2 = new RegExp(
      `<meta[^>]+content=["']([^"']+)["'][^>]+(?:property|name)=["']${key}["']`,
      "i",
    );
    const m = html.match(re) || html.match(re2);
    if (m?.[1]) return decode(m[1]);
  }
  return "";
}

function decode(s: string) {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .trim();
}

export type UrlPreview = {
  url: string;
  title: string;
  image: string;
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
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
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
    const html = (await res.text()).slice(0, 250_000);
    const title =
      meta(html, ["og:title", "twitter:title"]) ||
      html.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1]?.trim() ||
      titleFallback;
    const image = meta(html, ["og:image", "twitter:image"]);
    return {
      url,
      title: decode(title).slice(0, 200),
      image,
      storeId: store.id,
      storeName: store.nameEn,
    };
  } catch {
    return {
      url,
      title: titleFallback,
      image: "",
      storeId: store.id,
      storeName: store.nameEn,
    };
  } finally {
    clearTimeout(timer);
  }
}
