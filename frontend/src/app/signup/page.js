"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Eye, EyeOff, Building2, User, Phone, Lock } from "lucide-react";

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

export default function SignupPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    business_name: "",
    admin_name: "",
    phone: "",
    password: "",
  });

  useEffect(() => setMounted(true), []);

  const update = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Client-side validation
    if (!form.business_name.trim()) return setError("Business name is required.");
    if (!form.admin_name.trim()) return setError("Your name is required.");
    if (!form.phone.trim() || form.phone.length < 10) return setError("Enter a valid phone number.");
    if (form.password.length < 6) return setError("Password must be at least 6 characters.");

    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Signup failed. Please try again.");
      }

      // Store auth data
      localStorage.setItem("gc_token", data.access_token);
      localStorage.setItem("gc_user", JSON.stringify({
        user_id: data.user_id,
        tenant_id: data.tenant_id,
        name: data.name,
        role: data.role,
      }));

      sessionStorage.setItem("gc_visited_landing", "true");
      sessionStorage.removeItem("gc_welcome_played");

      // Redirect to dashboard
      router.push("/");
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
          <Link href="/landing" className="flex items-center gap-2.5">
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
            Start managing
            <br />
            your poultry hub
            <br />
            <span className="text-white/50">like a pro.</span>
          </h2>
          <p
            className={`text-sm text-white/40 font-medium leading-relaxed transition-all duration-700 ${
              mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
            style={{ transitionDelay: "400ms" }}
          >
            Join 500+ poultry distributors who automated their supply chain
            with WhatsApp orders, IoT fleet tracking, and AI demand forecasting.
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
                Start managing your poultry hub like a pro.
              </h2>
              <p className="text-xs text-white/60 font-medium leading-relaxed">
                Join 500+ poultry distributors who automated their supply chain with WhatsApp orders, IoT fleet tracking, and AI demand forecasting.
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
              Create your account
            </h1>
            <p className="text-sm text-[#666666] font-medium mb-8">
              Already have an account?{" "}
              <Link href="/login" className="text-[#111111] font-bold underline underline-offset-4 hover:no-underline">
                Log in
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
            {/* Google Sign Up */}
            <button
              type="button"
              onClick={() => {
                // TODO: Wire up Google OAuth redirect
                window.location.href = `${API_BASE}/auth/google/login`;
              }}
              className="w-full flex items-center justify-center gap-3 px-7 py-3.5 bg-white border border-[#EBEBEB] text-sm font-semibold text-[#111111] hover:border-[#111111] hover:scale-[1.01] active:scale-[0.99] transition-all"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Sign up with Google
            </button>

            {/* Divider */}
            <div className="flex items-center gap-4">
              <div className="flex-1 h-px bg-[#EBEBEB]" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#C0C0C0]">or</span>
              <div className="flex-1 h-px bg-[#EBEBEB]" />
            </div>

            {/* Business Name */}
            <div className="relative">
              <Building2 size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#B0B0B0]" />
              <input
                type="text"
                placeholder="Business name"
                value={form.business_name}
                onChange={(e) => update("business_name", e.target.value)}
                className={inputClass}
                autoFocus
              />
            </div>

            {/* Admin Name */}
            <div className="relative">
              <User size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#B0B0B0]" />
              <input
                type="text"
                placeholder="Your full name"
                value={form.admin_name}
                onChange={(e) => update("admin_name", e.target.value)}
                className={inputClass}
              />
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
              />
            </div>

            {/* Password */}
            <div className="relative">
              <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#B0B0B0]" />
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Create a password"
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
                  Creating account...
                </span>
              ) : (
                <>
                  Create account
                  <ArrowRight size={14} />
                </>
              )}
            </button>
          </form>

          {/* Terms */}
          <p
            className={`mt-6 text-[10px] font-medium text-[#AEAEAE] leading-relaxed transition-all duration-700 ${
              mounted ? "opacity-100" : "opacity-0"
            }`}
            style={{ transitionDelay: "500ms" }}
          >
            By creating an account, you agree to Go Chicken&apos;s{" "}
            <a href="#" className="underline underline-offset-2">Terms of Service</a> and{" "}
            <a href="#" className="underline underline-offset-2">Privacy Policy</a>.
          </p>
        </div>
      </div>
    </div>
  );
}
