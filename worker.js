export default {
  async fetch(request) {

    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "*"
    }

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors })
    }

    const url = new URL(request.url)
    const q = url.searchParams.get("q")

    if (!q) {
      return new Response("Missing query", { status: 400, headers: cors })
    }

    const api =
      "https://www.fahasa.com/catalogsearch/result/?q=" +
      encodeURIComponent(q)

    const res = await fetch(api, {
      headers: {
        "User-Agent": "Mozilla/5.0"
      }
    })

    const html = await res.text()

    return new Response(html, {
      headers: {
        "Content-Type": "text/html",
        ...cors
      }
    })
  }
}
