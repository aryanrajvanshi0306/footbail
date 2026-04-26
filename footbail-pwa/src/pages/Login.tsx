import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSendOtp, useVerifyOtp } from "../hooks/useAuth";
import { Loader2, ChevronRight, Shield } from "lucide-react";

type Role = "player" | "coach" | "referee" | "admin";
type Step = "phone" | "otp";

const ROLES: { value: Role; label: string; emoji: string }[] = [
  { value: "player",  label: "Player",  emoji: "⚽" },
  { value: "coach",   label: "Coach",   emoji: "📋" },
  { value: "referee", label: "Referee", emoji: "🟨" },
  { value: "admin",   label: "Admin",   emoji: "🛡️" },
];

export default function Login() {
  const [step, setStep]   = useState<Step>("phone");
  const [phone, setPhone] = useState("");
  const [otp, setOtp]     = useState("");
  const [role, setRole]   = useState<Role>("player");
  const [devOtp, setDevOtp] = useState<string | null>(null);

  const sendOtp   = useSendOtp();
  const verifyOtp = useVerifyOtp();
  const navigate  = useNavigate();

  const handleSend = async () => {
    try {
      const res = await sendOtp.mutateAsync({ phone, role });
      if (res.dev_otp) setDevOtp(res.dev_otp);
      setStep("otp");
    } catch (e) {
      // error shown from mutation state
    }
  };

  const handleVerify = async () => {
    try {
      await verifyOtp.mutateAsync({ phone, otp, role });
      navigate("/dashboard");
    } catch (e) {
      // error shown from mutation state
    }
  };

  return (
    <div className="min-h-screen bg-hero-gradient flex flex-col items-center justify-center px-4">
      {/* Logo */}
      <div className="mb-8 text-center animate-fade-in">
        <h1 className="text-5xl font-black tracking-tight">
          <span className="text-[#00ff88]">foot</span>
          <span className="text-white">bAIl</span>
        </h1>
        <p className="text-[#6b7280] mt-2 text-sm">India's first AI-powered football club</p>
      </div>

      <div className="w-full max-w-md card animate-slide-up">
        {step === "phone" ? (
          <>
            <h2 className="text-xl font-bold text-white mb-6">Sign in / Register</h2>

            {/* Role selector */}
            <div className="grid grid-cols-4 gap-2 mb-6">
              {ROLES.map((r) => (
                <button
                  key={r.value}
                  onClick={() => setRole(r.value)}
                  className={`flex flex-col items-center gap-1 py-3 px-2 rounded-xl text-xs font-semibold
                    border transition-all
                    ${role === r.value
                      ? "border-[#00ff88] bg-[#00ff88]/10 text-[#00ff88]"
                      : "border-[#2a2a3d] text-[#6b7280] hover:border-[#4b5563]"
                    }`}
                >
                  <span className="text-xl">{r.emoji}</span>
                  {r.label}
                </button>
              ))}
            </div>

            {/* Phone input */}
            <label className="block mb-4">
              <span className="text-sm text-[#9ca3af] block mb-2">Mobile number</span>
              <div className="flex">
                <span className="inline-flex items-center px-3 bg-[#2a2a3d] border border-r-0
                                 border-[#3a3a50] rounded-l-xl text-[#9ca3af] text-sm">
                  +91
                </span>
                <input
                  type="tel"
                  maxLength={10}
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, ""))}
                  placeholder="98765 43210"
                  className="flex-1 bg-[#0a0a0f] border border-[#3a3a50] rounded-r-xl px-4 py-3
                             text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00ff88]
                             transition-colors text-sm"
                  onKeyDown={(e) => e.key === "Enter" && phone.length === 10 && handleSend()}
                />
              </div>
            </label>

            <button
              onClick={handleSend}
              disabled={phone.length !== 10 || sendOtp.isPending}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {sendOtp.isPending ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <>Send OTP <ChevronRight size={18} /></>
              )}
            </button>

            {sendOtp.isError && (
              <p className="text-[#ef4444] text-sm mt-3 text-center">
                {(sendOtp.error as Error).message}
              </p>
            )}
          </>
        ) : (
          <>
            <button onClick={() => setStep("phone")} className="text-[#00ff88] text-sm mb-4 hover:underline">
              ← Change number
            </button>
            <h2 className="text-xl font-bold text-white mb-2">Enter OTP</h2>
            <p className="text-sm text-[#6b7280] mb-6">Sent to +91 {phone}</p>

            {devOtp && (
              <div className="bg-[#00ff88]/10 border border-[#00ff88]/30 rounded-xl px-4 py-3 mb-4
                              flex items-center gap-2">
                <Shield size={16} className="text-[#00ff88] flex-shrink-0" />
                <span className="text-sm text-[#00ff88]">
                  Dev OTP: <strong className="font-mono">{devOtp}</strong>
                </span>
              </div>
            )}

            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
              placeholder="· · · · · ·"
              className="w-full bg-[#0a0a0f] border border-[#3a3a50] rounded-xl px-4 py-4
                         text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00ff88]
                         transition-colors text-center text-2xl font-mono tracking-[0.5em] mb-4"
              onKeyDown={(e) => e.key === "Enter" && otp.length === 6 && handleVerify()}
            />

            <button
              onClick={handleVerify}
              disabled={otp.length !== 6 || verifyOtp.isPending}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {verifyOtp.isPending
                ? <Loader2 size={18} className="animate-spin" />
                : <>Verify &amp; Sign In <ChevronRight size={18} /></>
              }
            </button>

            {verifyOtp.isError && (
              <p className="text-[#ef4444] text-sm mt-3 text-center">
                {(verifyOtp.error as Error).message}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
