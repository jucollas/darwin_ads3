import { z } from "zod";

/** Enums */
export const ChannelSchema = z.enum(["facebook_page", "instagram_business"]);
export const ObjectiveSchema = z.enum(["engagement", "traffic"]);
export const CampaignStatusSchema = z.enum(["active", "paused", "archived"]);
export const VariantStatusSchema = z.enum(["draft", "published", "killed"]);

const StrOrNull = z.union([z.string(), z.null()]);
const IsoOrNull = z.union([z.string(), z.null()]);

export const GenerateVariantsRequestSchema = z.object({
  user_prompt: z.string().min(1).max(2000),
});

export const VariantCreativeSchema = z.object({
  headline: z.string(),
  primary_text: z.string(),
  cta: z.string(),
  image_prompt: z.string(),
  image_url: z.string().nullable().optional(),
});

export const VariantExternalSchema = z.object({
  provider: z.string().nullable().optional(),
  post_id: z.string().nullable().optional(),
  post_url: z.string().nullable().optional(),
  published_at: z.string().nullable().optional(),
});

export const VariantSchema = z.object({
  id: z.string(),
  campaign_id: z.string(),
  generation: z.number().int(),
  parent_variant_id: z.string().nullable().optional(),
  status: z.enum(["draft", "published", "killed"]),
  creative: VariantCreativeSchema,
  external: VariantExternalSchema,
  created_at: z.string(),
}).passthrough();

/** Scheduler config */
export const SchedulerConfigSchema = z.object({
  enabled: z.boolean(),
  interval_seconds: z.number().int().positive(),
}).passthrough(); // permite campos extra si el backend añade más

export const SchedulerConfigUpdateSchema = z.object({
  enabled: z.boolean().optional(),
  interval_seconds: z.number().int().positive().optional(),
}).refine((v) => v.enabled !== undefined || v.interval_seconds !== undefined, {
  message: "Must provide at least one of: enabled, interval_seconds",
});

/** Run-now request */
export const SchedulerRunNowRequestSchema = z.object({
  threshold_up: z.number(),
  threshold_down: z.number(),
  dry_run: z.boolean().default(false),
  delete_remote_post: z.boolean().default(true),
});

/**
 * Run-now response:
 * no nos diste un contract fijo del backend,
 * entonces validamos algo mínimo y dejamos el resto libre
 */
export const SchedulerRunNowResponseSchema = z.object({
  ok: z.boolean().optional(),
}).passthrough();

export type SchedulerConfig = z.infer<typeof SchedulerConfigSchema>;
export type SchedulerRunNowRequest = z.infer<typeof SchedulerRunNowRequestSchema>;

/** A) Campaign (contexto fijo) */
// lib/contracts.ts


export const CampaignSchema = z.object({
  id: z.string(),

  // backend puede mandar null → normalizamos
  user_id: StrOrNull.transform((v) => v ?? "user_demo"),

  name: z.string(),
  channel: ChannelSchema,
  country: z.string().length(2).transform((v) => v || "CO"),

  product: z.object({
    name: z.string(),
    price_cop: z.number().int().nonnegative(),
  }),

  objective: ObjectiveSchema,

  // si backend lo manda null, lo ponemos activo por defecto
  status: z.union([CampaignStatusSchema, z.null()]).transform((v) => v ?? "active"),

  created_at: IsoOrNull.transform((v) => v ?? new Date().toISOString()),
}).passthrough();

/** Create Campaign (input mínimo) */
export const CampaignCreateSchema = z.object({
  name: z.string().min(2),
  channel: ChannelSchema,
  country: z.string().length(2).default("CO"),
  product: z.object({
    name: z.string().min(2),
    price_cop: z.number().int().nonnegative(),
  }),
  objective: ObjectiveSchema.default("engagement"),
});

/** B) Variant (organismo mutable) */

/** C) VariantMetrics */
export const VariantMetricsSchema = z.object({
  id: z.string(),
  variant_id: z.string(),
  impressions: z.number().int().nonnegative(),
  likes: z.number().int().nonnegative(),
  comments: z.number().int().nonnegative(),
  shares: z.number().int().nonnegative(),
  clicks: z.number().int().nonnegative(),
  fitness: z.number(),
  computed_at: z.string(),
});

/** LLM Variant Pack */
export const VariantPackSchema = z.object({
  type: z.literal("variant_pack"),
  version: z.literal("1.0"),
  variants: z
    .array(
      z.object({
        headline: z.string(),
        primary_text: z.string(),
        cta: z.string(),
        image_prompt: z.string(),
      })
    )
    .min(1),
  warnings: z.array(z.string()),
});

/** Stats overview mínimo (métricas generales) */
export const OverviewStatsSchema = z.object({
  campaigns_total: z.number().int().nonnegative(),
  variants_published: z.number().int().nonnegative(),
  variants_killed: z.number().int().nonnegative(),
  total_impressions: z.number().int().nonnegative(),
  total_engagements: z.number().int().nonnegative(),
  avg_fitness: z.number(),
});

/** Métricas por campaña: agregadas + variantes + latest metrics */
export const CampaignMetricsSchema = z.object({
  campaign_id: z.string(),
  variants_total: z.number().int().nonnegative(),
  variants_published: z.number().int().nonnegative(),
  variants_killed: z.number().int().nonnegative(),
  total_impressions: z.number().int().nonnegative(),
  total_engagements: z.number().int().nonnegative(),
  avg_fitness: z.number(),
  variants: z.array(
    VariantSchema.extend({
      latest_metrics: VariantMetricsSchema.nullable(),
    })
  ),
});

/** Envelope estándar */
export const ApiEnvelopeSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({ data: dataSchema });

/** Helpers de respuestas */
export const OkSchema = z.object({ ok: z.literal(true) });

/** Tipos TS */
export type Campaign = z.infer<typeof CampaignSchema>;
export type CampaignCreateInput = z.infer<typeof CampaignCreateSchema>;
export type Variant = z.infer<typeof VariantSchema>;
export type VariantMetrics = z.infer<typeof VariantMetricsSchema>;
export type VariantPack = z.infer<typeof VariantPackSchema>;
export type OverviewStats = z.infer<typeof OverviewStatsSchema>;
export type CampaignMetrics = z.infer<typeof CampaignMetricsSchema>;