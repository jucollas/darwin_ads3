interface Props {
  title: string;
  value: string;
  highlight?: boolean;
}

export default function MetricCard({ title, value, highlight }: Props) {
  return (
    <div
      className={`rounded-xl p-6 shadow-md ${
        highlight ? "bg-red-600 text-white" : "bg-white"
      }`}
    >
      <p className="text-sm opacity-80">{title}</p>
      <p className="text-3xl font-bold mt-2">{value}</p>
    </div>
  );
}