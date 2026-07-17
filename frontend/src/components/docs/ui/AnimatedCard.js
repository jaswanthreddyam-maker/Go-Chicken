"use client";
import React from 'react';
import { motion } from 'framer-motion';

export default function AnimatedCard({ children, delay = 0, index = 0 }) {
  // Stagger based on index if provided
  const staggerDelay = index * 0.15 + delay;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, delay: staggerDelay, type: "spring", stiffness: 100 }}
      whileHover={{ scale: 1.02 }}
      className="bg-white border border-[#EBEBEB] rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow"
    >
      {children}
    </motion.div>
  );
}
