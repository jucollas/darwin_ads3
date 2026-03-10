import Navbar from "@/components/Navbar";
import CampaignsDashboardView from "@/components/CampaignsDashboardView";

export default function CampaignsPage() {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <div className="p-8">
        <CampaignsDashboardView />
      </div>
    </div>
  );
}