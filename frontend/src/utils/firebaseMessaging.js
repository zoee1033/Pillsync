import { messaging, getToken as getMessagingToken, onMessage } from "../firebase";
import { registerDeviceToken } from "../services/deviceTokenService";
import { getToken as getAuthToken, saveToken } from "../utils/token";
import { performNotificationAction, performReminderAction } from "../services/notificationService";

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY || "";

let isMessagingInitialized = false;
let syncChannel = null;

if (typeof window !== "undefined" && "BroadcastChannel" in window) {
  syncChannel = new BroadcastChannel("pillsync_realtime_sync");
  syncChannel.onmessage = (event) => {
    console.log(`[TRACE ${new Date().toISOString()}] [STAGE 10: BROADCASTCHANNEL_EVENT_RECEIVED] BroadcastChannel message received in client tab:`, event.data);
    if (event.data?.type === "NOTIFICATION_ACTION_COMPLETED" || event.data?.type === "PILLSYNC_NOTIFICATION_ACTION_COMPLETED") {
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui", { detail: event.data }));
    }
  };
}

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

export const executeNotificationAction = async (action, reminderId, notificationId) => {
  if (!action) return;
  console.log(`[TRACE ${new Date().toISOString()}] [STAGE 7: EXECUTE_NOTIFICATION_ACTION] Executing action="${action}", reminderId=${reminderId}, notificationId=${notificationId}`);

  try {
    if (notificationId) {
      await performNotificationAction(notificationId, action);
    } else if (reminderId) {
      await performReminderAction(reminderId, action);
    }
  } catch (err) {
    console.error("Error executing notification action:", err);
  } finally {
    if (typeof window !== "undefined") {
      const payload = {
        type: "NOTIFICATION_ACTION_COMPLETED",
        notificationId,
        reminderId,
        action,
      };

      // 1. BroadcastChannel API sync across all tabs
      if (syncChannel) {
        console.log(`[TRACE ${new Date().toISOString()}] Posting NOTIFICATION_ACTION_COMPLETED to syncChannel from executeNotificationAction`);
        syncChannel.postMessage(payload);
      }

      // 2. Local CustomEvent fallback
      console.log(`[TRACE ${new Date().toISOString()}] Dispatching local pillsync_refresh_ui event from executeNotificationAction`);
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui", { detail: payload }));
    }
  }
};

export const initializeFirebaseMessaging = async () => {
  if (typeof window === "undefined" || isMessagingInitialized) {
    return null;
  }
  isMessagingInitialized = true;
  console.log(`[TRACE ${new Date().toISOString()}] initializeFirebaseMessaging() called ONCE`);

  if (!messaging) {
    return null;
  }

  const authToken = getAuthToken();
  if (!authToken) {
    return null;
  }
  // Sync token to IndexedDB for Service Worker background processing
  saveToken(authToken);

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
    try {
      await registration.update();
    } catch (updateErr) {
      console.warn("SW update check:", updateErr);
    }
    const tokenOptions = { serviceWorkerRegistration: registration };
    if (VAPID_KEY) {
      tokenOptions.vapidKey = VAPID_KEY;
    }
    const token = await getMessagingToken(messaging, tokenOptions);

    if (token) {
      const userStr = localStorage.getItem("user");
      const currentUserId = userStr ? JSON.parse(userStr)?.id : null;
      const existingToken = localStorage.getItem("fcm_token");
      const registeredUser = localStorage.getItem("fcm_token_user_id");

      if (existingToken !== token || (currentUserId && registeredUser !== String(currentUserId))) {
        const { browser, platform } = getBrowserInfo();
        await registerDeviceToken({
          fcm_token: token,
          device_name: navigator.userAgentData?.brands?.[0]?.brand || "Browser",
          browser,
          platform,
          is_active: true,
        });
        localStorage.setItem("fcm_token", token);
        if (currentUserId) {
          localStorage.setItem("fcm_token_user_id", String(currentUserId));
        }
      }
    }
  } catch (error) {
    console.error("Unable to initialize Firebase Messaging:", error);
  }

  // Listen for service worker postMessage events fallback
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.addEventListener("message", (event) => {
      console.log(`[TRACE ${new Date().toISOString()}] ServiceWorker message event in client tab:`, event.data);
      const type = event.data?.type;
      if (type === "PILLSYNC_NOTIFICATION_ACTION") {
        executeNotificationAction(event.data.action, event.data.reminderId, event.data.notificationId);
      } else if (type === "NOTIFICATION_ACTION_COMPLETED" || type === "PILLSYNC_NOTIFICATION_ACTION_COMPLETED") {
        window.dispatchEvent(new CustomEvent("pillsync_refresh_ui", { detail: event.data }));
      }
    });
  }

  // Check URL query parameters for action dispatch on window open
  if (typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search);
    const action = params.get("notification_action");
    const reminderId = params.get("reminder_id");
    const notificationId = params.get("notification_id");
    if (action && (reminderId || notificationId)) {
      executeNotificationAction(action, reminderId, notificationId);
      params.delete("notification_action");
      params.delete("reminder_id");
      params.delete("notification_id");
      const newUrl = window.location.pathname + (params.toString() ? `?${params.toString()}` : "");
      window.history.replaceState({}, document.title, newUrl);
    }
  }

  onMessage(messaging, (payload) => {
    console.log(`[TRACE ${new Date().toISOString()}] FCM onMessage received in client tab:`, payload);
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui", { detail: payload }));
    }
  });

  return true;
};
