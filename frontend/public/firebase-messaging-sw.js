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

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || payload.data?.title || '💊 Pill Reminder';
  const options = {
    body: payload.notification?.body || payload.data?.body || 'You have a medication reminder.',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    data: payload.data || {},
  };

  return self.registration.showNotification(title, options);
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const reminderId = event.notification.data?.reminder_id;
  const targetUrl = reminderId ? `/?open_reminder_id=${reminderId}` : '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
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
});
