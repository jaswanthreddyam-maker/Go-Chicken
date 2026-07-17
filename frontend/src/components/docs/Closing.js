"use client";
import React from 'react';
import { motion } from 'framer-motion';
import { ArrowDown } from 'lucide-react';

export default function Closing() {
  const steps = [
    "One WhatsApp Message",
    "One AI Assistant",
    "One Unified Platform"
  ];

  return (
    <section id="closing" className="min-h-screen flex flex-col items-center justify-center text-center px-4 bg-[#FAFAFA] py-24">
      <div className="max-w-4xl mx-auto flex flex-col items-center gap-8">
        {steps.map((step, idx) => (
          <React.Fragment key={idx}>
            <motion.h3
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.8, delay: idx * 0.4 }}
              className="text-3xl md:text-5xl font-bold tracking-tight text-[#666666]"
            >
              {step}
            </motion.h3>
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              whileInView={{ opacity: 1, height: 40 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: idx * 0.4 + 0.3 }}
            >
              <ArrowDown size={32} className="text-[#EBEBEB]" />
            </motion.div>
          </React.Fragment>
        ))}

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: steps.length * 0.4 }}
          className="mt-8"
        >
          <img src="/logo.png" alt="Go Chicken Logo" className="w-20 h-20 mx-auto mb-6 object-contain" />
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-[#111111] uppercase mb-12">
            Go Chicken
          </h1>
          
          <div className="pt-12 border-t border-[#EBEBEB] w-full max-w-sm mx-auto">
            <h4 className="text-xl font-bold text-[#111111] mb-2">Thank You</h4>
            <p className="text-[#666666] tracking-widest uppercase text-sm">Questions?</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
