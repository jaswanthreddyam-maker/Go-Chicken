"use client";

import React, { useState, useEffect } from "react";
import { FileText, Plus, Trash2, Search, RefreshCw, AlertCircle, GripVertical, ArrowRight, ArrowLeft } from "lucide-react";
import { DataTable, StatusBadge, Button, Input, Modal, Select, QuoteSummaryCard } from "@/components/ui";
import { Page, PageHeader } from "@/components/ui/PageLayout";
import { Form, FormField, Label } from "@/components/ui/FormSystem";
import { useDashboardData } from "@/context/DashboardDataContext";
import { useUI } from "@/context/UIContext";
import { QuoteDrawerContent } from "@/components/dashboard/DrawerContents";

const PRODUCT_OPTIONS = [
  { value: "Live Bird", label: "Live Bird (LB-001)" },
  { value: "Dressed", label: "Dressed (DR-002)" },
  { value: "Skinless", label: "Skinless (SL-003)" },
];
const DELIVERY_ZONES = ["ZONE-NORTH", "ZONE-EAST", "ZONE-SOUTH", "ZONE-WEST"];

export function QuotesTab() {
  const {
    quotesList,
    isLoadingQuotes,
    quotesError,
    retailers,
    fetchQuotes,
    createQuote,
    previewQuote,
    convertQuote,
  } = useDashboardData();

  const { openDrawer } = useUI();

  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form State
  const [step, setStep] = useState(1);
  const [customerId, setCustomerId] = useState("");
  const [deliveryZone, setDeliveryZone] = useState("");
  const [items, setItems] = useState([{ sku: "Live Bird", quantity_kg: "" }]);
  const [expiresAt, setExpiresAt] = useState("");

  // Preview API Output State
  const [previewData, setPreviewData] = useState(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  // Debouncing API Preview Lookups
  useEffect(() => {
    if (!customerId || items.length === 0 || items.some(i => !i.quantity_kg || parseFloat(i.quantity_kg) <= 0)) {
      const t = setTimeout(() => setPreviewData(null), 0);
      return () => clearTimeout(t);
    }

    const tLoading = setTimeout(() => setIsPreviewLoading(true), 0);
    const delayDebounce = setTimeout(async () => {
      try {
        const payloadItems = items.map(i => ({
          sku: i.sku,
          quantity_kg: parseFloat(i.quantity_kg)
        }));
        const preview = await previewQuote({
          customer_id: customerId,
          delivery_zone: deliveryZone || null,
          items: payloadItems
        });
        setPreviewData(preview);
      } catch (err) {
        console.error("Preview resolution error", err);
        setPreviewData(null);
      } finally {
        setIsPreviewLoading(false);
      }
    }, 250);

    return () => clearTimeout(delayDebounce);
  }, [customerId, deliveryZone, items, previewQuote]);

  // Form Handlers
  const handleAddItem = () => {
    setItems([...items, { sku: "Live Bird", quantity_kg: "" }]);
  };

  const handleRemoveItem = (index) => {
    if (items.length === 1) return;
    const nextItems = [...items];
    nextItems.splice(index, 1);
    setItems(nextItems);
  };

  const handleItemChange = (index, field, value) => {
    const nextItems = [...items];
    nextItems[index][field] = value;
    setItems(nextItems);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!customerId || items.length === 0 || items.some(i => !i.quantity_kg)) return;

    try {
      const payloadItems = items.map(i => ({
        sku: i.sku,
        quantity_kg: parseFloat(i.quantity_kg)
      }));
      await createQuote({
        customer_id: customerId,
        delivery_zone: deliveryZone || null,
        items: payloadItems,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : null
      });
      // Reset State
      handleCloseModal();
    } catch (err) {
      console.error(err);
    }
  };

  const handleCloseModal = () => {
    setCustomerId("");
    setDeliveryZone("");
    setItems([{ sku: "Live Bird", quantity_kg: "" }]);
    setPreviewData(null);
    setStep(1);
    setExpiresAt("");
    setShowCreateModal(false);
  };

  // Helper for source coloring in preview pills
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

  // Columns definition
  const columns = [
    {
      key: "quote_number",
      label: "Quote Number",
      align: "left",
      sortable: true,
      render: (val, row) => (
        <button
          onClick={() => openDrawer(<QuoteDrawerContent quote={row} />)}
          className="font-mono text-xs font-bold text-[var(--text-primary)] hover:underline text-left cursor-pointer focus-ring rounded"
          title="Click to view details"
        >
          {val}
        </button>
      ),
    },
    {
      key: "customer_id",
      label: "Retailer Shop",
      align: "left",
      sortable: true,
      render: (val) => {
        const retailer = retailers.find(r => r.id === val);
        return retailer ? retailer.name : "Retailer ID: " + String(val).slice(0, 8);
      },
    },
    {
      key: "total_amount",
      label: "Grand Total",
      align: "right",
      sortable: true,
      render: (val) => (
        <span className="font-extrabold text-[var(--text-primary)] tabular-nums">
          ₹{Number(val).toLocaleString()}
        </span>
      ),
    },
    {
      key: "status",
      label: "Status",
      align: "center",
      sortable: true,
      render: (val) => (
        <StatusBadge status={val.toLowerCase()} label={val} />
      ),
    },
    {
      key: "created_at",
      label: "Prepared Date",
      align: "center",
      sortable: true,
      render: (val) => new Date(val).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }),
    },
    {
      key: "actions",
      label: "Fulfillment",
      align: "center",
      render: (_, row) => (
        <div className="flex justify-center gap-2">
          {row.status === "APPROVED" && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => convertQuote(row.id)}
            >
              Convert Order
            </Button>
          )}
          {row.status === "PENDING_APPROVAL" && (
            <span className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider bg-[var(--bg-app)] border border-[var(--border-subtle)] px-2 py-1 rounded">
              Awaiting Approvals
            </span>
          )}
          {row.status === "CONVERTED" && (
            <span className="text-[10px] font-bold text-green-700 bg-green-50 border border-green-200 px-2 py-1 rounded">
              Order Dispatched
            </span>
          )}
          {row.status === "REJECTED" && (
            <span className="text-[10px] font-bold text-red-700 bg-red-50 border border-red-200 px-2 py-1 rounded">
              Rejected
            </span>
          )}
        </div>
      ),
    },
  ];

  const renderStepper = () => (
    <div className="flex items-center justify-between pb-8 mb-8 text-sm select-none relative before:absolute before:inset-x-0 before:bottom-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-neutral-200 before:to-transparent">
      {/* Step 1 */}
      <div className={`flex items-center gap-3 transition-all duration-300 ${step >= 1 ? "opacity-100" : "opacity-40 grayscale"}`}>
        <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
          step >= 1 ? "bg-black text-white shadow-md ring-4 ring-neutral-100" : "bg-neutral-100 text-neutral-500"
        }`}>
          1
        </span>
        <span className={`font-bold tracking-tight ${step >= 1 ? "text-neutral-900" : "text-neutral-500"}`}>
          Customer & Zone
        </span>
      </div>
      
      {/* Line 1 */}
      <div className={`flex-1 h-px mx-6 transition-colors duration-300 ${step >= 2 ? "bg-black" : "bg-neutral-200"}`} />

      {/* Step 2 */}
      <div className={`flex items-center gap-3 transition-all duration-300 ${step >= 2 ? "opacity-100" : "opacity-40 grayscale"}`}>
        <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
          step >= 2 ? "bg-black text-white shadow-md ring-4 ring-neutral-100" : "bg-neutral-100 text-neutral-500"
        }`}>
          2
        </span>
        <span className={`font-bold tracking-tight ${step >= 2 ? "text-neutral-900" : "text-neutral-500"}`}>
          Products & Pricing
        </span>
      </div>

      {/* Line 2 */}
      <div className={`flex-1 h-px mx-6 transition-colors duration-300 ${step >= 3 ? "bg-black" : "bg-neutral-200"}`} />

      {/* Step 3 */}
      <div className={`flex items-center gap-3 transition-all duration-300 ${step >= 3 ? "opacity-100" : "opacity-40 grayscale"}`}>
        <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
          step >= 3 ? "bg-black text-white shadow-md ring-4 ring-neutral-100" : "bg-neutral-100 text-neutral-500"
        }`}>
          3
        </span>
        <span className={`font-bold tracking-tight ${step >= 3 ? "text-neutral-900" : "text-neutral-500"}`}>
          Review & Save
        </span>
      </div>
    </div>
  );

  return (
    <Page>
      <PageHeader
        title="Poultry Pricing & Quotes"
        description="Prepare legal wholesale quotes with hierarchical client pricing, zone surcharges, and order checkout pipelines."
      >
        <Button
          variant="primary"
          size="md"
          onClick={() => setShowCreateModal(true)}
        >
          <Plus size={16} className="mr-1.5" /> Prepare Quote
        </Button>
      </PageHeader>

      <div className="space-y-4">
        <div className="flex justify-between items-center gap-4 flex-col sm:flex-row">
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
            <Input
              type="text"
              placeholder="Search quotes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchQuotes(false)}
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Refresh Quotes
          </Button>
        </div>

        <DataTable
          columns={columns}
          data={quotesList}
          loading={isLoadingQuotes}
          emptyIcon={FileText}
          emptyTitle="No pricing quotes found"
          emptyDescription="Prepare a custom quote snapshot with client price books to checkout."
          pageSize={10}
          searchQuery={searchQuery}
          searchKeys={["quote_number"]}
        />
      </div>

      {/* CREATE QUOTE MODAL */}
      <Modal
        open={showCreateModal}
        onClose={handleCloseModal}
        title="Prepare Custom Wholesale Quote"
        description="Create a legal wholesale quote with live pricing"
        size="lg"
      >
        <Form onSubmit={handleSubmit} className="space-y-8 max-h-[75vh] overflow-y-auto pr-2 px-2 pb-2">
          {renderStepper()}

          {/* STEP 1: CUSTOMER & ZONE SETUP */}
          {step === 1 && (
            <div className="space-y-7 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormField>
                  <Label htmlFor="retailer">Select Retailer Customer</Label>
                  <Select
                    id="retailer"
                    value={customerId}
                    onChange={(e) => setCustomerId(e.target.value)}
                    required
                  >
                    <option value="">-- Choose Account --</option>
                    {retailers.map(r => (
                      <option key={r.id} value={r.id}>{r.name} ({r.phone})</option>
                    ))}
                  </Select>
                </FormField>

                <FormField>
                  <Label htmlFor="zone">Delivery Logistics Zone (Surcharge Sourcing)</Label>
                  <Select
                    id="zone"
                    value={deliveryZone}
                    onChange={(e) => setDeliveryZone(e.target.value)}
                  >
                    <option value="">-- No Zone (Zero Surcharge) --</option>
                    {DELIVERY_ZONES.map(z => (
                      <option key={z} value={z}>{z.replace("-", " ")}</option>
                    ))}
                  </Select>
                </FormField>
              </div>

              <div className="space-y-4 pt-2">
                <div className="flex justify-between items-center border-b border-neutral-100 pb-2">
                  <Label className="mb-0 text-sm font-bold text-neutral-800">Product Items</Label>
                  <Button type="button" variant="outline" size="sm" onClick={handleAddItem} className="h-8 text-xs font-bold px-3">
                    <Plus size={14} className="mr-1" /> Add SKU
                  </Button>
                </div>

                <div className="space-y-3">
                  {items.map((item, idx) => (
                    <div key={idx} className="group flex items-center gap-4 p-3 bg-neutral-50/50 hover:bg-neutral-50 border border-neutral-200 hover:border-neutral-300 transition-all rounded-xl shadow-sm">
                      <GripVertical size={16} className="text-neutral-400 flex-shrink-0 cursor-grab hover:text-neutral-600" />
                      <div className="flex-1">
                        <Select
                          value={item.sku}
                          onChange={(e) => handleItemChange(idx, "sku", e.target.value)}
                          required
                          className="bg-white shadow-sm border-neutral-200"
                        >
                          {PRODUCT_OPTIONS.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </Select>
                      </div>
                      <div className="w-32 relative">
                        <Input
                          type="number"
                          placeholder="0.0"
                          value={item.quantity_kg}
                          onChange={(e) => handleItemChange(idx, "quantity_kg", e.target.value)}
                          required
                          min="1"
                          className="pr-8 text-right bg-white shadow-sm border-neutral-200 font-medium"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-neutral-400 pointer-events-none">
                          kg
                        </span>
                      </div>
                      <div className="w-8 flex justify-center">
                        {items.length > 1 ? (
                          <button
                            type="button"
                            onClick={() => handleRemoveItem(idx)}
                            className="p-1.5 text-neutral-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
                            title="Remove SKU line"
                          >
                            <Trash2 size={16} />
                          </button>
                        ) : (
                          <div className="w-8" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-6 border-t border-neutral-100">
                <Button type="button" variant="secondary" onClick={handleCloseModal}>
                  Cancel
                </Button>
                <Button
                  type="button"
                  variant="primary"
                  onClick={() => setStep(2)}
                  disabled={!customerId || items.some(i => !i.quantity_kg || parseFloat(i.quantity_kg) <= 0)}
                  className="flex items-center gap-1.5 min-w-[180px] justify-center"
                >
                  Continue to Products <ArrowRight size={16} className="ml-1" />
                </Button>
              </div>
            </div>
          )}

          {/* STEP 2: PRODUCTS & LIVE PRICING VERIFICATION */}
          {step === 2 && (
            <div className="space-y-7 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="space-y-4">
                <Label className="text-sm font-bold text-neutral-800">Live Price Book Pricing Resolution Preview</Label>
                <div className="border border-neutral-200 rounded-2xl overflow-hidden divide-y divide-neutral-100 bg-white shadow-sm">
                  {items.map((item, idx) => {
                    const resolved = previewData?.items?.[idx];
                    return (
                      <div key={idx} className="p-5 flex flex-col gap-3 transition-colors hover:bg-neutral-50/50">
                        <div className="flex justify-between items-center">
                          <div>
                            <span className="font-extrabold text-sm text-neutral-900 tracking-tight">{item.sku}</span>
                            <span className="text-xs text-neutral-500 block mt-1 font-medium">
                              {item.quantity_kg} kg {resolved ? `· ₹${resolved.unit_price}/kg` : ""}
                            </span>
                          </div>
                          {resolved && (
                            <span className="text-lg font-black text-neutral-900 tabular-nums">
                              ₹{Number(resolved.line_total).toLocaleString()}
                            </span>
                          )}
                        </div>
                        {resolved && (
                          <div className="flex justify-start">
                            <span className={getSourceBadgeClass(resolved.pricing_source)}>
                              {resolved.pricing_source.replace("_", " ")}
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Pricing resolution loader & summary card */}
              {isPreviewLoading && (
                <div className="flex items-center justify-center gap-3 text-sm font-bold text-neutral-500 py-6 bg-neutral-50 rounded-2xl border border-neutral-100 border-dashed">
                  <RefreshCw className="w-4 h-4 animate-spin" /> Resolving pricing books...
                </div>
              )}

              {previewData && !isPreviewLoading && (
                <div className="pt-2">
                  <QuoteSummaryCard
                    subtotal={previewData.subtotal_amount}
                    surcharge={previewData.zone_surcharge_amount}
                    total={previewData.total_amount}
                  />
                </div>
              )}

              <div className="flex justify-between gap-3 pt-6 border-t border-neutral-100">
                <Button type="button" variant="secondary" onClick={() => setStep(1)} className="flex items-center gap-1.5">
                  <ArrowLeft size={16} className="mr-1" /> Back
                </Button>
                <Button
                  type="button"
                  variant="primary"
                  onClick={() => setStep(3)}
                  disabled={!previewData || isPreviewLoading}
                  className="flex items-center gap-1.5 min-w-[180px] justify-center"
                >
                  Continue to Review <ArrowRight size={16} className="ml-1" />
                </Button>
              </div>
            </div>
          )}

          {/* STEP 3: FINAL REVIEW & SAVE EXPIRY */}
          {step === 3 && (
            <div className="space-y-7 animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="bg-neutral-50 border border-neutral-200 rounded-2xl p-6 space-y-4">
                <h4 className="text-xs font-bold text-neutral-500 uppercase tracking-widest">
                  Review Details
                </h4>
                <div className="grid grid-cols-2 gap-6 text-sm">
                  <div>
                    <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider mb-1">Retailer Customer</p>
                    <p className="font-bold text-neutral-900 text-base">
                      {retailers.find(r => r.id === customerId)?.name}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider mb-1">Logistics Zone</p>
                    <p className="font-bold text-neutral-900 text-base">
                      {deliveryZone || "No Zone Surcharge"}
                    </p>
                  </div>
                </div>
              </div>

              <FormField>
                <Label htmlFor="expires" className="font-bold">Quote Expiration Date (Optional)</Label>
                <Input
                  id="expires"
                  type="date"
                  value={expiresAt}
                  onChange={(e) => setExpiresAt(e.target.value)}
                  className="max-w-md shadow-sm border-neutral-200"
                />
              </FormField>

              {previewData && (
                <div className="pt-2">
                  <QuoteSummaryCard
                    subtotal={previewData.subtotal_amount}
                    surcharge={previewData.zone_surcharge_amount}
                    total={previewData.total_amount}
                  />
                </div>
              )}

              <div className="flex justify-between gap-3 pt-6 border-t border-neutral-100">
                <Button type="button" variant="secondary" onClick={() => setStep(2)} className="flex items-center gap-1.5">
                  <ArrowLeft size={16} className="mr-1" /> Back
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={!customerId || isPreviewLoading}
                  className="min-w-[180px]"
                >
                  Generate Quote Snapshot
                </Button>
              </div>
            </div>
          )}

          {/* Bottom Info Note Banner */}
          <div className="flex items-start gap-3 text-xs text-neutral-600 font-medium bg-blue-50/50 border border-blue-100 rounded-xl p-4 mt-8 shadow-sm">
            <AlertCircle size={16} className="text-blue-500 flex-shrink-0 mt-0.5" />
            <span className="leading-relaxed text-blue-900/80">
              Live pricing will be automatically calculated based on the customer&apos;s specific price book tier, the requested quantity, and any applicable delivery zone surcharges.
            </span>
          </div>
        </Form>
      </Modal>
    </Page>
  );
}
