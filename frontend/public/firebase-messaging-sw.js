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
  const title = payload.notification?.title || 'Pill Reminder';
  const options = {
    body: payload.notification?.body || 'You have a medication reminder.',
    icon: '/favicon.ico',
  };

  return self.registration.showNotification(title, options);
});
