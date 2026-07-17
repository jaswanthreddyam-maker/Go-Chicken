"use client";
import React from 'react';
import SectionHeading from './ui/SectionHeading';
import AnimatedCard from './ui/AnimatedCard';
import { MessageSquareOff, TrendingUp, PhoneCall, PackageX, BookX, Truck } from 'lucide-react';

export default function Problem() {
  const problems = [
    { icon: MessageSquareOff, title: "Orders lost in WhatsApp chats" },
    { icon: TrendingUp, title: "Prices change every morning" },
    { icon: PhoneCall, title: "Retailers keep calling" },
    { icon: PackageX, title: "Inventory is never accurate" },
    { icon: BookX, title: "Khata maintained in notebooks" },
    { icon: Truck, title: "No visibility after dispatch" },
  ];

  return (
    <section id="problem" className="min-h-screen py-24 px-6 md:px-12 bg-white flex flex-col justify-center max-w-5xl mx-auto">
      <SectionHeading 
        title="Today's Reality" 
        subtitle="The manual chaos throttling wholesale poultry distributors." 
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {problems.map((prob, idx) => (
          <AnimatedCard key={idx} index={idx}>
            <div className="flex flex-col gap-4">
              <div className="w-10 h-10 rounded-full bg-[#FAFAFA] flex items-center justify-center border border-[#EBEBEB]">
                <prob.icon size={18} className="text-[#666666]" />
              </div>
              <p className="font-bold text-[#111111] leading-tight">
                <span className="text-[#FF4444] mr-2">❌</span>
                {prob.title}
              </p>
            </div>
          </AnimatedCard>
        ))}
      </div>
    </section>
  );
}
