"use client";

import React, { useState } from "react";
import { Edit3, Clock, Activity, RefreshCw, Search, Package } from "lucide-react";
import { Button, DataTable, StatusBadge, Toast, ErrorBanner } from "@/components/ui";
import { Page, PageHeader, PageContent, PageSection } from "@/components/ui/PageLayout";
import { Form, Input } from "@/components/ui/FormSystem";
import { useDashboardData } from "@/context/DashboardDataContext";
import { useUI } from "@/context/UIContext";
import { OrderDrawerContent } from "@/components/dashboard/DrawerContents";

/**
 * OrdersTab — Live Orders & Rate Card Controls
 * Refactored: Consumes UIContext & DashboardDataContext. Click ID to open Right Drawer.
 */
export function OrdersTab() {
  const {
    ordersList,
    productPrices,
    isLoadingOrders,
    isLoadingPrices,
    ordersError,
    pricesError,
    handleStatusToggle,
    handleUpdateRate,
    fetchPrices,
    fetchOrders,
  } = useDashboardData();

  const { openDrawer, toasts, addToast, removeToast } = useUI();
  const [editingPrice, setEditingPrice] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Columns definition
  const columns = [
    {
      key: "id",
      label: "Order ID",
      align: "left",
      sortable: true,
      render: (val, row) => (
        <button
          onClick={() => openDrawer(<OrderDrawerContent order={row} />)}
          className="font-mono text-xs font-bold text-[var(--text-primary)] hover:underline text-left cursor-pointer focus-ring rounded"
          title="Click to view details"
        >
          {String(val || "").slice(0, 8)}
        </button>
      ),
    },
    {
      key: "phone_number",
      label: "Phone Number",
      align: "left",
      sortable: true,
      render: (val) => val || "Manual Ingestion",
    },
    {
      key: "item_type",
      label: "Item Type",
      align: "left",
      sortable: true,
      render: (val) => <span className="font-extrabold">{val}</span>,
    },
    {
      key: "quantity_kg",
      label: "Quantity",
      align: "right",
      sortable: true,
      render: (val) => (
        <span className="bg-[var(--bg-app)] text-[var(--text-primary)] font-bold px-2 py-1 rounded border border-[var(--border-subtle)] tabular-nums">
          {val} kg
        </span>
      ),
    },
    {
      key: "total_amount",
      label: "Total Amount",
      align: "right",
      sortable: true,
      render: (val, row) => {
        const amt = val || row.quantity_kg * 180;
        return (
          <span className="font-extrabold text-[var(--text-primary)] tabular-nums">
            ₹{amt.toLocaleString()}
          </span>
        );
      },
    },
    {
      key: "order_source",
      label: "Source",
      align: "center",
      sortable: true,
      render: (val) => (
        <StatusBadge
          status={val === "ollama" ? "active" : "inactive"}
          label={val === "ollama" ? "🤖 Ollama" : "📐 Regex"}
        />
      ),
    },
    {
      key: "status",
      label: "Status & Actions",
      align: "center",
      render: (val, row) => (
        <div className="flex items-center justify-center gap-2">
          {val === "pending" && (
            <>
              <StatusBadge status="pending" />
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleStatusToggle(row.id, "processing")}
              >
                <Activity className="w-3.5 h-3.5 mr-1" /> Process
              </Button>
            </>
          )}
          {val === "processing" && (
            <>
              <StatusBadge status="processing" className="animate-pulse" />
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleStatusToggle(row.id, "delivered")}
              >
                Mark Delivered
              </Button>
            </>
          )}
          {val === "delivered" && <StatusBadge status="delivered" />}
          {val === "cancelled" && <StatusBadge status="cancelled" />}
          {val !== "pending" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleStatusToggle(row.id, "pending")}
              title="Reset order status"
              className="px-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <Page>
      {/* Live Rate Card Section */}
      <PageSection title="Live Rate Card Control" description="Changes update immediately across the system, syncing with WhatsApp bot price lookups.">
        <div className="bg-[var(--bg-surface)] rounded-[var(--radius-lg)] border border-[var(--border-subtle)] p-4 sm:p-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6">
          {isLoadingPrices ? (
            <div className="col-span-3 space-y-2">
              <div className="h-16 bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] animate-pulse" />
            </div>
          ) : pricesError ? (
            <div className="col-span-3">
              <ErrorBanner message={pricesError} onRetry={() => fetchPrices(false)} />
            </div>
          ) : (
            productPrices.map((item, idx) => (
              <div
                key={idx}
                className="bg-[var(--bg-surface)] rounded-[var(--radius-lg)] p-5 border border-[var(--border-subtle)] transition-all hover:border-[var(--border-strong)] relative"
                style={{ transitionDuration: "var(--duration-fast)" }}
              >
                <div className="flex justify-between items-start mb-3">
                  <span className="text-label px-2 py-1 rounded bg-[var(--bg-app)] text-[var(--text-primary)] border border-[var(--border-subtle)]">
                    {item.item_type}
                  </span>
                  <span className="text-label text-[var(--text-secondary)]">
                    INR / kg
                  </span>
                </div>

                {editingPrice && editingPrice.item_type === item.item_type ? (
                  <Form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleUpdateRate(item.item_type, editingPrice.val);
                      setEditingPrice(null);
                    }}
                    className="mt-2 space-y-3"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-xl font-bold text-[var(--text-secondary)]">₹</span>
                      <Input
                        type="number"
                        value={editingPrice.val}
                        onChange={(e) =>
                          setEditingPrice({ ...editingPrice, val: e.target.value })
                        }
                        autoFocus
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button type="submit" variant="primary" size="sm" className="flex-1">
                        Save Rate
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setEditingPrice(null)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </Form>
                ) : (
                  <div className="mt-2 flex items-baseline justify-between">
                    <div>
                      <h4 className="text-display font-black text-[var(--text-primary)] tracking-tight">
                        ₹{item.price_per_kg}
                      </h4>
                      <p className="text-label text-[var(--text-secondary)] mt-1">
                        Live Inquiries
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setEditingPrice({
                          item_type: item.item_type,
                          val: item.price_per_kg.toString(),
                        })
                      }
                    >
                      <Edit3 className="w-3.5 h-3.5 mr-1" /> Edit
                    </Button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </PageSection>

      {/* Live Order Feed Section */}
      <PageSection title="Live Order Feed" description="Fulfillment triggers instant confirmation messages directly to registered retailers.">
        <div className="space-y-4">
          <div className="flex justify-between items-center gap-4 flex-col sm:flex-row">
            {/* Search filter input */}
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
              <Input
                type="text"
                placeholder="Search orders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchOrders(false)}
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Refresh Feed
            </Button>
          </div>

          {toasts &&
            toasts.map((t) => (
              <Toast
                key={t.id}
                message={t.message}
                type={t.type}
                onClose={() => removeToast(t.id)}
              />
            ))}

          <DataTable
            columns={columns}
            data={ordersList}
            loading={isLoadingOrders}
            emptyIcon={Package}
            emptyTitle="No live orders found"
            emptyDescription="Live orders from WhatsApp and Ollama streams will display here."
            pageSize={10}
            searchQuery={searchQuery}
            searchKeys={["phone_number", "item_type", "id"]}
          />
        </div>
      </PageSection>
    </Page>
  );
}
