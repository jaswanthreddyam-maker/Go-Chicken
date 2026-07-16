"use client";

import React, { createContext, useState, useEffect, useContext } from 'react';
import { translations } from '@/lib/translations';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState('English');
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    async function loadLanguagePref() {
      try {
        let API_BASE = process.env.NEXT_PUBLIC_API_URL;
        if (!API_BASE) {
          if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
            API_BASE = "https://go-chicken-production.up.railway.app/api/v1";
          } else {
            API_BASE = "http://localhost:8000/api/v1";
          }
        }
        API_BASE = API_BASE.replace(/\/+$/, "");
        if (!API_BASE.endsWith("/api/v1")) API_BASE += "/api/v1";
        const userStr = localStorage.getItem('gc_user');
        if (!userStr) {
          setIsLoaded(true);
          return;
        }
        const res = await fetch(`${API_BASE}/profile`, {
          credentials: "include"
        });
        if (res.ok) {
          const data = await res.json();
          if (data.app_language) {
            setLanguage(data.app_language);
          }
        }
      } catch (err) {
        console.error("Failed to load language preference", err);
      } finally {
        setIsLoaded(true);
      }
    }
    loadLanguagePref();
  }, []);

  const t = (key) => {
    if (!translations[language]) return key;
    return translations[language][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, isLoaded }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
