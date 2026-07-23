import React, { useEffect } from 'react';
import AppRoutes from './routes/AppRoutes';
import { initializeFirebaseMessaging } from './utils/firebaseMessaging';
import { getToken as getAuthToken } from './utils/token';

function App() {
  useEffect(() => {
    if (!getAuthToken()) {
      return;
    }

    initializeFirebaseMessaging();
  }, []);

  return (
    <div className="app">
      <AppRoutes />
    </div>
  );
}

export default App;
