import { proxyJsonToBackend } from "../../_lib/proxy";
import {
  SchedulerRunNowRequestSchema,
  SchedulerRunNowResponseSchema,
} from "@/lib/contracts";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  // backend: POST /scheduler/run-now
  return proxyJsonToBackend(req, "/scheduler/run-now", SchedulerRunNowResponseSchema, {
    validateRequestBody: SchedulerRunNowRequestSchema,
  });
}