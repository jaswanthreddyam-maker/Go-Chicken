"use client";
import React from 'react';
import SectionHeading from './ui/SectionHeading';
import AnimatedCard from './ui/AnimatedCard';

export default function Enterprise() {
  const features = [
    { title: "Immutable Quotes", desc: "Pricing snapshots are generated per order. No manual rate tampering." },
    { title: "CQRS", desc: "Read and write models are segregated for lightning-fast dashboard metrics." },
    { title: "Event Driven", desc: "Transactional outbox pattern ensures systems stay eventually consistent." },
    { title: "Multi-tenant", desc: "Strict server-side isolation prevents horizontal privilege escalation." },
    { title: "Live Ledger", desc: "Append-only khata events ensure perfect financial auditability." },
    { title: "Server-Sent Events", desc: "True real-time SPA experience without heavy websocket overhead." },
  ];

  return (
    <section id="engineering" className="py-24 px-6 md:px-12 bg-[#FAFAFA]">
      <div className="max-w-5xl mx-auto">
        <SectionHeading 
          title="Enterprise Engineering" 
          subtitle="Why businesses can trust Go Chicken." 
        />
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-12">
          {features.map((f, idx) => (
            <AnimatedCard key={idx} index={idx}>
              <h4 className="font-black text-[#111111] uppercase tracking-wide text-sm mb-3 pb-3 border-b border-[#EBEBEB]">
                {f.title}
              </h4>
              <p className="text-[#666666] text-sm leading-relaxed">
                {f.desc}
              </p>
            </AnimatedCard>
          ))}
        </div>
      </div>
    </section>
  );
}
