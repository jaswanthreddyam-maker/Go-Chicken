"use client";

import React from "react";
import { Package, Phone, DollarSign, Activity, FileText, ShoppingBag, Clock } from "lucide-react";
import { StatusBadge, Button, QuoteSummaryCard } from "@/components/ui";
import EventTimeline from "@/components/ui/EventTimeline";
import { useDashboardData } from "@/context/DashboardDataContext";

/**
 * OrderDrawerContent
 * Content rendered in Right Drawer for detailed Order view.
 */
export function OrderDrawerContent({ order }) {
  if (!order) return null;

  const orderTime = order.created_at
    ? new Date(order.created_at).toLocaleString()
    : "Just now";

  // Reusable Timeline Events matching the order's current state
  const timelineEvents = [
    {
      title: "Order Received",
      description: `Ingested successfully via ${order.order_source === "ollama" ? "LLM parse (Ollama)" : "Regex expression"}.`,
      timestamp: orderTime,
      status: "success",
    },
    {
      title: "Pricing Confirmed",
      description: `Matched with live rate card at ₹${(order.total_amount / order.quantity_kg || 180).toFixed(0)}/kg.`,
      timestamp: orderTime,
      status: "success",
    },
    {
      title: "Fulfillment Pipeline",
      description: order.status === "pending"
        ? "Awaiting dispatcher processing approval."
        : `Marked as ${order.status.toUpperCase()} in system outbox.`,
      timestamp: order.status !== "pending" ? "Updated" : "",
      status: order.status === "pending" ? "pending" : "success",
    },
    {
      title: "Delivery Status",
      description: order.status === "delivered"
        ? "Completed! WhatsApp confirmation receipt broadcasted."
        : "Awaiting final hand-off confirmation.",
      timestamp: order.status === "delivered" ? "Delivered" : "",
      status: order.status === "delivered" ? "success" : "neutral",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Overview Block */}
      <div className="bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-5 space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-label text-[var(--text-secondary)]">Fulfillment Status</span>
          <StatusBadge status={order.status} />
        </div>
        <div className="h-px bg-[var(--border-subtle)]" />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Product</p>
            <p className="text-body font-bold text-[var(--text-primary)] uppercase mt-0.5">{order.item_type}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Quantity</p>
            <p className="text-body font-bold text-[var(--text-primary)] mt-0.5">{order.quantity_kg} kg</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Price per KG</p>
            <p className="text-body font-bold text-[var(--text-primary)] mt-0.5">₹{(order.total_amount / order.quantity_kg || 180).toFixed(0)}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Invoice Subtotal</p>
            <p className="text-body font-extrabold text-[var(--text-primary)] mt-0.5">
              ₹{(order.total_amount || order.quantity_kg * 180).toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Customer Info */}
      <div className="space-y-3">
        <h4 className="text-caption font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
          <Phone size={14} className="text-[var(--text-secondary)]" /> Customer Connection
        </h4>
        <div className="border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-4 space-y-2">
          <div className="flex justify-between text-caption">
            <span className="text-[var(--text-secondary)]">WhatsApp Phone</span>
            <span className="font-bold text-[var(--text-primary)]">{order.phone_number || "Manual Input"}</span>
          </div>
          <div className="flex justify-between text-caption">
            <span className="text-[var(--text-secondary)]">NLP Model Source</span>
            <span className="font-mono font-bold text-[var(--text-primary)]">
              {order.order_source === "ollama" ? "llama3-7b-nomic" : "system-regex"}
            </span>
          </div>
        </div>
      </div>

      {/* Event Timeline */}
      <div className="space-y-3">
        <h4 className="text-caption font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
          <Activity size={14} className="text-[var(--text-secondary)]" /> Audit Trail Pipeline
        </h4>
        <EventTimeline events={timelineEvents} />
      </div>
    </div>
  );
}

/**
 * RetailerDrawerContent
 * Content rendered in Right Drawer for detailed Retailer view.
 */
export function RetailerDrawerContent({ retailer }) {
  const { ordersList } = useDashboardData();
  if (!retailer) return null;

  const isOutstanding = retailer.balance > 0;

  // Derive ledger history dynamically from live orders and balance
  const retailerOrders = (ordersList || []).filter(
    (o) => o.phone_number && (o.phone_number === retailer.phone || o.phone_number.includes(retailer.phone || ""))
  );

  const ledgerHistory = retailerOrders.map((o) => ({
    title: `Order #${String(o.id || "").slice(0, 8)} (${o.item_type})`,
    description: `Quantity: ${o.quantity_kg}kg · Status: ${o.status.toUpperCase()}`,
    timestamp: o.created_at ? new Date(o.created_at).toLocaleDateString() : "Recent",
    status: o.status === "delivered" ? "success" : "pending",
  }));

  ledgerHistory.push({
    title: isOutstanding ? "Outstanding Debit Due" : "Account Settled / In Credit",
    description: isOutstanding
      ? `Current balance of ₹${retailer.balance.toLocaleString()} pending.`
      : `No outstanding balance due.`,
    timestamp: retailer.lastPaid || "Active",
    status: isOutstanding ? "warning" : "success",
  });

  return (
    <div className="space-y-6">
      {/* Profile Overview */}
      <div className="bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-5 space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-label text-[var(--text-secondary)]">Retailer Account ID</span>
          <span className="font-mono text-xs font-bold">{retailer.id}</span>
        </div>
        <div className="h-px bg-[var(--border-subtle)]" />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Shop Name</p>
            <p className="text-body font-bold text-[var(--text-primary)] mt-0.5">{retailer.name || retailer.shopName}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Phone</p>
            <p className="text-body font-bold text-[var(--text-primary)] mt-0.5">{retailer.phone}</p>
          </div>
          <div className="col-span-2">
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Current Balance</p>
            <p
              className={`text-2xl font-black mt-0.5 ${
                isOutstanding ? "text-[var(--danger-text)]" : "text-[var(--success-text)]"
              }`}
            >
              {retailer.balance > 0
                ? `₹${retailer.balance.toLocaleString()}`
                : `Credit Advance: ₹${Math.abs(retailer.balance).toLocaleString()}`}
            </p>
          </div>
        </div>
      </div>

      {/* Ledger History */}
      <div className="space-y-3">
        <h4 className="text-caption font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
          <Clock size={14} className="text-[var(--text-secondary)]" /> Ledger Statement Events
        </h4>
        <EventTimeline events={ledgerHistory} />
      </div>
    </div>
  );
}

/**
 * QuoteDrawerContent
 * Content rendered in Right Drawer for detailed Quote view.
 */
export function QuoteDrawerContent({ quote }) {
  const { retailers, approveQuote, rejectQuote, convertQuote } = useDashboardData();
  
  if (!quote) return null;

  const retailer = retailers.find(r => r.id === quote.customer_id);
  const retailerName = retailer ? retailer.name : "Retailer " + quote.customer_id.toString().slice(0, 8);

  const quoteTime = quote.created_at
    ? new Date(quote.created_at).toLocaleString()
    : "Just now";

  const expiryTime = quote.expires_at
    ? new Date(quote.expires_at).toLocaleString()
    : "Never";

  // Reusable Timeline Events matching the quote's current state
  const timelineEvents = [
    {
      title: "Quote Prepared",
      description: `Created successfully as version ${quote.quote_version} in system.`,
      timestamp: quoteTime,
      status: "success",
    },
    {
      title: "Pricing Validation",
      description: quote.status === "PENDING_APPROVAL"
        ? "Exceeds ₹100,000 auto-approval threshold. Pending manual reviewer validation."
        : "Approved for checkout conversion.",
      timestamp: quoteTime,
      status: quote.status === "PENDING_APPROVAL" ? "pending" : "success",
    },
    {
      title: "Fulfillment Conversion",
      description: quote.status === "CONVERTED"
        ? `Order successfully created. Outbox event dispatched.`
        : quote.status === "REJECTED"
        ? "Quote rejected by administration."
        : "Awaiting retailer conversion request.",
      timestamp: quote.status === "CONVERTED" || quote.status === "REJECTED" ? "Updated" : "",
      status: quote.status === "CONVERTED"
        ? "success"
        : quote.status === "REJECTED"
        ? "warning"
        : "neutral",
    },
  ];

  // Helper for source coloring
  const getSourceBadgeClass = (source) => {
    switch (source) {
      case "CUSTOMER_OVERRIDE":
        return "text-green-700 bg-green-50 border border-green-200 px-1.5 py-0.5 rounded text-[10px] font-bold";
      case "TIER_PRICEBOOK":
        return "text-blue-700 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded text-[10px] font-bold";
      case "ZONE":
        return "text-orange-700 bg-orange-50 border border-orange-200 px-1.5 py-0.5 rounded text-[10px] font-bold";
      default:
        return "text-neutral-700 bg-neutral-50 border border-neutral-200 px-1.5 py-0.5 rounded text-[10px] font-bold";
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Block */}
      <div className="bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-5 space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <span className="text-label text-[var(--text-secondary)]">Quote Reference</span>
            <h4 className="font-mono text-sm font-black text-[var(--text-primary)] mt-0.5">{quote.quote_number}</h4>
          </div>
          <StatusBadge status={quote.status.toLowerCase()} label={quote.status} />
        </div>
        <div className="h-px bg-[var(--border-subtle)]" />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Retailer Account</p>
            <p className="text-body font-bold text-[var(--text-primary)] mt-0.5">{retailerName}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Delivery Zone</p>
            <p className="text-body font-bold text-[var(--text-primary)] mt-0.5 uppercase">{quote.delivery_zone || "None"}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Created At</p>
            <p className="text-caption font-bold text-[var(--text-primary)] mt-0.5">{quoteTime}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Expires At</p>
            <p className="text-caption font-bold text-[var(--text-primary)] mt-0.5">{expiryTime}</p>
          </div>
        </div>
      </div>

      {/* Quote Items List */}
      <div className="space-y-3">
        <h4 className="text-caption font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
          <Package size={14} className="text-[var(--text-secondary)]" /> Line Items ({quote.items?.length || 0})
        </h4>
        <div className="border border-[var(--border-subtle)] rounded-[var(--radius-lg)] overflow-hidden divide-y divide-[var(--border-subtle)] bg-white">
          {quote.items && quote.items.map((item, idx) => (
            <div key={item.id || idx} className="p-4 flex flex-col gap-2">
              <div className="flex justify-between items-start">
                <div>
                  <span className="font-extrabold text-xs text-[var(--text-primary)] uppercase">{item.sku}</span>
                  <span className="text-[10px] text-[var(--text-secondary)] block mt-0.5 font-bold">
                    {item.quantity_kg} kg @ ₹{item.unit_price}/kg
                  </span>
                </div>
                <span className="text-xs font-black text-[var(--text-primary)] tabular-nums">
                  ₹{Number(item.line_total).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-start">
                <span className={getSourceBadgeClass(item.pricing_source)}>
                  {item.pricing_source.replace("_", " ")}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Financial Summary Breakdown */}
      <QuoteSummaryCard 
        subtotal={quote.subtotal_amount} 
        surcharge={quote.zone_surcharge_amount} 
        total={quote.total_amount} 
      />

      {/* Audit Timeline */}
      <div className="space-y-3">
        <h4 className="text-caption font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
          <Activity size={14} className="text-[var(--text-secondary)]" /> Quote Timeline State
        </h4>
        <EventTimeline events={timelineEvents} />
      </div>

      {/* Action Footer Button Group */}
      {(quote.status === "PENDING_APPROVAL" || quote.status === "APPROVED") && (
        <div className="flex gap-3 pt-2 border-t border-[var(--border-subtle)]">
          {quote.status === "PENDING_APPROVAL" && (
            <>
              <Button
                variant="primary"
                className="flex-1"
                onClick={() => approveQuote(quote.id)}
              >
                Approve Quote
              </Button>
              <Button
                variant="secondary"
                className="flex-1 text-[var(--danger-text)] border-[var(--danger-border)] hover:bg-red-50/50"
                onClick={() => rejectQuote(quote.id)}
              >
                Reject
              </Button>
            </>
          )}
          {quote.status === "APPROVED" && (
            <Button
              variant="primary"
              className="w-full"
              onClick={() => convertQuote(quote.id)}
            >
              Convert to Order
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
