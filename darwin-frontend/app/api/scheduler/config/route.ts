import { proxyJsonToBackend } from "../../_lib/proxy";
import {
  SchedulerConfigSchema,
  SchedulerConfigUpdateSchema,
} from "@/lib/contracts";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  // backend: GET /scheduler/config
  return proxyJsonToBackend(req, "/scheduler/config", SchedulerConfigSchema);
}

export async function PUT(req: Request) {
  // backend: PUT /scheduler/config
  return proxyJsonToBackend(req, "/scheduler/config", SchedulerConfigSchema, {
    validateRequestBody: SchedulerConfigUpdateSchema,
  });
}