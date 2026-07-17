"use client";
import React from 'react';
import { motion } from 'framer-motion';

export default function WhyWhatsapp() {
  return (
    <section id="whatsapp" className="min-h-screen flex flex-col items-center justify-center text-center px-4 bg-white py-24">
      <div className="max-w-4xl mx-auto flex flex-col gap-12 md:gap-24">
        {["No App.", "No Training.", "No Learning Curve.", "Just WhatsApp."].map((text, idx) => (
          <motion.h2
            key={idx}
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8, delay: idx * 0.3 }}
            className={`text-5xl md:text-8xl font-black tracking-tighter ${
              idx === 3 ? "text-[#111111]" : "text-[#AEAEAE]"
            }`}
          >
            {text}
          </motion.h2>
        ))}
      </div>
    </section>
  );
}
