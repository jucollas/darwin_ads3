import Navbar from "@/components/Navbar";
import CampaignCreateView from "@/components/CampaignCreateView";

export default function NewCampaignPage() {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <div className="p-8">
        <CampaignCreateView />
      </div>
    </div>
  );
}