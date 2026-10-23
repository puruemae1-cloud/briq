/**
 * Tell Naver that pages were added or updated (IndexNow).
 *
 * Reads the live sitemap and submits www.briq.kr URLs whose lastmod is within
 * INDEXNOW_DAYS (default 2), newest first, plus the main pages without query
 * strings. One request holds at most INDEXNOW_CAP URLs (default 2000, Naver's
 * ceiling is 10000). The key file in public/ must already be deployed.
 */
import { readdirSync, readFileSync } from "node:fs";

const SITE = "https://www.briq.kr";
const HOST = "www.briq.kr";
const DAYS = Number(process.env.INDEXNOW_DAYS || 2);
const CAP = Number(process.env.INDEXNOW_CAP || 2000);

function indexNowKey() {
  const name = readdirSync("public").find((file) => /^[a-f0-9]{32}\.txt$/.test(file));
  if (!name) throw new Error("public/<32-hex>.txt IndexNow key is missing");
  const key = name.slice(0, -4);
  const body = readFileSync(`public/${name}`, "utf8").trim();
  if (body !== key) throw new Error("IndexNow key file contents do not match its name");
  return key;
}

function locs(xml) {
  return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);
}

function urlEntries(xml) {
  return [...xml.matchAll(/<url>([\s\S]*?)<\/url>/g)].map((match) => {
    const block = match[1];
    const loc = block.match(/<loc>([^<]+)<\/loc>/);
    const mod = block.match(/<lastmod>([^<]+)<\/lastmod>/);
    return {
      url: loc ? loc[1] : "",
      at: Date.parse(mod ? mod[1] : ""),
    };
  });
}

async function loadUrls(cutoff) {
  const index = await (await fetch(`${SITE}/sitemap-index.xml`)).text();
  const products = [];
  const pages = [];
  for (const mapUrl of locs(index)) {
    const xml = await (await fetch(mapUrl)).text();
    for (const { url, at } of urlEntries(xml)) {
      if (!url.startsWith(`${SITE}/`) && url !== SITE) continue;
      if (url.includes("?")) continue;
      if (url.includes("/product/")) {
        if (Number.isFinite(at) && at >= cutoff) products.push({ url, at });
      } else {
        pages.push(url);
      }
    }
  }
  products.sort((a, b) => b.at - a.at);
  const chosen = products.slice(0, CAP).map((row) => row.url);
  return [...new Set([...pages, ...chosen])];
}

const key = indexNowKey();
const cutoff = Date.now() - DAYS * 24 * 60 * 60 * 1000;
const urlList = await loadUrls(cutoff);
console.log(`indexnow candidates=${urlList.length} days=${DAYS} cap=${CAP}`);
if (urlList.length === 0) process.exit(0);

const response = await fetch("https://searchadvisor.naver.com/indexnow", {
  method: "POST",
  headers: { "content-type": "application/json; charset=utf-8" },
  body: JSON.stringify({
    host: HOST,
    key,
    keyLocation: `${SITE}/${key}.txt`,
    urlList,
  }),
});
const text = await response.text();
console.log(`indexnow status=${response.status} body=${text.slice(0, 300)}`);
if (response.status !== 200 && response.status !== 202) process.exit(1);
