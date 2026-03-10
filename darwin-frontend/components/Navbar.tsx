export default function Navbar() {
  return (
    <div className="bg-black text-white px-8 py-4 flex justify-between items-center">
      <div className="flex items-center gap-3">
        <span className="text-red-600 font-bold text-2xl">DarwinAds</span>
      </div>

      <div className="flex items-center gap-6 text-sm">
        <span className="hover:text-red-500 cursor-pointer">Analytics</span>
        <span className="hover:text-red-500 cursor-pointer">Settings</span>
        <div className="w-8 h-8 bg-gray-600 rounded-full" />
      </div>
    </div>
  );
}