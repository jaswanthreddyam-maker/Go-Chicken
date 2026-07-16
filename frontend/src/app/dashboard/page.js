"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  LayoutDashboard, Truck, Wallet, BrainCircuit, AlertTriangle,
  Thermometer, MapPin, Package, Bell, Search, ChevronRight, Activity, CheckCircle2, Clock, RefreshCw, Zap, Edit3, Save, Send, Tag, ShoppingCart, WifiOff, AlertCircle, X, Menu, User, FileText
} from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import AuthGuard from '@/components/AuthGuard';
import { useUI } from '@/context/UIContext';
import { useDashboardData, DashboardDataProvider } from '@/context/DashboardDataContext';
import NotificationCenter from '@/components/dashboard/NotificationCenter';
import CommandPalette from '@/components/ui/CommandPalette';
import Drawer from '@/components/ui/Drawer';
import { OrderDrawerContent, RetailerDrawerContent, QuoteDrawerContent } from '@/components/dashboard/DrawerContents';

import { Card, Modal, Button, Form, FormField, Label, Input, Select, Toast, TableSkeleton, ChartSkeleton, classifyError, Page, PageHeader, DataTable } from '@/components/ui';
import { OverviewTab } from '@/components/dashboard/OverviewTab';
import { OrdersTab } from '@/components/dashboard/OrdersTab';
import { KhataTab } from '@/components/dashboard/KhataTab';
import { AITab } from '@/components/dashboard/AITab';
import { InventoryTab } from '@/components/dashboard/InventoryTab';
import { QuotesTab } from '@/components/dashboard/QuotesTab';
import { RetailersTab } from '@/components/dashboard/RetailersTab';

function GoChickenDashboard() {
  const router = useRouter();
  const { t } = useLanguage();
  
  // ── Consume UI context ──
  const {
    activeTab,
    handleTabChange,
    setPaletteOpen,
    drawerOpen,
    drawerContent,
    openDrawer,
    closeDrawer,
    toasts,
    addToast,
    removeToast
  } = useUI();

  // ── Consume Data context ──
  const {
    ordersList,
    productPrices,
    trucks,
    retailers,
    isLoadingOrders,
    isLoadingPrices,
    isLoadingTrucks,
    ordersError,
    pricesError,
    trucksError,
    fetchOrders,
    fetchPrices,
    fetchTrucks,
    fetchRetailers,
    fetchAll,
    handleRefresh,
    handleStatusToggle,
    handleUpdateRate,
    handlePaymentSubmit,
    handleAddTruck,
    livePulse,
    eventCount
  } = useDashboardData();

  const [currentTime, setCurrentTime] = useState(new Date());
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddTruckModal, setShowAddTruckModal] = useState(false);
  const [showSplash, setShowSplash] = useState(true); 
  const [fadeSplash, setFadeSplash] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showRefreshVideo, setShowRefreshVideo] = useState(false);

  // ── Clock Effect ──
  useEffect(() => {
    const clockTimer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(clockTimer);
  }, []);

  // ── Welcome Splash Animation ──
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('gc_user');
      const visitedLanding = sessionStorage.getItem('gc_visited_landing');
      const welcomePlayed = sessionStorage.getItem('gc_welcome_played');

      if (!token || !visitedLanding) {
        router.replace('/');
        return;
      }

      if (welcomePlayed) {
        setTimeout(() => {
          setShowSplash(false);
          setFadeSplash(true);
        }, 0);
        return;
      }

      const initTimer = setTimeout(() => {
        setShowSplash(true);
        setFadeSplash(false);
      }, 0);

      const timer = setTimeout(() => {
        setFadeSplash(true);
        setTimeout(() => {
          setShowSplash(false);
          sessionStorage.setItem('gc_welcome_played', 'true');
        }, 500);
      }, 4000);

      return () => {
        clearTimeout(initTimer);
        clearTimeout(timer);
      };
    }
  }, [router]);

  // ── Modal & Drawer action listeners for Command Palette triggers ──
  useEffect(() => {
    const handleTriggerPayment = () => setShowPaymentModal(true);
    const handleTriggerAddTruck = () => setShowAddTruckModal(true);
    const handleOpenOrderDrawer = (e) => openDrawer(<OrderDrawerContent order={e.detail} />);
    const handleOpenRetailerDrawer = (e) => openDrawer(<RetailerDrawerContent retailer={e.detail} />);
    const handleOpenQuoteDrawer = (e) => openDrawer(<QuoteDrawerContent quote={e.detail} />);
    
    window.addEventListener("gc_trigger_record_payment", handleTriggerPayment);
    window.addEventListener("gc_trigger_add_truck", handleTriggerAddTruck);
    window.addEventListener("gc_open_drawer_order", handleOpenOrderDrawer);
    window.addEventListener("gc_open_drawer_retailer", handleOpenRetailerDrawer);
    window.addEventListener("gc_open_drawer_quote", handleOpenQuoteDrawer);

    return () => {
      window.removeEventListener("gc_trigger_record_payment", handleTriggerPayment);
      window.removeEventListener("gc_trigger_add_truck", handleTriggerAddTruck);
      window.removeEventListener("gc_open_drawer_order", handleOpenOrderDrawer);
      window.removeEventListener("gc_open_drawer_retailer", handleOpenRetailerDrawer);
      window.removeEventListener("gc_open_drawer_quote", handleOpenQuoteDrawer);
    };
  }, [openDrawer]);

  const activeAlerts = trucks.filter(t => t.status === 'alert').length;
  const totalOutstanding = retailers.filter(r => Number(r.balance) > 0).reduce((acc, curr) => acc + Number(curr.balance), 0);
  const totalCapacity = trucks.reduce((sum, truck) => sum + (truck.max_capacity_kg || truck.capacity || 0), 0);

  // ── Error Banner Component ─────────────────────────────────────────
  const ErrorBanner = ({ message, onRetry }) => (
    <div className="flex flex-col items-center justify-center py-12 text-[#666666] bg-white border border-[#EBEBEB] rounded-xl">
      <WifiOff size={32} className="mb-3 text-[#111111]" />
      <p className="font-semibold text-xs uppercase tracking-wider">{message}</p>
      <Button
        onClick={onRetry}
        variant="primary"
        className="mt-4"
      >
        Try Again
      </Button>
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
          { id: 'quotes', icon: FileText, label: t('Quotes & Pricing') },
          { id: 'inventory', icon: Package, label: 'Inventory' },
          { id: 'retailers', icon: User, label: 'Retailers' },
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
          
          {/* Live Pulse & Event Counter */}
          <div className="flex items-center gap-2 px-3 py-1 bg-[#FAFAFA] border border-[#EBEBEB] rounded-full">
            <span className="relative flex h-2.5 w-2.5">
              {livePulse && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${livePulse ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]' : 'bg-green-500'}`}></span>
            </span>
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-[#111111]">
              Live
            </span>
            <div className="h-3 w-px bg-[#EBEBEB] mx-1"></div>
            <span className="text-[10px] font-bold text-[#666666]">
              Today's Activity: <span className="text-[#111111]">{eventCount}</span>
            </span>
          </div>
        </div>
        <div className="flex items-center gap-6">
          {/* Command Palette Trigger Input */}
          <div className="relative cursor-pointer" onClick={() => setPaletteOpen(true)}>
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
            <input
              type="text"
              readOnly
              placeholder="Search... (Ctrl+K)"
              className="pl-9 pr-4 py-1.5 bg-[#FAFAFA] border border-[#EBEBEB] rounded-lg text-xs text-[#111111] focus:bg-white focus:border-[#111111] transition-all outline-none w-48 cursor-pointer"
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
            <NotificationCenter />
          </div>
        </div>
      </div>
    </header>
  );

  const BottomNav = () => {
    const navItems = [
      { id: 'overview', icon: LayoutDashboard, label: t('Overview') },
      { id: 'orders', icon: ShoppingCart, label: t('Orders') },
      { id: 'retailers', icon: User, label: t('Retailers') },
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
                <span className="absolute top-1 right-1/3 w-2.5 h-2.5 bg-black rounded-full"></span>
              )}
            </button>
          );
        })}
      </div>
    );
  };

  // Legacies rendering tab helpers removed in favor of direct standard import instantiations

  return (
    <div
      className="min-h-screen bg-[#FAFAFA] text-[#111111] font-sans flex flex-col md:flex-row w-full overflow-x-hidden pb-20 md:pb-0"
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
          {activeTab === 'overview' && <OverviewTab />}
          {activeTab === 'orders' && <OrdersTab />}
          {activeTab === 'inventory' && <InventoryTab />}
          {activeTab === 'khata' && <KhataTab setShowPaymentModal={setShowPaymentModal} />}
          {activeTab === 'retailers' && <RetailersTab />}
          {activeTab === 'ai' && <AITab />}
          {activeTab === 'quotes' && <QuotesTab />}

          {activeTab === 'fleet' && (
            <Page>
              <PageHeader
                title="Fleet Management"
                description="Manage IoT-enabled trucks and deliveries."
              >
                <Button
                  variant="primary"
                  size="md"
                  onClick={() => setShowAddTruckModal(true)}
                >
                  + Add Truck
                </Button>
              </PageHeader>

              <DataTable
                columns={[
                  {
                    key: "license_plate",
                    label: "License Plate",
                    align: "left",
                    sortable: true,
                    render: (val, row) => (
                      <span className="font-bold">{val || row.plate}</span>
                    ),
                  },
                  {
                    key: "max_capacity_kg",
                    label: "Capacity",
                    align: "right",
                    sortable: true,
                    render: (val, row) => (
                      <span className="tabular-nums">{(val || row.capacity || 0).toLocaleString()} kg</span>
                    ),
                  },
                  {
                    key: "iot_device_id",
                    label: "IoT Device ID",
                    align: "left",
                    sortable: true,
                    render: (val, row) => (
                      <span className="bg-[var(--bg-app)] text-[var(--text-primary)] border border-[var(--border-subtle)] px-2 py-1 rounded font-mono text-[10px]">
                        {val || String(row.id || "").slice(0, 8)}
                      </span>
                    ),
                  },
                  {
                    key: "actions",
                    label: "Action",
                    align: "center",
                    render: (_, row) => (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => setTrucks(prev => prev.filter(t => t.id !== row.id))}
                      >
                        Delete
                      </Button>
                    ),
                  },
                ]}
                data={trucks}
                loading={isLoadingTrucks}
                emptyIcon={Truck}
                emptyTitle="No trucks registered"
                emptyDescription="Register your delivery fleet vehicles to monitor IoT temperature data."
                searchQuery={searchQuery}
                searchKeys={["license_plate", "plate", "iot_device_id"]}
                pageSize={10}
              />
            </Page>
          )}
        </main>

        {BottomNav()}

        {/* ── Monochromatic Sliding Bottom Sheets for Modals ── */}
        <Modal
          open={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          title="Record Payment"
          size="md"
        >
          <Form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            handlePaymentSubmit({
              retailer_id: formData.get("retailer_id"),
              amount: Number(formData.get("amount")),
              note: formData.get("note")
            });
            setShowPaymentModal(false);
          }}>
            <Modal.Body className="space-y-4">
              <FormField>
                <Label required>Retailer</Label>
                <Select name="retailer_id" required>
                  <option value="">Select Retailer</option>
                  {retailers.map(r => (
                    <option key={r.id} value={r.id}>{r.name || r.shopName} ({r.phone})</option>
                  ))}
                </Select>
              </FormField>
              <FormField>
                <Label required>Amount (₹)</Label>
                <Input name="amount" type="number" required placeholder="5000" />
              </FormField>
              <FormField>
                <Label>Reference Note</Label>
                <Input name="note" type="text" placeholder="Paid via UPI" />
              </FormField>
            </Modal.Body>
            <Modal.Footer>
              <Button variant="secondary" onClick={() => setShowPaymentModal(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                Save Payment
              </Button>
            </Modal.Footer>
          </Form>
        </Modal>

        <Modal
          open={showAddTruckModal}
          onClose={() => setShowAddTruckModal(false)}
          title="Add New Truck"
          size="md"
        >
          <Form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            handleAddTruck({
              license_plate: formData.get("plate"),
              max_capacity_kg: Number(formData.get("capacity")),
              iot_device_id: formData.get("deviceId")
            });
            setShowAddTruckModal(false);
          }}>
            <Modal.Body className="space-y-4">
              <FormField>
                <Label required>License Plate</Label>
                <Input name="plate" type="text" required placeholder="e.g. AP 16 XY 1234" />
              </FormField>
              <FormField>
                <Label required>Capacity (kg)</Label>
                <Input name="capacity" type="number" required placeholder="2000" />
              </FormField>
              <FormField>
                <Label>IoT Device ID</Label>
                <Input name="deviceId" type="text" placeholder="e.g. T-104" />
              </FormField>
            </Modal.Body>
            <Modal.Footer>
              <Button variant="secondary" onClick={() => setShowAddTruckModal(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                Add Truck
              </Button>
            </Modal.Footer>
          </Form>
        </Modal>

        {/* ── Global Search Command Palette ── */}
        <CommandPalette />

        {/* ── Universal Detail Drawer ── */}
        <Drawer open={drawerOpen} onClose={closeDrawer}>
          {drawerContent}
        </Drawer>

        {showRefreshVideo && (
          <div className="fixed inset-0 z-[100] bg-white animate-in fade-in duration-300">
            <video
              src="/desktop_welcome.mp4#t=0"
              autoPlay
              muted
              playsInline
              className="hidden md:block w-full h-full object-cover"
            />
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

export default function ProtectedDashboard(props) {
  return (
    <AuthGuard>
      <DashboardDataProvider>
        <GoChickenDashboard {...props} />
      </DashboardDataProvider>
    </AuthGuard>
  );
}
