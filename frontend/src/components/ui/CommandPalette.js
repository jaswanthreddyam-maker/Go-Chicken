"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { Search, Compass, ShieldAlert, Zap, CornerDownLeft } from "lucide-react";
import { useUI } from "@/context/UIContext";
import { useDashboardData } from "@/context/DashboardDataContext";
import SearchService from "@/services/SearchService";

/**
 * CommandPalette — Triggered by Ctrl+K.
 * Fuzzy searches routes, live records, and dashboard action triggers.
 */
export default function CommandPalette() {
  const {
    paletteOpen,
    setPaletteOpen,
    handleTabChange,
    openDrawer,
    addToast
  } = useUI();

  const {
    ordersList,
    retailers,
    trucks,
    quotesList
  } = useDashboardData();

  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // ── Retrieve fuzzy search results ──
  const results = useMemo(() => {
    return SearchService.query(query, {
      orders: ordersList,
      retailers,
      trucks,
      quotes: quotesList
    });
  }, [query, ordersList, retailers, trucks, quotesList]);

  // Reset selected item when query changes
  useEffect(() => {
    const t = setTimeout(() => setSelectedIndex(0), 0);
    return () => clearTimeout(t);
  }, [query]);

  // Focus input on open
  useEffect(() => {
    if (paletteOpen) {
      const t = setTimeout(() => {
        setQuery("");
        inputRef.current?.focus();
      }, 0);
      return () => clearTimeout(t);
    }
  }, [paletteOpen]);

  // ── Keyboard navigation inside the palette ──
  const handleKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, results.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + results.length) % Math.max(1, results.length));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results[selectedIndex]) {
        handleSelect(results[selectedIndex]);
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      setPaletteOpen(false);
    }
  };

  const handleSelect = (item) => {
    setPaletteOpen(false);
    
    if (item.type === "nav") {
      handleTabChange(item.path);
      addToast(`Navigated to ${item.title}`, "info");
    } else if (item.type === "action") {
      if (item.actionId === "refresh_dashboard") {
        window.dispatchEvent(new CustomEvent("gc_refresh_dashboard"));
      } else {
        // Dispatch global event for modal trigger
        window.dispatchEvent(new CustomEvent(`gc_trigger_${item.actionId}`));
      }
    } else if (item.type === "record") {
      handleTabChange(item.tab);
      // Dispatch custom event to trigger detail drawer for the clicked record
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent(`gc_open_drawer_${item.category.toLowerCase()}`, {
          detail: item.record
        }));
      }, 100);
    }
  };

  if (!paletteOpen) return null;

  return (
    <div
      className="fixed inset-0 flex items-start justify-center pt-[15vh] p-4 animate-in fade-in duration-150"
      style={{
        backgroundColor: "rgba(0, 0, 0, 0.4)",
        backdropFilter: "blur(1px)",
        zIndex: "var(--z-popover)",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) setPaletteOpen(false);
      }}
    >
      <div
        className="w-full max-w-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] flex flex-col overflow-hidden shadow-2xl animate-in scale-in duration-300"
        onKeyDown={handleKeyDown}
      >
        {/* Search Input */}
        <div className="flex items-center px-4 border-b border-[var(--border-subtle)]">
          <Search size={18} className="text-[var(--text-tertiary)] flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search orders, retailers, fleet, actions... (ESC to close)"
            className="w-full h-12 px-3 text-caption text-[var(--text-primary)] font-medium placeholder:text-[var(--text-tertiary)] bg-transparent outline-none border-none"
          />
        </div>

        {/* Results List */}
        <div ref={listRef} className="max-h-72 overflow-y-auto divide-y divide-[var(--border-subtle)] p-2">
          {results.length > 0 ? (
            results.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={idx}
                  onClick={() => handleSelect(item)}
                  className={`flex items-center justify-between p-3 rounded-[var(--radius-md)] cursor-pointer transition-colors ${
                    isSelected ? "bg-[var(--bg-elevated)]" : "hover:bg-[var(--bg-app)]"
                  }`}
                  style={{ transitionDuration: "var(--duration-fast)" }}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    {item.type === "nav" && <Compass size={16} className="text-[var(--text-secondary)]" />}
                    {item.type === "action" && <Zap size={16} className="text-amber-600" />}
                    {item.type === "record" && <ShieldAlert size={16} className="text-[var(--text-secondary)]" />}
                    <div className="min-w-0">
                      <p className="text-caption font-bold text-[var(--text-primary)] truncate">
                        {item.title}
                      </p>
                      <p className="text-[10px] text-[var(--text-secondary)] font-medium truncate">
                        {item.description}
                      </p>
                    </div>
                  </div>
                  {isSelected && (
                    <span className="text-[9px] font-bold text-[var(--text-tertiary)] uppercase flex items-center gap-0.5">
                      Select <CornerDownLeft size={10} />
                    </span>
                  )}
                </div>
              );
            })
          ) : (
            <p className="text-caption text-[var(--text-secondary)] text-center py-8 font-medium">
              No results match &quot;{query}&quot;
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
