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


export function AITab({ MOCK_AI_FORECAST, MOCK_SCATTER_DATA }) {
  return (

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
}
