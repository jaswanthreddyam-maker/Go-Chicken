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


export function KhataTab({ setShowPaymentModal, searchQuery, MOCK_KHATA }) {
  return (

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
}
