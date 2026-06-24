"use client";

import { useEffect, useState, useMemo } from "react";
import { api } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";
import { CheckCircle, Clock, Video, FileText, Users, CalendarDays, TrendingUp, MessageSquare, Bell } from "lucide-react";
import Link from "next/link";
import Header from "@/components/Header";

const static_card_style = "rounded-xl bg-white p-6 shadow-sm ring-1 ring-black/5";

export default function TherapistDashboardPage() {
  const { t } = useLanguage();
  const [stats, setStats] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const [statsRes, apptsRes, patientsRes, notificationsRes] = await Promise.all([
        api.get("/therapist/stats"),
        api.get("/therapist/appointments"),
        api.get("/therapist/patients"),
        api.get("/therapist/notifications?unread_only=true"),
      ]);
      setStats(statsRes?.data || null);
      setAppointments(apptsRes?.data || []);
      setPatients(patientsRes?.data || []);
      setNotifications(Array.isArray(notificationsRes?.data) ? notificationsRes.data : []);
    } catch (err) {
      setError(err.message || t("Failed to load dashboard"));
    } finally {
      setLoading(false);
    }
  };

  const pendingAppointments = useMemo(() => appointments.filter(a => a.status === 'pending'), [appointments]);
  
  const todayDate = new Date().toISOString().split('T')[0];
  const todaysSchedule = useMemo(() => appointments.filter(a => {
    if (!a.start_time) return false;
    return a.start_time.startsWith(todayDate) && ['booked', 'confirmed', 'rescheduled'].includes(a.status);
  }).sort((a,b) => new Date(a.start_time) - new Date(b.start_time)), [appointments, todayDate]);

  if (loading) return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-8 animate-pulse">
      <div className={`h-32 md:col-span-12 ${static_card_style} bg-gray-50`} />
      <div className={`h-64 md:col-span-8 ${static_card_style} bg-gray-50`} />
      <div className={`h-64 md:col-span-4 ${static_card_style} bg-gray-50`} />
    </div>
  );

  return (
    <div className="pb-20">
      <div className="flex justify-between items-end mb-8">
        <Header
          title={t("Practitioner Overview")}
          subtitle={t("Here's a snapshot of your workload today.")}
        />
        <div className="flex items-center gap-4 hidden md:flex mb-2">
          <button className="relative p-3 bg-white rounded-xl ring-1 ring-black/5 hover:bg-gray-50 transition-colors shadow-sm">
            <Bell className="w-5 h-5 text-gray-600" />
            {notifications.length > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white ring-2 ring-white">
                {notifications.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-gray-800">
          {error}
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className={`${static_card_style} flex flex-col gap-2 relative overflow-hidden group`}>
          <div className="flex items-center gap-3 mb-1">
            <div className="text-gray-400">
              <CalendarDays className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{t("Sessions")}</span>
          </div>
          <span className="text-3xl font-bold tracking-tight text-gray-900">{stats?.sessions_today || 0}</span>
        </div>

        <div className={`${static_card_style} flex flex-col gap-2 relative overflow-hidden group`}>
           <div className="flex items-center gap-3 mb-1">
            <div className="text-gray-400">
              <Clock className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{t("Pending")}</span>
          </div>
          <span className="text-3xl font-bold tracking-tight text-gray-900">{stats?.pending_requests || pendingAppointments.length}</span>
        </div>

        <div className={`${static_card_style} flex flex-col gap-2 relative overflow-hidden group`}>
          <div className="flex items-center gap-3 mb-1">
            <div className="text-gray-400">
              <Users className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{t("Patients")}</span>
          </div>
          <span className="text-3xl font-bold tracking-tight text-gray-900">{patients?.length || stats?.active_patients || 0}</span>
        </div>

        <div className={`${static_card_style} flex flex-col gap-2 relative overflow-hidden group`}>
           <div className="flex items-center gap-3 mb-1">
            <div className="text-gray-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{t("Total")}</span>
          </div>
          <span className="text-3xl font-bold tracking-tight text-gray-900">{stats?.total_appointments || 0}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        
        {/* Left Column: Today's Schedule */}
        <div className={`md:col-span-8 ${static_card_style} flex flex-col`}>
          <div className="flex justify-between items-center mb-6">
             <h2 className="text-lg font-bold tracking-tight text-gray-900">{t("Today's Schedule")}</h2>
             <Link href="/therapist/appointments" className="text-emerald-600 hover:text-emerald-700 font-semibold text-sm transition-colors">{t("View All →")}</Link>
          </div>

          <div className="space-y-4">
            {todaysSchedule.length > 0 ? todaysSchedule.map(appt => (
              <div key={appt.id} className="group flex items-center justify-between p-4 rounded-xl ring-1 ring-gray-100 bg-gray-50 hover:bg-emerald-50/50 transition-all duration-200">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-white ring-1 ring-black/5 flex flex-col items-center justify-center font-bold text-gray-700 shadow-sm">
                    <span className="text-sm">{new Date(appt.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}).replace(/ AM| PM/, '')}</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 text-base">{appt.patient_name}</h3>
                    <div className="flex items-center gap-2 text-xs text-gray-500 mt-1 font-medium">
                      <span className="flex items-center gap-1 bg-white px-2 py-0.5 rounded shadow-sm ring-1 ring-black/5"><Video className="w-3 h-3"/> {t(appt.mode || "Online")}</span>
                      {appt.status === "confirmed" && <span className="flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded shadow-sm ring-1 ring-emerald-200"><CheckCircle className="w-3 h-3"/> {t("Confirmed")}</span>}
                    </div>
                  </div>
                </div>
                <Link href={`/therapist/patients/${appt.user_id}`} className="px-4 py-2 bg-white text-gray-700 font-bold rounded-lg ring-1 ring-gray-200 shadow-sm hover:bg-gray-50 hover:text-gray-900 transition-all active:scale-[0.98] text-sm hidden sm:block">
                  {t("Dossier")}
                </Link>
              </div>
            )) : (
              <div className="w-full flex items-center justify-center p-8 border-2 border-dashed border-gray-200 rounded-xl bg-gray-50/50">
                <div className="flex flex-col items-center flex-1 py-4">
                  <CalendarDays className="w-8 h-8 text-gray-400 mb-3" />
                  <span className="text-sm font-medium text-gray-500">{t("No sessions scheduled today.")}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Alerts & Requests */}
        <div className={`md:col-span-4 ${static_card_style} flex flex-col`}>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold tracking-tight text-gray-900">{t("Action Items")}</h2>
            <span className="bg-red-50 text-red-700 ring-1 ring-red-200 text-xs px-2.5 py-1 rounded-full font-bold">{notifications.length || pendingAppointments.length} {t("Pending")}</span>
          </div>

          <div className="flex-1 space-y-4">
             {notifications.length > 0 ? notifications.slice(0, 5).map((item) => (
                <div key={item.id} className="p-4 bg-amber-50/50 ring-1 ring-amber-100 rounded-xl">
                  <h4 className="font-bold text-gray-900 text-sm">{item.title}</h4>
                  <p className="text-xs text-gray-600 mt-1 mb-3 line-clamp-2 leading-relaxed">{item.message}</p>
                  <Link href="/therapist/appointments" className="w-full flex items-center justify-center py-2 bg-white text-amber-700 font-bold ring-1 ring-amber-200 rounded-lg hover:bg-amber-50 hover:shadow-sm transition-all text-sm">
                    {t("Review Request")}
                  </Link>
                </div>
              )) : (
                 <div className="h-full min-h-[150px] flex flex-col items-center justify-center p-6 text-center">
                  <CheckCircle className="w-8 h-8 text-emerald-300 mb-2" />
                  <p className="text-gray-500 font-medium text-sm">{t("You are all caught up!")}</p>
                </div>
              )}
          </div>

          <div className="mt-6 pt-6 border-t border-gray-100">
             <Link href="/therapist/messages" className="group flex items-center justify-between p-4 rounded-xl bg-gray-50 ring-1 ring-gray-100 hover:bg-emerald-50 hover:ring-emerald-100 transition-all">
               <div className="flex items-center gap-3">
                 <MessageSquare className="w-5 h-5 text-gray-400 group-hover:text-emerald-600" />
                 <span className="text-sm font-bold text-gray-700 group-hover:text-emerald-700">{t("Inbox")}</span>
               </div>
               <span className="text-gray-400 group-hover:text-emerald-600 group-hover:translate-x-1 transition-transform">&rarr;</span>
             </Link>
          </div>

        </div>

      </div>
    </div>
  );
}
