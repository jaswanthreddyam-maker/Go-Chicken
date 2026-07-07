"use client";

import React, { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    const user_id = searchParams.get("user_id");
    const tenant_id = searchParams.get("tenant_id");
    const name = searchParams.get("name");
    const role = searchParams.get("role");
    const error = searchParams.get("error");

    if (error) {
      router.push(`/login?error=${encodeURIComponent(error)}`);
      return;
    }

    if (user_id) {
      localStorage.setItem("gc_user", JSON.stringify({
        user_id,
        tenant_id,
        name,
        role,
      }));
      sessionStorage.setItem("gc_visited_landing", "true");
      sessionStorage.removeItem("gc_welcome_played");
      router.push("/dashboard");
    } else {
      router.push("/login?error=Invalid OAuth response");
    }
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center p-6">
      <div className="text-center space-y-4">
        <svg className="w-8 h-8 animate-spin mx-auto text-[#111111]" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 100" />
        </svg>
        <p className="text-sm font-bold uppercase tracking-wider text-[#111111]">
          Completing authentication...
        </p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center">
        <p className="text-sm font-bold uppercase tracking-wider text-[#111111]">Loading...</p>
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}
