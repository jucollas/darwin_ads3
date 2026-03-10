import { z } from "zod";
import { proxyJsonToBackend } from "../../_lib/proxy";
import { VariantPackSchema } from "@/lib/contracts";

export const dynamic = "force-dynamic";

const PromptSchema = z.object({
  name: z.string(),
  system: z.string(),
  user_template: z.any(),
  output_contract: VariantPackSchema,
  rules: z.array(z.string()),
});

export async function GET(req: Request) {
  return proxyJsonToBackend(req, "/ai/campaign-prompt", PromptSchema);
}