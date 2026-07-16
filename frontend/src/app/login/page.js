"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Eye, EyeOff, Phone, Lock } from "lucide-react";
import { supabase } from "@/lib/supabase";

const getApiBase = () => {
  let url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      url = "https://go-chicken-steel.vercel.app/api/v1";
    } else {
      url = "http://localhost:8000/api/v1";
    }
  }
  url = url.replace(/\/+$/, "");
  if (!url.endsWith("/api/v1")) url += "/api/v1";
  return url;
};
const API_BASE = getApiBase();

export default function LoginPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    phone: "",
    password: "",
  });

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 0);
    return () => clearTimeout(t);
  }, []);

  const update = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.phone.trim()) return setError("Phone number is required.");
    if (!form.password) return setError("Password is required.");

    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Login failed. Please try again.");
      }

      // Store user details, token is now handled via HTTP-only cookie
      localStorage.setItem("gc_user", JSON.stringify({
        user_id: data.user_id,
        tenant_id: data.tenant_id,
        name: data.name,
        role: data.role,
      }));

      sessionStorage.setItem("gc_visited_landing", "true");
      sessionStorage.removeItem("gc_welcome_played");

      // Redirect to dashboard
      router.push("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputClass =
    "w-full pl-11 pr-4 py-3.5 bg-white border border-[#EBEBEB] text-sm font-medium text-[#111111] placeholder:text-[#B0B0B0] focus:outline-none focus:border-[#111111] transition-colors";

  return (
    <div className="min-h-screen bg-[#FAFAFA] flex">
      {/* ── Left Panel: Branding ─────────────────────────────── */}
      <div className="hidden lg:flex lg:w-[45%] bg-[#111111] text-white flex-col justify-between p-12 relative overflow-hidden">
        {/* Decorative grid */}
        <div className="absolute inset-0 opacity-[0.04]">
          <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
                <path d="M 60 0 L 0 0 0 60" fill="none" stroke="white" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        <div className="relative z-10">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="p-1 border border-white/20">
              <img src="/logo.png" alt="Go Chicken" className="w-5 h-5 object-contain invert" />
            </div>
            <span className="text-sm font-extrabold tracking-tight uppercase">Go Chicken</span>
          </Link>
        </div>

        <div className="relative z-10 max-w-md">
          <h2
            className={`text-4xl font-black leading-[1] tracking-[-0.02em] mb-6 transition-all duration-700 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
            }`}
            style={{ transitionDelay: "200ms" }}
          >
            Welcome back
            <br />
            <span className="text-white/50">to your hub.</span>
          </h2>
          <p
            className={`text-sm text-white/40 font-medium leading-relaxed transition-all duration-700 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
            style={{ transitionDelay: "400ms" }}
          >
            Your orders, fleet, and retailer ledger are waiting.
            Pick up right where you left off.
          </p>
        </div>

        <div className="relative z-10">
          <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-white/25">
            © 2026 Go Chicken. All rights reserved.
          </p>
        </div>
      </div>

      {/* ── Right Panel: Form ────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center px-4 py-8 sm:p-8 lg:p-12 w-full">
        <div className="w-full max-w-[420px] sm:bg-white sm:border sm:border-[#EBEBEB] sm:p-8 transition-all">
          {/* Mobile header and branding (using only existing text) */}
          <div className="lg:hidden mb-8">
            <div className="flex items-center gap-2.5 mb-6">
              <div className="p-1 border border-[#EBEBEB]">
                <img src="/logo.png" alt="Go Chicken" className="w-5 h-5 object-contain" />
              </div>
              <span className="text-sm font-extrabold tracking-tight uppercase text-[#111111]">Go Chicken</span>
            </div>
            <div className="p-5 bg-[#111111] text-white border border-[#111111]">
              <h2 className="text-xl font-black tracking-tight mb-2">
                Welcome back to your hub.
              </h2>
              <p className="text-xs text-white/60 font-medium leading-relaxed">
                Your orders, fleet, and retailer ledger are waiting. Pick up right where you left off.
              </p>
            </div>
          </div>

          <div
            className={`transition-all duration-700 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
            }`}
            style={{ transitionDelay: "100ms" }}
          >
            <h1 className="text-2xl font-black tracking-tight text-[#111111] mb-2">
              Log in to your account
            </h1>
            <p className="text-sm text-[#666666] font-medium mb-8">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="text-[#111111] font-bold underline underline-offset-4 hover:no-underline">
                Sign up
              </Link>
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className={`space-y-4 transition-all duration-700 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
            style={{ transitionDelay: "250ms" }}
          >
            {/* Google Login */}
            <button
              type="button"
              onClick={async () => {
                const { error } = await supabase.auth.signInWithOAuth({
                  provider: 'google',
                  options: {
                    redirectTo: `${window.location.origin}/auth/callback`,
                  },
                });
                if (error) setError(error.message);
              }}
              className="w-full flex items-center justify-center gap-3 px-7 py-3.5 bg-white border border-[#EBEBEB] text-sm font-semibold text-[#111111] hover:border-[#111111] hover:scale-[1.01] active:scale-[0.99] transition-all"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>

            {/* Divider */}
            <div className="flex items-center gap-4">
              <div className="flex-1 h-px bg-[#EBEBEB]" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#C0C0C0]">or</span>
              <div className="flex-1 h-px bg-[#EBEBEB]" />
            </div>

            {/* Phone */}
            <div className="relative">
              <Phone size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#B0B0B0]" />
              <input
                type="tel"
                placeholder="Phone number"
                value={form.phone}
                onChange={(e) => update("phone", e.target.value)}
                className={inputClass}
                autoFocus
              />
            </div>

            {/* Password */}
            <div className="relative">
              <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#B0B0B0]" />
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                className={`${inputClass} pr-12`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#B0B0B0] hover:text-[#111111] transition-colors"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {/* Forgot password link */}
            <div className="flex justify-end">
              <a href="#" className="text-[11px] font-bold uppercase tracking-wider text-[#999999] hover:text-[#111111] transition-colors">
                Forgot password?
              </a>
            </div>

            {/* Error */}
            {error && (
              <div className="text-xs font-bold text-red-600 bg-red-50 border border-red-100 px-4 py-3">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 px-7 py-3.5 bg-[#111111] text-white text-xs font-bold uppercase tracking-wider hover:bg-black hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 100" />
                  </svg>
                  Signing in...
                </span>
              ) : (
                <>
                  Log in
                  <ArrowRight size={14} />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div
            className={`mt-8 flex items-center gap-4 transition-all duration-700 ${
              mounted ? "opacity-100" : "opacity-0"
            }`}
            style={{ transitionDelay: "450ms" }}
          >
            <div className="flex-1 h-px bg-[#EBEBEB]" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#C0C0C0]">or</span>
            <div className="flex-1 h-px bg-[#EBEBEB]" />
          </div>

          {/* WhatsApp login hint */}
          <div
            className={`mt-6 transition-all duration-700 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
            style={{ transitionDelay: "550ms" }}
          >
            <button
              type="button"
              disabled
              className="w-full flex items-center justify-center gap-2.5 px-7 py-3.5 border border-[#EBEBEB] text-[#999999] text-xs font-bold uppercase tracking-wider cursor-not-allowed"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
              </svg>
              Continue with WhatsApp
              <span className="text-[8px] font-bold bg-[#EBEBEB] text-[#999999] px-1.5 py-0.5 ml-1 uppercase tracking-wider">Soon</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
