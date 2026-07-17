"use client";
import React from 'react';
import SectionHeading from './ui/SectionHeading';
import { motion } from 'framer-motion';
import { MessageCircle, Brain, Calculator, FileText, CheckCircle2, Box, BookOpen, LayoutDashboard } from 'lucide-react';

export default function LiveDemo() {
  const steps = [
    { icon: MessageCircle, label: "Retailer sends message", delay: 0 },
    { icon: Brain, label: "AI understands intent", delay: 1 },
    { icon: Calculator, label: "Pricing Engine fetches rate", delay: 2 },
    { icon: FileText, label: "Quote generated", delay: 3 },
    { icon: CheckCircle2, label: "Retailer confirms", delay: 4 },
    { icon: Box, label: "Inventory drops", delay: 5 },
    { icon: BookOpen, label: "Khata records debit", delay: 6 },
    { icon: LayoutDashboard, label: "Dashboard updates instantly", delay: 7 },
  ];

  return (
    <section id="demo" className="py-24 px-6 md:px-12 bg-[#FAFAFA]">
      <div className="max-w-5xl mx-auto">
        <SectionHeading 
          title="The 'Wow' Moment" 
          subtitle="Everything under 1 second. Zero screen refreshes." 
        />
        
        <div className="mt-16 flex flex-col items-center">
          <div className="w-full max-w-2xl bg-white border border-[#EBEBEB] rounded-2xl p-8 shadow-sm flex flex-col gap-6">
            {steps.map((step, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: step.delay * 0.4 }}
                className="flex items-center gap-4"
              >
                <div className="w-10 h-10 rounded-full bg-[#111111] text-white flex items-center justify-center flex-shrink-0">
                  <step.icon size={18} />
                </div>
                <div className="flex-1 border-b border-dashed border-[#EBEBEB] pb-2">
                  <p className="font-bold text-[#111111]">{step.label}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
