"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
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

function CallbackContent() {
  const router = useRouter();
  const [status, setStatus] = useState("Authenticating...");

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const { data, error } = await supabase.auth.getSession();
        
        if (error || !data.session) {
          throw new Error("No session found");
        }

        const accessToken = data.session.access_token;
        const providerToken = data.session.provider_token || "";

        // Send to our backend
        const res = await fetch(`${getApiBase()}/auth/oauth/google`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            access_token: accessToken,
            provider_token: providerToken
          }),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Failed to log in via backend");
        }

        const backendData = await res.json();

        // Save local standard gc_auth user details
        localStorage.setItem("gc_user", JSON.stringify({
          user_id: backendData.user_id,
          tenant_id: backendData.tenant_id,
          name: backendData.name,
          role: backendData.role,
        }));
        sessionStorage.setItem("gc_visited_landing", "true");
        sessionStorage.removeItem("gc_welcome_played");

        // We explicitly clear the Supabase session so we solely rely on gc_auth
        await supabase.auth.signOut();

        router.push("/dashboard");
      } catch (err) {
        console.error("Auth callback error:", err);
        router.push("/login?error=oauth_failed");
      }
    };

    handleCallback();
  }, [router]);

  return (
    <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center p-6">
      <div className="text-center space-y-4">
        <svg className="w-8 h-8 animate-spin mx-auto text-[#111111]" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 100" />
        </svg>
        <p className="text-sm font-bold uppercase tracking-wider text-[#111111]">
          {status}
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
