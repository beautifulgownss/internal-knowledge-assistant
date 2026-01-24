import { NextRequest } from "next/server";

export async function GET(
  _req: NextRequest,
  ctx: { params: Promise<{ collection_id: string }> }
) {
  const { collection_id } = await ctx.params;

  const resp = await fetch(
    `${process.env.FASTAPI_BASE_URL}/v1/collections/${collection_id}/stats`,
    { method: "GET" }
  );

  const data = await resp.text();
  return new Response(data, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}
