"use client";

import React, { useState } from "react";
import { Wallet, Search } from "lucide-react";
import { DataTable, StatusBadge, Button, Input } from "@/components/ui";
import { Page, PageHeader } from "@/components/ui/PageLayout";
import { useDashboardData } from "@/context/DashboardDataContext";
import { useUI } from "@/context/UIContext";
import { RetailerDrawerContent } from "@/components/dashboard/DrawerContents";

/**
 * KhataTab — Retailer Ledger Dashboard
 * Refactored: Consumes UIContext & DashboardDataContext. Click ID to open Right Drawer.
 */
export function KhataTab({ setShowPaymentModal }) {
  const { retailers, fetchRetailers } = useDashboardData();
  const { openDrawer } = useUI();
  const [searchQuery, setSearchQuery] = useState("");

  const columns = [
    {
      key: "id",
      label: "Retailer ID",
      align: "left",
      sortable: true,
      render: (val, row) => (
        <button
          onClick={() => openDrawer(<RetailerDrawerContent retailer={row} />)}
          className="font-mono text-xs font-bold text-[var(--text-primary)] hover:underline text-left cursor-pointer focus-ring rounded"
          title="Click to view details"
        >
          {String(val || "").slice(0, 8)}
        </button>
      ),
    },
    {
      key: "shopName",
      label: "Shop Details",
      align: "left",
      sortable: true,
      render: (val, row) => (
        <div>
          <p className="font-bold text-[var(--text-primary)]">{val || row.name}</p>
          <p className="text-[11px] text-[var(--text-secondary)] font-medium">
            {row.phone}
          </p>
        </div>
      ),
    },
    {
      key: "lastPaid",
      label: "Last Payment Date",
      align: "center",
      sortable: true,
      render: (val) => val || "—",
    },
    {
      key: "balance",
      label: "Ledger Balance",
      align: "right",
      sortable: true,
      render: (val) => {
        const num = Number(val || 0);
        return (
          <span
            className={`font-bold tabular-nums ${
              num > 0
                ? "text-[var(--danger-text)]"
                : "text-[var(--success-text)]"
            }`}
          >
            {num > 0
              ? `₹${num.toLocaleString()}`
              : `Advance: ₹${Math.abs(num).toLocaleString()}`}
          </span>
        );
      },
    },
    {
      key: "actions",
      label: "Reminders",
      align: "center",
      hideOnMobile: true,
      render: (_, row) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            console.log(`Reminder sent to ${row.shopName || row.name}`)
          }
        >
          Send WhatsApp
        </Button>
      ),
    },
  ];

  return (
    <Page>
      <PageHeader
        title="Ledger Balance Dashboard"
        description="Manage outstanding retailer payments and transaction limits."
      >
        <Button
          variant="primary"
          size="md"
          onClick={() => setShowPaymentModal(true)}
        >
          + Record Payment
        </Button>
      </PageHeader>

      <div className="space-y-4">
        {/* Search filter input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
          <Input
            type="text"
            placeholder="Search retailers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <DataTable
          columns={columns}
          data={retailers}
          searchQuery={searchQuery}
          searchKeys={["shopName", "name", "id", "phone"]}
          emptyIcon={Wallet}
          emptyTitle="No retailer accounts"
          emptyDescription="Add retailers to start tracking their credit ledger."
          defaultSortKey="balance"
          defaultSortDir="desc"
          pageSize={10}
        />
      </div>
    </Page>
  );
}
