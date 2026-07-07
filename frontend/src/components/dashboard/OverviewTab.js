"use client";
import React from 'react';
import { 
  ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, Legend, Line, 
  ScatterChart, Scatter, ZAxis
} from 'recharts';
import { 
  BrainCircuit, Truck, AlertTriangle, Wallet, MapPin, Thermometer, 
  Package, Search, Clock, FileText, ChevronRight, CheckCircle2, MoreHorizontal,
  ChevronUp, ChevronDown
} from 'lucide-react';
import { Card, StatBox, TableSkeleton, ChartSkeleton } from '@/components/ui';
import AnimatedButton from '@/components/AnimatedButton';


export function OverviewTab({ t, MOCK_AI_FORECAST, MOCK_SALES_DATA, trucks, retailers, isLoadingTrucks, totalOutstanding, totalCapacity, activeAlerts }) {
  return (

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
}
