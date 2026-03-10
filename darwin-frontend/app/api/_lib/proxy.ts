import { cookies } from "next/headers";
import { z } from "zod";

export const runtime = "nodejs";

function backendBaseUrl() {
  const base = process.env.BACKEND_BASE_URL;
  if (!base) throw new Error("BACKEND_BASE_URL is not set");
  return base.replace(/\/+$/, "");
}

function buildBackendUrl(req: Request, backendPath: string) {
  const base = backendBaseUrl();
  const url = new URL(req.url);
  const qs = url.search ? url.search : "";
  const path = backendPath.startsWith("/") ? backendPath : `/${backendPath}`;
  return `${base}${path}${qs}`;
}

async function getForwardAuthHeader(req: Request) {
  // 1) si el cliente ya manda Authorization, lo pasamos
  const auth = req.headers.get("authorization");
  if (auth) return auth;

  // 2) si no, intentamos cookie HttpOnly (async en Next reciente)
  const cookieName = process.env.AUTH_COOKIE_NAME || "token";
  const cookieStore = await cookies();
  const token = cookieStore.get(cookieName)?.value;

  return token ? `Bearer ${token}` : null;
}

async function filterRequestHeaders(req: Request) {
  const out = new Headers();

  req.headers.forEach((value, key) => {
    const k = key.toLowerCase();
    if (["host", "connection", "content-length"].includes(k)) return;
    out.set(key, value);
  });

  const auth = await getForwardAuthHeader(req);
  if (auth) out.set("authorization", auth);

  out.set("cache-control", "no-store");
  return out;
}

function copyResponseHeaders(from: Headers) {
  const to = new Headers();
  from.forEach((v, k) => {
    const kl = k.toLowerCase();
    if (kl === "transfer-encoding") return;
    to.set(k, v);
  });

  const anyFrom: any = from as any;
  if (typeof anyFrom.getSetCookie === "function") {
    const arr: string[] = anyFrom.getSetCookie();
    if (arr?.length) {
      to.delete("set-cookie");
      for (const c of arr) to.append("set-cookie", c);
    }
  }

  return to;
}

async function fetchBackend(req: Request, backendPath: string) {
  const url = buildBackendUrl(req, backendPath);
  const headers = await filterRequestHeaders(req);

  const method = req.method.toUpperCase();
  const hasBody = !["GET", "HEAD"].includes(method);

  const controller = new AbortController();
  const timeoutMs = Number(process.env.BACKEND_TIMEOUT_MS ?? 15000);
  const t = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const body = hasBody ? await req.arrayBuffer() : undefined;

    return await fetch(url, {
      method,
      headers,
      body: hasBody ? body : undefined,
      redirect: "manual",
      cache: "no-store",
      signal: controller.signal,
    });
  } finally {
    clearTimeout(t);
  }
}

// --- el resto de tu archivo proxy.ts puede quedarse igual ---
// Asegúrate de que proxyToBackend y proxyJsonToBackend llamen a fetchBackend como ya lo hacían.

/** Passthrough puro (stream) */
export async function proxyToBackend(req: Request, backendPath: string) {
  let backendRes: Response;
  try {
    backendRes = await fetchBackend(req, backendPath);
  } catch (e: any) {
    return new Response(
      JSON.stringify({ error: "BackendUnavailable", message: e?.message ?? "fetch failed" }),
      { status: 502, headers: { "content-type": "application/json" } }
    );
  }

  return new Response(backendRes.body, {
    status: backendRes.status,
    statusText: backendRes.statusText,
    headers: copyResponseHeaders(backendRes.headers),
  });
}

/**
 * Proxy JSON robusto:
 * - si backend devuelve 2xx: parsea JSON, valida con schema, y responde {data: ...}
 * - si backend devuelve 4xx/5xx: passthrough (para no romper error contract del backend)
 */
export async function proxyJsonToBackend<T extends z.ZodTypeAny>(
  req: Request,
  backendPath: string,
  dataSchema: T,
  options?: { validateRequestBody?: z.ZodTypeAny }
) {
  // Validación del request body (opcional)
  if (options?.validateRequestBody) {
    const method = req.method.toUpperCase();
    if (!["GET", "HEAD"].includes(method)) {
      const clone = req.clone();
      const body = await clone.json().catch(() => null);
      const parsed = options.validateRequestBody.safeParse(body);
      if (!parsed.success) {
        return new Response(
          JSON.stringify({ error: "ValidationError", details: parsed.error.flatten() }),
          { status: 400, headers: { "content-type": "application/json" } }
        );
      }
    }
  }

  let backendRes: Response;
  try {
    backendRes = await fetchBackend(req, backendPath);
  } catch (e: any) {
    return new Response(
      JSON.stringify({ error: "BackendUnavailable", message: e?.message ?? "fetch failed" }),
      { status: 502, headers: { "content-type": "application/json" } }
    );
  }

  // Si backend responde error, lo pasamos tal cual
  if (!backendRes.ok) {
    return new Response(backendRes.body, {
      status: backendRes.status,
      statusText: backendRes.statusText,
      headers: copyResponseHeaders(backendRes.headers),
    });
  }

  // Esperamos JSON en éxito
  const json = await backendRes.json().catch(() => null);
  const parsedDirect = dataSchema.safeParse(json);
  const parsedData =
    json && typeof json === "object" && "data" in (json as any)
      ? dataSchema.safeParse((json as any).data)
      : null;

  const parsed = parsedDirect.success
    ? parsedDirect
    : parsedData && parsedData.success
    ? parsedData
    : parsedDirect; // para mantener error details

  if (!parsed.success) {
    return new Response(
      JSON.stringify({
        error: "InvalidBackendResponse",
        message: "Backend response does not match contract",
        details: parsed.error.flatten(),
      }),
      { status: 502, headers: { "content-type": "application/json" } }
    );
  }

  // Normalizamos a envelope {data: ...}
  return new Response(JSON.stringify({ data: parsed.data }), {
    status: 200,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}