"use client";

import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, Legend, Line
} from 'recharts';
import { 
  BrainCircuit, Truck, AlertTriangle, Wallet, MapPin, Thermometer, Settings, Check, ArrowLeft, ArrowRight
} from 'lucide-react';
import { Card, KPIStatCard, Button } from '@/components/ui';
import { useLanguage } from '@/context/LanguageContext';
import { useDashboardData } from '@/context/DashboardDataContext';
import { useUI } from '@/context/UIContext';
import PreferenceService from '@/services/PreferenceService';
import CountUp from 'react-countup';

const DEFAULT_LAYOUT = ["forecast", "fleet", "alerts", "outstanding"];

export function OverviewTab() {
  const { t } = useLanguage();
  const { handleTabChange } = useUI();
  const {
    MOCK_AI_FORECAST,
    MOCK_SALES_DATA,
    trucks,
    retailers,
    isLoadingTrucks,
    totalOutstanding,
    totalCapacity,
    activeAlerts,
    operationsFeed
  } = useDashboardData();

  // ── Layout Personalization State ──
  const [layout, setLayout] = useState(() => PreferenceService.get("overview_layout", DEFAULT_LAYOUT));
  const [customizeMode, setCustomizeMode] = useState(false);

  const handleMove = (index, direction) => {
    const nextLayout = [...layout];
    const targetIdx = index + direction;
    if (targetIdx < 0 || targetIdx >= nextLayout.length) return;
    
    // Swap elements
    const temp = nextLayout[index];
    nextLayout[index] = nextLayout[targetIdx];
    nextLayout[targetIdx] = temp;
    
    setLayout(nextLayout);
    PreferenceService.set("overview_layout", nextLayout);
  };

  const renderCard = (cardId, index) => {
    const controls = customizeMode && (
      <div className="absolute top-2 right-2 flex gap-1 z-20">
        <button
          onClick={(e) => { e.stopPropagation(); handleMove(index, -1); }}
          disabled={index === 0}
          className="p-1 bg-white border border-[var(--border-subtle)] rounded-[var(--radius-sm)] hover:bg-[var(--bg-elevated)] disabled:opacity-30 disabled:cursor-not-allowed text-[var(--text-primary)]"
          title="Move Left"
        >
          <ArrowLeft size={10} />
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); handleMove(index, 1); }}
          disabled={index === layout.length - 1}
          className="p-1 bg-white border border-[var(--border-subtle)] rounded-[var(--radius-sm)] hover:bg-[var(--bg-elevated)] disabled:opacity-30 disabled:cursor-not-allowed text-[var(--text-primary)]"
          title="Move Right"
        >
          <ArrowRight size={10} />
        </button>
      </div>
    );

    if (cardId === "forecast") {
      return (
        <div key="forecast" className="relative group flex-1 min-w-[240px]">
          <KPIStatCard
            title={t("Tomorrow's Forecast")}
            value={
              <div className="flex items-center gap-1">
                <CountUp end={MOCK_AI_FORECAST.predictedKg} duration={1} preserveValue separator="," /> kg
              </div>
            }
            icon={BrainCircuit}
            subtitle={`↑ 8.8% vs Today (${MOCK_AI_FORECAST.confidence}% confidence)`}
            trend="up"
          />
          {controls}
        </div>
      );
    }
    if (cardId === "fleet") {
      return (
        <div key="fleet" className="relative group flex-1 min-w-[240px]">
          <KPIStatCard
            title={t("Active Fleet")}
            value={isLoadingTrucks ? '...' : `${trucks.filter(t => t.status === 'safe').length}/${trucks.length}`}
            icon={Truck}
            subtitle={`Total Capacity: ${totalCapacity.toLocaleString()} kg`}
          />
          {controls}
        </div>
      );
    }
    if (cardId === "alerts") {
      return (
        <div key="alerts" className="relative group flex-1 min-w-[240px]">
          <KPIStatCard
            title={t("Critical IoT Alerts")}
            value={activeAlerts.toString()}
            icon={AlertTriangle}
            alert={activeAlerts > 0}
            subtitle="T-102 exceeding 30°C"
            trend="down"
          />
          {controls}
        </div>
      );
    }
    if (cardId === "outstanding") {
      return (
        <div key="outstanding" className="relative group flex-1 min-w-[240px]">
          <KPIStatCard
            title={t("Total Outstanding")}
            value={
              <div className="flex items-center">
                ₹<CountUp end={totalOutstanding} duration={1} preserveValue separator="," />
              </div>
            }
            icon={Wallet}
            subtitle={`From ${retailers.filter(r => Number(r.balance) > 0).length} retailers`}
            trend="down"
          />
          {controls}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Personalization Toggle */}
      <div className="flex justify-end -mb-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCustomizeMode((prev) => !prev)}
        >
          {customizeMode ? (
            <span className="flex items-center gap-1"><Check size={14} /> Done</span>
          ) : (
            <span className="flex items-center gap-1"><Settings size={14} /> Customize Layout</span>
          )}
        </Button>
      </div>

      {/* Metric Row */}
      <div className="flex md:grid overflow-x-auto md:overflow-visible snap-x snap-mandatory sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6 pb-4 md:pb-0 -mx-4 px-4 sm:-mx-6 sm:px-6 md:mx-0 md:px-0 scrollbar-none after:content-[''] after:w-4 after:flex-shrink-0 sm:after:hidden">
        {layout.map((cardId, index) => renderCard(cardId, index))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <Card className="lg:col-span-2 p-4 sm:p-6 bg-white border border-[var(--border-subtle)]">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-h3 text-[var(--text-primary)]">{t('Sales vs AI Forecast')}</h3>
            <select className="text-xs bg-[#FAFAFA] border border-[#EBEBEB] rounded-lg px-2.5 py-1.5 outline-none font-bold text-[#111111]">
              <option>Last 7 Days</option>
              <option>This Month</option>
            </select>
          </div>
          <div className="h-56 sm:h-72 lg:h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={MOCK_SALES_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F5F5F5" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontWeight: 'semibold' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontWeight: 'semibold' }} />
                <RechartsTooltip
                  contentStyle={{ borderRadius: '8px', border: '1px solid var(--border-subtle)', backgroundColor: '#FFFFFF', color: '#111111', fontSize: '11px' }}
                  cursor={{ stroke: '#111111', strokeWidth: 1, strokeDasharray: '4 4' }}
                />
                <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: '11px', fontWeight: 'bold' }} />
                <Line type="monotone" dataKey="actual" name="Actual Sales (kg)" stroke="#111111" strokeWidth={2.5} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="predicted" name="AI Predicted (kg)" stroke="#666666" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-4 sm:p-6 flex flex-col bg-white border border-[var(--border-subtle)]">
          <h3 className="text-h3 text-[var(--text-primary)] mb-6">{t('Live Truck Status')}</h3>
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
          <Button
            onClick={() => handleTabChange('fleet')}
            className="mt-4 w-full"
            variant="primary"
          >
            {t('View Fleet Map')}
          </Button>
        </Card>
      </div>

      {/* ── Operations Feed ── */}
      <div className="mt-6">
        <Card className="p-4 sm:p-6 bg-white border border-[var(--border-subtle)]">
          <h3 className="text-h3 text-[var(--text-primary)] mb-4">{t('Operations Feed')}</h3>
          <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
            {operationsFeed && operationsFeed.length > 0 ? (
              operationsFeed.map(op => (
                <div key={op.id} className="flex items-center gap-3 p-3 bg-[#FAFAFA] rounded-xl border border-[#EBEBEB] hover:border-[#111111] transition-all animate-in slide-in-from-top-2 duration-300">
                  <div className="text-xl">{op.icon}</div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-[#111111] text-sm">{op.title}</span>
                      <span className="text-[10px] font-bold text-[#666666]">{op.time}</span>
                    </div>
                    <div className="flex justify-between items-center mt-1">
                      <span className="text-xs text-[#666666]">{op.desc}</span>
                      <span className="text-xs font-bold text-green-600 animate-pulse">{op.value}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-[#666666] font-semibold uppercase tracking-wider text-center py-4 flex flex-col items-center gap-2">
                <span className="animate-spin text-xl">⏳</span>
                Listening for live events...
              </p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
