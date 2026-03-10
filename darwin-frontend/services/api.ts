// services/api.ts
export type Channel = "facebook_page" | "instagram_business";
export type Objective = "engagement" | "traffic";

export type CampaignStatus = "active" | "paused" | "archived";

export type CampaignCreateInput = {
  name: string;
  channel: Channel;
  country: string; // "CO"
  product: { name: string; price_cop: number };
  objective: Objective;
  status?: CampaignStatus; // backend tiene default active
};

export type Campaign = {
  id: string;
  user_id: string | null;
  name: string;
  channel: Channel;
  country: string;
  product: { name: string; price_cop: number };
  objective: Objective;
  status: CampaignStatus;
  created_at: string;
};

export type Variant = {
  id: string;
  campaign_id: string;
  generation: number;
  parent_variant_id: string | null;
  status: "draft" | "published" | "killed";
  creative: {
    headline: string;
    primary_text: string;
    cta: string;
    image_prompt: string;
    image_url: string | null;
  };
  external: {
    provider: string | null;
    post_id: string | null;
    post_url: string | null;
    published_at: string | null;
  };
  created_at: string;
};

export async function createCampaign(input: CampaignCreateInput) {
  const res = await fetch("/api/campaigns", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`POST /api/campaigns failed: ${res.status} ${txt}`);
  }
  const json = await res.json();
  return json.data as Campaign;
}

export async function generateVariants(campaignId: string, user_prompt: string) {
  const res = await fetch(`/api/campaigns/${campaignId}/variants/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_prompt }),
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`POST variants/generate failed: ${res.status} ${txt}`);
  }
  const json = await res.json();
  return json.data as Variant[];
}
/** */


export type AiCampaignPromptData = {
  name: string;
  system: string;
  user_template: any;
  output_contract: any;
  rules: string[];
};

export type OverviewStats = {
  campaigns_total: number;
  variants_published: number;
  variants_killed: number;
  total_impressions: number;
  total_engagements: number;
  avg_fitness: number;
};

export type VariantMetrics = {
  id: string;
  variant_id: string;
  impressions: number;
  likes: number;
  comments: number;
  shares: number;
  clicks: number;
  fitness: number;
  computed_at: string;
};


export type CampaignMetrics = {
  campaign_id: string;
  variants_total: number;
  variants_published: number;
  variants_killed: number;
  total_impressions: number;
  total_engagements: number;
  avg_fitness: number;
  variants: Array<Variant & { latest_metrics: VariantMetrics | null }>;
};

type UnpublishResponse = {
  affected_count: number;
  affected: Variant[];
};

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  const json = await res.json();
  return json.data as T; // gateway devuelve { data: ... }
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  // si backend manda error, lo devolvemos legible
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`POST ${path} failed: ${res.status} ${txt}`);
  }

  const json = await res.json();
  return json.data as T;
}

export function getAiCampaignPrompt() {
  return apiGet<AiCampaignPromptData>("/api/ai/campaign-prompt");
}

async function apiDelete(path: string): Promise<void> {
  const res = await fetch(path, { method: "DELETE" });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`DELETE ${path} failed: ${res.status} ${txt}`);
  }
}

export function getCampaigns() {
  return apiGet<Campaign[]>("/api/campaigns");
}

export function getOverviewMetrics() {
  return apiGet<OverviewStats>("/api/metrics/overview");
}

export function getCampaignMetrics(id: string) {
  return apiGet<CampaignMetrics>(`/api/campaigns/${id}/metrics`);
}

export function publishCampaign(id: string) {
  return apiPost<Variant>(`/api/campaigns/${id}/publish`);
}

export function unpublishCampaign(id: string) {
  return apiPost<UnpublishResponse>(`/api/campaigns/${id}/unpublish`);
}

export function deleteCampaign(id: string) {
  return apiDelete(`/api/campaigns/${id}`);
}

export type Variant = {
  id: string;
  campaign_id: string;
  generation: number;
  parent_variant_id: string | null;
  status: "draft" | "published" | "killed";
  creative: {
    headline: string;
    primary_text: string;
    cta: string;
    image_prompt: string;
    image_url: string | null;
  };
  external: {
    provider?: string | null;
    post_id?: string | null;
    post_url?: string | null;
    published_at?: string | null;
  };
  created_at: string;
};