"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Edit3, Clock, Activity, RefreshCw, Search, Package, Zap, ChevronDown, ChevronUp, CheckCircle, TrendingUp, X, Check } from "lucide-react";
import { Button, DataTable, StatusBadge, Toast, ErrorBanner } from "@/components/ui";
import { Page, PageHeader, PageContent, PageSection } from "@/components/ui/PageLayout";
import { Form, Input } from "@/components/ui/FormSystem";
import { useDashboardData } from "@/context/DashboardDataContext";
import { useUI } from "@/context/UIContext";
import { OrderDrawerContent } from "@/components/dashboard/DrawerContents";

/**
 * OrdersTab — Live Orders & Rate Card Controls
 */
const AnimatedConfidence = ({ confidence }) => {
  const [displayConf, setDisplayConf] = useState(0);
  const [phase, setPhase] = useState("scanning"); // scanning -> resolving -> complete

  useEffect(() => {
    let timer;
    if (confidence) {
      setPhase("scanning");
      let count = 0;
      
      const interval = setInterval(() => {
        count += Math.floor(Math.random() * 15) + 5;
        if (count >= confidence) {
          clearInterval(interval);
          setDisplayConf(confidence);
          setPhase("complete");
        } else {
          setDisplayConf(count);
          if (count > confidence * 0.7) setPhase("resolving");
        }
      }, 100);
      
      return () => clearInterval(interval);
    }
  }, [confidence]);

  return (
    <div className="text-right">
      <div className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)] font-bold">
        {phase === "scanning" ? "Scanning..." : phase === "resolving" ? "Resolving..." : "Confidence"}
      </div>
      <div className={`text-sm font-bold ${phase === "complete" ? "text-emerald-500" : "text-[var(--text-secondary)]"}`}>
        {displayConf}%
      </div>
    </div>
  );
};

const AcceptButton = ({ pendingRec, acceptRecommendation, ignoreRecommendation }) => {
  const [isPublishing, setIsPublishing] = useState(false);
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    if (!pendingRec.expires_at) return;
    
    const checkExpiry = () => {
      setIsExpired(new Date() > new Date(pendingRec.expires_at));
    };
    
    checkExpiry();
    const interval = setInterval(checkExpiry, 1000);
    return () => clearInterval(interval);
  }, [pendingRec.expires_at]);

  const handleAccept = () => {
    if (isExpired) return;
    setIsPublishing(true);
    setTimeout(() => {
      acceptRecommendation(pendingRec.raw_id);
    }, 500);
  };

  if (isPublishing) {
    return (
      <div className="flex gap-2 pt-2 border-t border-[var(--border-subtle)] items-center justify-center p-2 text-emerald-500 font-bold text-sm">
        <RefreshCw className="w-4 h-4 animate-spin mr-2" /> Publishing new price...
      </div>
    );
  }

  return (
    <div className="flex gap-2 pt-2 border-t border-[var(--border-subtle)]">
      <Button 
        variant={isExpired ? "outline" : "primary"}
        size="sm" 
        disabled={isExpired}
        className={isExpired ? "flex-1 opacity-50 cursor-not-allowed" : "flex-1 bg-emerald-600 hover:bg-emerald-700 border-emerald-600"}
        onClick={handleAccept}
      >
        <Check className="w-4 h-4 mr-1.5" /> {isExpired ? "Expired" : "Accept"}
      </Button>
      <Button 
        variant="outline" 
        size="sm" 
        onClick={() => ignoreRecommendation(pendingRec.raw_id)}
      >
        <X className="w-4 h-4" />
      </Button>
    </div>
  );
};

export function OrdersTab() {
  const {
    ordersList,
    productPrices,
    isLoadingPrices,
    isLoadingMarket,
    ordersError,
    pricesError,
    marketIntelligence,
    acceptRecommendation,
    ignoreRecommendation,
    simulateMarket,
    handleStatusToggle,
    handleUpdateRate,
    fetchPrices,
    fetchOrders,
  } = useDashboardData();

  const { openDrawer, toasts, addToast, removeToast } = useUI();
  const [editingPrice, setEditingPrice] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [showSimMenu, setShowSimMenu] = useState(false);

  // Hidden Keyboard Shortcut for Simulation Menu
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "m") {
        setShowSimMenu(prev => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

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
      {/* Simulation Developer Menu (Hidden) */}
      {showSimMenu && (
        <div className="bg-purple-900/10 border-b border-purple-500/30 p-2 text-xs flex justify-between gap-2 px-4 items-center">
          <span className="bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded font-mono font-bold text-[10px] tracking-widest border border-purple-500/30">
            DEV MODE: Simulation Controls Enabled
          </span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => simulateMarket('weekend-demand')} className="border-purple-500 text-purple-300 h-6 text-[10px]">Weekend Demand</Button>
            <Button size="sm" variant="outline" onClick={() => simulateMarket('feed-cost-spike')} className="border-purple-500 text-purple-300 h-6 text-[10px]">Feed Cost Spike</Button>
            <Button size="sm" variant="outline" onClick={() => simulateMarket('no-action')} className="border-purple-500 text-purple-300 h-6 text-[10px]">No Action Needed</Button>
            <Button size="sm" variant="outline" onClick={() => simulateMarket('clear')} className="border-red-500 text-red-300 h-6 text-[10px]">Clear</Button>
          </div>
        </div>
      )}

      {/* AI Market Intelligence Engine */}
      <PageSection title="AI Market Intelligence Engine" description="Live rate cards powered by real-time market observations and deterministic AI analysis.">
        
        {/* Expandable Intelligence Panel */}
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] mb-6 overflow-hidden">
          <div 
            className="p-4 flex items-center justify-between cursor-pointer hover:bg-[var(--bg-app)] transition-colors"
            onClick={() => setShowAIPanel(!showAIPanel)}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                <Zap className="w-4 h-4 text-emerald-500" />
              </div>
              <div>
                <h3 className="text-[var(--text-primary)] font-bold text-sm">Monitoring Status: <span className="text-emerald-500">Active</span></h3>
                <p className="text-[var(--text-secondary)] text-xs mt-0.5">
                  {marketIntelligence?.snapshot ? `Analyzed ${marketIntelligence.snapshot.source_count} sources at ${new Date(marketIntelligence.snapshot.captured_at).toLocaleTimeString()}` : 'Collecting baseline signals...'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {marketIntelligence?.snapshot && (
                <div className="hidden sm:flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)] font-bold">Snapshot ID</div>
                    <div className="text-xs font-mono font-bold text-[var(--text-secondary)]">MS-{new Date(marketIntelligence.snapshot.captured_at).toISOString().split('T')[0].replace(/-/g, '')}-{marketIntelligence.snapshot.id.substring(0,4).toUpperCase()}</div>
                  </div>
                  <AnimatedConfidence confidence={marketIntelligence.snapshot.confidence} />
                </div>
              )}
              {showAIPanel ? <ChevronUp className="w-5 h-5 text-[var(--text-tertiary)]" /> : <ChevronDown className="w-5 h-5 text-[var(--text-tertiary)]" />}
            </div>
          </div>
          
          {showAIPanel && marketIntelligence?.snapshot && (
            <div className="p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-app)] grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-3">Market Snapshot</h4>
                <p className="text-sm text-[var(--text-primary)] mb-4">{marketIntelligence.snapshot.summary}</p>
                <div className="space-y-2">
                  {marketIntelligence.snapshot.signals.map((sig, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                        <div>
                          <span className="font-bold text-[var(--text-primary)]">{sig.source}:</span>{' '}
                          <span className="text-[var(--text-secondary)]">{sig.signal}</span>
                        </div>
                      </div>
                      {sig.weight && (
                        <div className="text-emerald-500 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded text-xs">
                          {sig.weight}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-3">Audit Timeline</h4>
                <div className="relative pl-4 space-y-4 before:absolute before:inset-0 before:ml-[5px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-[var(--border-subtle)] before:to-transparent">
                  <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-3 h-3 rounded-full border border-emerald-500 bg-[var(--bg-app)] text-emerald-500 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow" />
                    <div className="w-[calc(100%-2rem)] md:w-[calc(50%-1.5rem)] text-xs text-[var(--text-secondary)]">Snapshot Generated</div>
                  </div>
                  <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-3 h-3 rounded-full border border-emerald-500 bg-[var(--bg-app)] text-emerald-500 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow" />
                    <div className="w-[calc(100%-2rem)] md:w-[calc(50%-1.5rem)] text-xs text-[var(--text-secondary)] font-bold text-emerald-500">AI Analysis Completed</div>
                  </div>
                  <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-3 h-3 rounded-full border border-[var(--border-subtle)] bg-[var(--bg-app)] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow" />
                    <div className="w-[calc(100%-2rem)] md:w-[calc(50%-1.5rem)] text-xs text-[var(--text-tertiary)]">Awaiting Human Approval</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

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
            productPrices.map((item, idx) => {
              const pendingRec = marketIntelligence?.recommendations?.find(r => r.sku === item.item_type);
              const isNoAction = pendingRec?.recommended_price === pendingRec?.current_price;
              
              return (
                <div
                  key={idx}
                  className={`bg-[var(--bg-surface)] rounded-[var(--radius-lg)] p-5 border transition-all relative ${
                    pendingRec && !isNoAction ? 'border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'border-[var(--border-subtle)] hover:border-[var(--border-strong)]'
                  }`}
                  style={{ transitionDuration: "var(--duration-fast)" }}
                >
                  <div className="flex justify-between items-start mb-3">
                    <span className={`text-label px-2 py-1 rounded bg-[var(--bg-app)] border ${pendingRec && !isNoAction ? 'border-emerald-500/30 text-emerald-600' : 'border-[var(--border-subtle)] text-[var(--text-primary)]'}`}>
                      {item.item_type}
                    </span>
                    {pendingRec ? (
                      <span className="text-[10px] font-mono text-[var(--text-tertiary)] font-bold">
                        {pendingRec.id}
                        {pendingRec.expires_at && <span className="ml-2 text-orange-500 bg-orange-500/10 px-1 py-0.5 rounded">Expires: {new Date(pendingRec.expires_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>}
                      </span>
                    ) : (
                      <span className="text-label text-[var(--text-secondary)]">
                        INR / kg
                      </span>
                    )}
                  </div>

                  {pendingRec ? (
                    <div className="mt-4 space-y-4">
                      {isNoAction ? (
                        <div className="flex flex-col items-center justify-center py-4 bg-emerald-500/5 rounded-lg border border-emerald-500/20 text-center">
                          <CheckCircle className="w-8 h-8 text-emerald-500 mb-2" />
                          <h4 className="text-lg font-bold text-[var(--text-primary)]">₹{item.price_per_kg} is Optimal</h4>
                          <p className="text-xs text-[var(--text-secondary)] mt-1 max-w-[200px]">No pricing changes recommended based on current market conditions.</p>
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="mt-4"
                            onClick={() => ignoreRecommendation(pendingRec.raw_id)}
                          >
                            Dismiss
                          </Button>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)] font-bold">Current Price</p>
                              <h4 className="text-xl font-bold text-[var(--text-secondary)] line-through opacity-70">
                                ₹{item.price_per_kg}
                              </h4>
                            </div>
                            <div className="text-right">
                              <p className="text-[10px] uppercase tracking-wider text-emerald-500 font-bold flex items-center justify-end gap-1">
                                <TrendingUp className="w-3 h-3" /> Recommended
                              </p>
                              <h4 className="text-display font-black text-emerald-500 tracking-tight">
                                ₹{pendingRec.recommended_price}
                              </h4>
                            </div>
                          </div>
                          
                          {pendingRec.impact && (
                            <div className="grid grid-cols-3 gap-2 bg-[var(--bg-app)] p-2 rounded-md border border-[var(--border-subtle)] text-center divide-x divide-[var(--border-subtle)]">
                              <div>
                                <p className="text-[9px] uppercase tracking-wider text-[var(--text-tertiary)] font-bold mb-0.5">Est. Revenue</p>
                                <p className="text-xs font-bold text-emerald-500">{pendingRec.impact.expected_daily_revenue}</p>
                              </div>
                              <div>
                                <p className="text-[9px] uppercase tracking-wider text-[var(--text-tertiary)] font-bold mb-0.5">Margin</p>
                                <p className="text-xs font-bold text-emerald-500">{pendingRec.impact.estimated_margin}</p>
                              </div>
                              <div>
                                <p className="text-[9px] uppercase tracking-wider text-[var(--text-tertiary)] font-bold mb-0.5">Retailers</p>
                                <p className="text-xs font-bold text-[var(--text-secondary)]">{pendingRec.impact.affected_retailers}</p>
                              </div>
                            </div>
                          )}

                          <div className="bg-emerald-500/5 rounded-md p-3 border border-emerald-500/10">
                            <p className="text-xs text-[var(--text-primary)] mb-2 font-bold flex justify-between">
                              <span>Reasoning:</span>
                              <span className="text-emerald-500">{pendingRec.confidence_score}% Confidence</span>
                            </p>
                            <ul className="text-xs text-[var(--text-secondary)] space-y-1 list-disc pl-4">
                              {pendingRec.reasoning.map((reason, i) => (
                                <li key={i}>{reason}</li>
                              ))}
                            </ul>
                          </div>

                          <AcceptButton pendingRec={pendingRec} acceptRecommendation={acceptRecommendation} ignoreRecommendation={ignoreRecommendation} />
                          
                          <div className="pt-3 flex items-center justify-between text-[8px] uppercase tracking-wider text-[var(--text-tertiary)] border-t border-[var(--border-subtle)] mt-4">
                            <div>
                              <span className="font-bold">Market Intelligence Engine v1.0</span><br/>
                              <span>Policy: pricing-policy-v1</span>
                            </div>
                            <div className="text-right">
                              <span>Analysis Time</span><br/>
                              <span className="font-bold">312 ms</span>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  ) : editingPrice && editingPrice.item_type === item.item_type ? (
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
              );
            })
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
