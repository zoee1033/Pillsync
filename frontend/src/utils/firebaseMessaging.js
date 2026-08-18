import { initializeApp } from "firebase/app";
import { getMessaging, getToken as getMessagingToken, onMessage } from "firebase/messaging";
import api from "../services/api";
import { registerDeviceToken } from "../services/deviceTokenService";
import { getToken as getAuthToken, saveToken } from "./token";

const firebaseConfig = {
  apiKey: "AIzaSyDpfMcDZVZGQ3T1695VJ4YqfFoYigHRv6c",
  authDomain: "pillsync-medication-system.firebaseapp.com",
  projectId: "pillsync-medication-system",
  storageBucket: "pillsync-medication-system.firebasestorage.app",
  messagingSenderId: "1008449714646",
  appId: "1:1008449714646:web:60218763e421f95ec5cc77",
  measurementId: "G-VF1M18W5GQ",
};

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY || null;

let app = null;
let messaging = null;
let isMessagingInitialized = false;

try {
  app = initializeApp(firebaseConfig);
  if (typeof window !== "undefined" && "Notification" in window) {
    messaging = getMessaging(app);
  }
} catch (e) {
  console.warn("Firebase App initialization failed:", e);
}

const getBrowserInfo = () => {
  const ua = navigator.userAgent;
  let browser = "Unknown";
  let platform = navigator.platform || "Unknown";

  if (ua.includes("Firefox/")) browser = "Firefox";
  else if (ua.includes("Edg/")) browser = "Edge";
  else if (ua.includes("Chrome/")) browser = "Chrome";
  else if (ua.includes("Safari/")) browser = "Safari";

  return { browser, platform };
};

export const executeNotificationAction = async (action, reminderId, notificationId) => {
  console.log(`[TRACE ${new Date().toISOString()}] [STAGE 7: EXECUTE_NOTIFICATION_ACTION] Action="${action}", Notification ID=${notificationId}, Reminder ID=${reminderId}`);
  if (!action) return;

  const authToken = getAuthToken();
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {};

  let endpoint = "";
  if (notificationId) {
    endpoint = `/notifications/${notificationId}/action?action_type=${action}`;
  } else if (reminderId) {
    endpoint = `/notifications/reminder/${reminderId}/action?action_type=${action}`;
  }

  if (endpoint) {
    try {
      const res = await api.put(endpoint, null, { headers });
      console.log(`[TRACE ${new Date().toISOString()}] [STAGE 9: DATABASE_UPDATE] API put succeeded:`, res.data);
    } catch (err) {
      console.error("Failed to execute notification action via API:", err);
    } finally {
      const payload = {
        type: "PILLSYNC_NOTIFICATION_ACTION_COMPLETED",
        notificationId,
        reminderId,
        action,
      };
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("pillsync_refresh_ui", { detail: payload }));
      }
    }
  }
};

export const showBrowserToast = async (title, body, tag, data = {}, isRefillAlert = false) => {
  if (typeof window === "undefined" || !("Notification" in window)) {
    return;
  }

  if (Notification.permission === "default") {
    try {
      await Notification.requestPermission();
    } catch (e) {}
  }

  console.log(`[TRACE ${new Date().toISOString()}] [STAGE 9: BROWSER_PERMISSION_CHECK] Notification.permission="${Notification.permission}"`);

  if (Notification.permission !== "granted") {
    console.warn(`[TRACE ${new Date().toISOString()}] [STAGE 9: BROWSER_PERMISSION_CHECK] Permission not granted: "${Notification.permission}"`);
    return;
  }

  const actions = isRefillAlert ? [
    { action: "view_medicine", title: "🛒 Restock Now" },
    { action: "dismiss", title: "✕ Dismiss" }
  ] : [
    { action: "taken", title: "✅ Taken" },
    { action: "skipped", title: "⏭ Skipped" }
  ];

  const swOptions = {
    body,
    icon: "/favicon.ico",
    badge: "/favicon.ico",
    tag: tag || `pillsync_${Date.now()}`,
    renotify: true,
    data,
    actions
  };

  const domOptions = {
    body,
    icon: "/favicon.ico",
    tag: tag || `pillsync_${Date.now()}`
  };

  let shown = false;

  if ("serviceWorker" in navigator) {
    try {
      console.log(`[TRACE ${new Date().toISOString()}] [STAGE 6: SERVICE_WORKER_READY] Checking navigator.serviceWorker.ready...`);
      const reg = await Promise.race([
        navigator.serviceWorker.ready,
        new Promise((resolve) => setTimeout(() => resolve(null), 1000))
      ]);

      if (reg && reg.showNotification) {
        console.log(`[TRACE ${new Date().toISOString()}] [STAGE 7: SHOW_NOTIFICATION_EXECUTION] Executing reg.showNotification("${title}")...`);
        await reg.showNotification(title, swOptions);
        console.log(`[TRACE ${new Date().toISOString()}] [STAGE 7: SHOW_NOTIFICATION_EXECUTION] reg.showNotification() SUCCEEDED.`);
        shown = true;
      } else {
        console.warn(`[TRACE ${new Date().toISOString()}] [STAGE 6: SERVICE_WORKER_READY] ServiceWorker registration not ready or missing showNotification.`);
      }
    } catch (swErr) {
      console.warn(`[TRACE ${new Date().toISOString()}] [STAGE 7 ERROR] reg.showNotification failed:`, swErr);
    }
  }

  if (!shown) {
    try {
      console.log(`[TRACE ${new Date().toISOString()}] [STAGE 7: DOM_NOTIFICATION_FALLBACK] Executing new Notification("${title}")...`);
      const n = new Notification(title, domOptions);
      console.log(`[TRACE ${new Date().toISOString()}] [STAGE 7: DOM_NOTIFICATION_FALLBACK] new Notification() SUCCEEDED.`);
      n.onclick = () => {
        window.focus();
        if (isRefillAlert) {
          window.location.href = "/medicines";
        } else {
          window.location.href = "/notifications";
        }
      };
    } catch (domErr) {
      console.error(`[TRACE ${new Date().toISOString()}] [STAGE 7 ERROR] DOM Notification failed:`, domErr);
    }
  }
};

export const initializeFirebaseMessaging = async () => {
  if (typeof window === "undefined" || isMessagingInitialized) {
    return null;
  }
  isMessagingInitialized = true;

  const authToken = getAuthToken();
  if (!authToken) {
    return null;
  }

  saveToken(authToken);

  let registration = null;
  if ("serviceWorker" in navigator) {
    try {
      registration = await navigator.serviceWorker.register("/firebase-messaging-sw.js");
      console.log(`[TRACE ${new Date().toISOString()}] [SW_CONTROLLER_AUDIT] navigator.serviceWorker.controller:`, Boolean(navigator.serviceWorker.controller));
      console.log(`[TRACE ${new Date().toISOString()}] [SW_CONTROLLER_AUDIT] registration.active:`, Boolean(registration?.active));
      console.log(`[TRACE ${new Date().toISOString()}] [SW_CONTROLLER_AUDIT] registration.waiting:`, Boolean(registration?.waiting));
      console.log(`[TRACE ${new Date().toISOString()}] [SW_CONTROLLER_AUDIT] registration.installing:`, Boolean(registration?.installing));
      try {
        await registration.update();
      } catch (updateErr) {
        console.warn("SW update check:", updateErr);
      }
    } catch (swErr) {
      console.warn("SW registration error:", swErr);
    }
  }

  if ("Notification" in window && Notification.permission === "default") {
    try {
      await Notification.requestPermission();
    } catch (permErr) {
      console.warn("Notification permission request:", permErr);
    }
  }

  if (messaging && registration && Notification.permission === "granted") {
    try {
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
      console.error("Unable to initialize Firebase Messaging token:", error);
    }
  }

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.addEventListener("message", (event) => {
      const type = event.data?.type;
      if (type === "PILLSYNC_NOTIFICATION_ACTION") {
        executeNotificationAction(event.data.action, event.data.reminderId, event.data.notificationId);
      } else if (type === "NOTIFICATION_ACTION_COMPLETED" || type === "PILLSYNC_NOTIFICATION_ACTION_COMPLETED") {
        window.dispatchEvent(new CustomEvent("pillsync_refresh_ui", { detail: event.data }));
      }
    });
  }

  if (messaging) {
    onMessage(messaging, async (payload) => {
      const title = payload.notification?.title || payload.data?.title || "💊 Pill Reminder";
      const body = payload.notification?.body || payload.data?.body || "It's time to take your medication.";
      const reminderId = payload.data?.reminder_id || payload.notification?.data?.reminder_id;
      const notificationId = payload.data?.notification_id || payload.notification?.data?.notification_id;
      const notifType = payload.data?.notification_type || payload.notification?.data?.notification_type;

      const isRefillAlert = notifType?.toLowerCase() === "refill" ||
        Boolean(title?.toLowerCase().includes("refill")) ||
        Boolean(title?.toLowerCase().includes("out of stock")) ||
        Boolean(body?.toLowerCase().includes("out of stock")) ||
        Boolean(body?.toLowerCase().includes("remaining")) ||
        Boolean(body?.toLowerCase().includes("no tablets"));

      await showBrowserToast(title, body, `notif_${notificationId || reminderId || Date.now()}`, { reminder_id: reminderId, notification_id: notificationId }, isRefillAlert);

      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("pillsync_refresh_ui", { detail: payload }));
      }
    });
  }

  return messaging;
};

let shownNotificationIds = new Set();
let isSyncStarted = false;
let isInitialFetchComplete = false;
let maxSeenNotificationId = 0;
let lastPollTimestamp = 0;
let pollWorker = null;
let pollIntervalId = null;

export const stopNotificationSync = () => {
  if (pollWorker) {
    try {
      pollWorker.postMessage("stop");
      pollWorker.terminate();
    } catch (e) {}
    pollWorker = null;
  }
  if (pollIntervalId) {
    clearInterval(pollIntervalId);
    pollIntervalId = null;
  }
  isSyncStarted = false;
  isInitialFetchComplete = false;
  console.log(`[TRACE ${new Date().toISOString()}] stopNotificationSync() executed. Polling timer cleaned up.`);
};

export const startNotificationSync = () => {
  if (typeof window === "undefined") return;
  if (isSyncStarted) return;
  isSyncStarted = true;

  console.log(`[TRACE ${new Date().toISOString()}] [STAGE 4: SYNC_INITIALIZATION] startNotificationSync() initialized.`);

  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission().catch(() => {});
  }

  const checkUnread = async (reason = "INTERVAL_TICK") => {
    const now = Date.now();
    const elapsed = now - lastPollTimestamp;

    // Prevent race conditions: throttle rapid duplicate checks triggered within 800ms by multi-lifecycle events
    if (isInitialFetchComplete && elapsed < 800 && reason !== "INITIAL_LAUNCH") {
      console.log(`[TRACE ${new Date().toISOString()}] [POLL_THROTTLE] Throttling rapid check (${reason}). Elapsed: ${elapsed}ms < 800ms`);
      return;
    }
    lastPollTimestamp = now;

    const timeStr = new Date(now).toLocaleTimeString("en-US", { hour12: false }) + "." + String(now % 1000).padStart(3, "0");
    console.log(`[POLL_TIMING] Timestamp: ${timeStr} | Reason: ${reason} | Elapsed: ${elapsed}ms`);

    try {
      const authToken = getAuthToken();
      if (!authToken) return;

      const res = await api.get("/notifications/unread");
      const list = res.data;

      if (Array.isArray(list)) {
        console.log(`[TRACE ${new Date().toISOString()}] [STAGE 5: UNREAD_POLLING_CHECK] checkUnread(${reason}) returned ${list.length} unread notification(s). IDs: [${list.map(i => i.id).join(",")}]`);

        let hasNewForUI = false;

        if (!isInitialFetchComplete) {
          // INITIAL LAUNCH: Seed shownNotificationIds & cursor with historical unread notifications so popups ARE NEVER REPLAYED!
          for (const item of list) {
            shownNotificationIds.add(item.id);
            if (item.id > maxSeenNotificationId) {
              maxSeenNotificationId = item.id;
            }
          }
          isInitialFetchComplete = true;
          console.log(`[TRACE ${new Date().toISOString()}] [INITIAL_LAUNCH_SEED] Initialized notification cursor. maxSeenNotificationId=${maxSeenNotificationId}, Seeded ${shownNotificationIds.size} historical IDs. Popups suppressed.`);
          hasNewForUI = true; // Dispatch refresh event to update bell icon and unread badge count!
        } else {
          // SUBSEQUENT TICKS: Trigger browser toast ONLY for NEW notifications arriving after app startup
          for (const item of list) {
            if (!shownNotificationIds.has(item.id) && item.id > maxSeenNotificationId) {
              console.log(`[TRACE ${new Date().toISOString()}] [STAGE 10: NEW_NOTIFICATION_TOAST] New notification detected ID=${item.id}. Triggering toast...`);
              shownNotificationIds.add(item.id);
              maxSeenNotificationId = Math.max(maxSeenNotificationId, item.id);
              hasNewForUI = true;

              const title = item.title || "💊 Pill Reminder";
              const body = item.message || "Medication reminder due";
              const notifTag = `notif_${item.id}`;
              const notifData = { notification_id: item.id, reminder_id: item.reminder_id };

              const isRefillAlert = item.notification_type?.toLowerCase() === "refill" ||
                Boolean(item.title?.toLowerCase().includes("refill")) ||
                Boolean(item.title?.toLowerCase().includes("out of stock")) ||
                Boolean(item.message?.toLowerCase().includes("out of stock")) ||
                Boolean(item.message?.toLowerCase().includes("remaining")) ||
                Boolean(item.message?.toLowerCase().includes("no tablets"));

              await showBrowserToast(title, body, notifTag, notifData, isRefillAlert);
            } else {
              shownNotificationIds.add(item.id);
            }
          }
        }

        if (hasNewForUI) {
          window.dispatchEvent(new CustomEvent("pillsync_refresh_ui", { detail: { unread_count: list.length } }));
        }
      }
    } catch (err) {
      console.error(`[TRACE ${new Date().toISOString()}] [STAGE 5 ERROR] checkUnread failed:`, err);
    }
  };

  // Immediate first check
  checkUnread("INITIAL_LAUNCH");

  // 1. Web Worker Background Thread Timer (Single Timer Instance)
  try {
    const workerCode = `
      let timer = null;
      self.onmessage = function(e) {
        if (e.data === 'start') {
          if (timer) clearInterval(timer);
          timer = setInterval(function() {
            self.postMessage('tick');
          }, 4000);
        } else if (e.data === 'stop') {
          if (timer) clearInterval(timer);
          timer = null;
        }
      };
    `;
    const blob = new Blob([workerCode], { type: "application/javascript" });
    pollWorker = new Worker(URL.createObjectURL(blob));
    pollWorker.onmessage = () => {
      checkUnread("WEB_WORKER_TICK");
    };
    pollWorker.postMessage("start");
  } catch (wErr) {
    console.warn("Web Worker timer creation failed, falling back to setInterval:", wErr);
    pollIntervalId = setInterval(() => checkUnread("SET_INTERVAL_FALLBACK"), 4000);
  }

  // 2. Lifecycle Event Listeners for Instant Triggering
  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      checkUnread("VISIBILITY_CHANGE");
    }
  });

  window.addEventListener("focus", () => {
    checkUnread("WINDOW_FOCUS");
  });

  window.addEventListener("pageshow", () => {
    checkUnread("PAGE_SHOW");
  });

  window.addEventListener("online", () => {
    checkUnread("NETWORK_ONLINE");
  });

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.ready.then(() => {
      checkUnread("SW_READY");
    }).catch(() => {});
  }
};
