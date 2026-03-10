import { z } from "zod";
import { proxyJsonToBackend } from "@/app/api/_lib/proxy";
import { VariantSchema, GenerateVariantsRequestSchema } from "@/lib/contracts";

export const dynamic = "force-dynamic";

export async function POST(
  req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params;

  return proxyJsonToBackend(
    req,
    `/campaigns/${id}/variants/generate`,
    z.array(VariantSchema),
    { validateRequestBody: GenerateVariantsRequestSchema }
  );
}