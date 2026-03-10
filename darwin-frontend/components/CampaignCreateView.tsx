"use client";

import { useMemo, useState } from "react";
import {
  Campaign,
  CampaignCreateInput,
  CampaignStatus,
  Channel,
  Objective,
  Variant,
  createCampaign,
  generateVariants,
} from "@/services/api";

type Decision = "pending" | "accepted" | "rejected";

function VariantPill({ status }: { status: Variant["status"] }) {
  const cls =
    status === "published"
      ? "bg-green-500"
      : status === "killed"
      ? "bg-red-500"
      : "bg-gray-400";
  return (
    <span className={`text-white text-[11px] px-2 py-1 rounded-full ${cls}`}>
      {status}
    </span>
  );
}

export default function CampaignCreateView() {
  // 1) Campaign form (manual)
  const [form, setForm] = useState<CampaignCreateInput>({
    name: "",
    channel: "facebook_page",
    country: "CO",
    product: { name: "", price_cop: 0 },
    objective: "engagement",
    status: "active",
  });

  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [campaign, setCampaign] = useState<Campaign | null>(null);

  // 2) Generate variants (assisted)
  const [userPrompt, setUserPrompt] = useState("");
  const [genLoading, setGenLoading] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  const [variants, setVariants] = useState<Variant[]>([]);
  const [activeIdx, setActiveIdx] = useState(0);

  // local edits (UI only)
  const [variantEdits, setVariantEdits] = useState<Record<string, Variant["creative"]>>({});
  const [decisions, setDecisions] = useState<Record<string, Decision>>({});

  const canCreate =
    form.name.trim().length >= 1 &&
    form.product.name.trim().length >= 1 &&
    Number.isFinite(form.product.price_cop) &&
    form.product.price_cop >= 0 &&
    !createLoading;

  const canGenerate = !!campaign?.id && userPrompt.trim().length > 0 && !genLoading;

  const currentVariant = variants[activeIdx] ?? null;
  const currentCreative = currentVariant
    ? variantEdits[currentVariant.id] ?? currentVariant.creative
    : null;

  const acceptedCount = useMemo(
    () => Object.values(decisions).filter((d) => d === "accepted").length,
    [decisions]
  );

  async function onCreateCampaign() {
    setCreateError(null);
    setCampaign(null);

    // reset variants state when creating new campaign
    setVariants([]);
    setVariantEdits({});
    setDecisions({});
    setActiveIdx(0);
    setGenError(null);

    try {
      setCreateLoading(true);
      const c = await createCampaign(form);
      setCampaign(c);
    } catch (e: any) {
      setCreateError(e?.message ?? "Unknown error");
    } finally {
      setCreateLoading(false);
    }
  }

  async function onGenerateVariants() {
    setGenError(null);
    if (!campaign?.id) {
      setGenError("Primero crea la campaña.");
      return;
    }

    try {
      setGenLoading(true);

      // backend: POST /campaigns/{id}/variants/generate  -> retorna 3 VariantOut (draft)
      const vs = await generateVariants(campaign.id, userPrompt);

      setVariants(vs);
      setActiveIdx(0);

      // init local edits + decisions
      const edits: Record<string, Variant["creative"]> = {};
      const dec: Record<string, Decision> = {};
      for (const v of vs) {
        edits[v.id] = { ...v.creative };
        dec[v.id] = "pending";
      }
      setVariantEdits(edits);
      setDecisions(dec);
    } catch (e: any) {
      setGenError(e?.message ?? "Failed to generate variants");
    } finally {
      setGenLoading(false);
    }
  }

  function moveVariant(delta: number) {
    if (!variants.length) return;
    setActiveIdx((i) => {
      const next = i + delta;
      if (next < 0) return variants.length - 1;
      if (next >= variants.length) return 0;
      return next;
    });
  }

  function setCreativeField<K extends keyof Variant["creative"]>(
    key: K,
    value: Variant["creative"][K]
  ) {
    if (!currentVariant) return;
    setVariantEdits((p) => ({
      ...p,
      [currentVariant.id]: {
        ...(p[currentVariant.id] ?? currentVariant.creative),
        [key]: value,
      },
    }));
  }

  function decide(d: Decision) {
    if (!currentVariant) return;
    setDecisions((p) => ({ ...p, [currentVariant.id]: d }));
  }

  return (
    <div className="grid grid-cols-2 gap-8">
      {/* LEFT: Campaign (manual) + Generate variants */}
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <div className="bg-black text-white px-6 py-5">
          <p className="text-red-600 font-bold tracking-wide">DARWIN ADS</p>
          <h1 className="text-2xl font-bold mt-1">Create Campaign</h1>
          <p className="text-white/70 text-sm mt-1">
            Primero creas el contexto (Campaign). Luego generas 3 variantes asistidas.
          </p>
        </div>

        <div className="p-6 flex flex-col gap-6">
          {/* Campaign form */}
          <div className="border rounded-2xl p-5">
            <p className="text-sm font-semibold mb-3">Campaign (Fixed Context)</p>

            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="text-sm text-gray-600">Name</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                  className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="Promo Hamburguesa Cali"
                />
              </div>

              <div>
                <label className="text-sm text-gray-600">Channel</label>
                <select
                  value={form.channel}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, channel: e.target.value as Channel }))
                  }
                  className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  <option value="facebook_page">facebook_page</option>
                  <option value="instagram_business">instagram_business</option>
                </select>
              </div>

              <div>
                <label className="text-sm text-gray-600">Country</label>
                <input
                  value={form.country}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, country: e.target.value.toUpperCase().slice(0, 2) }))
                  }
                  className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="CO"
                />
              </div>

              <div>
                <label className="text-sm text-gray-600">Objective</label>
                <select
                  value={form.objective}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, objective: e.target.value as Objective }))
                  }
                  className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  <option value="engagement">engagement</option>
                  <option value="traffic">traffic</option>
                </select>
              </div>

              <div>
                <label className="text-sm text-gray-600">Status</label>
                <select
                  value={form.status ?? "active"}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, status: e.target.value as CampaignStatus }))
                  }
                  className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  <option value="active">active</option>
                  <option value="paused">paused</option>
                  <option value="archived">archived</option>
                </select>
              </div>

              <div className="col-span-2">
                <label className="text-sm text-gray-600">Product Name</label>
                <input
                  value={form.product.name}
                  onChange={(e) =>
                    setForm((p) => ({ ...p, product: { ...p.product, name: e.target.value } }))
                  }
                  className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="Hamburguesa Doble"
                />
              </div>

              <div className="col-span-2">
                <label className="text-sm text-gray-600">Product Price (COP)</label>
                <input
                  type="number"
                  value={form.product.price_cop ?? 0}
                  onChange={(e) =>
                    setForm((p) => ({
                      ...p,
                      product: { ...p.product, price_cop: Number(e.target.value || 0) },
                    }))
                  }
                  className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                  min={0}
                />
              </div>
            </div>

            <button
              onClick={onCreateCampaign}
              disabled={!canCreate}
              className="mt-5 bg-red-600 disabled:opacity-60 disabled:cursor-not-allowed hover:bg-red-700 text-white py-3 rounded-full font-semibold transition w-full flex items-center justify-center gap-2"
            >
              {createLoading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white/60 border-t-white rounded-full animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Campaign"
              )}
            </button>

            {createError && (
              <div className="mt-4 border border-red-200 bg-red-50 text-red-700 p-3 rounded-xl text-sm">
                {createError}
              </div>
            )}

            {campaign && (
              <div className="mt-4 border border-green-200 bg-green-50 text-green-800 p-4 rounded-xl text-sm">
                <p className="font-semibold">Campaign creada ✅</p>
                <p className="mt-1">
                  ID: <span className="font-mono">{campaign.id}</span>
                </p>
              </div>
            )}
          </div>

          {/* Generate variants (assisted) */}
          <div className="border rounded-2xl p-5">
            <p className="text-sm font-semibold">Generate Variants (Assisted)</p>
            <p className="text-xs text-gray-600 mt-1">
              Backend: POST /campaigns/{`{campaign_id}`}/variants/generate
            </p>

            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder='Ej: "Quiero promocionar mi hamburguesa doble en Cali con 2x1"'
              className="mt-3 border rounded-xl p-4 h-28 w-full resize-none focus:outline-none focus:ring-2 focus:ring-red-500"
            />

            <button
              onClick={onGenerateVariants}
              disabled={!canGenerate}
              className="mt-3 bg-black disabled:opacity-60 disabled:cursor-not-allowed hover:bg-black/90 text-white py-3 rounded-full font-semibold transition w-full flex items-center justify-center gap-2"
            >
              {genLoading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white/60 border-t-white rounded-full animate-spin" />
                  Generating...
                </>
              ) : (
                "Generate 3 Variants"
              )}
            </button>

            {!campaign?.id && (
              <p className="text-xs text-gray-500 mt-2">
                Crea una campaña para habilitar la generación.
              </p>
            )}

            {genError && (
              <div className="mt-3 border border-red-200 bg-red-50 text-red-700 p-3 rounded-xl text-sm">
                {genError}
              </div>
            )}

            {variants.length > 0 && (
              <div className="mt-4 bg-black text-white p-4 rounded-xl text-sm">
                <p className="font-semibold mb-2">Generated</p>
                <p className="text-gray-300">
                  {variants.length} variantes creadas y asignadas a la campaña (draft en DB).
                </p>
                <p className="text-gray-300 mt-1">
                  Accepted: <span className="text-white">{acceptedCount}</span> / {variants.length}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* RIGHT: Variants editor (3 proposals with arrows) */}
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <div className="bg-black text-white px-6 py-5 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Variant Proposals</h2>
            <p className="text-white/70 text-sm mt-1">
              Las 3 variantes (draft) devueltas por el backend para esta Campaign.
            </p>
          </div>
          <span className="text-xs bg-red-600 px-3 py-1 rounded-full">Variants</span>
        </div>

        <div className="p-6">
          {variants.length === 0 ? (
            <p className="text-sm text-gray-500">
              Genera variantes para verlas aquí.
            </p>
          ) : (
            <>
              {/* navigation */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => moveVariant(-1)}
                    className="w-10 h-10 rounded-full border hover:bg-gray-100 flex items-center justify-center"
                    title="Previous"
                  >
                    ←
                  </button>
                  <button
                    onClick={() => moveVariant(1)}
                    className="w-10 h-10 rounded-full border hover:bg-gray-100 flex items-center justify-center"
                    title="Next"
                  >
                    →
                  </button>

                  <div className="ml-2 text-sm">
                    <span className="font-semibold">Variant</span>{" "}
                    {activeIdx + 1} / {variants.length}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {currentVariant && <VariantPill status={currentVariant.status} />}
                  <div className="flex gap-2">
                    <button
                      onClick={() => decide("accepted")}
                      className={`px-4 py-2 rounded-full text-sm font-semibold border ${
                        currentVariant && decisions[currentVariant.id] === "accepted"
                          ? "bg-green-600 text-white border-green-600"
                          : "hover:bg-gray-100"
                      }`}
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => decide("rejected")}
                      className={`px-4 py-2 rounded-full text-sm font-semibold border ${
                        currentVariant && decisions[currentVariant.id] === "rejected"
                          ? "bg-red-600 text-white border-red-600"
                          : "border-red-200 text-red-700 hover:bg-red-50"
                      }`}
                    >
                      Reject
                    </button>
                  </div>
                </div>
              </div>

              {/* chips */}
              <div className="mt-4 flex gap-2 flex-wrap">
                {variants.map((v, idx) => {
                  const d = decisions[v.id] ?? "pending";
                  const cls =
                    d === "accepted"
                      ? "bg-green-50 border-green-200 text-green-800"
                      : d === "rejected"
                      ? "bg-red-50 border-red-200 text-red-700"
                      : "bg-gray-50 border-gray-200 text-gray-700";

                  return (
                    <button
                      key={v.id}
                      onClick={() => setActiveIdx(idx)}
                      className={`text-xs px-3 py-2 rounded-full border ${cls} ${
                        idx === activeIdx ? "ring-2 ring-red-500" : ""
                      }`}
                      title={v.creative.headline}
                    >
                      #{idx + 1} • {d}
                    </button>
                  );
                })}
              </div>

              {/* editor */}
              {currentVariant && currentCreative && (
                <div className="mt-5 grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <label className="text-sm text-gray-600">Headline</label>
                    <input
                      value={currentCreative.headline}
                      onChange={(e) => setCreativeField("headline", e.target.value)}
                      className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>

                  <div>
                    <label className="text-sm text-gray-600">CTA</label>
                    <input
                      value={currentCreative.cta}
                      onChange={(e) => setCreativeField("cta", e.target.value)}
                      className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>

                  <div>
                    <label className="text-sm text-gray-600">Image URL (optional)</label>
                    <input
                      value={currentCreative.image_url ?? ""}
                      onChange={(e) => setCreativeField("image_url", e.target.value || null)}
                      className="mt-1 w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500"
                      placeholder="https://..."
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="text-sm text-gray-600">Primary Text</label>
                    <textarea
                      value={currentCreative.primary_text}
                      onChange={(e) => setCreativeField("primary_text", e.target.value)}
                      className="mt-1 w-full border rounded-xl p-4 h-28 resize-none focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="text-sm text-gray-600">Image Prompt</label>
                    <textarea
                      value={currentCreative.image_prompt}
                      onChange={(e) => setCreativeField("image_prompt", e.target.value)}
                      className="mt-1 w-full border rounded-xl p-4 h-24 resize-none focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>
                </div>
              )}

              <div className="mt-5 text-xs text-gray-500">
                ✅ Estas variantes ya fueron creadas en la DB como <b>draft</b> al generarlas.  
                ✏️ Los cambios que haces aquí son locales (UI). Para guardar edits/rechazos en DB,
                hace falta un endpoint tipo <b>PATCH /variants/{`{id}`}</b> o <b>DELETE /variants/{`{id}`}</b>.
              </div>

              <details className="mt-4 bg-gray-50 border rounded-xl p-4">
                <summary className="cursor-pointer text-sm font-semibold">
                  Current variant JSON (edited)
                </summary>
                <pre className="mt-3 text-xs overflow-auto">
                  {currentVariant
                    ? JSON.stringify(
                        {
                          ...currentVariant,
                          creative: currentCreative,
                          decision: decisions[currentVariant.id],
                        },
                        null,
                        2
                      )
                    : "—"}
                </pre>
              </details>
            </>
          )}
        </div>
      </div>
    </div>
  );
}