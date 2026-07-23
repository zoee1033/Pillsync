import { messaging, getToken as getMessagingToken, onMessage } from "../firebase";
import { registerDeviceToken } from "../services/deviceTokenService";
import { getToken as getAuthToken } from "../utils/token";

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY || "";

const getBrowserInfo = () => {
  if (typeof navigator === "undefined") {
    return {
      browser: "unknown",
      platform: "unknown",
    };
  }

  return {
    browser: navigator.userAgent || "unknown",
    platform: navigator.platform || "unknown",
  };
};

export const initializeFirebaseMessaging = async () => {
  if (typeof window === "undefined") {
    return null;
  }

  if (!messaging) {
    return null;
  }

  if (!getAuthToken()) {
    return null;
  }

  if (!("Notification" in window) || !("serviceWorker" in navigator)) {
    return null;
  }

  if (Notification.permission === "denied") {
    return null;
  }

  if (Notification.permission === "default") {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      return null;
    }
  }

  try {
    const registration = await navigator.serviceWorker.register("/firebase-messaging-sw.js");
    const tokenOptions = { serviceWorkerRegistration: registration };
    if (VAPID_KEY) {
      tokenOptions.vapidKey = VAPID_KEY;
    }
    const token = await getMessagingToken(messaging, tokenOptions);

    if (token) {
      const existingToken = localStorage.getItem("fcm_token");
      if (existingToken !== token) {
        const { browser, platform } = getBrowserInfo();
        await registerDeviceToken({
          fcm_token: token,
          device_name: navigator.userAgentData?.brands?.[0]?.brand || "Browser",
          browser,
          platform,
          is_active: true,
        });
        localStorage.setItem("fcm_token", token);
      }
    }
  } catch (error) {
    console.error("Unable to initialize Firebase Messaging:", error);
  }

  onMessage(messaging, (payload) => {
    const title = payload?.notification?.title || "Pill Reminder";
    const body = payload?.notification?.body || "You have a medication reminder.";

    if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
      new Notification(title, {
        body,
        icon: "/favicon.ico",
      });
    }
  });

  return true;
};
