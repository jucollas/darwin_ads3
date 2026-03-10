import { proxyJsonToBackend } from "../../../_lib/proxy";
import { VariantSchema } from "@/lib/contracts";

export const dynamic = "force-dynamic";

export async function POST(req: Request, ctx: { params: { id: string } }) {
  return proxyJsonToBackend(req, `/campaigns/${ctx.params.id}/publish`, VariantSchema);
}