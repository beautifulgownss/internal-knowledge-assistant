import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.text();

  const resp = await fetch(`${process.env.FASTAPI_BASE_URL}/v1/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  const data = await resp.text();
  return new NextResponse(data, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}
