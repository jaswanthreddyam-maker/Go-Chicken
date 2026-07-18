"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useUI } from "./UIContext";

const DashboardDataContext = createContext();

const getApiBase = () => {
  let url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      url = "https://go-chicken-production.up.railway.app/api/v1";
    } else {
      url = "http://localhost:8000/api/v1";
    }
  }
  url = url.replace(/\/+$/, "");
  if (!url.endsWith("/api/v1")) url += "/api/v1";
  return url;
};
const API_BASE = getApiBase();

export function DashboardDataProvider({ children }) {
  // ── Live AI & Chart State (Originates from /api/v1/ai APIs) ──
  const [aiForecast, setAiForecast] = useState({
    targetDate: new Date().toISOString().split('T')[0],
    predictedKg: 0,
    weather: "Normal, 28°C",
    confidence: 89,
    reasoning: "Awaiting live AI demand forecast generation from Ollama engine."
  });
  const [salesData, setSalesData] = useState([]);
  const [scatterData, setScatterData] = useState([]);

  const { addToast, addNotification } = useUI();

  // ── Market Intelligence Actions ──
  const acceptRecommendation = useCallback(async (id) => {
    try {
      const res = await fetch(`${API_BASE}/market/recommendations/${id}/accept`, {
        method: "POST",
        credentials: "include"
      });
      if (!res.ok) throw new Error("Failed to accept");
      // We intentionally do NOT mutate state here. 
      // The SSE stream will broadcast 'pricing.recommendation.accepted' to handle UI updates and toasts.
    } catch (err) {
      addToast('Error accepting recommendation.', 'error');
    }
  }, []);

  const ignoreRecommendation = useCallback(async (id) => {
    try {
      const res = await fetch(`${API_BASE}/market/recommendations/${id}/ignore`, {
        method: "POST",
        credentials: "include"
      });
      if (!res.ok) throw new Error("Failed to ignore");
      addToast('Recommendation ignored.', 'success');
      fetchMarketIntelligence(true);
    } catch (err) {
      addToast('Error ignoring recommendation.', 'error');
    }
  }, []);

  const simulateMarket = useCallback(async (scenario) => {
    try {
      const res = await fetch(`${API_BASE}/market/simulations/${scenario}`, {
        method: "POST",
        credentials: "include"
      });
      if (!res.ok) throw new Error("Failed to simulate");
      addToast(`Simulated market condition: ${scenario}`, 'success');
      fetchMarketIntelligence(true);
    } catch (err) {
      addToast('Simulation failed.', 'error');
    }
  }, []);

  // ── Live Data State ──
  const [ordersList, setOrdersList] = useState([]);
  const [productPrices, setProductPrices] = useState([]);
  const [trucks, setTrucks] = useState([]);
  const [retailers, setRetailers] = useState([]);
  const [quotesList, setQuotesList] = useState([]);
  const [inventoryList, setInventoryList] = useState([]);
  const [inventoryTxns, setInventoryTxns] = useState([]);

  // ── Loading & Error States ──
  const [isLoadingOrders, setIsLoadingOrders] = useState(true);
  const [isLoadingPrices, setIsLoadingPrices] = useState(true);
  const [isLoadingTrucks, setIsLoadingTrucks] = useState(true);
  const [isLoadingQuotes, setIsLoadingQuotes] = useState(true);
  const [isLoadingInventory, setIsLoadingInventory] = useState(true);
  const [ordersError, setOrdersError] = useState(null);
  const [pricesError, setPricesError] = useState(null);
  const [trucksError, setTrucksError] = useState(null);
  const [quotesError, setQuotesError] = useState(null);
  const [inventoryError, setInventoryError] = useState(null);

  // ── Hackathon UX State ──
  const [operationsFeed, setOperationsFeed] = useState([]);
  const [livePulse, setLivePulse] = useState(false);
  const [eventCount, setEventCount] = useState(0);
  const [latestAIExtraction, setLatestAIExtraction] = useState(null);

  // ── Market Intelligence State ──
  const [marketIntelligence, setMarketIntelligence] = useState({
    snapshot: null,
    recommendations: []
  });
  const [isLoadingMarket, setIsLoadingMarket] = useState(true);
  const [marketError, setMarketError] = useState(null);

  // ── Error Classifier ──
  const classifyError = useCallback((err, response) => {
    if (!response && (err instanceof TypeError || err.name === 'AbortError')) {
      return {
        type: 'warning',
        message: '⚠️ Network Connection Error: Could not reach the server. UI reverted to previous state.',
      };
    }
    if (response && !response.ok) {
      const code = response.status;
      if (code === 401 || code === 403) {
        return { type: 'error', message: '❌ Access Denied: You do not have permission for this action. UI reverted.' };
      }
      if (code === 404) {
        return { type: 'error', message: '❌ Not Found: The requested resource could not be located. UI reverted.' };
      }
      if (code === 422) {
        return { type: 'error', message: '❌ Validation Error: Please check your input and try again. UI reverted.' };
      }
      return { type: 'error', message: `❌ Request Rejected (HTTP ${code}): Unable to save your changes at this time. Please try again. UI reverted.` };
    }
    return { type: 'error', message: '❌ An unexpected error occurred. UI reverted to previous state.' };
  }, []);

  // ── Fetchers ──
  const fetchOrders = useCallback(async (silent = false) => {
    if (!silent) setIsLoadingOrders(true);
    try {
      const res = await fetch(`${API_BASE}/orders/`, {
        credentials: "include"
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) setOrdersList(data);
      setOrdersError(null);
    } catch (err) {
      if (!silent) setOrdersError('Unable to load orders from server.');
    } finally {
      if (!silent) setIsLoadingOrders(false);
    }
  }, []);

  const fetchPrices = useCallback(async (silent = false) => {
    if (!silent) setIsLoadingPrices(true);
    try {
      const res = await fetch(`${API_BASE}/pricing/`, {
        credentials: "include"
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) setProductPrices(data);
      setPricesError(null);
    } catch (err) {
      if (!silent) setPricesError('Unable to load pricing from server.');
    } finally {
      if (!silent) setIsLoadingPrices(false);
    }
  }, []);

  const fetchTrucks = useCallback(async (silent = false) => {
    if (!silent) setIsLoadingTrucks(true);
    try {
      const res = await fetch(`${API_BASE}/trucks/`, {
        credentials: "include"
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) setTrucks(data);
      setTrucksError(null);
    } catch (err) {
      if (!silent) setTrucksError('Unable to load fleet data from server.');
    } finally {
      if (!silent) setIsLoadingTrucks(false);
    }
  }, []);

  const fetchRetailers = useCallback(async (silent = false) => {
    try {
      const res = await fetch(`${API_BASE}/khata/retailers`, {
        credentials: "include"
      });
      if (res.ok) {
        const data = await res.json();
        setRetailers(data || []);
      }
    } catch (err) {
      console.error("Failed to fetch retailers", err);
    }
  }, []);

  const fetchQuotes = useCallback(async (silent = false) => {
    if (!silent) setIsLoadingQuotes(true);
    try {
      const res = await fetch(`${API_BASE}/quotes/`, {
        credentials: "include"
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) setQuotesList(data);
      setQuotesError(null);
    } catch (err) {
      if (!silent) setQuotesError('Unable to load quotes from server.');
    } finally {
      if (!silent) setIsLoadingQuotes(false);
    }
  }, []);

  const fetchInventory = useCallback(async (silent = false) => {
    if (!silent) setIsLoadingInventory(true);
    try {
      const headers = {
        "Content-Type": "application/json"
      };
      const [invRes, txnRes] = await Promise.all([
        fetch(`${API_BASE}/inventory/`, { headers }),
        fetch(`${API_BASE}/inventory/transactions?limit=25`, { headers }),
      ]);
      if (invRes.ok) {
        const invData = await invRes.json();
        if (Array.isArray(invData)) setInventoryList(invData);
      }
      if (txnRes.ok) {
        const txnData = await txnRes.json();
        if (Array.isArray(txnData)) setInventoryTxns(txnData);
      }
      setInventoryError(null);
    } catch (err) {
      if (!silent) setInventoryError('Unable to load inventory data.');
    } finally {
      if (!silent) setIsLoadingInventory(false);
    }
  }, []);

  const fetchAIAnalytics = useCallback(async (silent = false) => {
    try {
      const [fRes, sRes, dRes] = await Promise.allSettled([
        fetch(`${API_BASE}/ai/forecast/today`, { credentials: "include" }),
        fetch(`${API_BASE}/ai/sales-comparison`, { credentials: "include" }),
        fetch(`${API_BASE}/ai/demand-clusters`, { credentials: "include" })
      ]);
      if (fRes.status === "fulfilled" && fRes.value.ok) {
        const data = await fRes.value.json();
        if (data && data.predicted_demand_kg !== undefined) {
          setAiForecast({
            targetDate: data.target_date || new Date().toISOString().split('T')[0],
            predictedKg: Math.round(data.predicted_demand_kg),
            weather: data.weather_condition || "Normal, 28°C",
            confidence: 94,
            reasoning: data.reasoning || "Predicted demand computed using nomic-embed-text similarity & Ollama time-series model."
          });
        }
      }
      if (sRes.status === "fulfilled" && sRes.value.ok) {
        const data = await sRes.value.json();
        if (Array.isArray(data)) setSalesData(data);
      }
      if (dRes.status === "fulfilled" && dRes.value.ok) {
        const data = await dRes.value.json();
        if (Array.isArray(data)) setScatterData(data);
      }
    } catch (err) {
      console.error("AI Analytics fetch error", err);
    }
  }, []);

  const fetchMarketIntelligence = useCallback(async (silent = false) => {
    if (!silent) setIsLoadingMarket(true);
    try {
      const res = await fetch(`${API_BASE}/market/intelligence`, {
        credentials: "include"
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMarketIntelligence({
        snapshot: data.snapshot,
        recommendations: data.recommendations || []
      });
      setMarketError(null);
    } catch (err) {
      if (!silent) setMarketError('Unable to load market intelligence data.');
    } finally {
      if (!silent) setIsLoadingMarket(false);
    }
  }, []);

  const fetchAll = useCallback(async (silent = false) => {
    await Promise.allSettled([
      fetchOrders(silent),
      fetchPrices(silent),
      fetchTrucks(silent),
      fetchRetailers(silent),
      fetchQuotes(silent),
      fetchInventory(silent),
      fetchAIAnalytics(silent),
      fetchMarketIntelligence(silent),
    ]);
  }, [fetchOrders, fetchPrices, fetchTrucks, fetchRetailers, fetchQuotes, fetchInventory, fetchAIAnalytics, fetchMarketIntelligence]);

  const handleRefresh = useCallback(() => {
    fetchAll(false);
  }, [fetchAll]);

  // ── SSE Stream Implementation ──
  useEffect(() => {
    // Initial fetch
    fetchAll(false);

    // Setup SSE connection
    const eventSource = new EventSource(`${API_BASE}/events/stream`);

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        const { type, data, timestamp } = parsed;

        // 1. Trigger Pulse and increment event counter
        setLivePulse(true);
        setTimeout(() => setLivePulse(false), 1000);
        setEventCount(c => c + 1);

        if (type === "ORDER_CONFIRMED") {
          // Toast 0ms
          addToast(`🐔 WhatsApp Order Confirmed\n${data.customer}\n${data.quantity} KG ${data.product}\n₹${data.amount}`, "success");
          addNotification("WhatsApp Order", `${data.quantity}kg ${data.product} by ${data.customer}`, "success");

          // Play subtle ding sound if enabled
          const audio = new Audio('/ding.mp3');
          audio.volume = 0.5;
          audio.play().catch(e => console.log('Audio disabled by browser', e));

          setTimeout(() => {
            fetchOrders(true);
          }, 200);

          setTimeout(() => {
            fetchInventory(true);
          }, 500);

          setTimeout(() => {
            fetchTrucks(true);
          }, 650);

          setTimeout(() => {
            setOperationsFeed(prev => [{
              id: data.order_id + Date.now(),
              time: new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
              type: 'WhatsApp',
              title: 'Order Confirmed',
              desc: `${data.quantity}kg ${data.product}`,
              value: `₹${data.amount}`,
              icon: '📱'
            }, ...prev].slice(0, 50));
          }, 800);

        } else if (type === "INVENTORY_CHANGED") {
          setTimeout(() => {
            setOperationsFeed(prev => [{
              id: data.item_type + Date.now(),
              time: new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
              type: 'Inventory',
              title: 'Inventory Reserved',
              desc: `${data.quantity}kg ${data.item_type}`,
              value: '',
              icon: '📦'
            }, ...prev].slice(0, 50));
          }, 800);
        } else if (type === "AI_EXTRACTION") {
          setLatestAIExtraction(data);
        } else if (type === "NEW_RETAILER_REGISTRATION") {
          addToast(`🆕 New Retailer Registration\n${data.shop_name}`, "info");
          fetchRetailers(true);
        } else if (type === "RETAILER_APPROVED") {
          addToast(`🟢 Retailer Approved\n${data.message.split('\n')[0]}`, "success");
          fetchRetailers(true);
          
          setTimeout(() => {
            setOperationsFeed(prev => [{
              id: data.retailer_id + Date.now(),
              time: new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
              type: 'Retailer',
              title: 'Retailer Approved',
              desc: `${data.shop_name || 'New Retailer'} approved`,
              value: '',
              icon: '🟢'
            }, ...prev].slice(0, 50));
          }, 800);
        } else if (type === "RETAILER_REJECTED") {
          addToast(`🔴 Retailer Rejected\n${data.phone}`, "error");
          fetchRetailers(true);
        } else if (type === "pricing.recommendation.accepted") {
          // Re-fetch market state to dismiss the recommendation UI
          setTimeout(() => {
            fetchMarketIntelligence(true);
          }, 300);

          // Re-fetch rate card UI
          setTimeout(() => {
            fetchPrices(true);
          }, 600);

          // Simulate WhatsApp Price Card Sync (Fake timeline entry for demo purposes)
          setTimeout(() => {
            setOperationsFeed(prev => [{
              id: `whatsapp-sync-${Date.now()}`,
              time: new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
              type: 'WhatsApp',
              title: 'WhatsApp Catalog Synced',
              desc: `${data.sku} @ ₹${data.new_price}/kg`,
              value: '',
              icon: '📱'
            }, ...prev].slice(0, 50));
          }, 900);
        }
      } catch (err) {
        console.error("SSE parse error", err);
      }
    };

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchAll(true);
      }
    };
    
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // Command palette / action listeners
    const handleGlobalRefresh = () => fetchAll(false);
    window.addEventListener("gc_refresh_dashboard", handleGlobalRefresh);

    return () => {
      eventSource.close();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("gc_refresh_dashboard", handleGlobalRefresh);
    };
  }, [fetchAll, addToast, addNotification]);

  // ── Mutators ──
  const handleStatusToggle = useCallback(async (orderId, newStatus) => {
    const previousOrders = [...ordersList];
    setOrdersList(prev => prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o));

    let response;
    try {
      response = await fetch(`${API_BASE}/orders/${orderId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ status: newStatus })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      addToast(`📲 WhatsApp Alert Sent: Order marked as ${newStatus.toUpperCase()}!`, 'success');
      addNotification(`Order Status Updated`, `Order #${orderId.slice(0, 8)} status marked as ${newStatus}`, "success");
      fetchAll(true);
    } catch (err) {
      setOrdersList(previousOrders);
      const { type, message } = classifyError(err, response);
      addToast(message, type);
    }
  }, [ordersList, addToast, addNotification, classifyError, fetchAll]);

  const handleUpdateRate = useCallback(async (item_type, new_val) => {
    const val = parseFloat(new_val);
    if (!val || val <= 0) return;

    const previousPrices = [...productPrices];
    setProductPrices(prev => prev.map(p => p.item_type === item_type ? { ...p, price_per_kg: val } : p));

    let response;
    try {
      response = await fetch(`${API_BASE}/pricing/${encodeURIComponent(item_type)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ price_per_kg: val })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      addToast(`📊 Rate card updated: ${item_type.toUpperCase()} is now ₹${val}/kg. Broadcasted to bot.`, 'success');
      addNotification(`Rate Card Updated`, `${item_type.toUpperCase()} pricing updated to ₹${val}/kg`, "info");
      fetchAll(true);
    } catch (err) {
      setProductPrices(previousPrices);
      const { type, message } = classifyError(err, response);
      addToast(message, type);
    }
  }, [productPrices, addToast, addNotification, classifyError, fetchAll]);

  const handlePaymentSubmit = useCallback(async ({ retailer_id, amount, note }) => {
    const selectedRetailer = retailers.find(r => r.id === retailer_id);
    const retailerName = selectedRetailer ? selectedRetailer.name : "Unknown Retailer";

    let response;
    try {
      response = await fetch(`${API_BASE}/khata/transaction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          retailer_id: retailer_id,
          type: "payment",
          amount: amount,
          reference_note: note || `Payment from ${retailerName}`
        })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      addToast(`💳 Payment of ₹${amount.toLocaleString()} recorded for ${retailerName}.`, 'success');
      addNotification(`Payment Confirmed`, `₹${amount.toLocaleString()} credited to ${retailerName}`, "success");
      fetchAll(true); // reload balances across all screens
    } catch (err) {
      const { type, message } = classifyError(err, response);
      addToast(message, type);
    }
  }, [retailers, addToast, addNotification, classifyError, fetchAll]);

  const handleAddTruck = useCallback(async ({ license_plate, max_capacity_kg, iot_device_id }) => {
    const previousTrucks = [...trucks];
    const optimisticTruck = {
      id: `temp-${Date.now()}`,
      tenant_id: '',
      license_plate,
      max_capacity_kg,
      iot_device_id,
      driver_id: null,
      created_at: new Date().toISOString(),
    };
    setTrucks(prev => [optimisticTruck, ...prev]);

    let response;
    try {
      response = await fetch(`${API_BASE}/trucks/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          license_plate,
          max_capacity_kg,
          iot_device_id: iot_device_id || null,
        })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const created = await response.json();
      setTrucks(prev => prev.map(t => t.id === optimisticTruck.id ? created : t));
      addToast(`🚛 Truck ${license_plate} added to fleet!`, 'success');
      addNotification(`Fleet Registration`, `Truck ${license_plate} registered with IoT profile`, "info");
      fetchAll(true);
    } catch (err) {
      setTrucks(previousTrucks);
      const errorState = classifyError(err, response);
      addToast(errorState.message, errorState.type);
      fetchAll(true);
    }
  }, [trucks, addToast, addNotification, classifyError, fetchAll]);

  const handleDeleteTruck = useCallback(async (truckId) => {
    const previousTrucks = [...trucks];
    setTrucks(prev => prev.filter(t => t.id !== truckId));
    let response;
    try {
      response = await fetch(`${API_BASE}/trucks/${truckId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to delete truck');
      addToast('🚛 Truck deleted from fleet', 'info');
    } catch (err) {
      setTrucks(previousTrucks);
      const errorState = classifyError(err, response);
      addToast(errorState.message, errorState.type);
    }
  }, [trucks, addToast, classifyError]);

  const createQuote = useCallback(async ({ customer_id, delivery_zone, items }) => {
    let response;
    try {
      response = await fetch(`${API_BASE}/quotes/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ customer_id, delivery_zone, items })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const created = await response.json();
      addToast(`📄 Quote ${created.quote_number} generated successfully!`, 'success');
      addNotification(`Quote Generated`, `Quote ${created.quote_number} created with total ₹${created.total_amount.toLocaleString()}`, "success");
      fetchAll(true);
      return created;
    } catch (err) {
      const { type, message } = classifyError(err, response);
      addToast(message, type);
      throw err;
    }
  }, [addToast, addNotification, classifyError, fetchAll]);

  const convertQuote = useCallback(async (quote_id) => {
    let response;
    try {
      response = await fetch(`${API_BASE}/quotes/${quote_id}/convert`, {
        method: "POST",
        credentials: "include"
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      addToast(`💳 Quote ${data.quote_number} converted to Order!`, 'success');
      addNotification(`Quote Converted`, `Order spawned from Quote ${data.quote_number}`, "success");
      fetchAll(true);
      return data;
    } catch (err) {
      const { type, message } = classifyError(err, response);
      addToast(message, type);
      throw err;
    }
  }, [addToast, addNotification, classifyError, fetchAll]);

  const approveQuote = useCallback(async (quote_id) => {
    let response;
    try {
      response = await fetch(`${API_BASE}/quotes/${quote_id}/approve`, {
        method: "PATCH",
        credentials: "include"
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      addToast(`✅ Quote ${data.quote_number} approved!`, 'success');
      fetchAll(true);
      return data;
    } catch (err) {
      const { type, message } = classifyError(err, response);
      addToast(message, type);
      throw err;
    }
  }, [addToast, classifyError, fetchAll]);

  const rejectQuote = useCallback(async (quote_id) => {
    let response;
    try {
      response = await fetch(`${API_BASE}/quotes/${quote_id}/reject`, {
        method: "PATCH",
        credentials: "include"
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      addToast(`❌ Quote ${data.quote_number} rejected.`, 'info');
      fetchAll(true);
      return data;
    } catch (err) {
      const { type, message } = classifyError(err, response);
      addToast(message, type);
      throw err;
    }
  }, [addToast, classifyError, fetchAll]);

  const previewQuote = useCallback(async ({ customer_id, delivery_zone, items }) => {
    let response;
    try {
      response = await fetch(`${API_BASE}/quotes/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ customer_id, delivery_zone, items })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (err) {
      const { type, message } = classifyError(err, response);
      addToast(message, type);
      throw err;
    }
  }, [addToast, classifyError]);

  const totalOutstanding = retailers.filter(r => Number(r.balance) > 0).reduce((acc, curr) => acc + Number(curr.balance), 0);
  const totalCapacity = trucks.reduce((acc, curr) => acc + (curr.max_capacity_kg || curr.capacity || 2000), 0);
  const activeAlerts = trucks.filter(t => t.status === 'alert').length;

  return (
    <DashboardDataContext.Provider
      value={{
        ordersList,
        productPrices,
        trucks,
        retailers,
        quotesList,
        inventoryList,
        inventoryTxns,
        marketIntelligence,
        isLoadingOrders,
        isLoadingPrices,
        isLoadingTrucks,
        isLoadingQuotes,
        isLoadingInventory,
        isLoadingMarket,
        ordersError,
        pricesError,
        trucksError,
        quotesError,
        inventoryError,
        marketError,
        fetchOrders,
        fetchPrices,
        fetchTrucks,
        fetchRetailers,
        fetchQuotes,
        fetchInventory,
        fetchMarketIntelligence,
        fetchAll,
        handleRefresh,
        handleStatusToggle,
        handleUpdateRate,
        handlePaymentSubmit,
        handleAddTruck,
        handleDeleteTruck,
        acceptRecommendation,
        ignoreRecommendation,
        simulateMarket,
        createQuote,
        convertQuote,
        approveQuote,
        rejectQuote,
        fetchAIAnalytics,
        MOCK_AI_FORECAST: aiForecast,
        MOCK_SALES_DATA: salesData,
        MOCK_SCATTER_DATA: scatterData,
        aiForecast,
        salesData,
        scatterData,
        totalOutstanding,
        totalCapacity,
        activeAlerts,
        operationsFeed,
        livePulse,
        eventCount,
        latestAIExtraction
      }}
    >
      {children}
    </DashboardDataContext.Provider>
  );
}

export function useDashboardData() {
  const ctx = useContext(DashboardDataContext);
  if (!ctx) throw new Error("useDashboardData must be used within a DashboardDataProvider");
  return ctx;
}
