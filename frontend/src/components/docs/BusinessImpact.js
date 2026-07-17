"use client";
import React from 'react';
import SectionHeading from './ui/SectionHeading';
import MetricCard from './ui/MetricCard';

export default function BusinessImpact() {
  const impacts = [
    { before: "Manual pricing", after: "Automatic" },
    { before: "Notebook Khata", after: "Live Ledger" },
    { before: "Phone calls", after: "WhatsApp" },
    { before: "Delayed updates", after: "Real-time" },
  ];

  return (
    <section id="impact" className="py-24 px-6 md:px-12 bg-white">
      <div className="max-w-4xl mx-auto">
        <SectionHeading 
          title="Business Impact" 
          subtitle="How Go Chicken transforms operations instantly." 
        />
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
          {impacts.map((impact, idx) => (
            <MetricCard 
              key={idx}
              index={idx}
              beforeValue={impact.before}
              afterValue={impact.after}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
