"use client";

import { useState } from "react";
import { aiCampaignDraft, CampaignDraft, Channel } from "@/services/api";

export default function CreateCampaignPanel() {
  const [prompt, setPrompt] = useState("");
  const [channel, setChannel] = useState<Channel>("facebook_page");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [draft, setDraft] = useState<CampaignDraft | null>(null);

  async function onGenerate() {
    setError(null);
    setLoading(true);
    setDraft(null);

    try {
      const result = await aiCampaignDraft({ prompt, channel });
      setDraft(result);
    } catch (e: any) {
      setError(e?.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white p-6 rounded-xl shadow-md flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-bold">Create Campaign from Brief</h2>
        <p className="text-gray-500">AI-Powered Assistant</p>
      </div>

      <div className="flex gap-3 items-center">
        <label className="text-sm text-gray-600">Channel</label>
        <select
          value={channel}
          onChange={(e) => setChannel(e.target.value as Channel)}
          className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
        >
          <option value="facebook_page">Facebook Page</option>
          <option value="instagram_business">Instagram Business</option>
        </select>
      </div>

      <textarea
        placeholder="Describe your campaign idea..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        className="border rounded-xl p-4 h-32 resize-none focus:outline-none focus:ring-2 focus:ring-red-500"
      />

      <button
        onClick={onGenerate}
        disabled={loading || prompt.trim().length === 0}
        className="bg-red-600 disabled:opacity-60 disabled:cursor-not-allowed hover:bg-red-700 text-white py-3 rounded-full font-semibold transition flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="inline-block w-4 h-4 border-2 border-white/60 border-t-white rounded-full animate-spin" />
            Generating...
          </>
        ) : (
          "Generate Campaign"
        )}
      </button>

      {error && (
        <div className="border border-red-200 bg-red-50 text-red-700 p-3 rounded-xl text-sm">
          {error}
        </div>
      )}

      <div className="bg-black text-white p-4 rounded-xl text-sm">
        <p className="font-semibold mb-2">Parsed Campaign Data:</p>

        {!draft && !loading && (
          <p className="text-gray-300">Generate to see parsed data…</p>
        )}

        {draft && (
          <ul className="space-y-1 text-gray-300">
            <li>
              Campaign Name: <span className="text-white">"{draft.campaign_name}"</span>
            </li>
            <li>
              Channel: <span className="text-white">{draft.channel}</span>
            </li>

            {draft.creative?.headline && (
              <li>
                Headline: <span className="text-white">"{draft.creative.headline}"</span>
              </li>
            )}

            {draft.creative?.cta && (
              <li>
                CTA: <span className="text-white">"{draft.creative.cta}"</span>
              </li>
            )}

            {draft.budget?.daily_cop != null && (
              <li>
                Budget: <span className="text-white">{draft.budget.daily_cop.toLocaleString()} COP/day</span>
              </li>
            )}

            {draft.creative?.hashtags?.length ? (
              <li>
                Hashtags:{" "}
                <span className="text-white">
                  {draft.creative.hashtags.join(" ")}
                </span>
              </li>
            ) : null}
          </ul>
        )}
      </div>

      {draft && (
        <details className="bg-gray-50 border rounded-xl p-4">
          <summary className="cursor-pointer text-sm font-semibold">
            View full JSON
          </summary>
          <pre className="mt-3 text-xs overflow-auto">
            {JSON.stringify(draft, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}