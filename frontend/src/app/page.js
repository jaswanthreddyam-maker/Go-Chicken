"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  Legend, ScatterChart, Scatter, ZAxis
} from 'recharts';
import {
  LayoutDashboard, Truck, Wallet, BrainCircuit, AlertTriangle,
  Thermometer, MapPin, Package, Bell, Search, ChevronRight, Activity, CheckCircle2, Clock, RefreshCw, Zap, Edit3, Save, Send, Tag, ShoppingCart, WifiOff, AlertCircle, X, Menu, User
} from 'lucide-react';
import AnimatedButton from '@/components/AnimatedButton';
import { useLanguage } from '@/context/LanguageContext';

// ── API Base URL (from .env.local) ───────────────────────────────────
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ── Static mock data that will NOT be replaced by API calls ──────────
const MOCK_AI_FORECAST = {
  targetDate: "2026-07-03",
  predictedKg: 1850,
  weather: "Rainy, 28°C",
  confidence: 94,
  reasoning: "Upcoming weekend surge detected. Historical data shows 15% bump on rainy Fridays."
};

const MOCK_KHATA = [
  { id: 'R-01', shopName: 'Raju Chicken Center', balance: 8200, lastPaid: '2026-07-01', phone: '+91 9876543210' },
  { id: 'R-02', shopName: 'Bhavani Poultry', balance: 14500, lastPaid: '2026-06-28', phone: '+91 9876543211' },
  { id: 'R-03', shopName: 'Kalyan Meats', balance: -1200, lastPaid: '2026-07-02', phone: '+91 9876543212' },
  { id: 'R-04', shopName: 'Durga Broilers', balance: 4500, lastPaid: '2026-06-30', phone: '+91 9876543213' }
];

const MOCK_SALES_DATA = [
  { date: 'Jun 26', actual: 1600, predicted: 1650 },
  { date: 'Jun 27', actual: 1750, predicted: 1700 },
  { date: 'Jun 28', actual: 2100, predicted: 2000 },
  { date: 'Jun 29', actual: 1400, predicted: 1450 },
  { date: 'Jun 30', actual: 1550, predicted: 1500 },
  { date: 'Jul 01', actual: 1620, predicted: 1600 },
  { date: 'Jul 02', actual: 1700, predicted: 1750 },
];

const MOCK_SCATTER_DATA = [
  { x: 1, y: 1600, z: 200, name: 'Cluster A' },
  { x: 2, y: 1650, z: 200, name: 'Cluster A' },
  { x: 3, y: 1700, z: 200, name: 'Cluster A' },
  { x: 10, y: 2100, z: 200, name: 'Cluster B' },
  { x: 11, y: 2150, z: 200, name: 'Cluster B' },
];

// ── Reusable UI Components (Stark Monochromatic B&W) ─────────────────

const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-xl border border-[#EBEBEB] overflow-hidden ${className}`}>
    {children}
  </div>
);

const StatBox = ({ title, value, icon: Icon, alert = false, subtitle, trend }) => (
  <Card className={`p-4 sm:p-5 min-w-[240px] sm:min-w-[260px] md:min-w-0 snap-start flex-shrink-0 transition-all hover:border-[#111111] ${alert ? 'border-red-300 bg-red-50/20' : ''}`}>
    <div className="flex justify-between items-start">
      <div className="space-y-1 min-w-0 flex-1">
        <p className={`text-[9px] sm:text-[10px] font-bold uppercase tracking-wider ${alert ? 'text-red-700' : 'text-[#666666]'}`}>{title}</p>
        <h3 className={`text-xl sm:text-2xl font-extrabold tracking-tight ${alert ? 'text-red-800' : 'text-[#111111]'}`}>{value}</h3>
        {subtitle && (
          <div className="flex items-center gap-1 mt-1">
            <span className={`text-[9px] sm:text-[10px] font-semibold tracking-wide ${trend === 'up' ? 'text-[#111111]' : trend === 'down' ? 'text-red-600' : 'text-[#666666]'}`}>
              {subtitle}
            </span>
          </div>
        )}
      </div>
      <div className={`p-2 rounded-lg border flex-shrink-0 ${alert ? 'bg-red-50 border-red-150 text-red-600' : 'bg-[#FAFAFA] border-[#EBEBEB] text-[#111111]'}`}>
        <Icon size={16} />
      </div>
    </div>
  </Card>
);

// ── B&W Rectangular Pulse Skeletons ──────────────────────────────────
const TableSkeleton = ({ rows = 4, cols = 5 }) => (
  <div className="animate-pulse p-6 bg-white space-y-4">
    {Array.from({ length: rows }).map((_, r) => (
      <div key={r} className="flex gap-4 items-center">
        {Array.from({ length: cols }).map((_, c) => (
          <div key={c} className="h-4 bg-[#EBEBEB] rounded flex-1"></div>
        ))}
      </div>
    ))}
  </div>
);

const ChartSkeleton = () => (
  <div className="animate-pulse bg-white border border-[#EBEBEB] rounded-xl p-6 h-80 flex flex-col justify-between">
    <div className="flex justify-between items-center mb-6">
      <div className="h-5 bg-[#EBEBEB] rounded w-1/3"></div>
      <div className="h-8 bg-[#EBEBEB] rounded w-20"></div>
    </div>
    <div className="flex-1 flex items-end gap-3 pb-4">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="bg-[#EBEBEB] rounded-t flex-1" style={{ height: `${20 + (i * 7) % 70}%` }}></div>
      ))}
    </div>
  </div>
);

// ── Monochromatic Toast Notification ─────────────────────────────────
const Toast = ({ message, type = 'info', onClose }) => {
  const borderStyles = {
    success: 'border-[#111111] text-[#111111]',
    error: 'border-red-600 text-red-700',
    warning: 'border-amber-500 text-amber-800',
    info: 'border-[#EBEBEB] text-[#111111]',
  };
  const icons = {
    success: <CheckCircle2 size={16} className="text-[#111111]" />,
    error: <AlertCircle size={16} className="text-red-600" />,
    warning: <AlertTriangle size={16} className="text-amber-500" />,
    info: <Send size={16} className="text-[#111111]" />,
  };

  return (
    <div className={`border-l-4 bg-white border border-y-[#EBEBEB] border-r-[#EBEBEB] px-4 py-3 flex items-center justify-between text-xs font-semibold shadow-sm animate-in fade-in slide-in-from-top duration-200 ${borderStyles[type]}`}>
      <span className="flex items-center gap-2">
        {icons[type]} {message}
      </span>
      <button onClick={onClose} className="hover:opacity-70 text-[#666666] ml-4"><X size={14} /></button>
    </div>
  );
};

// ── Sanitized Error Classifier ───────────────────────────────────────
function classifyError(err, response) {
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
}

export default function GoChickenDashboard({ defaultTab = 'overview' }) {
  const router = useRouter();
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [showNotifications, setShowNotifications] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddTruckModal, setShowAddTruckModal] = useState(false);
  const [showSplash, setShowSplash] = useState(true); // Default true to prevent UI flashing
  const [fadeSplash, setFadeSplash] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showRefreshVideo, setShowRefreshVideo] = useState(false);

  // Sync tab switching to browser address bar without reloads
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    if (typeof window !== 'undefined') {
      const newPath = tabId === 'overview' ? '/' : `/${tabId}`;
      window.history.pushState(null, '', newPath);
    }
  };

  // ── Live Data State (fetched from API) ─────────────────────────────
  const [ordersList, setOrdersList] = useState([]);
  const [productPrices, setProductPrices] = useState([]);
  const [trucks, setTrucks] = useState([]);

  // ── Loading & Error States ─────────────────────────────────────────
  const [isLoadingOrders, setIsLoadingOrders] = useState(true);
  const [isLoadingPrices, setIsLoadingPrices] = useState(true);
  const [isLoadingTrucks, setIsLoadingTrucks] = useState(true);
  const [ordersError, setOrdersError] = useState(null);
  const [pricesError, setPricesError] = useState(null);
  const [trucksError, setTrucksError] = useState(null);

  // ── UI Feedback State ──────────────────────────────────────────────
  const [editingPrice, setEditingPrice] = useState(null);
  const [priceSuccessMsg, setPriceSuccessMsg] = useState(null);
  const [toasts, setToasts] = useState([]);
  const toastIdRef = useRef(0);

  // ── Toast Helper ───────────────────────────────────────────────────
  const addToast = useCallback((message, type = 'info', duration = 5000) => {
    const id = ++toastIdRef.current;
    setToasts(prev => [...prev, { id, message, type }]);
    if (duration > 0) {
      setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // ── Data Fetch Functions ───────────────────────────────────────────
  const fetchOrders = useCallback(async (silent = false) => {
    if (!silent) setIsLoadingOrders(true);
    try {
      const res = await fetch(`${API_BASE}/orders/`);
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
      const res = await fetch(`${API_BASE}/pricing/`);
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
      const res = await fetch(`${API_BASE}/trucks/`);
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

  const fetchAll = useCallback(async (silent = false) => {
    await Promise.allSettled([
      fetchOrders(silent),
      fetchPrices(silent),
      fetchTrucks(silent),
    ]);
  }, [fetchOrders, fetchPrices, fetchTrucks]);

  const handleRefresh = useCallback(() => {
    setShowRefreshVideo(true);
    fetchAll(false);
    setTimeout(() => {
      setShowRefreshVideo(false);
    }, 4000);
  }, [fetchAll]);

  // ── Initial Load + 15s Polling with Page Visibility API ────────────
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchAll(false);
    const clockTimer = setInterval(() => setCurrentTime(new Date()), 60000);
    const pollTimer = setInterval(() => {
      if (document.hidden) return;
      fetchAll(true);
    }, 15000);

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchAll(true);
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(clockTimer);
      clearInterval(pollTimer);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchAll]);

  // ── Session Flow & Welcome Splash Animation ────────────────────
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('gc_token');
      const visitedLanding = sessionStorage.getItem('gc_visited_landing');
      const welcomePlayed = sessionStorage.getItem('gc_welcome_played');

      // 1. If not authenticated or opening app for first time in browser session -> face the landing page
      if (!token || !visitedLanding) {
        router.replace('/landing');
        return;
      }

      // 2. If already logged in and welcome video already played in this session -> show dashboard directly
      if (welcomePlayed) {
        setShowSplash(false);
        setFadeSplash(true);
        return;
      }

      // 3. Play Go Chicken welcome animated video for 4 seconds, then reveal dashboard
      setShowSplash(true);
      setFadeSplash(false);
      const timer = setTimeout(() => {
        setFadeSplash(true);
        setTimeout(() => {
          setShowSplash(false);
          sessionStorage.setItem('gc_welcome_played', 'true');
        }, 500);
      }, 4000);

      return () => clearTimeout(timer);
    }
  }, [router]);

  // ── Optimistic Status Toggle (with differentiated error rollback) ──
  const handleStatusToggle = async (orderId, newStatus) => {
    const previousOrders = [...ordersList];
    setOrdersList(prev => prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o));

    let response;
    try {
      response = await fetch(`${API_BASE}/orders/${orderId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      addToast(`📲 WhatsApp Alert Sent: Order marked as ${newStatus.toUpperCase()}!`, 'success');
    } catch (err) {
      setOrdersList(previousOrders);
      const { type, message } = classifyError(err, response);
      addToast(message, type, 8000);
    }
  };

  // ── Optimistic Rate Update ─────────────────────────────────────────
  const handleUpdateRate = async (item_type, new_val) => {
    const val = parseFloat(new_val);
    if (!val || val <= 0) return;

    const previousPrices = [...productPrices];
    setProductPrices(prev => prev.map(p => p.item_type === item_type ? { ...p, price_per_kg: val } : p));
    setEditingPrice(null);

    let response;
    try {
      response = await fetch(`${API_BASE}/pricing/${encodeURIComponent(item_type)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ price_per_kg: val })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      addToast(`📊 Rate card updated: ${item_type.toUpperCase()} is now ₹${val}/kg. Broadcasted to bot.`, 'success');
    } catch (err) {
      setProductPrices(previousPrices);
      const { type, message } = classifyError(err, response);
      addToast(message, type, 8000);
    }
  };

  // ── Record Payment (POST /api/v1/khata/transaction) ────────────────
  const handlePaymentSubmit = async (e) => {
    e.preventDefault();
    const retailerName = e.target.retailer.value;
    const amount = parseFloat(e.target.amount.value);
    const note = e.target.note.value;

    setShowPaymentModal(false);

    let response;
    try {
      response = await fetch(`${API_BASE}/khata/transaction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          retailer_id: "00000000-0000-0000-0000-000000000000",
          type: "payment",
          amount: amount,
          reference_note: note || `Payment from ${retailerName}`
        })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      addToast(`💳 Payment of ₹${amount.toLocaleString()} recorded for ${retailerName}.`, 'success');
    } catch (err) {
      const { type, message } = classifyError(err, response);
      addToast(message, type, 8000);
    }
  };

  // ── Add Truck (calls POST /api/v1/trucks) ──────────────────────────
  const handleAddTruck = async (e) => {
    e.preventDefault();
    const plate = e.target.plate.value;
    const capacity = parseInt(e.target.capacity.value);
    const deviceId = e.target.deviceId.value;

    const previousTrucks = [...trucks];
    const optimisticTruck = {
      id: `temp-${Date.now()}`,
      tenant_id: '',
      license_plate: plate,
      max_capacity_kg: capacity,
      iot_device_id: deviceId,
      driver_id: null,
      created_at: new Date().toISOString(),
    };
    setTrucks(prev => [optimisticTruck, ...prev]);
    setShowAddTruckModal(false);

    let response;
    try {
      response = await fetch(`${API_BASE}/trucks/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          license_plate: plate,
          max_capacity_kg: capacity,
          iot_device_id: deviceId || null,
        })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const created = await response.json();
      setTrucks(prev => prev.map(t => t.id === optimisticTruck.id ? created : t));
      addToast(`🚛 Truck ${plate} added to fleet!`, 'success');
    } catch (err) {
      setTrucks(previousTrucks);
      const { type, message } = classifyError(err, response);
      addToast(message, type, 8000);
    }
  };

  const activeAlerts = trucks.filter(t => t.status === 'alert').length;
  const totalOutstanding = MOCK_KHATA.filter(k => k.balance > 0).reduce((acc, curr) => acc + curr.balance, 0);
  const totalCapacity = trucks.reduce((sum, truck) => sum + (truck.max_capacity_kg || truck.capacity || 0), 0);

  // ── Error Banner Component ─────────────────────────────────────────
  const ErrorBanner = ({ message, onRetry }) => (
    <div className="flex flex-col items-center justify-center py-12 text-[#666666] bg-white border border-[#EBEBEB] rounded-xl">
      <WifiOff size={32} className="mb-3 text-[#111111]" />
      <p className="font-semibold text-xs uppercase tracking-wider">{message}</p>
      <AnimatedButton
        onClick={onRetry}
        className="mt-4 w-auto px-6"
      >
        Try Again
      </AnimatedButton>
    </div>
  );

  // ── Navigation Components (Strict Monochrome B&W) ─────────────────

  const Sidebar = () => (
    <div className="w-64 bg-white text-[#111111] min-h-screen flex-col fixed left-0 top-0 border-r border-[#EBEBEB] hidden md:flex z-40">
      <div className="p-6 border-b border-[#EBEBEB]">
        <div className="flex items-center gap-2.5">
          <div className="p-1 rounded-md bg-white border border-[#EBEBEB]">
            <img src="/logo.png" alt="Go Chicken Logo" className="w-5 h-5 object-contain" />
          </div>
          <div>
            <h1 className="text-sm font-extrabold tracking-tight uppercase text-[#111111]">Go Chicken</h1>
            <p className="text-[#666666] text-[9px] font-bold tracking-wider uppercase">Enterprise SaaS</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-4 mt-6 space-y-1">
        {[
          { id: 'overview', icon: LayoutDashboard, label: t('Overview') },
          { id: 'orders', icon: ShoppingCart, label: t('Orders & Pricing') },
          { id: 'fleet', icon: Truck, label: t('IoT Fleet'), alert: activeAlerts > 0 },
          { id: 'khata', icon: Wallet, label: t('Retailer Khata') },
          { id: 'ai', icon: BrainCircuit, label: t('AI Forecasting') }
        ].map(item => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleTabChange(item.id)}
              className={`w-full flex items-center justify-between px-4 py-2.5 rounded-lg transition-colors ${isActive
                ? 'bg-[#111111] text-white font-semibold'
                : 'text-[#666666] hover:bg-[#FAFAFA] hover:text-[#111111]'
                }`}
            >
              <div className="flex items-center gap-3">
                <item.icon size={16} strokeWidth={isActive ? 2.5 : 2} />
                <span className="font-semibold text-xs uppercase tracking-wider">{item.label}</span>
              </div>
              {item.alert && (
                <span className="h-2 w-2 rounded-full bg-black"></span>
              )}
            </button>
          );
        })}
      </nav>

      <Link href="/profile" className="block p-4 m-4 bg-[#FAFAFA] hover:bg-white rounded-xl border border-[#EBEBEB] hover:border-[#111111] transition-all cursor-pointer group">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#111111] text-white flex items-center justify-center font-extrabold text-xs group-hover:scale-105 transition-transform">
            JS
          </div>
          <div>
            <p className="text-xs font-bold text-[#111111]">Jagan Supplies</p>
            <p className="text-[9px] text-[#666666] flex items-center gap-1 font-semibold uppercase mt-0.5">
              <MapPin size={8} /> Vijayawada Hub
            </p>
          </div>
        </div>
      </Link>
    </div>
  );

  const Header = () => (
    <header className="bg-white h-16 border-b border-[#EBEBEB] flex items-center justify-between px-6 md:px-8 sticky top-0 z-30">
      {/* Mobile Top App Bar */}
      <div className="flex items-center justify-between w-full md:hidden">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-md bg-white border border-[#EBEBEB]">
            <img src="/logo.png" alt="Go Chicken Logo" className="w-4 h-4 object-contain" />
          </div>
          <span className="font-extrabold text-sm tracking-tight text-[#111111] uppercase">Go Chicken</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="p-2 text-[#666666] hover:text-[#111111] rounded-lg transition-colors"
            aria-label="Toggle mobile menu"
          >
            {showMobileMenu ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {showMobileMenu && (
        <div className="absolute top-[64px] right-4 z-40 md:hidden">
          <div className="bg-white border border-[#EBEBEB] rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-2 flex flex-col min-w-[160px] animate-wave origin-top-right">
            <button
              onClick={() => { handleRefresh(); setShowMobileMenu(false); }}
              className="flex items-center justify-start gap-3 px-4 py-2.5 text-xs font-bold text-[#111111] hover:bg-[#FAFAFA] rounded-xl transition-colors w-full"
            >
              <RefreshCw size={16} className="text-[#666666]" /> {t('Refresh')}
            </button>
            <div className="h-px w-full bg-[#EBEBEB] my-0.5"></div>
            <button
              onClick={() => { setShowNotifications(!showNotifications); setShowMobileMenu(false); }}
              className="flex items-center justify-between px-4 py-2.5 text-xs font-bold text-[#111111] hover:bg-[#FAFAFA] rounded-xl transition-colors w-full"
            >
              <div className="flex items-center gap-3">
                <Bell size={16} className="text-[#666666]" /> {t('Alerts')}
              </div>
              {activeAlerts > 0 && (
                <span className="bg-black text-white text-[9px] px-1.5 py-0.5 rounded-full font-bold ml-2">{activeAlerts}</span>
              )}
            </button>
            <div className="h-px w-full bg-[#EBEBEB] my-0.5"></div>
            <Link
              href="/profile"
              onClick={() => setShowMobileMenu(false)}
              className="flex items-center justify-start gap-3 px-4 py-2.5 text-xs font-bold text-[#111111] hover:bg-[#FAFAFA] rounded-xl transition-colors w-full"
            >
              <User size={16} className="text-[#666666]" /> {t('Profile')}
            </Link>
          </div>
        </div>
      )}

      {/* Desktop Header */}
      <div className="hidden md:flex items-center justify-between w-full">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-extrabold text-[#111111] tracking-tight capitalize">
            {t(activeTab === 'ai' ? 'AI Forecast' : activeTab.replace('-', ' '))}
          </h2>
        </div>
        <div className="flex items-center gap-6">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search..."
              className="pl-9 pr-4 py-1.5 bg-[#FAFAFA] border border-[#EBEBEB] rounded-lg text-xs text-[#111111] focus:bg-white focus:border-[#111111] transition-all outline-none w-48"
            />
          </div>
          <button
            onClick={() => handleRefresh()}
            title="Refresh dashboard data"
            className="p-1.5 text-[#666666] hover:text-[#111111] hover:bg-[#FAFAFA] border border-transparent hover:border-[#EBEBEB] rounded-lg transition-all"
          >
            <RefreshCw size={16} />
          </button>
          <div className="flex items-center gap-4 border-l pl-6 border-[#EBEBEB]">
            <div className="text-right">
              <p className="text-xs font-bold text-[#111111]" suppressHydrationWarning>
                {currentTime.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' })}
              </p>
              <p className="text-[10px] text-[#666666] font-medium" suppressHydrationWarning>{currentTime.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</p>
            </div>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-1.5 text-[#666666] hover:text-[#111111] hover:bg-[#FAFAFA] border border-transparent hover:border-[#EBEBEB] rounded-lg transition-all"
            >
              <Bell size={18} />
              {activeAlerts > 0 && (
                <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-black rounded-full border border-white"></span>
              )}
            </button>
          </div>
        </div>
      </div>

      {showNotifications && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowNotifications(false)}
          ></div>
          <div className="absolute right-6 top-14 w-72 bg-white border border-[#EBEBEB] rounded-xl overflow-hidden z-50 shadow-[0_8px_30px_rgb(0,0,0,0.12)] animate-wave origin-top-right">
            <div className="p-3 bg-[#FAFAFA] border-b border-[#EBEBEB] font-bold text-[#111111] text-xs uppercase tracking-wider">{t('Notifications')}</div>
            <div className="divide-y divide-[#EBEBEB] max-h-60 overflow-auto">
              <div className="p-3.5 text-xs hover:bg-[#FAFAFA] transition-colors">
                <p className="font-bold text-[#111111]">Truck T-102 Temperature Alert</p>
                <p className="text-[#666666] mt-0.5">Exceeded 30°C in Patamata.</p>
              </div>
              <div className="p-3.5 text-xs hover:bg-[#FAFAFA] transition-colors">
                <p className="font-bold text-emerald-700">Payment Confirmed</p>
                <p className="text-[#666666] mt-0.5">₹5,000 credited to Khata R-01.</p>
              </div>
            </div>
          </div>
        </>
      )}
    </header>
  );

  const BottomNav = () => {
    const navItems = [
      { id: 'overview', icon: LayoutDashboard, label: t('Overview') },
      { id: 'orders', icon: ShoppingCart, label: t('Orders') },
      { id: 'fleet', icon: Truck, label: t('Fleet'), alert: activeAlerts > 0 },
      { id: 'khata', icon: Wallet, label: t('Khata') }
    ];

    return (
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-[#EBEBEB] flex justify-around items-center pt-2 pb-6 md:pb-2 md:hidden shadow-[0_-4px_24px_rgba(0,0,0,0.02)]">
        {navItems.map(item => {
          const isActive = activeTab === item.id;
          const IconComponent = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => handleTabChange(item.id)}
              className="flex flex-col items-center justify-center flex-1 py-1 text-center relative"
            >
              <div className={`p-1 rounded-md transition-colors ${isActive ? 'text-[#111111]' : 'text-[#666666]'}`}>
                <IconComponent size={20} strokeWidth={isActive ? 2.5 : 2} />
              </div>
              <span className={`text-[9px] font-bold uppercase tracking-wider mt-0.5 ${isActive ? 'text-[#111111]' : 'text-[#666666]'}`}>
                {item.label}
              </span>
              {item.alert && (
                <span className="absolute top-1 right-1/3 w-2 h-2 bg-black rounded-full"></span>
              )}
            </button>
          );
        })}
      </div>
    );
  };

  // ── Tab Layout Renderers ───────────────────────────────────────────

  const renderOverview = () => (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Horizontal Snap Scroll Row on Mobile, Normal Grid on Desktop */}
      <div className="flex md:grid overflow-x-auto md:overflow-visible snap-x snap-mandatory sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6 pb-4 md:pb-0 -mx-4 px-4 sm:-mx-6 sm:px-6 md:mx-0 md:px-0 scrollbar-none after:content-[''] after:w-4 after:flex-shrink-0 sm:after:hidden">
        <StatBox
          title={t("Tomorrow's Forecast")}
          value={`${MOCK_AI_FORECAST.predictedKg} kg`}
          icon={BrainCircuit}
          subtitle={`↑ 8.8% vs Today (${MOCK_AI_FORECAST.confidence}% confidence)`}
          trend="up"
        />
        <StatBox
          title={t("Active Fleet")}
          value={isLoadingTrucks ? '...' : `${trucks.filter(t => t.status === 'safe').length}/${trucks.length}`}
          icon={Truck}
          subtitle={`Total Capacity: ${totalCapacity.toLocaleString()} kg`}
        />
        <StatBox
          title={t("Critical IoT Alerts")}
          value={activeAlerts.toString()}
          icon={AlertTriangle}
          alert={activeAlerts > 0}
          subtitle="T-102 exceeding 30°C"
          trend="down"
        />
        <StatBox
          title={t("Total Outstanding")}
          value={`₹${totalOutstanding.toLocaleString()}`}
          icon={Wallet}
          subtitle="From 12 retailers"
          trend="down"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <Card className="lg:col-span-2 p-4 sm:p-6 bg-white">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-[#111111]">{t('Sales vs AI Forecast')}</h3>
            <select className="text-xs bg-[#FAFAFA] border border-[#EBEBEB] rounded-lg px-2.5 py-1.5 outline-none font-bold text-[#111111]">
              <option>Last 7 Days</option>
              <option>This Month</option>
            </select>
          </div>
          <div className="h-56 sm:h-72 lg:h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={MOCK_SALES_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F5F5F5" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#666666', fontSize: 10, fontWeight: 'semibold' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#666666', fontSize: 10, fontWeight: 'semibold' }} />
                <RechartsTooltip
                  contentStyle={{ borderRadius: '8px', border: '1px solid #EBEBEB', backgroundColor: '#FFFFFF', color: '#111111', fontSize: '11px' }}
                  cursor={{ stroke: '#111111', strokeWidth: 1, strokeDasharray: '4 4' }}
                />
                <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: '11px', fontWeight: 'bold' }} />
                <Line type="monotone" dataKey="actual" name="Actual Sales (kg)" stroke="#111111" strokeWidth={2.5} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="predicted" name="AI Predicted (kg)" stroke="#666666" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-4 sm:p-6 flex flex-col bg-white">
          <h3 className="font-extrabold text-sm uppercase tracking-wider text-[#111111] mb-6">{t('Live Truck Status')}</h3>
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {isLoadingTrucks ? (
              <div className="space-y-3">
                <div className="h-16 bg-[#FAFAFA] border border-[#EBEBEB] rounded-xl animate-pulse"></div>
                <div className="h-16 bg-[#FAFAFA] border border-[#EBEBEB] rounded-xl animate-pulse"></div>
              </div>
            ) : trucks.length === 0 ? (
              <p className="text-xs text-[#666666] font-semibold uppercase tracking-wider text-center py-8">No trucks registered.</p>
            ) : (
              trucks.map((truck, idx) => (
                <div key={truck.id || idx} className="p-4 rounded-xl border border-[#EBEBEB] bg-white hover:border-[#111111] transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#111111] text-xs">{truck.iot_device_id || truck.id?.toString().slice(0, 8)}</span>
                      <span className="text-[10px] font-bold text-[#666666] bg-[#FAFAFA] px-2 py-0.5 rounded border border-[#EBEBEB]">{truck.license_plate || truck.plate}</span>
                    </div>
                    {truck.status === 'alert' ? (
                      <span className="flex items-center gap-1 text-[10px] font-bold text-red-700 border border-red-200 bg-red-50/50 px-2 py-0.5 rounded-full animate-pulse">
                        <Thermometer size={10} /> {truck.temp}°C
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[10px] font-bold text-[#111111] border border-[#EBEBEB] bg-[#FAFAFA] px-2 py-0.5 rounded-full">
                        <Thermometer size={10} /> {truck.temp || '—'}°C
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[#666666] mb-3">
                    <MapPin size={12} className="text-[#666666]" />
                    <span className="font-medium">{truck.last_location || 'Vijayawada Outer Ring Rd'}</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-bold text-[#666666] uppercase tracking-wider">
                      <span>Loaded Capacity</span>
                      <span>{truck.loaded || 0} / {truck.max_capacity_kg || truck.capacity || 2000} kg</span>
                    </div>
                    <div className="w-full bg-[#FAFAFA] border border-[#EBEBEB] h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${truck.status === 'alert' ? 'bg-red-600' : 'bg-[#111111]'}`}
                        style={{ width: `${truck.loaded ? (truck.loaded / (truck.max_capacity_kg || truck.capacity || 1)) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          <AnimatedButton
            onClick={() => handleTabChange('fleet')}
            className="mt-4 w-full"
          >
            {t('View Fleet Map')}
          </AnimatedButton>
        </Card>
      </div>
    </div>
  );

  const renderOrders = () => (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Rate Card Panel */}
      <Card className="p-0 overflow-hidden bg-white border border-[#EBEBEB]">
        <div className="p-6 border-b border-[#EBEBEB] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Tag className="text-[#111111]" size={18} />
              <h3 className="font-extrabold text-sm uppercase tracking-wider text-[#111111]">Live Rate Card Control</h3>
            </div>
            <p className="text-xs text-[#666666] mt-1">
              Changes update immediately across the system, syncing with WhatsApp bot price lookups.
            </p>
          </div>
          <span className="self-start md:self-auto bg-[#FAFAFA] text-[#111111] border border-[#EBEBEB] px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5">
            <Zap size={12} className="text-[#111111]" /> Active Database Connection
          </span>
        </div>

        {priceSuccessMsg && (
          <Toast message={priceSuccessMsg} type="success" onClose={() => setPriceSuccessMsg(null)} />
        )}

        <div className="p-4 sm:p-6 bg-[#FAFAFA] grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 border-t border-[#EBEBEB]">
          {isLoadingPrices ? (
            <div className="col-span-3 space-y-2">
              <div className="h-16 bg-white border border-[#EBEBEB] rounded-xl animate-pulse"></div>
            </div>
          ) : pricesError ? (
            <div className="col-span-3">
              <ErrorBanner message={pricesError} onRetry={() => fetchPrices(false)} />
            </div>
          ) : (
            productPrices.map((item, idx) => (
              <div key={idx} className="bg-white rounded-xl p-5 border border-[#EBEBEB] transition-colors hover:border-[#111111] relative">
                <div className="flex justify-between items-start mb-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded bg-[#FAFAFA] text-[#111111] border border-[#EBEBEB]">
                    {item.item_type}
                  </span>
                  <span className="text-[10px] font-bold text-[#666666] uppercase">INR / kg</span>
                </div>

                {editingPrice && editingPrice.item_type === item.item_type ? (
                  <div className="mt-2 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xl font-bold text-[#666666]">₹</span>
                      <input
                        type="number"
                        value={editingPrice.val}
                        onChange={(e) => setEditingPrice({ ...editingPrice, val: e.target.value })}
                        className="w-full text-xl font-bold px-3 py-1 border border-[#111111] rounded-lg focus:outline-none bg-[#FAFAFA] text-[#111111]"
                        autoFocus
                      />
                    </div>
                    <div className="flex gap-2">
                      <AnimatedButton
                        onClick={() => handleUpdateRate(item.item_type, editingPrice.val)}
                        className="flex-1"
                      >
                        Save Rate
                      </AnimatedButton>
                      <button
                        onClick={() => setEditingPrice(null)}
                        className="bg-[#FAFAFA] border border-[#EBEBEB] hover:bg-[#F0F0F0] text-[#111111] font-bold text-xs px-3 py-2 rounded-lg"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-2 flex items-baseline justify-between">
                    <div>
                      <h4 className="text-3xl font-extrabold text-[#111111] tracking-tight">₹{item.price_per_kg}</h4>
                      <p className="text-[10px] font-semibold text-[#666666] uppercase mt-1">Live Inquiries</p>
                    </div>
                    <button
                      onClick={() => setEditingPrice({ item_type: item.item_type, val: item.price_per_kg.toString() })}
                      className="bg-white border border-[#EBEBEB] hover:bg-[#FAFAFA] text-[#111111] px-3 py-1.5 rounded-lg flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider"
                    >
                      <Edit3 size={12} /> Edit
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Orders Table */}
      <Card className="p-0 overflow-hidden bg-white border border-[#EBEBEB]">
        <div className="p-6 border-b border-[#EBEBEB] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Package className="text-[#111111]" size={18} />
              <h3 className="font-extrabold text-sm uppercase tracking-wider text-[#111111]">Live Order Feed</h3>
            </div>
            <p className="text-xs text-[#666666] mt-1">
              Fulfillment triggers instant confirmation messages directly to registered retailers.
            </p>
          </div>
          <button
            onClick={() => fetchOrders(false)}
            className="self-start md:self-auto bg-white hover:bg-[#FAFAFA] text-[#111111] px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 border border-[#EBEBEB]"
          >
            <RefreshCw size={12} /> Refresh Feed
          </button>
        </div>

        {toasts.map(t => (
          <Toast key={t.id} message={t.message} type={t.type} onClose={() => removeToast(t.id)} />
        ))}

        {isLoadingOrders ? (
          <TableSkeleton rows={4} cols={7} />
        ) : ordersError ? (
          <ErrorBanner message={ordersError} onRetry={() => fetchOrders(false)} />
        ) : (
          <>
            {/* ── Desktop/Tablet Table (hidden on small mobile) ── */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#FAFAFA] border-b border-[#EBEBEB] text-[10px] uppercase tracking-wider text-[#666666] font-bold">
                    <th className="p-4 pl-6">Order ID</th>
                    <th className="p-4">Phone Number</th>
                    <th className="p-4">Item Type</th>
                    <th className="p-4">Quantity</th>
                    <th className="p-4">Total Amount</th>
                    <th className="p-4">AI Source</th>
                    <th className="p-4 text-center pr-6">Status & Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EBEBEB] text-xs font-medium text-[#111111]">
                  {ordersList.filter(o => !searchQuery || o.phone_number?.includes(searchQuery) || o.item_type?.toLowerCase().includes(searchQuery.toLowerCase()) || o.id?.toLowerCase().includes(searchQuery.toLowerCase())).map((order, idx) => (
                    <tr key={order.id || idx} className="hover:bg-[#FAFAFA]/50 transition-colors">
                      <td className="p-4 pl-6">
                        <p className="font-mono text-xs font-bold text-[#111111]">{(order.id || '').toString().slice(0, 8)}</p>
                        <p className="text-[10px] text-[#666666] mt-0.5 font-semibold">{order.created_at ? new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}</p>
                      </td>
                      <td className="p-4 font-bold">{order.phone_number || "Manual Ingestion"}</td>
                      <td className="p-4">
                        <span className="font-extrabold">{order.item_type}</span>
                      </td>
                      <td className="p-4">
                        <span className="bg-[#FAFAFA] text-[#111111] font-bold px-2 py-1 rounded border border-[#EBEBEB]">
                          {order.quantity_kg} kg
                        </span>
                      </td>
                      <td className="p-4 font-extrabold text-[#111111]">
                        ₹{order.total_amount ? order.total_amount.toLocaleString() : (order.quantity_kg * 180).toLocaleString()}
                      </td>
                      <td className="p-4">
                        <span className="inline-flex items-center bg-[#FAFAFA] text-[#111111] border border-[#EBEBEB] px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                          {order.order_source === 'ollama' ? '🤖 Ollama' : '📐 Regex'}
                        </span>
                      </td>
                      <td className="p-4 text-center pr-6">
                        <div className="flex items-center justify-center gap-2">
                          {order.status === 'pending' && (
                            <>
                              <span className="bg-[#FAFAFA] text-[#666666] border border-[#EBEBEB] px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                                <Clock size={10} /> Pending
                              </span>
                              <button
                                onClick={() => handleStatusToggle(order.id, 'processing')}
                                className="bg-[#111111] hover:bg-black text-white px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 shadow-sm"
                              >
                                <Activity size={10} /> Process
                              </button>
                              <button
                                onClick={() => handleStatusToggle(order.id, 'delivered')}
                                className="bg-white border border-[#EBEBEB] hover:bg-[#FAFAFA] text-[#111111] px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1"
                              >
                                <Truck size={10} /> Deliver
                              </button>
                            </>
                          )}
                          {order.status === 'processing' && (
                            <>
                              <span className="bg-white text-[#111111] border border-[#111111] px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 animate-pulse">
                                <Activity size={10} /> Processing
                              </span>
                              <button
                                onClick={() => handleStatusToggle(order.id, 'delivered')}
                                className="bg-[#111111] hover:bg-black text-white px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1"
                              >
                                <Truck size={10} /> Mark Delivered
                              </button>
                            </>
                          )}
                          {order.status === 'delivered' && (
                            <span className="border border-[#EBEBEB] text-[#111111] px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-1">
                              <CheckCircle2 size={10} /> Delivered ✓
                            </span>
                          )}
                          {order.status === 'cancelled' && (
                            <span className="border border-red-200 bg-red-50/50 text-red-700 px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-1">
                              Cancelled
                            </span>
                          )}
                          {order.status !== 'pending' && (
                            <button
                              onClick={() => handleStatusToggle(order.id, 'pending')}
                              title="Reset order status"
                              className="text-[#666666] hover:text-[#111111] p-1 rounded hover:bg-[#FAFAFA] transition-colors border border-transparent hover:border-[#EBEBEB]"
                            >
                              <RefreshCw size={10} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {ordersList.length === 0 && (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-[#666666] font-bold uppercase tracking-wider text-xs">
                        <Package size={32} className="mx-auto mb-2 opacity-50 text-[#111111]" />
                        <p>No live orders found.</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* ── Mobile Card View (shown only on small screens) ── */}
            <div className="sm:hidden divide-y divide-[#EBEBEB]">
              {ordersList.filter(o => !searchQuery || o.phone_number?.includes(searchQuery) || o.item_type?.toLowerCase().includes(searchQuery.toLowerCase()) || o.id?.toLowerCase().includes(searchQuery.toLowerCase())).map((order, idx) => (
                <div key={order.id || idx} className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-mono text-xs font-bold text-[#111111]">{(order.id || '').toString().slice(0, 8)}</p>
                      <p className="text-[10px] text-[#666666] font-semibold mt-0.5">{order.created_at ? new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}</p>
                    </div>
                    <span className="inline-flex items-center bg-[#FAFAFA] text-[#111111] border border-[#EBEBEB] px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider">
                      {order.order_source === 'ollama' ? '🤖 Ollama' : '📐 Regex'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <p className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">Item</p>
                      <p className="font-extrabold text-sm text-[#111111]">{order.item_type}</p>
                    </div>
                    <div className="text-right space-y-0.5">
                      <p className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">Amount</p>
                      <p className="font-extrabold text-sm text-[#111111]">₹{order.total_amount ? order.total_amount.toLocaleString() : (order.quantity_kg * 180).toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="bg-[#FAFAFA] text-[#111111] font-bold px-2 py-1 rounded border border-[#EBEBEB] text-[10px]">
                      {order.quantity_kg} kg
                    </span>
                    <p className="text-[10px] text-[#666666] font-semibold">{order.phone_number || "Manual"}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap pt-1">
                    {order.status === 'pending' && (
                      <>
                        <span className="bg-[#FAFAFA] text-[#666666] border border-[#EBEBEB] px-2 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                          <Clock size={10} /> Pending
                        </span>
                        <button
                          onClick={() => handleStatusToggle(order.id, 'processing')}
                          className="bg-[#111111] hover:bg-black text-white px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 flex-1 justify-center"
                        >
                          <Activity size={10} /> Process
                        </button>
                        <button
                          onClick={() => handleStatusToggle(order.id, 'delivered')}
                          className="bg-white border border-[#EBEBEB] hover:bg-[#FAFAFA] text-[#111111] px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 flex-1 justify-center"
                        >
                          <Truck size={10} /> Deliver
                        </button>
                      </>
                    )}
                    {order.status === 'processing' && (
                      <>
                        <span className="bg-white text-[#111111] border border-[#111111] px-2 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 animate-pulse">
                          <Activity size={10} /> Processing
                        </span>
                        <button
                          onClick={() => handleStatusToggle(order.id, 'delivered')}
                          className="bg-[#111111] hover:bg-black text-white px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 flex-1 justify-center"
                        >
                          <Truck size={10} /> Delivered
                        </button>
                      </>
                    )}
                    {order.status === 'delivered' && (
                      <span className="border border-[#EBEBEB] text-[#111111] px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                        <CheckCircle2 size={10} /> Delivered ✓
                      </span>
                    )}
                    {order.status === 'cancelled' && (
                      <span className="border border-red-200 bg-red-50/50 text-red-700 px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                        Cancelled
                      </span>
                    )}
                    {order.status !== 'pending' && (
                      <button
                        onClick={() => handleStatusToggle(order.id, 'pending')}
                        title="Reset"
                        className="text-[#666666] hover:text-[#111111] p-1.5 rounded hover:bg-[#FAFAFA] border border-[#EBEBEB]"
                      >
                        <RefreshCw size={12} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {ordersList.length === 0 && (
                <div className="text-center py-12 text-[#666666] font-bold uppercase tracking-wider text-xs">
                  <Package size={32} className="mx-auto mb-2 opacity-50 text-[#111111]" />
                  <p>No live orders found.</p>
                </div>
              )}
            </div>
          </>
        )}
      </Card>
    </div>
  );

  const renderKhata = () => (
    <div className="animate-in fade-in duration-300 space-y-6">
      <Card className="p-0 bg-white">
        <div className="p-4 sm:p-6 border-b border-[#EBEBEB] flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 bg-white">
          <div>
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-[#111111]">Ledger Balance Dashboard</h3>
            <p className="text-xs text-[#666666] mt-1">Manage outstanding retailer payments and transaction limits.</p>
          </div>
          <button
            onClick={() => setShowPaymentModal(true)}
            className="self-start sm:self-auto bg-[#111111] hover:bg-black text-white px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider shadow-sm"
          >
            + Record Payment
          </button>
        </div>
        {/* ── Desktop/Tablet Table ── */}
        <div className="hidden sm:block overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#FAFAFA] border-b border-[#EBEBEB] text-[10px] uppercase tracking-wider text-[#666666] font-bold">
                <th className="p-4 pl-6">Retailer ID</th>
                <th className="p-4">Shop Details</th>
                <th className="p-4">Last Payment Date</th>
                <th className="p-4 text-right pr-6">Ledger Balance</th>
                <th className="p-4 text-center">Reminders</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EBEBEB] text-xs font-medium">
              {MOCK_KHATA.filter(k => k.shopName.toLowerCase().includes(searchQuery.toLowerCase()) || k.id.toLowerCase().includes(searchQuery.toLowerCase()) || k.phone.includes(searchQuery)).map((retailer, idx) => (
                <tr key={idx} className="hover:bg-[#FAFAFA]/50 transition-colors group">
                  <td className="p-4 pl-6 font-mono text-[#111111]">{retailer.id}</td>
                  <td className="p-4">
                    <p className="font-extrabold text-[#111111]">{retailer.shopName}</p>
                    <p className="text-[10px] text-[#666666] font-semibold">{retailer.phone}</p>
                  </td>
                  <td className="p-4 text-[#666666] font-bold">{retailer.lastPaid}</td>
                  <td className="p-4 text-right pr-6 font-extrabold">
                    <span className={retailer.balance > 0 ? 'text-red-700' : 'text-emerald-700'}>
                      {retailer.balance > 0 ? `₹${retailer.balance.toLocaleString()}` : `Advance: ₹${Math.abs(retailer.balance).toLocaleString()}`}
                    </span>
                  </td>
                  <td className="p-4 text-center">
                    <button
                      onClick={() => console.log(`Reminder sent to ${retailer.shopName}`)}
                      className="bg-white border border-[#EBEBEB] hover:bg-[#FAFAFA] text-[#111111] font-bold text-[10px] uppercase tracking-wider px-2 py-1 rounded transition-opacity"
                    >
                      Send WhatsApp
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* ── Mobile Card View ── */}
        <div className="sm:hidden divide-y divide-[#EBEBEB]">
          {MOCK_KHATA.filter(k => k.shopName.toLowerCase().includes(searchQuery.toLowerCase()) || k.id.toLowerCase().includes(searchQuery.toLowerCase()) || k.phone.includes(searchQuery)).map((retailer, idx) => (
            <div key={idx} className="p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-extrabold text-sm text-[#111111]">{retailer.shopName}</p>
                  <p className="text-[10px] text-[#666666] font-semibold mt-0.5">{retailer.phone}</p>
                </div>
                <span className="font-mono text-[10px] bg-[#FAFAFA] border border-[#EBEBEB] px-2 py-0.5 rounded text-[#666666]">{retailer.id}</span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[9px] font-bold text-[#666666] uppercase tracking-wider">Last Paid</p>
                  <p className="text-xs font-bold text-[#111111]">{retailer.lastPaid}</p>
                </div>
                <div className="text-right">
                  <p className="text-[9px] font-bold text-[#666666] uppercase tracking-wider">Balance</p>
                  <p className={`text-sm font-extrabold ${retailer.balance > 0 ? 'text-red-700' : 'text-emerald-700'}`}>
                    {retailer.balance > 0 ? `₹${retailer.balance.toLocaleString()}` : `Advance: ₹${Math.abs(retailer.balance).toLocaleString()}`}
                  </p>
                </div>
              </div>
              <button
                onClick={() => console.log(`Reminder sent to ${retailer.shopName}`)}
                className="w-full bg-white border border-[#EBEBEB] hover:bg-[#FAFAFA] text-[#111111] font-bold text-[10px] uppercase tracking-wider px-3 py-2 rounded-lg transition-colors"
              >
                Send WhatsApp Reminder
              </button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );

  const renderAI = () => (
    <div className="animate-in fade-in duration-300 space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <Card className="lg:col-span-1 p-4 sm:p-6 bg-white border border-[#EBEBEB] flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-6 border-b border-[#EBEBEB] pb-4">
              <BrainCircuit className="text-[#111111]" size={18} />
              <h3 className="font-extrabold text-xs uppercase tracking-wider text-[#111111]">Ollama Llama3 Engine</h3>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">Target Forecast Date</p>
                <p className="font-extrabold text-[#111111] mt-0.5">{MOCK_AI_FORECAST.targetDate}</p>
              </div>
              <div>
                <p className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">Predicted Volatility</p>
                <h2 className="text-4xl font-extrabold text-[#111111] tracking-tight mt-1">{MOCK_AI_FORECAST.predictedKg} <span className="text-sm font-semibold text-[#666666]">kg</span></h2>
              </div>
            </div>
          </div>

          <div className="mt-8 space-y-3">
            <div className="bg-[#FAFAFA] border border-[#EBEBEB] rounded-xl p-4">
              <p className="text-[9px] font-bold text-[#666666] uppercase tracking-wider">Environmental Context</p>
              <p className="font-bold text-xs text-[#111111] mt-1">{MOCK_AI_FORECAST.weather}</p>
            </div>
            <div className="bg-[#FAFAFA] border border-[#EBEBEB] rounded-xl p-4">
              <p className="text-[9px] font-bold text-[#666666] uppercase tracking-wider">AI Reasoning</p>
              <p className="text-xs text-[#666666] leading-relaxed mt-1 font-medium">{MOCK_AI_FORECAST.reasoning}</p>
            </div>
          </div>
        </Card>

        <Card className="lg:col-span-2 p-4 sm:p-6 flex flex-col bg-white">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 mb-6 border-b border-[#EBEBEB] pb-4">
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-[#111111]">Vector Similarity Search</h3>
            <p className="text-[10px] font-bold text-[#666666] bg-[#FAFAFA] px-2 py-1 rounded border border-[#EBEBEB] self-start sm:self-auto">nomic-embed-text</p>
          </div>
          <div className="flex-1 w-full min-h-[250px] sm:min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F5F5F5" />
                <XAxis type="number" dataKey="x" name="Feature X" tick={false} axisLine={false} />
                <YAxis type="number" dataKey="y" name="Demand (kg)" axisLine={false} tickLine={false} tick={{ fill: '#666666', fontSize: 10, fontWeight: 'bold' }} />
                <ZAxis type="number" dataKey="z" range={[50, 400]} />
                <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ borderRadius: '8px', border: '1px solid #EBEBEB', fontSize: '11px', color: '#111111' }} />
                <Scatter name="Demand Clusters" data={MOCK_SCATTER_DATA} fill="#111111" opacity={0.8} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );

  return (
    <div
      className="min-h-screen text-[#111111] font-sans flex flex-col md:flex-row w-full overflow-x-hidden pb-20 md:pb-0"
      style={{
        backgroundColor: '#FAFAFA',
        backgroundImage: "url('/chicken-pattern.svg')",
        backgroundRepeat: 'repeat',
        backgroundSize: '500px 500px',
      }}
    >
      {/* ── Welcome Splash Animation ── */}
      {showSplash && (
        <div className={`fixed inset-0 z-[100] flex flex-col bg-white transition-opacity duration-500 ${fadeSplash ? 'opacity-0' : 'opacity-100'}`}>
          {/* Desktop Video */}
          <video
            src="/desktop_welcome.mp4#t=0"
            autoPlay
            muted
            playsInline
            preload="auto"
            poster="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            className="hidden md:block absolute inset-0 w-full h-full object-cover"
          />
          {/* Mobile Video */}
          <video
            src="/mobile_welcome.mp4#t=0.5"
            autoPlay
            muted
            playsInline
            preload="auto"
            poster="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            className="block md:hidden absolute inset-0 w-full h-full object-contain"
          />
        </div>
      )}

      {/* ── Sidebar (Hidden on Mobile) ── */}
      {Sidebar()}

      <div className="flex-1 md:ml-64 flex flex-col min-h-screen">
        {Header()}

        <main className="flex-1 p-4 sm:p-6 md:p-8 overflow-auto">
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'orders' && renderOrders()}
          {activeTab === 'khata' && renderKhata()}
          {activeTab === 'ai' && renderAI()}

          {activeTab === 'fleet' && (
            <Card className="p-0 bg-white">
              <div className="p-4 sm:p-6 border-b border-[#EBEBEB] flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 bg-white">
                <div>
                  <h3 className="font-extrabold text-sm uppercase tracking-wider text-[#111111]">Fleet Management</h3>
                  <p className="text-xs text-[#666666] mt-1">Manage IoT-enabled trucks and deliveries.</p>
                </div>
                <button
                  onClick={() => setShowAddTruckModal(true)}
                  className="self-start sm:self-auto bg-[#111111] hover:bg-black text-white px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider shadow-sm animate-in fade-in"
                >
                  + Add Truck
                </button>
              </div>

              {isLoadingTrucks ? (
                TableSkeleton({ rows: 3, cols: 4 })
              ) : trucksError ? (
                ErrorBanner({ message: trucksError, onRetry: () => fetchTrucks(false) })
              ) : (
                <>
                  {/* ── Desktop/Tablet Table ── */}
                  <div className="hidden sm:block overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-[#FAFAFA] border-b border-[#EBEBEB] text-[10px] uppercase tracking-wider text-[#666666] font-bold">
                          <th className="p-4 pl-6">License Plate</th>
                          <th className="p-4">Capacity (kg)</th>
                          <th className="p-4">IoT Device ID</th>
                          <th className="p-4 text-center">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#EBEBEB] text-xs font-medium text-[#111111]">
                        {trucks.filter(t => {
                          const q = searchQuery.toLowerCase();
                          const plate = (t.license_plate || t.plate || '').toLowerCase();
                          const devId = (t.iot_device_id || t.id || '').toString().toLowerCase();
                          return plate.includes(q) || devId.includes(q);
                        }).map((truck, idx) => (
                          <tr key={truck.id || idx} className="hover:bg-[#FAFAFA]/50 transition-colors">
                            <td className="p-4 pl-6 font-bold">{truck.license_plate || truck.plate}</td>
                            <td className="p-4 font-bold">{truck.max_capacity_kg || truck.capacity} kg</td>
                            <td className="p-4">
                              <span className="bg-[#FAFAFA] text-[#111111] border border-[#EBEBEB] px-2 py-1 rounded font-mono text-[10px]">{truck.iot_device_id || truck.id?.toString().slice(0, 8)}</span>
                            </td>
                            <td className="p-4 text-center">
                              <button
                                onClick={() => setTrucks(prev => prev.filter(t => t.id !== truck.id))}
                                className="text-red-700 hover:underline font-bold uppercase text-[10px] tracking-wider"
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))}
                        {trucks.length === 0 && (
                          <tr>
                            <td colSpan={4} className="text-center py-12 text-[#666666] font-bold uppercase tracking-wider">
                              <Truck size={32} className="mx-auto mb-2 opacity-50 text-[#111111]" />
                              <p>No trucks registered.</p>
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  {/* ── Mobile Card View ── */}
                  <div className="sm:hidden divide-y divide-[#EBEBEB]">
                    {trucks.filter(t => {
                      const q = searchQuery.toLowerCase();
                      const plate = (t.license_plate || t.plate || '').toLowerCase();
                      const devId = (t.iot_device_id || t.id || '').toString().toLowerCase();
                      return plate.includes(q) || devId.includes(q);
                    }).map((truck, idx) => (
                      <div key={truck.id || idx} className="p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <p className="font-bold text-sm text-[#111111]">{truck.license_plate || truck.plate}</p>
                          <span className="bg-[#FAFAFA] text-[#111111] border border-[#EBEBEB] px-2 py-0.5 rounded font-mono text-[10px]">{truck.iot_device_id || truck.id?.toString().slice(0, 8)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[9px] font-bold text-[#666666] uppercase tracking-wider">Capacity</p>
                            <p className="text-xs font-bold text-[#111111]">{truck.max_capacity_kg || truck.capacity} kg</p>
                          </div>
                          <button
                            onClick={() => setTrucks(prev => prev.filter(t => t.id !== truck.id))}
                            className="text-red-700 font-bold uppercase text-[10px] tracking-wider border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-50"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                    {trucks.length === 0 && (
                      <div className="text-center py-12 text-[#666666] font-bold uppercase tracking-wider text-xs">
                        <Truck size={32} className="mx-auto mb-2 opacity-50 text-[#111111]" />
                        <p>No trucks registered.</p>
                      </div>
                    )}
                  </div>
                </>
              )}
            </Card>
          )}
        </main>

        {BottomNav()}

        {/* ── Monochromatic Sliding Bottom Sheets for Modals ── */}

        {showPaymentModal && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-end md:items-center justify-center z-50 transition-opacity">
            <div className="w-full md:max-w-md bg-white border border-[#EBEBEB] rounded-t-2xl md:rounded-2xl p-6 shadow-2xl animate-in slide-in-from-bottom md:zoom-in-95 duration-300">
              <div className="w-12 h-1 bg-[#EBEBEB] rounded-full mx-auto mb-6 md:hidden"></div>

              <h3 className="text-base font-extrabold text-[#111111] uppercase tracking-wider mb-6">Record Payment</h3>
              <form onSubmit={handlePaymentSubmit} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-[#666666] mb-1">Retailer Name</label>
                  <input name="retailer" type="text" required className="w-full px-3 py-2 border border-[#EBEBEB] rounded-lg focus:outline-none focus:border-[#111111] text-xs font-semibold text-[#111111] bg-[#FAFAFA]" placeholder="e.g. Raju Chicken Center" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-[#666666] mb-1">Amount (₹)</label>
                  <input name="amount" type="number" required className="w-full px-3 py-2 border border-[#EBEBEB] rounded-lg focus:outline-none focus:border-[#111111] text-xs font-semibold text-[#111111] bg-[#FAFAFA]" placeholder="5000" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-[#666666] mb-1">Reference Note</label>
                  <input name="note" type="text" className="w-full px-3 py-2 border border-[#EBEBEB] rounded-lg focus:outline-none focus:border-[#111111] text-xs font-semibold text-[#111111] bg-[#FAFAFA]" placeholder="Paid via UPI" />
                </div>
                <div className="flex gap-3 pt-4 pb-4 md:pb-0">
                  <button type="button" onClick={() => setShowPaymentModal(false)} className="flex-1 px-4 py-2.5 bg-[#FAFAFA] hover:bg-[#F0F0F0] border border-[#EBEBEB] text-[#111111] rounded-lg font-bold text-xs uppercase tracking-wider transition-colors">Cancel</button>
                  <AnimatedButton type="submit" className="flex-1">Save Payment</AnimatedButton>
                </div>
              </form>
            </div>
          </div>
        )}

        {showAddTruckModal && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] flex items-end md:items-center justify-center z-50 transition-opacity">
            <div className="w-full md:max-w-md bg-white border border-[#EBEBEB] rounded-t-2xl md:rounded-2xl p-6 shadow-2xl animate-in slide-in-from-bottom md:zoom-in-95 duration-300">
              <div className="w-12 h-1 bg-[#EBEBEB] rounded-full mx-auto mb-6 md:hidden"></div>

              <h3 className="text-base font-extrabold text-[#111111] uppercase tracking-wider mb-6">Add New Truck</h3>
              <form onSubmit={handleAddTruck} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-[#666666] mb-1">License Plate</label>
                  <input name="plate" type="text" required className="w-full px-3 py-2 border border-[#EBEBEB] rounded-lg focus:outline-none focus:border-[#111111] text-xs font-semibold text-[#111111] bg-[#FAFAFA]" placeholder="e.g. AP 16 XY 1234" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-[#666666] mb-1">Capacity (kg)</label>
                  <input name="capacity" type="number" required className="w-full px-3 py-2 border border-[#EBEBEB] rounded-lg focus:outline-none focus:border-[#111111] text-xs font-semibold text-[#111111] bg-[#FAFAFA]" placeholder="2000" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-[#666666] mb-1">IoT Device ID</label>
                  <input name="deviceId" type="text" className="w-full px-3 py-2 border border-[#EBEBEB] rounded-lg focus:outline-none focus:border-[#111111] text-xs font-semibold text-[#111111] bg-[#FAFAFA]" placeholder="e.g. T-104" />
                </div>
                <div className="flex gap-3 pt-4 pb-4 md:pb-0">
                  <button type="button" onClick={() => setShowAddTruckModal(false)} className="flex-1 px-4 py-2.5 bg-[#FAFAFA] hover:bg-[#F0F0F0] border border-[#EBEBEB] text-[#111111] rounded-lg font-bold text-xs uppercase tracking-wider transition-colors">Cancel</button>
                  <AnimatedButton type="submit" className="flex-1">Add Truck</AnimatedButton>
                </div>
              </form>
            </div>
          </div>
        )}

        {showRefreshVideo && (
          <div className="fixed inset-0 z-[100] bg-white animate-in fade-in duration-300">
            {/* Desktop Video */}
            <video
              src="/desktop_welcome.mp4#t=0"
              autoPlay
              muted
              playsInline
              className="hidden md:block w-full h-full object-cover"
            />
            {/* Mobile Video */}
            <video
              src="/mobile_welcome.mp4#t=0.5"
              autoPlay
              muted
              playsInline
              className="block md:hidden w-full h-full object-cover"
            />
          </div>
        )}
      </div>
    </div>
  );
}
