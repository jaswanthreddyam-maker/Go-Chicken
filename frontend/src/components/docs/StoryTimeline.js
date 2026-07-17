"use client";
import React from 'react';
import SectionHeading from './ui/SectionHeading';
import TimelineItem from './ui/TimelineItem';
import { motion } from 'framer-motion';

export default function StoryTimeline() {
  const events = [
    { time: "06:00 AM", title: "Raj opens WhatsApp.", desc: "120 unread messages from retailers." },
    { time: "07:30 AM", title: "Retailers ask today's price.", desc: "Clerks frantically copy-paste quotes." },
    { time: "08:45 AM", title: "Stock changes.", desc: "Sold out of Live Bird, but quotes were already sent." },
    { time: "10:00 AM", title: "Driver leaves.", desc: "Verbal instructions. No tracking." },
    { time: "12:15 PM", title: "Customer disputes pricing.", desc: "'You said ₹150 this morning!'" },
    { time: "06:00 PM", title: "Khata updated manually.", desc: "Hours spent reconciling notebooks." },
  ];

  return (
    <section id="raj" className="py-24 px-6 md:px-12 bg-[#FAFAFA] overflow-hidden">
      <div className="max-w-4xl mx-auto">
        <SectionHeading 
          title="Meet Raj" 
          subtitle="A day in the life of a modern poultry wholesaler." 
        />
        
        <div className="mt-16 pb-16">
          {events.map((event, idx) => (
            <TimelineItem 
              key={idx}
              index={idx}
              time={event.time}
              title={event.title}
              description={event.desc}
              isLast={idx === events.length - 1}
            />
          ))}
        </div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-center mt-24"
        >
          <h3 className="text-3xl md:text-6xl font-black tracking-tighter text-[#111111]">
            What if WhatsApp handled <span className="underline decoration-[#EBEBEB]">everything?</span>
          </h3>
        </motion.div>
      </div>
    </section>
  );
}
