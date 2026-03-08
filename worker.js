const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "*",
  "Content-Type": "application/json"
};

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS });
    }

    try {
      const url = new URL(request.url);
      const q = url.searchParams.get("q");

      if (!q) {
        return new Response(JSON.stringify({ items: [] }), { headers: CORS });
      }

      const fahasaUrl = "https://www.fahasa.com/catalogsearch/result/?q=" + encodeURIComponent(q);

      let html = "";
      try {
        const res = await fetch(fahasaUrl, {
          headers: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"
          }
        });
        html = await res.text();
      } catch (fetchErr) {
        return new Response(JSON.stringify({ items: [], error: "fetch_failed" }), { headers: CORS });
      }

      const items = parseFahasa(html);
      return new Response(JSON.stringify({ items }), { headers: CORS });

    } catch (e) {
      return new Response(JSON.stringify({ items: [], error: e.message }), { headers: CORS });
    }
  }
};

function parseFahasa(html) {
  const items = [];
  const blocks = html.match(/<li[^>]*class="[^"]*product[^"]*item[^"]*"[^>]*>[\s\S]*?<\/li>/gi) || [];

  for (const block of blocks) {
    try {
      let title = "";
      const tM = block.match(/class="[^"]*product-item-link[^"]*"[^>]*>\s*([\s\S]*?)\s*<\/a>/i)
               || block.match(/class="[^"]*product-name[^"]*"[^>]*>[\s\S]*?<a[^>]*>\s*([\s\S]*?)\s*<\/a>/i);
      if (tM) title = strip(tM[1]);
      if (!title) continue;

      let thumb = "";
      const iM = block.match(/(?:data-src|src)="(https?:\/\/[^"]*(?:fahasa|fhs|product)[^"]*\.(?:jpg|jpeg|png|webp)[^"]*)"/i)
               || block.match(/(?:data-src|src)="(https?:\/\/[^"]+\.(?:jpg|jpeg|png|webp))"/i);
      if (iM) thumb = iM[1].replace(/^http:\/\//, "https://");

      let author = "";
      const aM = block.match(/class="[^"]*author[^"]*"[^>]*>\s*([\s\S]*?)\s*<\/(?:span|div|p|a)>/i);
      if (aM) author = strip(aM[1]);

      let link = "";
      const lM = block.match(/href="(https?:\/\/[^"]*fahasa[^"]*)"/i);
      if (lM) link = lM[1];

      items.push({
        _source: "cf",
        volumeInfo: {
          title,
          authors: author ? [author] : [],
          publishedDate: "",
          categories: [],
          language: "vi",
          imageLinks: thumb ? { thumbnail: thumb } : null,
          infoLink: link
        }
      });

      if (items.length >= 10) break;
    } catch (_) {}
  }

  return items;
}

function strip(s) {
  return s.replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&#39;/g, "'").replace(/&quot;/g, '"')
    .replace(/\s+/g, " ").trim();
}
