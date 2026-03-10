import { z } from "zod";
import { proxyJsonToBackend } from "../_lib/proxy";
import { CampaignSchema, CampaignCreateSchema } from "@/lib/contracts";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return proxyJsonToBackend(req, "/campaigns", z.array(CampaignSchema));
}

export async function POST(req: Request) {
  return proxyJsonToBackend(req, "/campaigns", CampaignSchema, {
    validateRequestBody: CampaignCreateSchema,
  });
}