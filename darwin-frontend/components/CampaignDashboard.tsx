import MetricCard from "./MetricCard";
import CampaignTable from "./CampaignTable";
import { getCampaigns } from "@/services/api";

export default async function CampaignDashboard() {
  const campaigns = await getCampaigns();

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-3xl font-bold">Campaign Dashboard</h2>

      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Active Campaigns" value="12" highlight />
        <MetricCard title="Daily Budget" value="$150" />
        <MetricCard title="Total Conversions" value="345" />
        <MetricCard title="ROI" value="4.2x" />
      </div>

      <CampaignTable campaigns={campaigns} />
    </div>
  );
}