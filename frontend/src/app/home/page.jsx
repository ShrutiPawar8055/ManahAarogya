"use client";

import { useEffect, useState, useMemo } from "react";
import Header from "@/components/Header";
import AssessmentModal from "@/components/assessment/AssessmentModal";
import { useLanguage } from "@/context/LanguageContext";
import { api } from "@/lib/api";
import { getUserSession } from "@/lib/userSession";
import { useRouter } from "next/navigation";

const static_card_style = "rounded-xl bg-white p-6 shadow-sm ring-1 ring-black/5";

export default function Overview() {
  const { t } = useLanguage();
  const router = useRouter();
  const [dashboard, setDashboard] = useState(null);
  const [insights, setInsights] = useState(null);
  const [moodHistory, setMoodHistory] = useState([]);
  const [latestAssessment, setLatestAssessment] = useState(null);
  const [assessmentHistory, setAssessmentHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exerciseStarted, setExerciseStarted] = useState(false);
  const [isTherapist, setIsTherapist] = useState(false);
  const [assessmentModalOpen, setAssessmentModalOpen] = useState(false);

  async function loadDashboard() {
    setLoading(true);
    setError("");
    try {
      const [dashRes, insightsRes, historyRes, latestAssessmentRes, assessmentHistoryRes] = await Promise.all([
        api.get("/dashboard"),
        api.get("/insights/daily"),
        api.get("/mood/history?days=7"),
        api.get("/assessments/latest"),
        api.get("/assessments/history?limit=4"),
      ]);
      setDashboard(dashRes?.data || null);
      setInsights(insightsRes?.data || null);
      setMoodHistory(Array.isArray(historyRes?.data) ? historyRes.data : []);
      setLatestAssessment(latestAssessmentRes?.data || null);
      setAssessmentHistory(Array.isArray(assessmentHistoryRes?.data) ? assessmentHistoryRes.data : []);
    } catch (err) {
      setError(err.message || t("Failed to load dashboard"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const sessionUser = getUserSession();
    if (sessionUser?.role === "therapist") {
      setIsTherapist(true);
      setLoading(false);
      return;
    }
    loadDashboard();
  }, []);

  const paddedMoodHistory = useMemo(() => {
    if (!moodHistory) return [];
    const filledHistory = [...moodHistory];
    const today = new Date();
    while (filledHistory.length < 7) {
       const emptyDate = new Date(today);
       emptyDate.setDate(today.getDate() - (7 - filledHistory.length));
       filledHistory.unshift({ id: `empty-${filledHistory.length}`, mood_score: 0, created_at: emptyDate.toISOString(), empty: true });
    }
    return filledHistory;
  }, [moodHistory]);

  const latestScoreCards = useMemo(() => {
    return Array.isArray(latestAssessment?.scores) ? latestAssessment.scores : [];
  }, [latestAssessment]);

  const summaryText = useMemo(() => {
    if (!insights?.summary) return "We’re tracking your mood and habits to personalize support.";
    if (insights.summary.startsWith("Today’s snapshot:")) {
      return "We’re tracking your mood and habits to personalize support.";
    }
    return insights.summary;
  }, [insights]);

  const handleActionClick = (title) => {
    const lTitle = title.toLowerCase();
    if (lTitle.includes("mood")) {
      window.dispatchEvent(new Event("openMoodModal"));
    } else if (lTitle.includes("assessment") || lTitle.includes("retake")) {
      setAssessmentModalOpen(true);
    } else if (lTitle.includes("exercise")) {
      document.getElementById("exercise-for-you")?.scrollIntoView({ behavior: "smooth" });
    } else {
      document.getElementById("resources")?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <>
      <AssessmentModal
        open={assessmentModalOpen}
        onClose={() => setAssessmentModalOpen(false)}
        onCompleted={() => {
          void loadDashboard();
        }}
      />

      <Header
        title={t("Dashboard")}
        subtitle="Understand what’s happening, why, and what to do next."
      />

      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-gray-800">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 animate-pulse">
          <div className={`h-32 md:col-span-8 ${static_card_style} bg-gray-50`} />
          <div className={`h-32 md:col-span-4 ${static_card_style} bg-gray-50`} />
          <div className={`h-40 md:col-span-12 ${static_card_style} bg-gray-50`} />
        </div>
      ) : isTherapist ? (
        <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-white shadow-sm ring-1 ring-black/5 pb-20 mt-10">
           <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mb-6 ring-4 ring-emerald-50">
             <svg className="w-10 h-10 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
           </div>
           <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">Practitioner Interface</h2>
           <p className="text-lg text-gray-600 max-w-lg mb-10 leading-relaxed">
             This general wellness dashboard is designed for patients. Visit your dedicated Therapist panel to manage your schedule, accept appointments, and maintain clinical notes.
           </p>
           <button 
             onClick={() => router.push('/therapist')}
             className="rounded-xl bg-emerald-600 px-8 py-4 text-base font-bold text-white transition-all duration-200 hover:bg-emerald-700 hover:shadow-lg active:scale-95 focus:outline-none focus:ring-4 focus:ring-emerald-500/30"
           >
             Go to Therapist Portal
           </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 pb-20 text-gray-900">
          
          {/* Quick Actions - Irregular 7 / 5 split */}
          <div className="md:col-span-7 flex items-center justify-between rounded-xl bg-emerald-700/70 p-6 text-white shadow-sm ring-1 ring-emerald-800/50 opacity-95">
            <div>
              <h3 className="text-xl font-bold tracking-tight text-white mb-1">Therapy Room</h3>
              <p className="text-emerald-100 text-sm font-medium">Talk to our AI Voice Agents</p>
            </div>
            <div className="h-10 w-10 flex items-center justify-center opacity-80">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
            </div>
          </div>
          
          <a href="#exercise-for-you" className="md:col-span-5 group flex items-center justify-between rounded-xl bg-emerald-50 p-6 text-gray-900 shadow-sm ring-1 ring-emerald-200 hover:bg-emerald-100 transition-all duration-200 ease-in-out hover:shadow-md hover:-translate-y-0.5 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2">
            <div>
              <h3 className="text-xl font-bold tracking-tight text-gray-900 mb-1">Quick Exercise</h3>
              <p className="text-gray-800 text-sm font-medium">Do a quick breathing reset</p>
            </div>
            <div className="h-10 w-10 flex items-center justify-center text-gray-700 group-hover:translate-x-1 transition-transform duration-200 ease-in-out">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 4h8"/><path d="M9 2v4"/><path d="M15 2v4"/><path d="M12 10v10"/><path d="M8 14h8"/><path d="M6 22h12"/></svg>
            </div>
          </a>

          <div className={`md:col-span-12 ${static_card_style}`}>
            <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div className="max-w-3xl">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">Assessment Overview</p>
                <h2 className="text-2xl font-bold tracking-tight text-gray-900">
                  {latestAssessment?.feedback?.ui_summary || "Retake your test whenever you want a fresh dashboard readout."}
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-gray-600">
                  {latestAssessment?.feedback?.overall_summary ||
                    "Each retake generates updated scores and structured AI feedback using your recent platform activity."}
                </p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <span className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-gray-600">
                    Latest risk: {latestAssessment?.feedback?.risk_level || dashboard?.user_state?.risk_level || "low"}
                  </span>
                  <span className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-gray-600">
                    Attempts: {assessmentHistory.length}
                  </span>
                  {latestAssessment?.completed_at && (
                    <span className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-gray-600">
                      Last completed: {new Date(latestAssessment.completed_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>

              <button
                onClick={() => setAssessmentModalOpen(true)}
                className="shrink-0 rounded-xl bg-gray-900 px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-gray-800"
              >
                Retake Test
              </button>
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
              <div className="grid gap-4 md:grid-cols-2">
                {latestScoreCards.length > 0 ? latestScoreCards.map((score) => (
                  <article key={score.test_id} className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                          {score.title || score.test_id}
                        </p>
                        <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900">{score.score}</p>
                      </div>
                      <span className="rounded-full bg-white px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-gray-600 ring-1 ring-gray-200">
                        {score.severity}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-relaxed text-gray-600">{score.summary}</p>
                  </article>
                )) : (
                  <div className="md:col-span-2 rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50 p-6">
                    <h3 className="text-base font-bold text-gray-900">No completed assessment yet</h3>
                    <p className="mt-2 text-sm text-gray-500">
                      Start a test to generate your first score summary and AI feedback.
                    </p>
                  </div>
                )}
              </div>

              <div className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Recent Attempts</p>
                <div className="mt-4 space-y-3">
                  {assessmentHistory.length === 0 && (
                    <p className="text-sm text-gray-500">Your assessment history will appear here.</p>
                  )}
                  {assessmentHistory.map((attempt) => (
                    <div key={attempt.id} className="rounded-xl bg-white px-4 py-3 ring-1 ring-gray-200">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-bold text-gray-900">
                          {attempt.mode === "initial" ? "Initial Assessment" : "Retake Assessment"}
                        </p>
                        <span className="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider text-gray-600">
                          {attempt.feedback?.risk_level || attempt.risk_level || "low"}
                        </span>
                      </div>
                      <p className="mt-2 text-xs font-medium uppercase tracking-wider text-gray-400">
                        {new Date(attempt.completed_at || attempt.created_at).toLocaleString()}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(attempt.scores || []).map((score) => (
                          <span
                            key={`${attempt.id}-${score.test_id}`}
                            className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-100"
                          >
                            {score.title || score.test_id}: {score.score}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Stats & Story - Irregular 4 / 8 split */}
          <div className="md:col-span-4 flex flex-col gap-8">
             <div className={static_card_style}>
                <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-3">Risk & Trend</p>
                <div className="flex items-end justify-between">
                   <div>
                     <p className="text-2xl font-bold tracking-tight text-gray-900 capitalize truncate max-w-[120px]">{dashboard?.user_state?.risk_level || "low"}</p>
                     <p className="text-xs text-gray-500 font-medium mt-1">Risk Level</p>
                   </div>
                   <div className="text-right">
                     <p className="text-2xl font-bold tracking-tight text-gray-900 capitalize truncate max-w-[120px]">{dashboard?.user_state?.mood_trend || "unknown"}</p>
                     <p className="text-xs text-gray-500 font-medium mt-1">Mood Trend</p>
                   </div>
                </div>
             </div>
             
             <div className={`${static_card_style} flex-1`}>
                <div className="flex justify-between items-start mb-4">
                  <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider">7-Day Averages</p>
                </div>
                <div className="flex items-center gap-8">
                   <div>
                     <p className="text-3xl font-bold tracking-tight text-gray-900 truncate max-w-[100px]">{dashboard?.user_state?.mood_avg_7d ?? "—"}<span className="text-lg text-gray-400 font-semibold">/10</span></p>
                     <p className="text-xs text-gray-500 font-medium mt-1">Mood Score</p>
                   </div>
                   <div>
                     <p className="text-3xl font-bold tracking-tight text-gray-900 truncate max-w-[100px]">{insights?.signals?.habit_completion?.completed || 0}<span className="text-lg text-gray-400 font-semibold">/{insights?.signals?.habit_completion?.total || 0}</span></p>
                     <p className="text-xs text-gray-500 font-medium mt-1">Habits Done</p>
                   </div>
                </div>
             </div>
          </div>

          <div className={`md:col-span-8 ${static_card_style} flex flex-col`}>
             <p className="text-sm font-bold tracking-tight text-gray-900 mb-6">Your Story (Last 7 Days)</p>
             <div className="flex items-end justify-between gap-3 h-48 w-full">
                {paddedMoodHistory.map((item, idx) => (
                    <div key={item.id || idx} className={`flex flex-1 flex-col items-center gap-3 relative h-full justify-end group ${item.empty ? 'opacity-40' : ''}`}>
                      <div
                        className={`w-full max-w-[40px] rounded-t-md transition-all duration-300 ease-in-out group-hover:opacity-80 group-hover:scale-y-105 origin-bottom ${item.empty ? 'bg-gray-100' : 'bg-emerald-500'}`}
                        style={{ height: item.empty ? '10%' : `${Math.max(10, (Number(item.mood_score || 0) / 10) * 100)}%` }}
                        title={item.empty ? 'No data' : `${item.mood_score}/10`}
                      />
                      <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 shrink-0">
                        {item.empty ? "-" : String(item.created_at || "").slice(5, 10)}
                      </span>
                    </div>
                ))}
              </div>
          </div>

          {/* Current Focus - Full width card */}
          <div className={`md:col-span-12 ${static_card_style}`}>
             <h2 className="text-lg font-bold tracking-tight text-gray-900 mb-5">Identified Focus</h2>
             <div className="flex gap-3 flex-wrap">
               {(dashboard?.user_problems || []).map((item, idx) => (
                 <span key={`${item.name}-${idx}`} className="rounded-full ring-1 ring-gray-200 bg-gray-50 px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm transition-colors duration-200 hover:bg-gray-100 cursor-default">
                   {item.name} <span className="text-gray-400 font-medium ml-1">({item.severity})</span>
                 </span>
               ))}
               {(!dashboard?.user_problems || dashboard.user_problems.length === 0) && (
                 <div className="w-full flex items-center justify-center p-6 border-2 border-dashed border-gray-200 rounded-xl bg-gray-50/50">
                    <div className="flex flex-col items-center flex-1 py-4">
                        <svg className="w-8 h-8 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        <span className="text-sm font-medium text-gray-500">No specific focus identified yet.</span>
                    </div>
                 </div>
               )}
             </div>
          </div>

          {/* What's Happening & Exercise inline - Irregular 7 / 5 split */}
          <div className={`md:col-span-7 ${static_card_style}`}>
            <h2 className="text-lg font-bold tracking-tight text-gray-900 mb-3">What’s Happening (& Why)</h2>
            <p className="text-base text-gray-600 mb-8 leading-relaxed max-w-xl">{summaryText}</p>

            <div className="space-y-8">
              <div>
                <p className="text-sm font-bold tracking-tight text-gray-900 mb-4">Explanations</p>
                <ul className="space-y-3">
                  {(dashboard?.explanations || insights?.explanations || []).map((line, idx) => (
                    <li key={idx} className="text-sm text-gray-600 leading-relaxed flex gap-3">
                      <span className="text-gray-600 shrink-0">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      </span>
                      <span>{line}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <p className="text-sm font-bold tracking-tight text-gray-900 mb-4">Next Actions</p>
                <div className="space-y-4">
                  {(dashboard?.next_actions || insights?.next_actions || []).map((a, idx) => (
                    <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl ring-1 ring-gray-100 bg-gray-50 p-5 transition-all duration-200 hover:shadow-sm">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-gray-900 truncate">{a.title}</p>
                        <p className="mt-1 text-xs text-gray-500 line-clamp-2 leading-relaxed">{a.because}</p>
                      </div>
                      <button 
                        onClick={() => handleActionClick(a.title)} 
                        className="shrink-0 text-xs font-bold bg-white ring-1 ring-gray-200 text-gray-700 px-4 py-2.5 rounded-lg transition-all duration-200 ease-in-out hover:bg-gray-50 hover:text-gray-900 hover:shadow-sm active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
                      >
                         Take Action
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Exercise inline element directly on dashboard */}
          <div id="exercise-for-you" className={`md:col-span-5 ${static_card_style} flex flex-col`}>
             <div className="flex justify-between items-center mb-6">
               <h2 className="text-lg font-bold tracking-tight text-gray-900">Exercise for you</h2>
               <span className="text-xs font-semibold bg-gray-100 text-gray-600 px-3 py-1.5 rounded-full tracking-wider uppercase">1 min</span>
             </div>
             
             <div className="flex-1 flex flex-col items-center justify-center p-8 bg-emerald-50/50 rounded-xl ring-1 ring-emerald-100/50 relative overflow-hidden">
                <h3 className="text-base font-bold text-gray-900 mb-10 tracking-tight z-10">4-7-8 Breathing</h3>
                {exerciseStarted ? (
                  <div className="w-28 h-28 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/20 animate-[ping_4s_cubic-bezier(0,0,0.2,1)_infinite] flex items-center justify-center relative mb-10 z-10">
                    <span className="absolute text-white font-bold text-xs tracking-widest uppercase">Breathe</span>
                  </div>
                ) : (
                  <div className="w-28 h-28 rounded-full flex items-center justify-center relative mb-10 z-10">
                    <button
                      onClick={() => setExerciseStarted(true)}
                      className="w-24 h-24 rounded-full bg-emerald-500 hover:bg-emerald-600 hover:scale-105 active:scale-95 transition-all duration-200 text-white font-bold text-sm tracking-widest uppercase shadow-lg shadow-emerald-500/30 flex items-center justify-center cursor-pointer focus:outline-none focus:ring-4 focus:ring-emerald-500/30"
                    >
                      Start
                    </button>
                  </div>
                )}
                <div className="text-sm font-semibold text-gray-900 text-center space-y-2 z-10">
                  <p>1. Inhale for 4s</p>
                  <p>2. Hold for 7s</p>
                  <p>3. Exhale for 8s</p>
                </div>
                
                {/* Decorative background shapes for polish */}
                <div className="absolute top-[-10%] right-[-10%] w-40 h-40 bg-emerald-100/50 rounded-full blur-2xl z-0"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-32 h-32 bg-emerald-200/30 rounded-full blur-2xl z-0"></div>
             </div>
             <p className="text-xs font-medium text-gray-500 text-center mt-6 leading-relaxed max-w-[250px] mx-auto">Follow the rhythm of the circle to quickly lower anxiety.</p>
          </div>

          {/* Resources - Uses standard grid-cols-1 md:grid-cols-3 inside a full width span */}
          <div id="resources" className="md:col-span-12 pt-6">
            <h2 className="text-lg font-bold tracking-tight text-gray-900 mb-6">Recommended Resources</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {(dashboard?.recommended_resources || []).map((resource) => (
                <article
                  key={`${resource.id}-${resource.title}`}
                  className="group flex flex-col bg-white ring-1 ring-black/5 rounded-2xl overflow-hidden transition-all duration-300 ease-in-out hover:shadow-lg hover:ring-black/10 hover:-translate-y-1"
                >
                  <div className="aspect-video w-full bg-gray-100 relative overflow-hidden">
                    <img
                      src={resource.thumbnail_url || `https://picsum.photos/seed/${encodeURIComponent(resource.id + '-' + resource.title)}/600/350`}
                      alt={resource.title}
                      className="h-full w-full object-cover transition-transform duration-500 ease-in-out group-hover:scale-105"
                      loading="lazy"
                      referrerPolicy="no-referrer"
                      onError={(e) => { e.target.src = `https://picsum.photos/seed/${encodeURIComponent(resource.title)}/600/350`; }}
                    />
                    <div className="absolute top-4 left-4">
                       <span className="bg-white/95 px-3 py-1.5 rounded-md text-xs font-bold text-gray-900 shadow-sm uppercase tracking-wider backdrop-blur-sm">
                         {resource.type || resource.resource_type || "Guide"}
                       </span>
                    </div>
                  </div>
                  <div className="flex flex-1 flex-col p-6">
                    <h3 className="text-base font-bold text-gray-900 line-clamp-2 tracking-tight group-hover:text-gray-800 transition-colors duration-200">
                      {resource.title}
                    </h3>
                    <p className="mt-3 line-clamp-2 text-sm text-gray-600 leading-relaxed">
                      {resource.description || "A personalized resource picked to help support your current wellness journey."}
                    </p>
                    <div className="mt-6 flex items-center justify-between pt-5 border-t border-gray-100">
                      <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        {resource.category || "Wellness"}
                      </span>
                      <a
                        href={resource.url || "#"}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-bold text-gray-700 transition-colors duration-200 hover:text-gray-900 flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 rounded px-2 py-1 -mx-2 -my-1"
                        onClick={(event) => {
                          if (!resource.url) event.preventDefault();
                        }}
                      >
                        Read
                        <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                      </a>
                    </div>
                  </div>
                </article>
              ))}
              {(!dashboard?.recommended_resources || dashboard.recommended_resources.length === 0) && (
                <div className="md:col-span-3 rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50 p-12 flex flex-col items-center justify-center text-center transition-all duration-200 hover:bg-gray-100/50">
                  <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm ring-1 ring-black/5 mb-5">
                    <svg className="w-8 h-8 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 tracking-tight mb-2">No resources matched right now</h3>
                  <p className="text-sm text-gray-500 mb-6 max-w-sm leading-relaxed">Check back later or complete a quick check-in to get new, personalized recommendations.</p>
                  <button 
                    onClick={() => window.dispatchEvent(new Event("openMoodModal"))} 
                    className="bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 hover:text-gray-900 font-bold py-2.5 px-6 rounded-xl shadow-sm transition-all duration-200 ease-in-out active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
                  >
                    Complete Check-in
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
