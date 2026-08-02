import React, { useEffect } from 'react';
import AppRoutes from './routes/AppRoutes';
import { initializeFirebaseMessaging, startNotificationSync } from './utils/firebaseMessaging';
import { getToken as getAuthToken } from './utils/token';

function App() {
  useEffect(() => {
    const initNotifications = () => {
      if (getAuthToken()) {
        initializeFirebaseMessaging();
        startNotificationSync();
      }
    };

    initNotifications();

    window.addEventListener("pillsync_refresh_ui", initNotifications);
    window.addEventListener("storage", initNotifications);
    return () => {
      window.removeEventListener("pillsync_refresh_ui", initNotifications);
      window.removeEventListener("storage", initNotifications);
    };
  }, []);

  return (
    <div className="app">
      <AppRoutes />
    </div>
  );
}

export default App;
