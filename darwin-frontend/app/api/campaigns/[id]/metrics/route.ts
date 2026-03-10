import { proxyJsonToBackend } from "../../../_lib/proxy";
import { CampaignMetricsSchema } from "@/lib/contracts";

export const dynamic = "force-dynamic";

export async function GET(req: Request, ctx: { params: { id: string } }) {
  // backend recomendado: /campaigns/:id/stats
  // pero tú pediste “metrics”, así que mapeamos al backend que definas:
  return proxyJsonToBackend(req, `/campaigns/${ctx.params.id}/stats`, CampaignMetricsSchema);
}