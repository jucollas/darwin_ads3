import { proxyJsonToBackend } from "../../_lib/proxy";
import { OverviewStatsSchema } from "@/lib/contracts";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  // tu backend puede usar /stats/overview o /metrics/overview
  // aquí lo dejamos como /stats/overview para alinearlo con el modelo
  return proxyJsonToBackend(req, "/metrics/overview", OverviewStatsSchema);
}