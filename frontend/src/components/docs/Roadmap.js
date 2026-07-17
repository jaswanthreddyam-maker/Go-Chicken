"use client";
import React from 'react';
import SectionHeading from './ui/SectionHeading';
import { motion } from 'framer-motion';

export default function Roadmap() {
  const stages = ["Today", "Pilot", "Regional", "National", "Platform"];

  return (
    <section id="roadmap" className="py-24 px-6 md:px-12 bg-[#111111] text-white">
      <div className="max-w-4xl mx-auto">
        <div className="mb-12 text-center md:text-left">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-3xl md:text-5xl font-black tracking-tighter text-white"
          >
            Maturity Timeline
          </motion.h2>
        </div>
        
        <div className="mt-16 relative">
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-[#333333] -translate-y-1/2 hidden md:block" />
          
          <motion.div 
            initial={{ width: 0 }}
            whileInView={{ width: "100%" }}
            viewport={{ once: true }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className="absolute top-1/2 left-0 h-0.5 bg-white -translate-y-1/2 hidden md:block z-0"
          />

          <div className="flex flex-col md:flex-row justify-between gap-8 md:gap-4 relative z-10">
            {stages.map((stage, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.3 }}
                className="flex flex-col items-center bg-[#111111] py-2 md:px-4"
              >
                <div className="w-4 h-4 rounded-full bg-white mb-4 shadow-[0_0_15px_rgba(255,255,255,0.5)]" />
                <span className="font-bold uppercase tracking-widest text-sm">{stage}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
