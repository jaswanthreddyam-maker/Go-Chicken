"use client";
import React from 'react';
import { motion } from 'framer-motion';

export default function TimelineItem({ time, title, description, isLast = false, index = 0 }) {
  return (
    <div className="relative pl-8 md:pl-0">
      {/* Mobile Vertical Line */}
      {!isLast && (
        <div className="absolute left-[11px] top-8 bottom-[-32px] w-0.5 bg-[#EBEBEB] md:hidden" />
      )}
      
      <div className="md:grid md:grid-cols-[1fr_auto_1fr] md:gap-8 items-center">
        {/* Time (Left side on desktop) */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5, delay: index * 0.2 }}
          className="md:text-right mb-2 md:mb-0"
        >
          <span className="text-sm font-bold text-[#AEAEAE] tracking-wider uppercase">{time}</span>
        </motion.div>

        {/* Dot / Line (Center on desktop) */}
        <div className="absolute left-0 top-1.5 md:relative md:left-auto md:top-auto flex flex-col items-center">
          <motion.div 
            initial={{ scale: 0 }}
            whileInView={{ scale: 1 }}
            viewport={{ once: true }}
            transition={{ type: "spring", delay: index * 0.2 }}
            className="w-6 h-6 rounded-full bg-[#111111] flex-shrink-0 border-4 border-white shadow-sm z-10"
          />
          {!isLast && (
            <motion.div 
              initial={{ height: 0 }}
              whileInView={{ height: "100%" }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: index * 0.2 }}
              className="hidden md:block w-0.5 bg-[#EBEBEB] absolute top-6 -bottom-12 z-0"
            />
          )}
        </div>

        {/* Content (Right side on desktop) */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5, delay: index * 0.2 + 0.1 }}
          className="bg-white border border-[#EBEBEB] rounded-xl p-5 shadow-sm"
        >
          <h4 className="font-bold text-[#111111] mb-1">{title}</h4>
          {description && <p className="text-sm text-[#666666]">{description}</p>}
        </motion.div>
      </div>
    </div>
  );
}
