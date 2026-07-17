"use client";
import React from 'react';
import { motion } from 'framer-motion';

export default function MetricCard({ beforeLabel, afterLabel, beforeValue, afterValue, index = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, delay: index * 0.15 }}
      className="bg-white border border-[#EBEBEB] rounded-xl overflow-hidden flex flex-col md:flex-row shadow-sm"
    >
      <div className="flex-1 p-5 md:p-6 bg-[#FAFAFA] border-b md:border-b-0 md:border-r border-[#EBEBEB]">
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#AEAEAE] block mb-2">{beforeLabel || "Before"}</span>
        <p className="text-[#666666] font-medium line-through opacity-70">{beforeValue}</p>
      </div>
      <div className="flex-1 p-5 md:p-6">
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#111111] block mb-2">{afterLabel || "After"}</span>
        <p className="text-[#111111] font-bold text-lg">{afterValue}</p>
      </div>
    </motion.div>
  );
}
