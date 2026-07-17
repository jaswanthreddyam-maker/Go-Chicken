"use client";
import React from 'react';
import { motion } from 'framer-motion';

export default function SectionHeading({ title, subtitle }) {
  return (
    <div className="mb-12 text-center md:text-left">
      <motion.h2 
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-3xl md:text-5xl font-black tracking-tighter text-[#111111]"
      >
        {title}
      </motion.h2>
      {subtitle && (
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
          className="mt-4 text-lg text-[#666666] font-medium"
        >
          {subtitle}
        </motion.p>
      )}
    </div>
  );
}
