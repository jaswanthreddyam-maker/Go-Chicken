"use client";
import React from 'react';
import { 
  ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, Legend, Line, 
  ScatterChart, Scatter, ZAxis
} from 'recharts';
import { 
  BrainCircuit, Truck, AlertTriangle, Wallet, MapPin, Thermometer, 
  Package, Search, Clock, FileText, ChevronRight, CheckCircle2, MoreHorizontal,
  ChevronUp, ChevronDown, Tag, Zap, Edit3, RefreshCw, Activity
} from 'lucide-react';
import AnimatedButton from '@/components/AnimatedButton';
import { Card, StatBox, TableSkeleton, ChartSkeleton, Toast, ErrorBanner } from '@/components/ui';


export function OrdersTab({ t, searchQuery, ordersList, productPrices, retailers, isLoadingOrders, isLoadingPrices, ordersError, pricesError, editingPrice, setEditingPrice, priceSuccessMsg, setPriceSuccessMsg, toasts }) {
  return (

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
}
