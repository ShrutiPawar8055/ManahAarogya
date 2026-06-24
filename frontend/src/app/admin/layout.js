"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Users, ShieldAlert, Stethoscope, BookOpen, Calendar, Bell, LayoutDashboard, LogOut, ShieldCheck } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";
import { getUserSession } from "@/lib/userSession";
import { api } from "@/lib/api";
import { NotificationProvider } from "@/context/NotificationContext";
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

const navItems = [
  { id: "dashboard", label: "Dashboard", href: "/admin", icon: LayoutDashboard },
  { id: "users", label: "Users", href: "/admin/users", icon: Users },
  { id: "moderation", label: "Moderation", href: "/admin/moderation", icon: ShieldAlert },
  { id: "therapists", label: "Therapists", href: "/admin/therapists", icon: Stethoscope },
  { id: "resources", label: "Resources", href: "/admin/resources", icon: BookOpen },
  { id: "events", label: "Events", href: "/admin/events", icon: Calendar },
  { id: "alerts", label: "Alerts", href: "/admin/alerts", icon: Bell },
];

export default function AdminLayout({ children }) {
  const { t } = useLanguage();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    async function verifyAdmin() {
      try {
        const sessionUser = getUserSession();
        // If no basic session exists, kick to login or home
        if (!sessionUser?.id) {
          router.replace("/home");
          return;
        }
        
        // Double-check with backend to prevent stale localStorage issues
        try {
          const res = await api.get("/profile/me");
          const actualRole = res?.user?.role || res?.data?.user?.role;
          
          if (actualRole === "admin" || sessionUser.role === "admin") {
            setAuthChecked(true);
            return;
          }
        } catch (e) {
          console.error("Failed to verify admin role with backend", e);
        }

        // If backend verification fails and localStorage doesn't say admin, boot them
        if (sessionUser.role !== "admin") {
          router.replace("/home");
        } else {
          // If network failed but localStorage says admin, let them in
          setAuthChecked(true);
        }
      } catch (e) {
        console.error("Auth check failed", e);
        router.replace("/home");
      }
    }
    
    verifyAdmin();
  }, [router]);

  const localizedNavItems = navItems.map((item) => ({ ...item, label: t(item.label) }));

  if (!authChecked) {
    return <div className="min-h-screen flex items-center justify-center text-sm text-gray-500">{t("Loading Admin Panel...")}</div>;
  }

  return (
    <div className={`flex h-screen relative overflow-hidden ${HOME_BACKGROUND_CONFIG.containerClassName}`}>
      {HOME_BACKGROUND_CONFIG.useAnimatedBackground && (
        <div className="fixed inset-0 z-0 pointer-events-none">
          <Grainient {...HOME_BACKGROUND_CONFIG.grainientProps} />
        </div>
      )}

      <div className="flex h-full w-full z-10 relative">
        {/* Sidebar */}
        <div className="h-full p-5 shrink-0">
          <aside
            className={`${
              sidebarCollapsed ? "w-20" : "w-[260px]"
            } ${box_shadow} bg-white rounded-[24px] h-full flex flex-col transition-all duration-300 ease-in-out`}
          >
            {/* Logo Area */}
            <div className="p-8 flex flex-col items-center">
              <div>
                {!sidebarCollapsed && (
                  <img
                    src="/logo_1.jpeg"
                    alt="Manah Arogya"
                    className="h-auto w-full object-contain mb-2"
                  />
                )}
                {sidebarCollapsed && (
                  <img
                    src="/logo_1_short.png"
                    alt="Logo Icon"
                    className="w-full h-auto"
                  />
                )}
              </div>
              {!sidebarCollapsed && (
                <div className="bg-emerald-50 border border-emerald-100 px-3 py-1 rounded-full flex items-center gap-1.5 mt-2 shadow-sm relative overflow-hidden group">
                  <div className="absolute inset-0 bg-emerald-100 opacity-0 group-hover:opacity-50 transition-opacity"></div>
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 relative z-10" />
                  <span className="text-[10px] font-bold text-emerald-700 tracking-wider uppercase relative z-10">{t("Administrator")}</span>
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="mx-4 border-t border-neutral-100" />

            {/* Navigation */}
            <nav className="flex-1 px-3 pt-4 pb-3 space-y-1 overflow-y-auto w-full scrollbar-none">
              {localizedNavItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ease-in-out ${
                      isActive
                        ? "bg-emerald-50 text-neutral-900 font-semibold shadow-[inset_0_1px_1px_rgba(255,255,255,1),0_1px_2px_rgba(16,185,129,0.1)] border border-emerald-100/50"
                        : "text-neutral-700 hover:bg-emerald-50/50 hover:text-neutral-900"
                    } ${sidebarCollapsed ? "justify-center" : ""}`}
                    title={sidebarCollapsed ? item.label : ""}
                  >
                    <div
                      className={`${
                        isActive ? "scale-105 text-emerald-700" : "group-hover:scale-105 group-hover:text-emerald-700 text-gray-400"
                      } transition-all duration-200`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    {!sidebarCollapsed && (
                      <span className="text-[14px] font-medium tracking-tight">
                        {item.label}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* Bottom Help */}
            <div className="mx-4 border-t border-neutral-100" />
            <div className="px-3 py-3 rounded-b-[24px]">
              <button
                onClick={() => {
                  window.localStorage.removeItem("user_session");
                  router.push("/signin");
                }}
                className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-neutral-700 hover:text-red-600 hover:bg-red-50/80 transition-all duration-200 ease-in-out ${
                  sidebarCollapsed ? "justify-center" : ""
                }`}
                title={sidebarCollapsed ? t("Sign Out") : ""}
              >
                <div className="group-hover:scale-105 transition-all duration-200 text-gray-400 group-hover:text-red-500">
                  <LogOut className="w-5 h-5" />
                </div>
                {!sidebarCollapsed && (
                  <span className="text-[14px] font-medium tracking-tight">
                    {t("Sign Out")}
                  </span>
                )}
              </button>
            </div>
          </aside>
        </div>

        {/* Main Content */}
        <main className="flex-1 p-6 overflow-y-auto w-full h-full">
          <div className="max-w-6xl mx-auto w-full">
            <NotificationProvider>{children}</NotificationProvider>
          </div>
        </main>
      </div>
    </div>
  );
}
