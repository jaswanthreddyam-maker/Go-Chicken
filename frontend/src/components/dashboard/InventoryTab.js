"use client";

import React, { useState, useEffect } from 'react';
import { Package, AlertTriangle, Truck, PlusCircle, Trash2, Sliders, RefreshCw, Clock } from 'lucide-react';
import { Button, Modal, DataTable, KPIStatCard, StatusBadge } from '@/components/ui';
import { Page, PageHeader, PageContent, PageSection, PageActions } from '@/components/ui/PageLayout';
import { Form, FormField, Label, Input, Select } from '@/components/ui/FormSystem';
import { useDashboardData } from '@/context/DashboardDataContext';

const getApiBase = () => {
  let url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      url = "https://go-chicken.vercel.app/api/v1";
    } else {
      url = "http://localhost:8000/api/v1";
    }
  }
  url = url.replace(/\/+$/, "");
  if (!url.endsWith("/api/v1")) url += "/api/v1";
  return url;
};
const API_BASE = getApiBase();

export function InventoryTab({ addToast }) {
  const { inventoryList, inventoryTxns, isLoadingInventory, fetchAll } = useDashboardData();
  const [activeModal, setActiveModal] = useState(null); // 'purchase' | 'waste' | 'adjustment' | null

  // Modal Form States
  const [formItem, setFormItem] = useState("BROILER");
  const [formQuantity, setFormQuantity] = useState("");
  const [formRemarks, setFormRemarks] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);



  const handleActionSubmit = async (e) => {
    e.preventDefault();
    if (!formQuantity || isNaN(formQuantity) || Number(formQuantity) === 0) {
      if (addToast) addToast("Please enter a valid non-zero quantity", "error");
      return;
    }
    setIsSubmitting(true);

    try {
      const headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": "00000000-0000-0000-0000-000000000001",
      };
      let endpoint = "";
      let payload = { item: formItem, quantity: Number(formQuantity) };

      if (activeModal === "purchase") {
        endpoint = "/inventory/purchase";
        payload.remarks = formRemarks || "Supplier Purchase";
      } else if (activeModal === "waste") {
        endpoint = "/inventory/waste";
        payload.quantity = Math.abs(Number(formQuantity));
        payload.reason = formRemarks || "Mortality / dead birds";
      } else if (activeModal === "adjustment") {
        endpoint = "/inventory/adjustment";
        payload.remarks = formRemarks || "Manual stock audit adjustment";
      }

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        if (addToast) addToast(`Successfully recorded ${activeModal.toUpperCase()}!`, "success");
        setActiveModal(null);
        setFormQuantity("");
        setFormRemarks("");
        fetchAll(true);
      } else {
        const errJson = await response.json().catch(() => ({}));
        if (addToast) addToast(errJson.detail || "Action failed", "error");
      }
    } catch (err) {
      console.error("Action error:", err);
      if (addToast) addToast("Network error executing inventory action", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Compute summary metrics
  const totalAvailable = inventoryList.reduce((acc, it) => acc + Number(it.available || 0), 0);
  const totalReserved = inventoryList.reduce((acc, it) => acc + Number(it.reserved || 0), 0);
  const totalLoaded = inventoryList.reduce((acc, it) => acc + Number(it.loaded || 0), 0);
  const lowStockCount = inventoryList.filter(it => it.status === "Low" || Number(it.available) < Number(it.minimum)).length;

  // Snapshot Table columns definition
  const snapshotColumns = [
    {
      key: "item",
      label: "Poultry Item",
      align: "left",
      sortable: true,
      render: (val) => (
        <span className="font-extrabold text-[var(--text-primary)] uppercase tracking-wide">
          {val}
        </span>
      ),
    },
    {
      key: "available",
      label: "Available",
      align: "right",
      sortable: true,
      render: (val) => `${Number(val || 0).toLocaleString()} KG`,
    },
    {
      key: "reserved",
      label: "Reserved",
      align: "right",
      sortable: true,
      render: (val) => (
        <span className="font-bold text-amber-700">
          {Number(val || 0).toLocaleString()} KG
        </span>
      ),
    },
    {
      key: "loaded",
      label: "Loaded",
      align: "right",
      sortable: true,
      render: (val) => (
        <span className="font-bold text-blue-700">
          {Number(val || 0).toLocaleString()} KG
        </span>
      ),
    },
    {
      key: "minimum",
      label: "Minimum Stock",
      align: "right",
      sortable: true,
      render: (val) => `${Number(val || 0).toLocaleString()} KG`,
    },
    {
      key: "status",
      label: "Status",
      align: "center",
      sortable: true,
      render: (val, row) => {
        const isLow = val === "Low" || Number(row.available) < Number(row.minimum);
        return <StatusBadge status={isLow ? "low" : "healthy"} />;
      },
    },
  ];

  // Ledger Table columns definition
  const ledgerColumns = [
    {
      key: "created_at",
      label: "Timestamp",
      align: "center",
      sortable: true,
      render: (val) => <span className="font-mono text-[11px] text-[var(--text-secondary)]">{val}</span>,
    },
    {
      key: "transaction_type",
      label: "Transaction Type",
      align: "left",
      sortable: true,
      render: (val) => <StatusBadge status={val} />,
    },
    {
      key: "quantity",
      label: "Quantity Change",
      align: "right",
      sortable: true,
      render: (val) => {
        const isPositive = Number(val) > 0;
        return (
          <span className={`font-extrabold font-mono ${isPositive ? "text-emerald-700" : "text-red-700"}`}>
            {isPositive ? `+${val}` : `${val}`} KG
          </span>
        );
      },
    },
    {
      key: "remarks",
      label: "Remarks & Reference",
      align: "left",
      render: (val) => val || "—",
    },
  ];

  return (
    <Page>
      <PageHeader
        title="Enterprise Inventory Subsystem"
        description="Real-time multi-state stock snapshot & immutable transaction ledger."
      >
        <PageActions>
          <Button
            variant="primary"
            size="md"
            onClick={() => { setActiveModal("purchase"); setFormRemarks("Morning Supplier Purchase"); }}
          >
            <PlusCircle className="w-4 h-4 mr-1.5" /> Purchase Stock
          </Button>
          <Button
            variant="destructive"
            size="md"
            onClick={() => { setActiveModal("waste"); setFormRemarks("Mortality / dead birds"); }}
          >
            <Trash2 className="w-4 h-4 mr-1.5" /> Record Waste
          </Button>
          <Button
            variant="outline"
            size="md"
            onClick={() => { setActiveModal("adjustment"); setFormRemarks("Manual weigh scale audit"); }}
          >
            <Sliders className="w-4 h-4 mr-1.5" /> Adjustment
          </Button>
          <Button
            variant="ghost"
            size="md"
            onClick={() => fetchAll(false)}
            title="Refresh Inventory"
            className="px-2"
          >
            <RefreshCw className={`w-4 h-4 ${isLoadingInventory ? "animate-spin" : ""}`} />
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPIStatCard
            title="Available Stock"
            value={`${totalAvailable.toLocaleString()} KG`}
            icon={Package}
            subtitle="Ready for order reservation"
            loading={isLoadingInventory}
          />
          <KPIStatCard
            title="Reserved Stock"
            value={`${totalReserved.toLocaleString()} KG`}
            icon={Clock}
            subtitle="Locked by confirmed orders"
            loading={isLoadingInventory}
          />
          <KPIStatCard
            title="Loaded Stock"
            value={`${totalLoaded.toLocaleString()} KG`}
            icon={Truck}
            subtitle="In transit on delivery trucks"
            loading={isLoadingInventory}
          />
          <KPIStatCard
            title="Low Stock Alerts"
            value={`${lowStockCount} ${lowStockCount === 1 ? "Item" : "Items"}`}
            icon={AlertTriangle}
            subtitle="Below minimum reorder threshold"
            trend={lowStockCount > 0 ? "down" : "neutral"}
            alert={lowStockCount > 0}
            loading={isLoadingInventory}
          />
        </div>

        {/* Main Inventory Snapshot Table */}
        <PageSection title="Current Inventory Snapshot">
          <DataTable
            columns={snapshotColumns}
            data={inventoryList}
            loading={isLoadingInventory}
            emptyIcon={Package}
            emptyTitle="No inventory data found"
            emptyDescription="There are no products listed in your warehouse snapshot."
            pageSize={10}
          />
        </PageSection>

        {/* Immutable Transaction Ledger Section */}
        <PageSection title="Immutable Inventory Ledger">
          <DataTable
            columns={ledgerColumns}
            data={inventoryTxns}
            loading={isLoadingInventory}
            emptyIcon={Clock}
            emptyTitle="No transactions logged"
            emptyDescription="Inventory modifications and stock movements will appear here."
            pageSize={10}
          />
        </PageSection>
      </PageContent>

      {/* Action Modal (Purchase / Waste / Adjustment) */}
      <Modal
        open={activeModal !== null}
        onClose={() => setActiveModal(null)}
        title={
          activeModal === "purchase" ? "Purchase Incoming Stock" :
          activeModal === "waste" ? "Record Inventory Wastage" :
          activeModal === "adjustment" ? "Manual Stock Adjustment" : ""
        }
        description={
          activeModal === "purchase" ? "Receive inventory into warehouse" :
          activeModal === "waste" ? "Log dead birds or damaged stock" :
          activeModal === "adjustment" ? "Correct discrepancies from physical audit" : ""
        }
        size="md"
      >
        <Form onSubmit={handleActionSubmit}>
          <Modal.Body className="space-y-6">
            <FormField>
              <Label>Poultry Item</Label>
              <Select
                value={formItem}
                onChange={(e) => setFormItem(e.target.value)}
              >
                <option value="BROILER">Broiler</option>
                <option value="LAYER">Layer</option>
                <option value="DESI">Country Chicken</option>
              </Select>
            </FormField>

            <FormField>
              <Label>
                Quantity (kg) {activeModal === "adjustment" ? "(- for deduction, + for addition)" : ""}
              </Label>
              <div className="relative">
                <Input
                  type="number"
                  step="0.01"
                  required
                  placeholder={activeModal === "purchase" ? "e.g. 500" : "e.g. 5"}
                  value={formQuantity}
                  onChange={(e) => setFormQuantity(e.target.value)}
                  className="pr-12"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-[#999999] font-medium pointer-events-none">
                  kg
                </span>
              </div>
            </FormField>

            <FormField>
              <Label>Remarks</Label>
              <Input
                type="text"
                placeholder={activeModal === "purchase" ? "Morning supplier purchase" : "e.g. Supplier delivery"}
                value={formRemarks}
                onChange={(e) => setFormRemarks(e.target.value)}
              />
            </FormField>
          </Modal.Body>
          <Modal.Footer className="w-full gap-4">
            <Button
              variant="outline"
              onClick={() => setActiveModal(null)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isSubmitting}
              className="flex-1"
            >
              {isSubmitting ? "Saving..." : "Confirm Transaction"}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Page>
  );
}
