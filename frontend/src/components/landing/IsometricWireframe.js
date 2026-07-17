import React from "react";

// ── Isometric Dashboard Wireframe (SVG) ──────────────────────────────
// A complex isometric data-dashboard / logistics wireframe
// drawn entirely in thin grey lines — no fills, no gradients.
const IsometricWireframe = () => (
  <svg
    viewBox="0 0 560 480"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="w-full h-auto"
    aria-hidden="true"
  >
    {/* ── Isometric Grid Base ─────────────────────────────── */}
    <g stroke="#D4D4D4" strokeWidth="0.5" opacity="0.4">
      {Array.from({ length: 12 }).map((_, i) => (
        <line key={`gx-${i}`} x1={40 + i * 44} y1="40" x2={40 + i * 44} y2="440" />
      ))}
      {Array.from({ length: 10 }).map((_, i) => (
        <line key={`gy-${i}`} x1="40" y1={40 + i * 44} x2="520" y2={40 + i * 44} />
      ))}
    </g>

    {/* ── Main Dashboard Panel (Isometric Projection) ─────── */}
    <g stroke="#AEAEAE" strokeWidth="1.2">
      {/* Back panel */}
      <path d="M80 100 L480 100 L480 380 L80 380 Z" />
      {/* Top bar */}
      <rect x="80" y="100" width="400" height="32" />
      {/* Sidebar */}
      <rect x="80" y="132" width="90" height="248" />

      {/* Fake sidebar nav items */}
      <g stroke="#C8C8C8" strokeWidth="0.8">
        <rect x="92" y="148" width="66" height="8" rx="2" />
        <rect x="92" y="168" width="50" height="8" rx="2" />
        <rect x="92" y="188" width="58" height="8" rx="2" />
        <rect x="92" y="208" width="42" height="8" rx="2" />
        <rect x="92" y="228" width="54" height="8" rx="2" />
      </g>

      {/* Top bar dots (window controls) */}
      <circle cx="96" cy="116" r="4" stroke="#C8C8C8" />
      <circle cx="110" cy="116" r="4" stroke="#C8C8C8" />
      <circle cx="124" cy="116" r="4" stroke="#C8C8C8" />
    </g>

    {/* ── Content Area: Stat Cards Row ─────────────────────── */}
    <g stroke="#BEBEBE" strokeWidth="0.9">
      <rect x="186" y="144" width="84" height="48" rx="3" />
      <rect x="282" y="144" width="84" height="48" rx="3" />
      <rect x="378" y="144" width="84" height="48" rx="3" />
    </g>
    {/* Card inner lines (data indicators) */}
    <g stroke="#D4D4D4" strokeWidth="0.6">
      <line x1="196" y1="158" x2="230" y2="158" />
      <line x1="196" y1="168" x2="254" y2="168" />
      <line x1="196" y1="178" x2="240" y2="178" />
      <line x1="292" y1="158" x2="326" y2="158" />
      <line x1="292" y1="168" x2="350" y2="168" />
      <line x1="292" y1="178" x2="336" y2="178" />
      <line x1="388" y1="158" x2="422" y2="158" />
      <line x1="388" y1="168" x2="446" y2="168" />
      <line x1="388" y1="178" x2="432" y2="178" />
    </g>

    {/* ── Chart Area (Line Chart) ──────────────────────────── */}
    <g stroke="#BEBEBE" strokeWidth="0.9">
      <rect x="186" y="206" width="180" height="110" rx="3" />
    </g>
    {/* Chart axis lines */}
    <g stroke="#D4D4D4" strokeWidth="0.5">
      <line x1="200" y1="220" x2="200" y2="300" />
      <line x1="200" y1="300" x2="350" y2="300" />
    </g>
    {/* Chart data line */}
    <polyline
      points="210,290 230,272 250,278 270,254 290,260 310,238 330,242 348,226"
      stroke="#999999"
      strokeWidth="1.4"
      fill="none"
      strokeLinejoin="round"
    />
    {/* Second line (forecast dashed) */}
    <polyline
      points="210,286 230,276 250,280 270,262 290,268 310,248 330,250 348,236"
      stroke="#C8C8C8"
      strokeWidth="1"
      fill="none"
      strokeDasharray="4 3"
      strokeLinejoin="round"
    />
    {/* Data dots */}
    <g fill="none" stroke="#999999" strokeWidth="1">
      <circle cx="210" cy="290" r="2.5" />
      <circle cx="250" cy="278" r="2.5" />
      <circle cx="290" cy="260" r="2.5" />
      <circle cx="330" cy="242" r="2.5" />
    </g>

    {/* ── Table / List Area ─────────────────────────────────── */}
    <g stroke="#BEBEBE" strokeWidth="0.9">
      <rect x="378" y="206" width="84" height="110" rx="3" />
    </g>
    {/* Table rows */}
    <g stroke="#D8D8D8" strokeWidth="0.5">
      <line x1="386" y1="228" x2="454" y2="228" />
      <line x1="386" y1="248" x2="454" y2="248" />
      <line x1="386" y1="268" x2="454" y2="268" />
      <line x1="386" y1="288" x2="454" y2="288" />
    </g>
    {/* Table text placeholders */}
    <g stroke="#D4D4D4" strokeWidth="0.6">
      <line x1="390" y1="218" x2="420" y2="218" />
      <line x1="390" y1="238" x2="435" y2="238" />
      <line x1="390" y1="258" x2="425" y2="258" />
      <line x1="390" y1="278" x2="440" y2="278" />
      <line x1="390" y1="298" x2="418" y2="298" />
    </g>

    {/* ── Bottom Bar / Action Row ──────────────────────────── */}
    <g stroke="#BEBEBE" strokeWidth="0.9">
      <rect x="186" y="330" width="276" height="36" rx="3" />
    </g>
    <g stroke="#D4D4D4" strokeWidth="0.6">
      <rect x="196" y="340" width="56" height="16" rx="2" />
      <rect x="262" y="340" width="56" height="16" rx="2" />
      <rect x="328" y="340" width="80" height="16" rx="2" />
    </g>

    {/* ── Floating Isometric Cube (3D element) ─────────────── */}
    <g stroke="#B0B0B0" strokeWidth="1" transform="translate(60, 300)">
      {/* Front face */}
      <path d="M0 20 L30 0 L60 20 L30 40 Z" />
      {/* Top face */}
      <path d="M0 20 L30 0 L30 -20 L0 0 Z" />
      {/* Right face */}
      <path d="M30 0 L60 20 L60 0 L30 -20 Z" />
    </g>

    {/* ── Second floating cube ─────────────────────────────── */}
    <g stroke="#C0C0C0" strokeWidth="0.8" transform="translate(490, 60)">
      <path d="M0 16 L24 0 L48 16 L24 32 Z" />
      <path d="M0 16 L24 0 L24 -14 L0 2 Z" />
      <path d="M24 0 L48 16 L48 2 L24 -14 Z" />
    </g>

    {/* ── Connection lines (logistics network) ─────────────── */}
    <g stroke="#D0D0D0" strokeWidth="0.7" strokeDasharray="6 4">
      <line x1="90" y1="340" x2="186" y2="290" />
      <line x1="462" y1="260" x2="514" y2="76" />
      <line x1="90" y1="320" x2="60" y2="300" />
    </g>

    {/* ── Small node dots (network endpoints) ──────────────── */}
    <g fill="none" stroke="#B0B0B0" strokeWidth="1">
      <circle cx="90" cy="340" r="3" />
      <circle cx="514" cy="76" r="3" />
      <circle cx="186" cy="290" r="3" />
    </g>

    {/* ── Decorative measurement ticks (engineering feel) ──── */}
    <g stroke="#D4D4D4" strokeWidth="0.4">
      <line x1="40" y1="395" x2="520" y2="395" />
      {Array.from({ length: 13 }).map((_, i) => (
        <line key={`tick-${i}`} x1={40 + i * 40} y1="392" x2={40 + i * 40} y2="398" />
      ))}
    </g>
  </svg>
);

export default IsometricWireframe;
