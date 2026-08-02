"use client";
import { useEffect, useState } from "react";
import * as api from "@/lib/api";

export default function OtpVerification({ email, onVerify, onClose }: { email: string; onVerify: (code: string) => Promise<void>; onClose: () => void }) {
  const [code, setCode] = useState(""); const [seconds, setSeconds] = useState(60); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  useEffect(() => { const id = window.setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000); return () => clearInterval(id); }, []);
  async function submit() { if (code.length !== 6) return setError("Enter the 6-digit code."); setBusy(true); setError(""); try { await onVerify(code); } catch (e) { setError(e instanceof Error ? e.message : "Could not verify code."); } finally { setBusy(false); } }
  async function resend() { setBusy(true); try { await api.sendOtp(email); setSeconds(60); setError(""); } catch (e) { setError(e instanceof Error ? e.message : "Could not resend code."); } finally { setBusy(false); } }
  return <div className="fixed inset-0 z-[60] grid place-items-center bg-ink/60 p-4"><div className="w-full max-w-sm rounded-card bg-white p-6 shadow-2xl"><h2 className="font-display text-2xl text-canopy">Verify your email</h2><p className="mt-2 text-sm text-ink/65">Enter the 6-digit code sent to {email}.</p><input inputMode="numeric" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} className="mt-5 w-full rounded-lg border border-canopy/20 px-4 py-3 text-center text-xl tracking-[0.5em]" autoFocus />{error && <p className="mt-3 text-sm text-laterite">{error}</p>}<button disabled={busy} onClick={submit} className="mt-5 w-full rounded-full bg-laterite py-3 font-semibold text-white disabled:opacity-50">Verify and continue</button><div className="mt-4 flex justify-between text-sm"><button onClick={onClose} className="text-ink/60">Cancel</button><button disabled={busy || seconds > 0} onClick={resend} className="font-semibold text-canopy disabled:text-ink/40">{seconds ? `Resend in ${seconds}s` : "Resend code"}</button></div></div></div>;
}
