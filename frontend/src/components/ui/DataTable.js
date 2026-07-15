"use client";

import React, { useState, useMemo } from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from "lucide-react";

/**
 * DataTable — Enterprise-grade data table per the Design System.
 *
 * Features: sorting, pagination, sticky header, loading skeleton,
 *           integrated empty state, row actions, mobile card layout.
 *
 * Column Definition:
 *   {
 *     key: string,           // data accessor key
 *     label: string,         // header label
 *     align: 'left' | 'center' | 'right',  // column alignment (default: left)
 *     sortable: boolean,     // enable sorting on this column
 *     render: (value, row) => ReactNode,  // custom cell renderer
 *     mobileLabel: string,   // label shown in mobile card view (optional)
 *     hideOnMobile: boolean, // hide this column on mobile cards
 *   }
 *
 * Usage:
 *   <DataTable
 *     columns={columns}
 *     data={rows}
 *     loading={isLoading}
 *     emptyIcon={Package}
 *     emptyTitle="No inventory items"
 *     emptyDescription="Add your first stock item to get started."
 *     emptyAction={<Button>Add Stock</Button>}
 *     pageSize={10}
 *     searchQuery={searchQuery}
 *     searchKeys={['name', 'id']}
 *   />
 */

const ALIGN_CLASSES = {
  left: "text-left",
  center: "text-center",
  right: "text-right tabular-nums",
};

export default function DataTable({
  columns = [],
  data = [],
  loading = false,
  // Empty state
  emptyIcon: EmptyIcon,
  emptyTitle = "No data found",
  emptyDescription = "",
  emptyAction,
  // Pagination
  pageSize = 0, // 0 = no pagination
  // Sorting
  defaultSortKey = null,
  defaultSortDir = "asc",
  // Search filtering
  searchQuery = "",
  searchKeys = [],
  // Styling
  className = "",
  stickyHeader = true,
}) {
  // ── Sorting state ──
  const [sortKey, setSortKey] = useState(defaultSortKey);
  const [sortDir, setSortDir] = useState(defaultSortDir);

  // ── Pagination state ──
  const [currentPage, setCurrentPage] = useState(1);

  // ── Handle sort toggle ──
  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
    setCurrentPage(1);
  };

  // ── Process data: filter → sort → paginate ──
  const processedData = useMemo(() => {
    let result = [...data];

    // Filter by search
    if (searchQuery && searchKeys.length > 0) {
      const q = searchQuery.toLowerCase();
      result = result.filter((row) =>
        searchKeys.some((key) => {
          const val = row[key];
          return val != null && String(val).toLowerCase().includes(q);
        })
      );
    }

    // Sort
    if (sortKey) {
      result.sort((a, b) => {
        const aVal = a[sortKey];
        const bVal = b[sortKey];
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;
        if (typeof aVal === "number" && typeof bVal === "number") {
          return sortDir === "asc" ? aVal - bVal : bVal - aVal;
        }
        const cmp = String(aVal).localeCompare(String(bVal));
        return sortDir === "asc" ? cmp : -cmp;
      });
    }

    return result;
  }, [data, searchQuery, searchKeys, sortKey, sortDir]);

  // ── Pagination ──
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(processedData.length / pageSize)) : 1;
  const paginatedData =
    pageSize > 0
      ? processedData.slice((currentPage - 1) * pageSize, currentPage * pageSize)
      : processedData;

  // ── Loading skeleton ──
  if (loading) {
    return (
      <div className={`bg-[var(--bg-surface)] rounded-[var(--radius-lg)] border border-[var(--border-subtle)] overflow-hidden ${className}`}>
        <div className="animate-pulse">
          {/* Header skeleton */}
          <div className="flex gap-4 p-4 border-b border-[var(--border-subtle)] bg-[var(--bg-app)]">
            {columns.map((_, i) => (
              <div key={i} className="h-3 bg-[var(--border-subtle)] rounded flex-1" />
            ))}
          </div>
          {/* Row skeletons */}
          {Array.from({ length: 5 }).map((_, r) => (
            <div key={r} className="flex gap-4 p-4 border-b border-[var(--border-subtle)]">
              {columns.map((_, c) => (
                <div key={c} className="h-4 bg-[var(--border-subtle)] rounded flex-1" />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Empty state ──
  if (processedData.length === 0) {
    return (
      <div className={`bg-[var(--bg-surface)] rounded-[var(--radius-lg)] border border-[var(--border-subtle)] overflow-hidden ${className}`}>
        <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
          {EmptyIcon && (
            <div className="p-3 rounded-[var(--radius-lg)] bg-[var(--bg-app)] border border-[var(--border-subtle)] mb-4">
              <EmptyIcon size={32} className="text-[var(--text-tertiary)]" />
            </div>
          )}
          <h4 className="text-body font-bold text-[var(--text-primary)]">
            {emptyTitle}
          </h4>
          {emptyDescription && (
            <p className="text-caption text-[var(--text-secondary)] mt-1 max-w-xs">
              {emptyDescription}
            </p>
          )}
          {emptyAction && <div className="mt-4">{emptyAction}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-[var(--bg-surface)] rounded-[var(--radius-lg)] border border-[var(--border-subtle)] overflow-hidden ${className}`}>
      {/* ── Desktop/Tablet Table ── */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[var(--bg-app)] border-b border-[var(--border-subtle)]">
              {columns.map((col) => {
                const align = ALIGN_CLASSES[col.align || "left"];
                const isSorted = sortKey === col.key;
                return (
                  <th
                    key={col.key}
                    className={`p-4 text-label text-[var(--text-secondary)] select-none ${align} ${
                      stickyHeader ? "sticky top-0 bg-[var(--bg-app)] z-10" : ""
                    } ${col.sortable ? "cursor-pointer hover:text-[var(--text-primary)] transition-colors" : ""}`}
                    onClick={() => col.sortable && handleSort(col.key)}
                  >
                    <span className="inline-flex items-center gap-1">
                      {col.label}
                      {col.sortable && (
                        <span className="inline-flex flex-col">
                          {isSorted ? (
                            sortDir === "asc" ? (
                              <ChevronUp size={14} />
                            ) : (
                              <ChevronDown size={14} />
                            )
                          ) : (
                            <ChevronsUpDown size={14} className="opacity-40" />
                          )}
                        </span>
                      )}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-subtle)]">
            {paginatedData.map((row, rowIdx) => (
              <tr
                key={row.id || rowIdx}
                className="hover:bg-[var(--bg-app)] transition-colors"
                style={{ transitionDuration: "var(--duration-fast)" }}
              >
                {columns.map((col) => {
                  const align = ALIGN_CLASSES[col.align || "left"];
                  const value = row[col.key];
                  return (
                    <td
                      key={col.key}
                      className={`p-4 text-caption text-[var(--text-primary)] font-medium ${align}`}
                    >
                      {col.render ? col.render(value, row) : value}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Mobile Card View ── */}
      <div className="sm:hidden divide-y divide-[var(--border-subtle)]">
        {paginatedData.map((row, rowIdx) => (
          <div key={row.id || rowIdx} className="p-4 space-y-3">
            {columns
              .filter((col) => !col.hideOnMobile)
              .map((col) => {
                const value = row[col.key];
                return (
                  <div key={col.key} className="flex items-center justify-between gap-2">
                    <span className="text-label text-[var(--text-secondary)]">
                      {col.mobileLabel || col.label}
                    </span>
                    <span className="text-caption text-[var(--text-primary)] font-bold text-right">
                      {col.render ? col.render(value, row) : value}
                    </span>
                  </div>
                );
              })}
          </div>
        ))}
      </div>

      {/* ── Pagination Footer ── */}
      {pageSize > 0 && totalPages > 1 && (
        <div className="flex items-center justify-between p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-app)]">
          <p className="text-caption text-[var(--text-secondary)]">
            Showing {(currentPage - 1) * pageSize + 1}–
            {Math.min(currentPage * pageSize, processedData.length)} of{" "}
            {processedData.length}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-[var(--radius-md)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-ring"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-label text-[var(--text-primary)] px-3">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-[var(--radius-md)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-ring"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
