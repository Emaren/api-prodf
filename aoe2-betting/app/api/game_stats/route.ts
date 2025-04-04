// app/api/game_stats/route.ts
export async function GET() {
    const res = await fetch("http://aoe2-backend:8002/api/game_stats");
    const data = await res.json();
    return Response.json(data);
  }
  