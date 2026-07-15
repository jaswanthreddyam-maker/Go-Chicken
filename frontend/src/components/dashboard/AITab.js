"use client";

import React from 'react';
import { 
  ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, ZAxis, ScatterChart, Scatter
} from 'recharts';
import { BrainCircuit } from 'lucide-react';
import { Card } from '@/components/ui';
import { useDashboardData } from "@/context/DashboardDataContext";

export function AITab() {
  const { MOCK_AI_FORECAST, MOCK_SCATTER_DATA, latestAIExtraction } = useDashboardData();

  return (
    <div className="animate-in fade-in duration-300 space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <Card className="lg:col-span-1 p-4 sm:p-6 bg-white border border-[var(--border-subtle)] flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-6 border-b border-[var(--border-subtle)] pb-4">
              <BrainCircuit className="text-[var(--text-primary)]" size={18} />
              <h3 className="text-label text-[var(--text-primary)]">Ollama Llama3 Engine</h3>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-label text-[var(--text-secondary)]">Target Forecast Date</p>
                <p className="text-body font-bold text-[var(--text-primary)] mt-0.5">{MOCK_AI_FORECAST.targetDate}</p>
              </div>
              <div>
                <p className="text-label text-[var(--text-secondary)]">Predicted Volatility</p>
                <h2 className="text-display font-black text-[var(--text-primary)] tracking-tight mt-1">
                  {MOCK_AI_FORECAST.predictedKg} <span className="text-sm font-semibold text-[var(--text-secondary)]">kg</span>
                </h2>
              </div>
            </div>
          </div>

          <div className="mt-8 space-y-3">
            {latestAIExtraction && (
              <div className="bg-[#111111] text-white border border-[#333333] rounded-[var(--radius-lg)] p-4 animate-in slide-in-from-left-4 duration-500 shadow-xl">
                <p className="text-[10px] font-bold text-[#999999] uppercase tracking-widest mb-3 flex items-center justify-between">
                  <span>Latest Extraction</span>
                  <span className="text-green-400 animate-pulse flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-400"></span> Live
                  </span>
                </p>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <p className="text-[#999999] mb-0.5">Intent</p>
                    <p className="font-bold text-white">{latestAIExtraction.intent}</p>
                  </div>
                  <div>
                    <p className="text-[#999999] mb-0.5">Confidence</p>
                    <p className="font-bold text-white">{(latestAIExtraction.confidence * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-[#999999] mb-0.5">Product</p>
                    <p className="font-bold text-white">{latestAIExtraction.product || '-'}</p>
                  </div>
                  <div>
                    <p className="text-[#999999] mb-0.5">Quantity</p>
                    <p className="font-bold text-white">{latestAIExtraction.quantity ? `${latestAIExtraction.quantity}kg` : '-'}</p>
                  </div>
                </div>
              </div>
            )}
            <div className="bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-4">
              <p className="text-label text-[var(--text-secondary)]">Environmental Context</p>
              <p className="text-caption font-bold text-[var(--text-primary)] mt-1">{MOCK_AI_FORECAST.weather}</p>
            </div>
            <div className="bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-4">
              <p className="text-label text-[var(--text-secondary)]">AI Reasoning</p>
              <p className="text-caption text-[var(--text-secondary)] leading-relaxed mt-1 font-medium">{MOCK_AI_FORECAST.reasoning}</p>
            </div>
          </div>
        </Card>

        <Card className="lg:col-span-2 p-4 sm:p-6 flex flex-col bg-white border border-[var(--border-subtle)]">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 mb-6 border-b border-[var(--border-subtle)] pb-4">
            <h3 className="text-label text-[var(--text-primary)]">Vector Similarity Search</h3>
            <span className="text-label text-[var(--text-secondary)] bg-[var(--bg-app)] px-2 py-1 rounded border border-[var(--border-subtle)] self-start sm:self-auto">
              nomic-embed-text
            </span>
          </div>
          <div className="flex-1 w-full min-h-[250px] sm:min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F5F5F5" />
                <XAxis type="number" dataKey="x" name="Feature X" tick={false} axisLine={false} />
                <YAxis type="number" dataKey="y" name="Demand (kg)" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontWeight: 'bold' }} />
                <ZAxis type="number" dataKey="z" range={[50, 400]} />
                <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ borderRadius: '8px', border: '1px solid var(--border-subtle)', fontSize: '11px', color: 'var(--text-primary)' }} />
                <Scatter name="Demand Clusters" data={MOCK_SCATTER_DATA} fill="var(--text-primary)" opacity={0.8} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}
