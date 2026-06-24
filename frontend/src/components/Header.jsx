"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { onAuthStateChanged, signOut } from "firebase/auth";

import { auth } from "../../firebaseConfig";
import { LANGUAGE_OPTIONS, useLanguage } from "@/context/LanguageContext";
import { useNotification } from "@/context/NotificationContext";
import { clearUserSession, firstNameFromName, getUserSession, saveUserSession } from "@/lib/userSession";

export default function Header({ title, subtitle }) {
  const { language, setLanguage, t } = useLanguage();
  const [user, setUser] = useState(() => {
    const existing = getUserSession();
    if (!existing) return null;
    return {
      uid: existing.id,
      displayName: existing.name,
      email: existing.email,
      photoURL: null,
    };
  });
  const [showInfoMenu, setShowInfoMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const menuRef = useRef(null);

  const { notifications, unreadCount, markAllAsRead } = useNotification() || {
    notifications: [],
    unreadCount: 0,
    markAllAsRead: () => {},
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      if (currentUser) {
        saveUserSession({
          id: currentUser.uid,
          name: currentUser.displayName || "",
          first_name: firstNameFromName(currentUser.displayName || "", currentUser.email || ""),
          email: currentUser.email || "",
        });
      }
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowInfoMenu(false);
        setShowNotifications(false);
        setShowProfileMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleInfoClick = () => {
    setShowInfoMenu((prev) => !prev);
    setShowNotifications(false);
    setShowProfileMenu(false);
  };

  const handleNotificationClick = () => {
    if (!showNotifications && unreadCount > 0) {
      markAllAsRead();
    }
    setShowInfoMenu(false);
    setShowNotifications((prev) => !prev);
    setShowProfileMenu(false);
  };

  const handleProfileClick = () => {
    setShowProfileMenu((prev) => !prev);
    setShowInfoMenu(false);
    setShowNotifications(false);
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } finally {
      clearUserSession();
      setShowProfileMenu(false);
    }
  };

  return (
    <div className="mb-6 flex items-center justify-between">
      <div>
        <h1 className="font-google text-2xl font-bold text-gray-800">{title}</h1>
        <p className="text-sm text-gray-500">{subtitle}</p>
      </div>

      <div className="relative flex items-center gap-3" ref={menuRef}>
        <button
          className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-gray-200 bg-gray-50 transition-colors hover:bg-gray-100"
          aria-label={t("Info")}
          onClick={handleInfoClick}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke="#292929" strokeWidth="2" />
            <path d="M12 11.5V16" stroke="#292929" strokeWidth="2" strokeLinecap="round" />
            <circle cx="12" cy="8" r="1" fill="#292929" />
          </svg>
        </button>

        {showInfoMenu && (
          <div className="absolute right-0 top-14 z-50 w-72 overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-xl sm:right-[250px]">
            <div className="border-b border-gray-50 bg-gray-50/60 px-4 py-3">
              <h3 className="text-sm font-semibold text-gray-800">{t("Display Language")}</h3>
              <p className="mt-1 text-xs text-gray-500">{t("Choose how text appears across the platform.")}</p>
            </div>
            <div className="p-2">
              {LANGUAGE_OPTIONS.map((option) => (
                <button
                  key={option.code}
                  type="button"
                  onClick={() => {
                    setLanguage(option.code);
                    setShowInfoMenu(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-xl px-3 py-3 text-left text-sm transition-colors ${
                    language === option.code ? "bg-emerald-50 text-emerald-700" : "text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  <span className="font-medium">{option.label}</span>
                  {language === option.code && <span className="text-xs font-semibold uppercase tracking-wider">OK</span>}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="relative">
          <div className="flex h-12 items-center gap-3 rounded-full border-2 border-gray-200 bg-gray-50 px-4">
            <button
              className="relative flex h-9 w-9 items-center justify-center rounded-full transition-colors hover:bg-gray-100"
              onClick={handleNotificationClick}
              aria-label={t("Notifications")}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M9 17H5.6c-1.26 0-1.89 0-2.01-.1-.15-.11-.18-.18-.2-.36-.01-.16.37-.79 1.14-2.05C5.32 13.18 6 11.29 6 8.6 6 7.11 6.63 5.69 7.76 4.64A6.17 6.17 0 0 1 12 3c1.6 0 3.12.59 4.24 1.64A5.9 5.9 0 0 1 18 8.6c0 2.69.68 4.58 1.47 5.89.77 1.26 1.15 1.89 1.14 2.05-.02.18-.05.25-.2.36-.12.1-.75.1-2 .1H15m-6 0V18a3 3 0 0 0 6 0v-1"
                  stroke="#111827"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute right-0 top-0 flex h-4 w-4 items-center justify-center rounded-full border-2 border-white bg-red-500 text-[10px] font-bold text-white">
                  {unreadCount}
                </span>
              )}
            </button>

            <button className="flex items-center gap-2" onClick={handleProfileClick}>
              <div className="h-8 w-8 overflow-hidden rounded-full border-2 border-gray-700">
                {user?.photoURL ? (
                  <img
                    src={user.photoURL}
                    alt="Profile"
                    className="h-full w-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-emerald-500 text-sm font-bold text-white">
                    {user?.displayName?.charAt(0) || user?.email?.charAt(0) || t("User").charAt(0)}
                  </div>
                )}
              </div>
              <div className="hidden text-left sm:block">
                <div className="font-google text-[14px] font-bold text-gray-700">
                  {user?.displayName || t("User")}
                </div>
                <div className="max-w-[140px] truncate text-[10px] text-gray-400">
                  {user?.email || ""}
                </div>
              </div>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path
                  d="M7 10L12 15L17 10"
                  stroke="#000"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>

          {showNotifications && (
            <div className="absolute right-0 top-14 z-50 w-80 overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-xl">
              <div className="flex items-center justify-between border-b border-gray-50 bg-gray-50/60 px-4 py-3">
                <h3 className="text-sm font-semibold text-gray-800">{t("Notifications")}</h3>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-xs font-medium text-emerald-600 transition-colors hover:text-emerald-700"
                  >
                    {t("Mark all read")}
                  </button>
                )}
              </div>
              <div className="max-h-[300px] overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-sm text-gray-500">{t("No new notifications")}</div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={`border-b border-gray-50 p-4 ${notif.read ? "bg-white" : "bg-emerald-50/30"}`}
                    >
                      <h4
                        className={`text-sm ${notif.read ? "font-medium text-gray-700" : "font-semibold text-gray-900"}`}
                      >
                        {notif.title}
                      </h4>
                      <p className="mt-1 text-xs text-gray-500">{notif.message}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-52 overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-lg">
              <div className="border-b border-gray-50 px-4 py-3">
                <p className="mb-1 text-xs text-gray-500">{t("Signed in as")}</p>
                <p className="truncate text-sm font-medium text-gray-800">{user?.email || t("Guest")}</p>
              </div>
              <div className="py-1">
                {user ? (
                  <>
                    <Link href="/home" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                      {t("Dashboard")}
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                    >
                      {t("Logout")}
                    </button>
                  </>
                ) : (
                  <Link
                    href="/signin"
                    className="block px-4 py-2 text-sm text-emerald-600 hover:bg-emerald-50"
                  >
                    {t("Login / Sign up")}
                  </Link>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
