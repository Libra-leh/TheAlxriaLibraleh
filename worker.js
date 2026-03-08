export default {
  async fetch(request) {

    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "*"
    }

    // handle browser preflight request
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors })
    }

    const url = new URL(request.url)
    const q = url.searchParams.get("q")

    if (!q) {
      return new Response("Missing query", {
        status: 400,
        headers: cors
      })
    }

    const api =
      "https://tiki.vn/api/v2/products?q=" + encodeURIComponent(q)

    const res = await fetch(api, {
      headers: {
        "User-Agent": "Mozilla/5.0"
      }
    })

    const text = await res.text()

    return new Response(text, {
      headers: {
        "Content-Type": "application/json",
        ...cors
      }
    })
  }
}
