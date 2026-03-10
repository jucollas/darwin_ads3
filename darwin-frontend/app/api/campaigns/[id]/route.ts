import { proxyToBackend, proxyJsonToBackend } from "../../_lib/proxy";
import { z } from "zod";
import { CampaignSchema, VariantSchema } from "@/lib/contracts";

export const dynamic = "force-dynamic";

// Detalle coherente con tu modelo: Campaign + Variants
export async function GET(req: Request, ctx: { params: { id: string } }) {
  return proxyJsonToBackend(
    req,
    `/campaigns/${ctx.params.id}`,
    z.object({
      campaign: CampaignSchema,
      variants: z.array(VariantSchema),
    })
  );
}

// Delete: passthrough (si tu backend devuelve {ok:true} o 204)
export async function DELETE(req: Request, ctx: { params: { id: string } }) {
  return proxyToBackend(req, `/campaigns/${ctx.params.id}`);
}