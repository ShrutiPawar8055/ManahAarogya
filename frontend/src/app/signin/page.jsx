"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth, provider, signInWithPopup, db } from "../../../firebaseConfig";
import { doc, getDoc, setDoc, serverTimestamp } from "firebase/firestore";
import { firstNameFromName, saveUserSession } from "@/lib/userSession";
import { api } from "@/lib/api";

// Google Icon
const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
);

export default function SignIn() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    setError("");
    
    try {
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
      const idToken = await user.getIdToken();
      const userSession = saveUserSession({
        id: user.uid,
        name: user.displayName || "",
        first_name: firstNameFromName(user.displayName || "", user.email || ""),
        email: user.email || "",
      });
      const loginRes = await api.post("/auth/login", {
        token: idToken,
        uid: user.uid,
        email: user.email || "",
        name: user.displayName || "",
      });

      const backendRole = loginRes?.data?.user?.role || loginRes?.user?.role || "user";
      saveUserSession({
        id: user.uid,
        name: user.displayName || "",
        first_name: firstNameFromName(user.displayName || "", user.email || ""),
        email: user.email || "",
        role: backendRole,
      });

      let nextPath = loginRes?.data?.has_completed_assessment || loginRes?.has_completed_assessment ? "/home" : "/test";
      
      if (backendRole === "therapist") {
        nextPath = "/therapist";
      } else if (nextPath === "/home") {
        try {
          const onboardingRes = await api.get("/habits/onboarding/status");
          const onboarding = onboardingRes?.data || {};
          if (!onboarding.completed || (onboarding.habit_count || 0) === 0) {
            nextPath = "/home/habit-tracker?setup=1";
          }
        } catch (onboardingErr) {
          console.error("Could not verify onboarding status:", onboardingErr);
        }
      }

      void (async () => {
        try {
          const userRef = doc(db, "users", user.uid);
          const userDocSnapshot = await getDoc(userRef);
          if (!userDocSnapshot.exists()) {
            await setDoc(userRef, {
              uid: user.uid,
              email: user.email,
              displayName: userSession?.name || user.displayName || "",
              firstName: userSession?.first_name || firstNameFromName(user.displayName || "", user.email || ""),
              photoURL: user.photoURL,
              userDescription: "",
              testGiven: false,
              createdAt: serverTimestamp(),
            });
          }
        } catch (firestoreErr) {
          console.error("Firestore user sync failed, continuing with sign-in:", firestoreErr);
        }
      })();

      router.push(nextPath);
    } catch (err) {
      console.error("Google sign-in failed:", err);
      setError("Google sign-in failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex font-google justify-center items-center bg-gray-100">
      <div className="w-full lg:w-1/2  flex items-center justify-center p-8 bg-white rounded-3xl border border-gray-300">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className=" flex justify-center mb-8">
            <img src="/logo_1.jpeg" alt="Manah Arogya" className="w-auto h-16 rounded-xl" />
          </div>

          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-2">Sign In</h2>
            <p className="text-gray-500">Welcome! Please sign in to continue.</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Google Sign In */}
          <button
            onClick={handleGoogleSignIn}
            disabled={isLoading}
            className="w-full cursor-pointer flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <GoogleIcon />
            <span className="font-medium text-gray-700">Continue with Google</span>
          </button>
        </div>
      </div>
    </div>
  );
}
