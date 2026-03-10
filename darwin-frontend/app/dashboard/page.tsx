import Navbar from "@/components/Navbar";
import CreateCampaignPanel from "@/components/CreateCampaignPanel";
import CampaignDashboard from "@/components/CampaignDashboard";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />

      <div className="grid grid-cols-2 gap-8 p-8">
        {/*<CreateCampaignPanel />
        <CampaignDashboard />*/}
      </div>
    </div>
  );
}