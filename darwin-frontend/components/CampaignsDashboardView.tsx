"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/MetricCard";
import {
  Campaign,
  CampaignMetrics,
  OverviewStats,
  deleteCampaign,
  getCampaignMetrics,
  getCampaigns,
  getOverviewMetrics,
  publishCampaign,
  unpublishCampaign,
} from "@/services/api";

function StatusPill({ status }: { status: Campaign["status"] }) {
  const cls =
    status === "active"
      ? "bg-green-500"
      : status === "paused"
      ? "bg-yellow-500"
      : "bg-gray-500";
  return (
    <span className={`text-white text-xs px-3 py-1 rounded-full ${cls}`}>
      {status}
    </span>
  );
}

function VariantPill({ status }: { status: "draft" | "published" | "killed" }) {
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

export default function CampaignsDashboardView() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [actionLoading, setActionLoading] = useState<Record<string, string | null>>({});
  const [toast, setToast] = useState<{ type: "ok" | "err"; msg: string } | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedMetrics, setSelectedMetrics] = useState<CampaignMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [metricsErr, setMetricsErr] = useState<string | null>(null);

  async function refreshAll() {
    setErr(null);
    setLoading(true);
    try {
      const [c, o] = await Promise.all([getCampaigns(), getOverviewMetrics()]);
      setCampaigns(c);
      setOverview(o);
    } catch (e: any) {
      setErr(e?.message ?? "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshAll();
  }, []);

  async function openMetrics(id: string) {
    setSelectedId(id);
    setMetricsErr(null);
    setMetricsLoading(true);
    setSelectedMetrics(null);
    try {
      const m = await getCampaignMetrics(id);
      setSelectedMetrics(m);
    } catch (e: any) {
      setMetricsErr(e?.message ?? "Failed to load metrics");
    } finally {
      setMetricsLoading(false);
    }
  }

  async function runAction(id: string, action: "publish" | "unpublish" | "delete") {
    setToast(null);
    setActionLoading((p) => ({ ...p, [id]: action }));

    try {
      if (action === "publish") await publishCampaign(id);
      if (action === "unpublish") await unpublishCampaign(id);
      if (action === "delete") await deleteCampaign(id);

      setToast({ type: "ok", msg: `Action "${action}" executed` });

      // refresca tabla + overview
      await refreshAll();

      // si panel abierto, refrescar métricas
      if (selectedId === id) {
        await openMetrics(id);
      }
    } catch (e: any) {
      setToast({ type: "err", msg: e?.message ?? "Action failed" });
    } finally {
      setActionLoading((p) => ({ ...p, [id]: null }));
    }
  }

  const sortedCampaigns = useMemo(() => {
    return [...campaigns].sort((a, b) => b.created_at.localeCompare(a.created_at));
  }, [campaigns]);

  return (
    <div className="grid grid-cols-12 gap-8">
      {/* LEFT: overview + table */}
      <div className="col-span-8 flex flex-col gap-6">
        <div className="bg-white rounded-2xl shadow-md overflow-hidden">
          <div className="bg-black text-white px-6 py-5 flex items-center justify-between">
            <div>
              <p className="text-red-600 font-bold tracking-wide">DARWIN ADS</p>
              <h2 className="text-2xl font-bold mt-1">Campaigns Overview</h2>
              <p className="text-white/70 text-sm mt-1">
                General KPIs + campaigns table (actions included)
              </p>
            </div>
            <button
              onClick={refreshAll}
              className="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-full text-sm font-semibold"
            >
              Refresh
            </button>
          </div>

          <div className="p-6">
            {/* Overview cards */}
            <div className="grid grid-cols-4 gap-4">
              <MetricCard
                title="Campaigns Total"
                value={overview ? String(overview.campaigns_total) : "—"}
                highlight
              />
              <MetricCard
                title="Variants Published"
                value={overview ? String(overview.variants_published) : "—"}
              />
              <MetricCard
                title="Total Engagements"
                value={overview ? String(overview.total_engagements) : "—"}
              />
              <MetricCard
                title="Avg Fitness"
                value={overview ? String(overview.avg_fitness) : "—"}
              />
            </div>

            {/* Toast */}
            {toast && (
              <div
                className={`mt-5 rounded-xl p-3 text-sm border ${
                  toast.type === "ok"
                    ? "bg-green-50 border-green-200 text-green-800"
                    : "bg-red-50 border-red-200 text-red-700"
                }`}
              >
                {toast.msg}
              </div>
            )}

            {/* Errors */}
            {err && (
              <div className="mt-5 rounded-xl p-3 text-sm border bg-red-50 border-red-200 text-red-700">
                {err}
              </div>
            )}

            {/* Table */}
            <div className="mt-6 bg-white rounded-xl border overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-gray-100 text-sm">
                  <tr>
                    <th className="p-4">Campaign</th>
                    <th>Channel</th>
                    <th>Objective</th>
                    <th>Product</th>
                    <th>Status</th>
                    <th className="text-right pr-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td className="p-4 text-gray-500" colSpan={6}>
                        Loading campaigns...
                      </td>
                    </tr>
                  ) : sortedCampaigns.length === 0 ? (
                    <tr>
                      <td className="p-4 text-gray-500" colSpan={6}>
                        No campaigns yet.
                      </td>
                    </tr>
                  ) : (
                    sortedCampaigns.map((c) => {
                      const busy = actionLoading[c.id];
                      return (
                        <tr key={c.id} className="border-t hover:bg-gray-50">
                          <td className="p-4">
                            <div className="font-semibold">{c.name}</div>
                            <div className="text-xs text-gray-500">
                              {c.country} • {new Date(c.created_at).toLocaleString()}
                            </div>
                          </td>
                          <td className="text-sm">{c.channel}</td>
                          <td className="text-sm">{c.objective}</td>
                          <td className="text-sm">
                            {c.product.name} •{" "}
                            <span className="text-gray-600">
                              {c.product.price_cop.toLocaleString()} COP
                            </span>
                          </td>
                          <td>
                            <StatusPill status={c.status} />
                          </td>
                          <td className="text-right pr-4">
                            <div className="flex justify-end gap-2">
                              <button
                                onClick={() => openMetrics(c.id)}
                                className="px-3 py-2 rounded-full text-xs font-semibold border hover:bg-gray-100"
                              >
                                View metrics
                              </button>

                              <button
                                onClick={() => runAction(c.id, "publish")}
                                disabled={!!busy}
                                className="px-3 py-2 rounded-full text-xs font-semibold bg-black text-white hover:bg-black/90 disabled:opacity-60"
                              >
                                {busy === "publish" ? "Publishing..." : "Publish"}
                              </button>

                              <button
                                onClick={() => runAction(c.id, "unpublish")}
                                disabled={!!busy}
                                className="px-3 py-2 rounded-full text-xs font-semibold border border-red-200 text-red-700 hover:bg-red-50 disabled:opacity-60"
                              >
                                {busy === "unpublish" ? "Unpublishing..." : "Unpublish"}
                              </button>

                              <button
                                onClick={() => runAction(c.id, "delete")}
                                disabled={!!busy}
                                className="px-3 py-2 rounded-full text-xs font-semibold bg-red-600 text-white hover:bg-red-700 disabled:opacity-60"
                              >
                                {busy === "delete" ? "Deleting..." : "Delete"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-4 text-xs text-gray-500">
              Actions call: publish/unpublish affect <b>Variants</b>, not the campaign context.
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT: metrics panel */}
      <div className="col-span-4">
        <div className="bg-white rounded-2xl shadow-md overflow-hidden sticky top-8">
          <div className="bg-black text-white px-6 py-5">
            <h3 className="text-xl font-bold">Campaign Metrics</h3>
            <p className="text-white/70 text-sm mt-1">
              Aggregated stats + variants (latest snapshot)
            </p>
          </div>

          <div className="p-6">
            {!selectedId && (
              <div className="text-sm text-gray-500">
                Select a campaign → <b>View metrics</b>
              </div>
            )}

            {metricsLoading && (
              <div className="text-sm text-gray-500">Loading metrics...</div>
            )}

            {metricsErr && (
              <div className="rounded-xl p-3 text-sm border bg-red-50 border-red-200 text-red-700">
                {metricsErr}
              </div>
            )}

            {selectedMetrics && (
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 border rounded-xl p-4">
                    <div className="text-xs text-gray-500">Variants</div>
                    <div className="text-2xl font-bold">
                      {selectedMetrics.variants_total}
                    </div>
                  </div>
                  <div className="bg-gray-50 border rounded-xl p-4">
                    <div className="text-xs text-gray-500">Published</div>
                    <div className="text-2xl font-bold">
                      {selectedMetrics.variants_published}
                    </div>
                  </div>
                  <div className="bg-gray-50 border rounded-xl p-4">
                    <div className="text-xs text-gray-500">Engagements</div>
                    <div className="text-2xl font-bold">
                      {selectedMetrics.total_engagements}
                    </div>
                  </div>
                  <div className="bg-gray-50 border rounded-xl p-4">
                    <div className="text-xs text-gray-500">Avg Fitness</div>
                    <div className="text-2xl font-bold">
                      {selectedMetrics.avg_fitness}
                    </div>
                  </div>
                </div>

                <div className="border rounded-xl overflow-hidden">
                  <div className="bg-gray-100 px-4 py-3 text-sm font-semibold">
                    Variants
                  </div>

                  <div className="max-h-[420px] overflow-auto">
                    {selectedMetrics.variants.length === 0 ? (
                      <div className="p-4 text-sm text-gray-500">No variants.</div>
                    ) : (
                      selectedMetrics.variants.map((v) => (
                        <div key={v.id} className="p-4 border-t">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <div className="font-semibold text-sm">
                                Gen {v.generation} • {v.creative.headline}
                              </div>
                              <div className="text-xs text-gray-500 mt-1">
                                {v.external.post_url ? (
                                  <span>Post: {v.external.post_url}</span>
                                ) : (
                                  <span>Not published</span>
                                )}
                              </div>
                            </div>
                            <VariantPill status={v.status} />
                          </div>

                          <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                            <div className="bg-gray-50 border rounded-lg p-2">
                              <div className="text-gray-500">Impr.</div>
                              <div className="font-semibold">
                                {v.latest_metrics?.impressions ?? "—"}
                              </div>
                            </div>
                            <div className="bg-gray-50 border rounded-lg p-2">
                              <div className="text-gray-500">Clicks</div>
                              <div className="font-semibold">
                                {v.latest_metrics?.clicks ?? "—"}
                              </div>
                            </div>
                            <div className="bg-gray-50 border rounded-lg p-2">
                              <div className="text-gray-500">Fitness</div>
                              <div className="font-semibold">
                                {v.latest_metrics?.fitness ?? "—"}
                              </div>
                            </div>
                          </div>

                          <details className="mt-3">
                            <summary className="cursor-pointer text-xs font-semibold text-gray-700">
                              Show engagement breakdown
                            </summary>
                            <div className="mt-2 grid grid-cols-4 gap-2 text-xs">
                              {[
                                ["Likes", v.latest_metrics?.likes],
                                ["Comments", v.latest_metrics?.comments],
                                ["Shares", v.latest_metrics?.shares],
                                ["Clicks", v.latest_metrics?.clicks],
                              ].map(([k, val]) => (
                                <div key={String(k)} className="bg-gray-50 border rounded-lg p-2">
                                  <div className="text-gray-500">{k}</div>
                                  <div className="font-semibold">{val ?? "—"}</div>
                                </div>
                              ))}
                            </div>
                          </details>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <button
                  onClick={() => openMetrics(selectedMetrics.campaign_id)}
                  className="bg-red-600 hover:bg-red-700 text-white py-3 rounded-full font-semibold"
                >
                  Refresh campaign metrics
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}