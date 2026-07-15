"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useRef, useMemo } from "react";

const UIContext = createContext();

export function UIProvider({ children }) {
  // ── Theme State ──
  const [theme, setTheme] = useState("light");

  // ── Drawer State ──
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerContent, setDrawerContent] = useState(null);

  // ── Command Palette State ──
  const [paletteOpen, setPaletteOpen] = useState(false);

  // ── Toasts State ──
  const [toasts, setToasts] = useState([]);
  const toastIdRef = useRef(0);

  // ── Active Tab State (moved to UIContext to resolve tab navigation globally) ──
  const [activeTab, setActiveTab] = useState("overview");

  // ── Notifications State (Classified list of alerts originating from live triggers) ──
  const [notifications, setNotifications] = useState([]);

  // Sync tab switching to browser address bar without reloads
  const handleTabChange = useCallback((tabId) => {
    setActiveTab(tabId);
    if (typeof window !== 'undefined') {
      const newPath = tabId === 'overview' ? '/dashboard' : `/dashboard/${tabId}`;
      window.history.pushState(null, '', newPath);
    }
  }, []);

  // ── Theme initialization ──
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedTheme = localStorage.getItem("gc_theme") || "light";
      const t = setTimeout(() => setTheme(savedTheme), 0);
      document.documentElement.setAttribute("data-theme", savedTheme);
      if (savedTheme === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      return () => clearTimeout(t);
    }
  }, []);

  const toggleTheme = useCallback(() => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("gc_theme", nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
    if (nextTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  // ── Drawer Handlers ──
  const openDrawer = useCallback((content) => {
    setDrawerContent(content);
    setDrawerOpen(true);
  }, []);

  const closeDrawer = useCallback(() => {
    setDrawerOpen(false);
    // Delay clearing content so animations finish smoothly
    setTimeout(() => setDrawerContent(null), 300);
  }, []);

  // ── Toast Handlers ──
  const addToast = useCallback((message, type = "info", duration = 5000) => {
    const id = ++toastIdRef.current;
    setToasts((prev) => [...prev, { id, message, type }]);
    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // ── Notification Handlers ──
  const addNotification = useCallback((title, text, type = "info") => {
    setNotifications((prev) => [
      { id: Date.now(), title, text, type, read: false },
      ...prev
    ]);
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  // ── Shortcuts Registry (Single Source of Truth) ──
  const shortcuts = useMemo(() => [
    { key: "k", ctrlKey: true, description: "Toggle Command Palette", action: () => setPaletteOpen((prev) => !prev) },
    { key: "o", ctrlKey: false, description: "Go to Overview Tab", action: () => handleTabChange("overview") },
    { key: "d", ctrlKey: false, description: "Go to Orders Tab", action: () => handleTabChange("orders") },
    { key: "i", ctrlKey: false, description: "Go to Inventory Tab", action: () => handleTabChange("inventory") },
    { key: "f", ctrlKey: false, description: "Go to Fleet Map Tab", action: () => handleTabChange("fleet") },
    { key: "l", ctrlKey: false, description: "Go to Ledger Khata Tab", action: () => handleTabChange("khata") },
    { key: "a", ctrlKey: false, description: "Go to AI Forecasting Tab", action: () => handleTabChange("ai") },
    { key: "Escape", ctrlKey: false, description: "Close Drawer / Modals / Palette", action: () => {
        closeDrawer();
        setPaletteOpen(false);
      }
    }
  ], [closeDrawer, handleTabChange]);

  // ── Global Event Listener for Keyboard Shortcuts ──
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger shortcuts inside text inputs or textareas (except Escape or Ctrl+K)
      const isInput = ["INPUT", "SELECT", "TEXTAREA"].includes(e.target.tagName) || e.target.isContentEditable;
      
      const matched = shortcuts.find((s) => {
        const keyMatch = s.key.toLowerCase() === e.key.toLowerCase();
        const ctrlMatch = !!s.ctrlKey === (e.ctrlKey || e.metaKey);
        
        if (isInput && s.key !== "Escape" && !(s.key === "k" && s.ctrlKey)) {
          return false;
        }
        
        return keyMatch && ctrlMatch;
      });

      if (matched) {
        e.preventDefault();
        matched.action();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [shortcuts]);

  return (
    <UIContext.Provider
      value={{
        theme,
        toggleTheme,
        drawerOpen,
        drawerContent,
        openDrawer,
        closeDrawer,
        paletteOpen,
        setPaletteOpen,
        toasts,
        addToast,
        removeToast,
        activeTab,
        setActiveTab,
        handleTabChange,
        notifications,
        addNotification,
        markAllAsRead,
        shortcuts
      }}
    >
      {children}
    </UIContext.Provider>
  );
}

export function useUI() {
  const ctx = useContext(UIContext);
  if (!ctx) throw new Error("useUI must be used within a UIProvider");
  return ctx;
}
