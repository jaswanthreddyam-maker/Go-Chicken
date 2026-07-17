"use client";
import React from 'react';
import SectionHeading from './ui/SectionHeading';
import { motion } from 'framer-motion';
import { ArrowDown } from 'lucide-react';

export default function Architecture() {
  const flow = ["WhatsApp", "AI", "Business Rules", "Pricing", "Orders", "Khata", "Dashboard"];
  const techStack = ["Next.js", "FastAPI", "Supabase", "Groq", "Meta Cloud API"];

  return (
    <section id="architecture" className="py-24 px-6 md:px-12 bg-white text-center">
      <div className="max-w-3xl mx-auto">
        <SectionHeading title="The Architecture" />
        
        <div className="mt-12 flex flex-col items-center gap-4">
          {flow.map((step, idx) => (
            <React.Fragment key={idx}>
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.2 }}
                className="px-8 py-4 bg-[#FAFAFA] border border-[#EBEBEB] rounded-xl shadow-sm text-[#111111] font-bold uppercase tracking-widest text-sm w-full md:w-auto min-w-[240px]"
              >
                {step}
              </motion.div>
              {idx < flow.length - 1 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  whileInView={{ opacity: 1, height: 24 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: idx * 0.2 + 0.2 }}
                >
                  <ArrowDown size={24} className="text-[#AEAEAE]" />
                </motion.div>
              )}
            </React.Fragment>
          ))}
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: flow.length * 0.2 }}
          className="mt-24 pt-12 border-t border-[#EBEBEB]"
        >
          <p className="text-xs font-bold uppercase tracking-widest text-[#666666] mb-8">Built using</p>
          <div className="flex flex-wrap justify-center gap-4">
            {techStack.map((tech, idx) => (
              <span key={idx} className="px-4 py-2 border border-[#EBEBEB] rounded-full text-sm font-semibold text-[#111111] shadow-sm">
                {tech}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
