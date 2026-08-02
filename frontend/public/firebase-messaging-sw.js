importScripts('https://www.gstatic.com/firebasejs/10.11.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.11.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyDpfMcDZVZGQ3T1695VJ4YqfFoYigHRv6c",
  authDomain: "pillsync-medication-system.firebaseapp.com",
  projectId: "pillsync-medication-system",
  storageBucket: "pillsync-medication-system.firebasestorage.app",
  messagingSenderId: "1008449714646",
  appId: "1:1008449714646:web:60218763e421f95ec5cc77",
  measurementId: "G-VF1M18W5GQ"
});

const SW_VERSION = "2026-07-30-V2-PROD";
const SW_INSTANCE_ID = 'SW_' + Math.random().toString(36).substring(2, 9);
console.log(`[TRACE ${new Date().toISOString()}] [SW_INIT] Active SW Version: "${SW_VERSION}", Instance ID: ${SW_INSTANCE_ID}`);

self.addEventListener('install', (event) => {
  console.log(`[TRACE ${new Date().toISOString()}] [SW_INSTALL] Installing SW Version: "${SW_VERSION}". Calling self.skipWaiting().`);
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log(`[TRACE ${new Date().toISOString()}] [SW_ACTIVATE] Activating SW Version: "${SW_VERSION}". Calling self.clients.claim().`);
  event.waitUntil(self.clients.claim());
});

const messaging = firebase.messaging();

let syncChannel = null;
if (typeof BroadcastChannel !== 'undefined') {
  syncChannel = new BroadcastChannel('pillsync_realtime_sync');
}

const getStoredToken = () => {
  return new Promise((resolve) => {
    try {
      const request = indexedDB.open('pillsync_db', 1);
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains('auth')) {
          db.createObjectStore('auth');
        }
      };
      request.onsuccess = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains('auth')) {
          resolve(null);
          return;
        }
        const tx = db.transaction('auth', 'readonly');
        const store = tx.objectStore('auth');
        const getReq = store.get('access_token');
        getReq.onsuccess = () => resolve(getReq.result || null);
        getReq.onerror = () => resolve(null);
      };
      request.onerror = () => resolve(null);
    } catch (err) {
      resolve(null);
    }
  });
};

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || payload.data?.title || '💊 Pill Reminder';
  const reminderId = payload.data?.reminder_id || payload.notification?.data?.reminder_id;
  const notificationId = payload.data?.notification_id || payload.notification?.data?.notification_id;
  const notifType = payload.data?.notification_type || payload.notification?.data?.notification_type;

  console.log(`[TRACE ${new Date().toISOString()}] [STAGE 4: SW_ON_BACKGROUND_MESSAGE] SW ID: ${SW_INSTANCE_ID}, Notification ID: ${notificationId}, Reminder ID: ${reminderId}`, payload);

  const tag = notificationId ? `notification_${notificationId}` : (reminderId ? `reminder_${reminderId}` : `pillsync_${Date.now()}`);

  const isRefillAlert = notifType?.toLowerCase() === 'refill' ||
    Boolean(title?.toLowerCase().includes('refill')) ||
    Boolean(title?.toLowerCase().includes('out of stock')) ||
    Boolean(payload.notification?.body?.toLowerCase().includes('out of stock')) ||
    Boolean(payload.data?.body?.toLowerCase().includes('out of stock')) ||
    Boolean(payload.notification?.body?.toLowerCase().includes('no tablets')) ||
    Boolean(payload.data?.body?.toLowerCase().includes('no tablets'));

  const options = {
    body: payload.notification?.body || payload.data?.body || 'You have a medication reminder.',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    tag: tag,
    renotify: true,
    data: {
      reminder_id: reminderId,
      notification_id: notificationId,
      ...payload.data
    },
    actions: isRefillAlert ? [
      { action: 'view_medicine', title: '🛒 Restock Now' },
      { action: 'dismiss', title: '✕ Dismiss' }
    ] : [
      { action: 'taken', title: '✅ Taken' },
      { action: 'skipped', title: '⏭ Skipped' }
    ]
  };

  console.log(`[TRACE ${new Date().toISOString()}] [STAGE 5: SHOW_NOTIFICATION_EXECUTION] SW ID: ${SW_INSTANCE_ID}, Notification ID: ${notificationId}, Tag: ${tag}, Title: "${title}"`);
  return self.registration.showNotification(title, options);
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const action = event.action;
  const data = event.notification.data || {};
  const reminderId = data.reminder_id;
  const notificationId = data.notification_id;

  console.log(`[TRACE ${new Date().toISOString()}] [STAGE 6: NOTIFICATIONCLICK_EVENT] SW ID: ${SW_INSTANCE_ID}, Action: "${action || 'BODY_CLICK'}", Notification ID: ${notificationId}, Reminder ID: ${reminderId}`);

  if (action === 'dismiss') {
    return;
  }

  if (action === 'view_medicine' || action === 'restock') {
    const targetUrl = '/medicines';
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then(async (clientList) => {
        for (const client of clientList) {
          if (client.url && 'focus' in client) {
            client.navigate(targetUrl);
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
    );
    return;
  }

  if (action) {
    // ACTION BUTTON CLICKED: Perform 100% background processing ONLY!
    // NO UI, NO NAVIGATION, NO client.focus(), NO clients.openWindow()!
    event.waitUntil(
      (async () => {
        console.log(`[TRACE ${new Date().toISOString()}] Action button clicked: "${action}". Executing background fetch directly from SW ID: ${SW_INSTANCE_ID}`);
        const token = await getStoredToken();
        console.log(`[TRACE ${new Date().toISOString()}] [SW_AUTH_AUDIT] getStoredToken() returned: ${token ? 'JWT Token Present' : 'NULL'}`);

        const headers = { 'Content-Type': 'application/json' };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        console.log(`[TRACE ${new Date().toISOString()}] [SW_AUTH_AUDIT] Authorization header: ${headers['Authorization'] ? 'Bearer <PRESENT>' : 'MISSING'}`);

        let endpoint = '';
        if (notificationId) {
          endpoint = `http://127.0.0.1:8000/notifications/${notificationId}/action?action_type=${action}`;
        } else if (reminderId) {
          endpoint = `http://127.0.0.1:8000/notifications/reminder/${reminderId}/action?action_type=${action}`;
        }

        if (endpoint) {
          console.log(`[TRACE ${new Date().toISOString()}] [SW_FETCH_AUDIT] Request URL: ${endpoint}`);
          try {
            const fetchRes = await fetch(endpoint, { method: 'PUT', headers });
            console.log(`[TRACE ${new Date().toISOString()}] [SW_FETCH_AUDIT] fetchRes.status: ${fetchRes.status}, fetchRes.ok: ${fetchRes.ok}`);
            if (!fetchRes.ok) {
              const errText = await fetchRes.text();
              console.error(`[TRACE ${new Date().toISOString()}] [SW_FETCH_AUDIT ERROR] Response Status ${fetchRes.status} >= 400: ${errText}`);
            }
          } catch (err) {
            console.error('Service Worker background action fetch failed:', err);
          }
        }

        const payload = {
          type: 'NOTIFICATION_ACTION_COMPLETED',
          notificationId,
          reminderId,
          action
        };

        // Broadcast completion event to all open client tabs via client.postMessage
        const clientList = await clients.matchAll({ type: 'window', includeUncontrolled: true });
        for (const client of clientList) {
          if (client.url) {
            console.log(`[TRACE ${new Date().toISOString()}] Posting NOTIFICATION_ACTION_COMPLETED to client window: ${client.url}`);
            client.postMessage(payload);
          }
        }

        // Broadcast completion event via BroadcastChannel for any open tabs
        if (syncChannel) {
          console.log(`[TRACE ${new Date().toISOString()}] [STAGE 10: BROADCASTCHANNEL_EVENT] SW ID: ${SW_INSTANCE_ID} posting NOTIFICATION_ACTION_COMPLETED to syncChannel`);
          syncChannel.postMessage(payload);
        }
      })()
    );
  } else {
    // NOTIFICATION BODY CLICKED: Open or focus PillSync window and navigate to details
    console.log(`[TRACE ${new Date().toISOString()}] BODY CLICKED. Target navigation url: ${reminderId ? `/?open_reminder_id=${reminderId}` : '/notifications'}`);
    const targetUrl = reminderId ? `/?open_reminder_id=${reminderId}` : '/notifications';
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then(async (clientList) => {
        for (const client of clientList) {
          if (client.url && 'focus' in client) {
            client.navigate(targetUrl);
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
    );
  }
});
