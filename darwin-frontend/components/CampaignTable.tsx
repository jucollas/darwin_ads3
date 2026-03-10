import { Campaign } from "@/types/campaign";

interface Props {
  campaigns: Campaign[];
}

export default function CampaignTable({ campaigns }: Props) {
  const statusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500";
      case "killed":
        return "bg-red-500";
      default:
        return "bg-gray-400";
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      <table className="w-full text-left">
        <thead className="bg-gray-100 text-sm">
          <tr>
            <th className="p-4">Name</th>
            <th>Status</th>
            <th>Clicks</th>
            <th>Conv.</th>
          </tr>
        </thead>
        <tbody>
          {campaigns.map((c) => (
            <tr key={c.id} className="border-t hover:bg-gray-50">
              <td className="p-4">{c.name}</td>
              <td>
                <span
                  className={`text-white text-xs px-3 py-1 rounded-full ${statusColor(
                    c.status
                  )}`}
                >
                  {c.status}
                </span>
              </td>
              <td>{c.clicks ?? "-"}</td>
              <td>{c.conversions ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}