"use client";
import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { NotificationProvider } from "@/context/NotificationContext";
import { useLanguage } from "@/context/LanguageContext";
import { getUserSession } from "@/lib/userSession";
import { api } from "@/lib/api";
import MoodCheckInModal from "@/components/MoodCheckInModal";
import Grainient from "@/components/bg/bg";

const box_shadow = "shadow-[0_4px_20px_rgba(0,0,0,0.03)]";

const HOME_BACKGROUND_CONFIG = {
  useAnimatedBackground: true,
  containerClassName: "bg-white",
  grainientProps: {
    color1: "#c5fce2",
    color2: "#34d399",
    color3: "#0aa179",
    timeSpeed: 0.15,
    colorBalance: 0,
    warpStrength: 1,
    warpFrequency: 5,
    warpSpeed: 2,
    warpAmplitude: 50,
    blendAngle: 0,
    blendSoftness: 0.05,
    rotationAmount: 500,
    noiseScale: 3,
    grainAmount: 0.17,
    grainScale: 2,
    grainAnimated: false,
    contrast: 1.1,
    gamma: 1,
    saturation: 1,
    centerX: 0,
    centerY: 0,
    zoom: 0.9,
  },
};

const OverviewIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect width="7" height="9" x="3" y="3" rx="1" /><rect width="7" height="5" x="14" y="3" rx="1" /><rect width="7" height="9" x="14" y="12" rx="1" /><rect width="7" height="5" x="3" y="16" rx="1" />
  </svg>
);

const HabitIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);

const ChatbotIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" />
  </svg>
);

const ResourcesIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
  </svg>
);

const TherapyRoomIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 21h18"/>
    <path d="M5 21V7l7-4 7 4v14"/>
    <path d="M9 21v-6h6v6"/>
  </svg>
);

const ExercisesIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M8 4h8"/><path d="M9 2v4"/><path d="M15 2v4"/><path d="M12 10v10"/><path d="M8 14h8"/><path d="M6 22h12"/>
  </svg>
);

const AppointmentsIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect width="18" height="18" x="3" y="4" rx="2" ry="2" /><line x1="16" x2="16" y1="2" y2="6" /><line x1="8" x2="8" y1="2" y2="6" /><line x1="3" x2="21" y1="10" y2="10" />
  </svg>
);

const EventsIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M8 2v4" /><path d="M16 2v4" /><rect width="18" height="18" x="3" y="4" rx="2" /><path d="M3 10h18" /><path d="m9 16 2 2 4-4" />
  </svg>
);

const CommunityIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
);

const HelpIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><path d="M12 17h.01" />
  </svg>
);

const UserIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
  </svg>
);

const ShieldIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
  </svg>
);

// Navigation items
const navItems = [
  { id: "overview", label: "Overview", icon: OverviewIcon, href: "/home" },
  { id: "habit-tracker", label: "Habit Tracker", icon: HabitIcon, href: "/home/habit-tracker" },
  { id: "ai-chatbot", label: "AI Assistant", icon: ChatbotIcon, href: "/home/ai-chatbot" },
  { id: "voice-assistant", label: "Therapy Room", icon: TherapyRoomIcon, href: "/home/voice-assistant" },
  { id: "exercises", label: "Exercises", icon: ExercisesIcon, href: "/home/exercises" },
  { id: "resources", label: "Resources", icon: ResourcesIcon, href: "/home/resources" },
  { id: "appointments", label: "Appointments", icon: AppointmentsIcon, href: "/home/appointments" },
  { id: "events", label: "Events", icon: EventsIcon, href: "/home/events" },
  { id: "community", label: "Community", icon: CommunityIcon, href: "/home/community" },
  { id: "profile", label: "My Profile", icon: UserIcon, href: "/home/profile" },
];

export default function HomeLayout({ children }) {
  const { t } = useLanguage();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [userRole, setUserRole] = useState("user");
  const [moodModalOpen, setMoodModalOpen] = useState(false);
  const [savingMood, setSavingMood] = useState(false);
  const [moodError, setMoodError] = useState("");
  const pathname = usePathname();
  const router = useRouter();
  const collapseTimeoutRef = useRef(null);

  useEffect(() => {
    const sessionUser = getUserSession();
    if (!sessionUser?.id) {
      router.replace("/signin");
      return;
    }
    if (sessionUser?.role === "therapist") {
      router.replace("/therapist");
      return;
    }
    setUserRole(sessionUser.role || "user");
    setAuthChecked(true);

    const handleOpenMood = () => setMoodModalOpen(true);
    window.addEventListener("openMoodModal", handleOpenMood);
    return () => window.removeEventListener("openMoodModal", handleOpenMood);
  }, [router]);

  useEffect(() => {
    let mounted = true;
    async function checkMoodGate() {
      if (!authChecked) return;
      setMoodError("");
      const key = "mood_checkin_last_date";
      const today = new Date().toISOString().slice(0, 10);
      const local = typeof window !== "undefined" ? window.localStorage.getItem(key) : null;
      if (local === today) return;
      try {
        const res = await api.get("/mood/latest");
        const latest = res?.data;
        const latestDate = latest?.created_at ? String(latest.created_at).slice(0, 10) : null;
        if (latestDate === today) {
          window.localStorage.setItem(key, today);
          return;
        }
        if (mounted) setMoodModalOpen(true);
      } catch {
        if (mounted) setMoodModalOpen(true);
      }
    }
    checkMoodGate();
    return () => {
      mounted = false;
    };
  }, [authChecked, pathname]);

  const localizedNavItems = navItems.map((item) => ({ ...item, label: t(item.label) }));

  if (!authChecked) {
    return <div className="min-h-screen flex items-center justify-center text-sm text-gray-500">{t("Loading...")}</div>;
  }

  return (
    <div className={`flex h-screen relative overflow-hidden ${HOME_BACKGROUND_CONFIG.containerClassName}`}>
      {HOME_BACKGROUND_CONFIG.useAnimatedBackground && (
        <div className="fixed inset-0 z-0 pointer-events-none">
          <Grainient {...HOME_BACKGROUND_CONFIG.grainientProps} />
        </div>
      )}

      <div className="flex h-full w-full z-10 relative">
        <MoodCheckInModal
        open={moodModalOpen}
        saving={savingMood}
        error={moodError}
        onClose={() => setMoodModalOpen(false)}
        onSubmit={async (payload) => {
          setSavingMood(true);
          setMoodError("");
          try {
            await api.post("/mood/log", {
              mood_score: payload.mood_score,
              notes: payload.notes,
            });
            const today = new Date().toISOString().slice(0, 10);
            window.localStorage.setItem("mood_checkin_last_date", today);
            setMoodModalOpen(false);
          } catch (err) {
            setMoodError(err.message || "Failed to save mood");
          } finally {
            setSavingMood(false);
          }
        }}
      />
      
      {/* Sidebar */}
      <div className="h-full p-5 shrink-0">
        <aside
          className={`${sidebarCollapsed ? "w-20" : "w-[260px]"
            } ${box_shadow} bg-white rounded-[24px] h-full flex flex-col transition-all duration-300 ease-in-out`}
        >

          {/* Logo Area */}
          <div className="p-8 flex items-center">
            <div>
              {!sidebarCollapsed && (
                <img
                  src="/logo_1.jpeg"
                  alt="Manah Arogya"
                  className="h-auto w-full object-contain"
                />
              )}
              {sidebarCollapsed && (
                <img
                  src="/logo_1_short.png"
                  alt="Logo Icon"
                  className="w-full h-auto" />
              )}
            </div>
          </div>

          {/* Divider */}
          <div className="mx-4 border-t border-neutral-100" />

          {/* Navigation */}
          <nav className="flex-1 px-3 pt-4 pb-3 space-y-1 overflow-y-auto">
            {localizedNavItems.filter(item => !(userRole === "therapist" && item.id === "appointments")).map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ease-in-out ${isActive
                      ? "bg-emerald-50 text-neutral-900 font-semibold shadow-[inset_0_1px_1px_rgba(255,255,255,1),0_1px_2px_rgba(16,185,129,0.1)] border border-emerald-100/50"
                      : "text-neutral-700 hover:bg-emerald-50/50 hover:text-neutral-900"
                    } ${sidebarCollapsed ? "justify-center" : ""}`}
                  title={sidebarCollapsed ? item.label : ""}
                >
                  <div className={`${isActive ? "scale-105 text-gray-700" : "group-hover:scale-105 group-hover:text-gray-700"} transition-all duration-200`}>
                    <Icon />
                  </div>
                  {!sidebarCollapsed && <span className="text-[14px] font-medium tracking-tight">{item.label}</span>}
                </Link>
              );
            })}
            
            {userRole === "admin" && (
              <Link
                href="/admin"
                className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ease-in-out text-amber-700 hover:bg-amber-50 hover:text-amber-900 ${sidebarCollapsed ? "justify-center" : ""}`}
                title={sidebarCollapsed ? t("Admin Panel") : ""}
              >
                <div className="group-hover:scale-105 transition-all duration-200">
                  <ShieldIcon />
                </div>
                {!sidebarCollapsed && <span className="text-[14px] font-bold tracking-tight">{t("Admin Panel")}</span>}
              </Link>
            )}
            {userRole === "therapist" && (
              <Link
                href="/therapist"
                className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ease-in-out text-emerald-700 hover:bg-emerald-50 hover:text-emerald-900 mt-2 ${sidebarCollapsed ? "justify-center" : ""}`}
                title={sidebarCollapsed ? t("Therapist Panel") : ""}
              >
                <div className="group-hover:scale-105 transition-all duration-200">
                  <AppointmentsIcon />
                </div>
                {!sidebarCollapsed && <span className="text-[14px] font-bold tracking-tight">{t("Therapist Panel")}</span>}
              </Link>
            )}
          </nav>

          {/* Bottom Help */}
          <div className="mx-4 border-t border-neutral-100" />
          <div className="px-3 py-3">
            <a
              href="#"
              className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-neutral-700 hover:text-neutral-900 hover:bg-emerald-50/50 transition-all duration-200 ease-in-out ${sidebarCollapsed ? "justify-center" : ""}`}
              title={sidebarCollapsed ? t("Help & Support") : ""}
            >
              <div className="group-hover:scale-105 group-hover:text-gray-700 transition-all duration-200">
                <HelpIcon />
              </div>
              {!sidebarCollapsed && <span className="text-[14px] font-medium tracking-tight">{t("Help & Support")}</span>}
            </a>
          </div>
        </aside>
      </div>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-y-auto w-full h-full">
        <div className="max-w-6xl mx-auto w-full">
          <NotificationProvider>
            {children}
          </NotificationProvider>
        </div>
      </main>
    </div>
    </div>
  );
}
