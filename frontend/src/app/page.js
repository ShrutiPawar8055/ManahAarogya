"use client";

import { useTransform, motion, useInView } from "motion/react";
import { useRef } from "react";
import BgScroll, { useScrollContext } from "@/components/BgScroll";
import Link from "next/link";
import AnimatedTestimonialsDemo from "@/components/animated-testimonials-demo";
import FloatingLines from "@/components/ui/floatingLineBg";

// Scroll-linked text overlay component
function ScrollOverlay({ children, scrollRange, className = "", immediate = false }) {
  const ref = useRef(null);
  const { scrollYProgress } = useScrollContext();

  // For the first section (immediate=true), start fully visible
  // Clamp values to ensure monotonically increasing offsets (0 to 1)
  const fadeInStart = immediate ? 0 : Math.max(0, scrollRange[0] - 0.05);
  const fadeInEnd = immediate ? 0.001 : Math.max(0.001, scrollRange[0]);
  const fadeOutStart = Math.max(fadeInEnd + 0.001, scrollRange[1]);
  const fadeOutEnd = Math.min(1, scrollRange[1] + 0.05);

  const opacity = useTransform(
    scrollYProgress,
    [fadeInStart, fadeInEnd, fadeOutStart, fadeOutEnd],
    [immediate ? 1 : 0, 1, 1, 0]
  );

  return (
    <motion.div
      ref={ref}
      style={{ opacity }}
      className={`fixed inset-0 flex items-center justify-center pointer-events-none z-10 ${className}`}
    >
      {children}
    </motion.div>
  );
}

// Navbar Component
function Navbar({ isDark = false }) {
  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
      className="sticky top-2 left-0 right-0 z-50 px-4 md:px-0 pointer-events-none"
    >
      <div className={`mx-auto flex max-w-5xl items-center justify-between rounded-full backdrop-blur-xl border shadow-[0_8px_32px_rgba(0,0,0,0.08)] px-6 py-3 pointer-events-auto transition-colors duration-500 ${isDark ? 'bg-zinc-900/80 border-white/10' : 'bg-white/70 border-white/20'}`}>
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative h-10 w-10 overflow-hidden rounded-xl shadow-sm transition-transform group-hover:scale-105">
            <img src="/logo.png" alt="Logo" className="h-full w-full object-cover" />
          </div>
          <span className={`text-xl font-bold transition-colors duration-500 ${isDark ? 'text-white' : 'text-black'}`}>
            Manah Arogya
          </span>
        </Link>
        <div className={`hidden md:flex items-center gap-8 rounded-full px-6 py-2 border transition-colors duration-500 ${isDark ? 'bg-zinc-800/50 border-zinc-700/50' : 'bg-zinc-100/50 border-zinc-200/50'}`}>
          <Link
            href="#features"
            className={`text-sm font-medium transition-colors ${isDark ? 'text-zinc-300 hover:text-white' : 'text-zinc-600 hover:text-zinc-900'}`}
          >
            Features
          </Link>
          <Link
            href="#about"
            className={`text-sm font-medium transition-colors ${isDark ? 'text-zinc-300 hover:text-white' : 'text-zinc-600 hover:text-zinc-900'}`}
          >
            About
          </Link>
          <Link
            href="/contact"
            className={`text-sm font-medium transition-colors ${isDark ? 'text-zinc-300 hover:text-white' : 'text-zinc-600 hover:text-zinc-900'}`}
          >
            Contact
          </Link>
        </div>
        <div className="flex items-center gap-4">

          <Link href="/signin">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`relative overflow-hidden rounded-full px-6 py-2.5 text-sm font-semibold shadow-md transition-all hover:shadow-lg flex items-center justify-center cursor-pointer ${isDark ? 'bg-white text-zinc-900 hover:bg-zinc-200 hover:shadow-white/20' : 'bg-zinc-900 text-white hover:bg-zinc-800 hover:shadow-zinc-900/20'}`}
            >
              <span className="relative z-10">Login</span>
            </motion.div>
          </Link>
        </div>
      </div>
    </motion.nav>
  );
}

// CTA Button Component
function CTAButton({ children, primary = false, className = "" }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`
        px-8 py-3.5 rounded-full font-semibold text-sm md:text-base transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer
        ${primary
          ? "bg-zinc-900 text-white shadow-[0_8px_20px_rgba(0,0,0,0.12)] hover:shadow-[0_8px_25px_rgba(0,0,0,0.2)] hover:bg-zinc-800"
          : "bg-white/50 backdrop-blur-md border border-zinc-200 text-zinc-800 hover:bg-white/80 hover:border-zinc-300 shadow-sm"
        }
        ${className}
      `}
    >
      {children}
    </motion.div>
  );
}

const timelineData = [
  {
    title: "Sign in with Google",
    description: "Securely log in via Google to begin your personalized wellness journey seamlessly.",
    icon: "/timeline-icons/login.png",
    step: "Step 1"
  },
  {
    title: "Take an Assessment",
    description: "Answer a few simple, clinical-grade questions so we can understand your current mental state.",
    icon: "/timeline-icons/test.png",
    step: "Step 2"
  },
  {
    title: "AI & Resource Curation",
    description: "Our advanced AI agents analyze your test results to handpick the best resources and suggest daily habits.",
    icon: "/timeline-icons/ai.png",
    step: "Step 3"
  },
  {
    title: "Access Your Dashboard",
    description: "Everything you need in one place: habit tracking, therapy bookings, AI chat, peer support, and resource library.",
    icon: "/timeline-icons/dashboard.png",
    step: "Step 4"
  },
  {
    title: "See Real Progress",
    description: "Watch your mental well-being improve over time with consistent tracking and expert support.",
    icon: "/timeline-icons/growth.png",
    step: "Step 5"
  }
];

function TimelineSection() {
  return (
    <section className="py-24 bg-white relative overflow-hidden" id="how-it-works">
      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="text-center mb-16 md:mb-24">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl md:text-5xl font-bold tracking-tight text-zinc-900 mb-4"
          >
            How It Works
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-zinc-600 text-lg max-w-2xl mx-auto"
          >
            Your journey to mental well-being, simplified into five easy steps.
          </motion.p>
        </div>

        <div className="relative max-w-5xl mx-auto mt-12">
          {/* Vertical Line */}
          <div className="absolute left-8 md:left-1/2 top-4 bottom-4 w-[2px] bg-linear-to-b from-emerald-100 via-emerald-400 to-teal-100 -translate-x-1/2 rounded-full hidden md:block" />
          <div className="absolute left-8 top-4 bottom-4 w-[2px] bg-linear-to-b from-emerald-100 via-emerald-400 to-teal-100 -translate-x-1/2 rounded-full md:hidden" />

          {timelineData.map((item, index) => {
            const isEven = index % 2 === 0;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.6, delay: 0.1 }}
                className="relative flex items-center justify-between mb-16 md:mb-24 w-full flex-row"
              >
                {/* Desktop layout: 2 columns split by center */}
                <div className="hidden md:flex w-full items-center justify-center">
                  <div className={`w-1/2 flex items-center shrink-0 ${isEven ? 'justify-end pr-16' : 'justify-start pl-16 order-last'}`}>
                    {/* Card Content */}
                    <div className="bg-white p-6 md:p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border-2 border-gray-200 group hover:-translate-y-2 transition-all duration-300 hover:shadow-[0_8px_30px_rgb(16,185,129,0.15)] max-w-md w-[400px] relative z-20">
                      <h3 className="text-xl md:text-2xl font-bold text-zinc-900 mb-3">{item.title}</h3>
                      <p className="text-zinc-600 leading-relaxed text-sm md:text-base">{item.description}</p>
                    </div>
                  </div>
                  <div className={`w-1/2 flex items-center shrink-0 ${isEven ? 'justify-start pl-16 order-last' : 'justify-end pr-16'}`}>
                    {/* Time/Step indicator */}
                    <div className={`text-xl font-bold text-zinc-300 w-full ${isEven ? 'text-left' : 'text-right'}`}>
                      {item.step}
                    </div>
                  </div>
                </div>

                {/* Mobile layout */}
                <div className="md:hidden flex w-full relative z-20 border">
                  <div className="w-[calc(100%-5rem)] ml-auto bg-white p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-zinc-100 group hover:-translate-y-1 transition-transform">
                    <div className="text-sm font-bold text-emerald-600 mb-2">{item.step}</div>
                    <h3 className="text-xl font-bold text-zinc-900 mb-2">{item.title}</h3>
                    <p className="text-zinc-600 leading-relaxed text-sm">{item.description}</p>
                  </div>
                </div>

                {/* Center Icon (Absolute) */}
                <div className="absolute left-8 md:left-1/2 w-14 h-14 md:w-16 md:h-16 bg-white border-[6px] border-zinc-50 rounded-full flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(16,185,129,0.3)] -translate-x-1/2 z-30 transition-transform duration-300 group-hover:scale-110 shrink-0">
                  <img src={item.icon} alt="icon" className="w-10 h-10 object-cover" />
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  const ctaRef = useRef(null);
  const isCtaInView = useInView(ctaRef, { margin: "-100px 0px 0px 0px" });

  return (
    <main className="relative bg-white font-jakarta">
      <Navbar isDark={isCtaInView} />

      <BgScroll>
        {/* Hero Title - Frames 1-10 (left half of screen) */}
        <ScrollOverlay scrollRange={[0, 0.29]} immediate>
          <div className="relative w-full h-full flex items-center px-6 sm:px-8 md:px-16 lg:px-24 overflow-hidden">
            {/* Full-height left-to-right gradient */}
            <div className="absolute inset-y-0 left-0 w-full md:w-3/4 bg-linear-to-r from-emerald-200/40 via-teal-100/20 to-transparent blur-2xl -z-10 pointer-events-none" />

            <div className="max-w-xl md:mt-12 pt-16">
              <motion.h1
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 1 }}
                className="text-4xl sm:text-5xl md:text-6xl lg:text-6xl font-bold tracking-tighter text-zinc-900"
              >
                Nurturing Minds, <br />
                Embracing <span className="inline text-emerald-600">Wellness</span>
              </motion.h1>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 1.2 }}
                className="mt-6 text-base sm:text-lg md:text-xl text-zinc-600 max-w-md"
              >
                A one-stop solution <span className="inline font-semibold text-zinc-800">for your mental wellness</span>. Take tests, book therapy sessions, track your habits, and much more.
              </motion.p>

              {/* Feature Pills */}
              {/* <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 1.3 }}
                className="mt-6 flex flex-wrap gap-3 pointer-events-auto max-w-xl"
              >
                <div className="flex items-center gap-2 bg-white/80 backdrop-blur-sm border border-zinc-100 px-3 py-1.5 rounded-2xl shadow-xs transition-transform hover:scale-105">
                  <span className="text-xl">🧑‍⚕️</span>
                  <span className="text-sm font-bold text-zinc-800 leading-tight">Online<br />Therapy</span>
                </div>
                <div className="flex items-center gap-2 bg-white/80 backdrop-blur-sm border border-zinc-100 px-3 py-1.5 rounded-2xl shadow-xs transition-transform hover:scale-105">
                  <span className="text-xl">📋</span>
                  <span className="text-sm font-bold text-zinc-800 leading-tight">Mental Health<br />Tests</span>
                </div>
                <div className="flex items-center gap-2 bg-white/80 backdrop-blur-sm border border-zinc-100 px-3 py-1.5 rounded-2xl shadow-xs transition-transform hover:scale-105">
                  <span className="text-xl">📈</span>
                  <span className="text-sm font-bold text-zinc-800 leading-tight">Habit<br />Tracker</span>
                </div>
                <div className="flex items-center gap-2 bg-white/80 backdrop-blur-sm border border-zinc-100 px-3 py-1.5 rounded-2xl shadow-xs transition-transform hover:scale-105">
                  <span className="text-xl">🤝</span>
                  <span className="text-sm font-bold text-zinc-800 leading-tight">Peer Support<br />Forum</span>
                </div>
              </motion.div> */}

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 1.4 }}
                className="mt-8 flex flex-col sm:flex-row gap-4 pointer-events-auto items-center"
              >
                <Link href="/signin" passHref><CTAButton className="cursor-pointer" primary>Sign in <span className="text-lg">&rarr;</span></CTAButton></Link>
                <Link href="/home"><CTAButton className="cursor-pointer">Explore Features</CTAButton></Link>
              </motion.div>

              {/* Trust Badges */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 1.5 }}
                className="mt-6 flex flex-wrap items-center gap-4 text-sm font-semibold text-zinc-600 pointer-events-auto"
              >
              </motion.div>
            </div>
          </div>
        </ScrollOverlay>

        {/* About Manah Aarogya - Frames 18-23 (centered) */}
        <ScrollOverlay scrollRange={[0.55, 1]}>
          <div className="absolute inset-y-0 left-0 w-1/3 md:w-1/4 bg-linear-to-r from-orange-500/70 via-orange-200/70 to-transparent blur-3xl -z-10 pointer-events-none" />
          <div className="absolute inset-y-0 right-0 w-1/3 md:w-1/4 bg-linear-to-l from-lime-500/70 via-lime-200/70 to-transparent blur-3xl -z-10 pointer-events-none" />
        </ScrollOverlay>
        <ScrollOverlay scrollRange={[0.55, 0.71]}>
          <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
            {/* Left and Right Gradients */}

            <div className="text-center max-w-3xl px-6 relative z-10">
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-zinc-900 mb-4">
                Why Manah Arogya?
              </h2>
              <p className="text-zinc-600 text-sm md:text-md lg:text-lg leading-relaxed">
                Many college students face anxiety, depression, burnout, and loneliness
                but lack timely and accessible psychological support.
                Institutional counselling services are often limited or unavailable, especially in rural and
                semi-urban areas, and stigma further discourages help-seeking. Existing digital mental health
                platforms are often generic and costly.
              </p>
            </div>
          </div>
        </ScrollOverlay>
      </BgScroll>

      {/* Features Section */}
      <AnimatedTestimonialsDemo />

      {/* Timeline Section */}
      <TimelineSection />

      {/* Final CTA Section */}
      <section ref={ctaRef} className="relative z-20 bg-zinc-900 min-h-screen flex flex-col justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <FloatingLines />
        </div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.15),transparent_50%)] pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(20,184,166,0.15),transparent_50%)] pointer-events-none" />
        <div className="max-w-4xl w-full mx-auto px-6 text-center relative z-10 pointer-events-none">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-6xl font-bold tracking-tight text-white mb-8"
          >
            Ready to prioritize your mental wellbeing?
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-lg md:text-xl text-zinc-200 font-semibold mb-10 max-w-2xl mx-auto"
          >
            A hackathon project built to prioritize mental wellbeing for students through accessible AI and analytics.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="flex flex-col sm:flex-row gap-4 justify-center pointer-events-auto"
          >
            <Link href="/signin">
              <div className="px-8 py-4 rounded-full font-semibold text-base transition-all duration-300 bg-white text-zinc-900 hover:bg-zinc-100 hover:scale-105 shadow-[0_0_40px_rgba(255,255,255,0.2)] flex items-center justify-center cursor-pointer">
                Get Started for Free
              </div>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer - appears after scroll animation */}
      <footer className="relative z-20 bg-zinc-950 border-t border-zinc-900 pt-20 pb-12 px-6 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-3xl h-[2px] bg-linear-to-r from-transparent via-emerald-500/50 to-transparent" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 max-w-2xl h-[100px] bg-emerald-500/10 blur-[80px] pointer-events-none" />

        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12 md:gap-8 relative z-10 mb-16">
          <div className="col-span-1 md:col-span-2 flex flex-col items-start">
            <Link href="/" className="flex items-center gap-3 group mb-6">
              <div className="relative h-12 w-12 overflow-hidden rounded-xl shadow-lg transition-transform group-hover:scale-105 bg-white p-1">
                <img src="/logo.png" alt="Logo" className="h-full w-full object-cover rounded-lg" />
              </div>
              <span className="text-2xl font-bold text-white tracking-tight">
                Manah Arogya
              </span>
            </Link>
            <p className="text-base text-zinc-400 max-w-sm leading-relaxed mb-6">
              A comprehensive digital mental wellness platform for students. Connect, track, and heal with AI-driven, accessible support.
            </p>
            <div className="flex gap-4">
              <a href="#" className="h-10 w-10 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 hover:bg-zinc-800 hover:text-emerald-400 transition-all hover:border-emerald-500/30">
                <span className="sr-only">Twitter</span>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" /></svg>
              </a>
              <a href="#" className="h-10 w-10 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 hover:bg-zinc-800 hover:text-emerald-400 transition-all hover:border-emerald-500/30">
                <span className="sr-only">GitHub</span>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" /></svg>
              </a>
            </div>
          </div>

          <div>
            <h3 className="text-white font-semibold text-lg mb-6 tracking-wide">Product</h3>
            <ul className="space-y-4">
              <li><a href="#features" className="text-zinc-400 hover:text-emerald-400 transition-colors text-sm">Features</a></li>
              <li><a href="#how-it-works" className="text-zinc-400 hover:text-emerald-400 transition-colors text-sm">How it Works</a></li>
              <li><a href="#" className="text-zinc-400 hover:text-emerald-400 transition-colors text-sm">Pricing</a></li>
              <li><a href="#" className="text-zinc-400 hover:text-emerald-400 transition-colors text-sm">Testimonials</a></li>
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold text-lg mb-6 tracking-wide">Company</h3>
            <ul className="space-y-4">
              <li><a href="#" className="text-zinc-400 hover:text-emerald-400 transition-colors text-sm">About Us</a></li>
              <li><a href="#" className="text-zinc-400 hover:text-emerald-400 transition-colors text-sm">Careers</a></li>
              <li><a href="#" className="text-zinc-400 hover:text-emerald-400 transition-colors text-sm">Privacy Policy</a></li>
              <li><a href="#" className="text-zinc-400 hover:text-emerald-400 transition-colors text-sm">Terms of Service</a></li>
            </ul>
          </div>
        </div>

        <div className="max-w-6xl mx-auto pt-8 border-t border-zinc-900 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-zinc-500">
            © 2026 Manah Arogya. All rights reserved. Built for students, by students.
          </p>
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <span>Made with</span>
            <span className="text-gray-400">♥</span>
            <span>at Apex</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
