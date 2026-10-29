let requests = 0;
const instance = crypto.randomUUID();

console.info(`BENCH_DENO_READY ${JSON.stringify({ instance })}`);

export default {
  async fetch(request: Request): Promise<Response> {
    const path = new URL(request.url).pathname;
    if (path === "/ready") {
      return Response.json({ instance, requests });
    }
    if (path === "/plain") {
      requests++;
      return new Response("Hello, world!\n", {
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }
    if (path !== "/deno" && path !== "/deno/echo") {
      return new Response("Not Found", { status: 404 });
    }
    return Response.json({
      runtime: "deno",
      engine: "Deno Core / V8",
      method: request.method,
      path,
      body: await request.text(),
      requests: ++requests,
    });
  },
};
