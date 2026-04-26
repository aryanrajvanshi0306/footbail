import { useNavigate } from "react-router-dom";

export default function NotFound() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center px-4">
      <p className="text-8xl font-black text-[#00ff88] mb-4">404</p>
      <h1 className="text-2xl font-bold text-white mb-2">Page not found</h1>
      <p className="text-[#6b7280] mb-6">This page has gone off-side.</p>
      <button onClick={() => navigate("/dashboard")} className="btn-primary px-6 py-3">
        Back to Dashboard
      </button>
    </div>
  );
}
