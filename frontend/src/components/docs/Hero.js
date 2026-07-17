"use client";
import React from 'react';
import { motion } from 'framer-motion';

export default function Hero() {
  return (
    <section id="hero" className="min-h-screen flex flex-col items-center justify-center text-center px-4 relative overflow-hidden bg-[#FAFAFA]">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1, ease: "easeOut" }}
        className="w-16 h-16 mb-8"
      >
        <img src="/logo.png" alt="Go Chicken Logo" className="w-full h-full object-contain" />
      </motion.div>

      <motion.h1 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="text-6xl md:text-8xl font-black tracking-tighter text-[#111111] uppercase mb-4"
      >
        Go Chicken
      </motion.h1>

      <motion.p 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.4 }}
        className="text-xl md:text-3xl text-[#666666] font-medium tracking-tight mb-12 max-w-2xl"
      >
        The Operating System for Poultry Distribution.
      </motion.p>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.6 }}
        className="flex flex-col items-center gap-2 mb-16"
      >
        <p className="text-sm md:text-base font-bold text-[#111111] uppercase tracking-widest">Built for wholesalers.</p>
        <p className="text-sm md:text-base font-bold text-[#111111] uppercase tracking-widest">Powered by AI.</p>
        <p className="text-sm md:text-base font-bold text-[#111111] uppercase tracking-widest">Runs entirely through WhatsApp.</p>
      </motion.div>

      <motion.a 
        href="/#demo"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 1 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="px-8 py-4 bg-[#111111] text-white text-sm font-bold uppercase tracking-widest flex items-center gap-3 shadow-lg"
      >
        Watch Live Demo <span>→</span>
      </motion.a>
    </section>
  );
}
