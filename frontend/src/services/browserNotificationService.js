/**
 * Dedicated Browser Notification Service for PillSync.
 * Safely requests permission, presents native browser notifications,
 * handles click actions (tab focus or window navigation), and avoids duplicate triggers.
 */

const shownNotificationKeys = new Set();

export const requestBrowserNotificationPermission = async () => {
  if (!("Notification" in window)) {
    console.warn("[BrowserNotification] Native Notification API not supported by browser.");
    return false;
  }
  if (Notification.permission === "granted") {
    return true;
  }
  if (Notification.permission !== "denied") {
    const permission = await Notification.requestPermission();
    return permission === "granted";
  }
  return false;
};

export const showNativeBrowserNotification = async ({
  title,
  body,
  tag = null,
  data = {},
  icon = "/favicon.svg",
}) => {
  const isAllowed = await requestBrowserNotificationPermission();
  if (!isAllowed) return null;

  const notifKey = tag || `${title}-${body}`;
  if (shownNotificationKeys.has(notifKey)) {
    return null;
  }
  shownNotificationKeys.add(notifKey);
  setTimeout(() => shownNotificationKeys.delete(notifKey), 10000);

  try {
    const options = {
      body,
      icon,
      badge: icon,
      tag: notifKey,
      data,
      renotify: true,
    };

    const notification = new Notification(title, options);

    notification.onclick = (event) => {
      event.preventDefault();
      if (window) {
        window.focus();
      }

      if (data && data.medicine_id) {
        window.location.href = `/medicines`;
      } else {
        window.location.href = `/dashboard`;
      }
      notification.close();
    };

    return notification;
  } catch (err) {
    console.warn("[BrowserNotification] Error displaying native notification:", err);
    return null;
  }
};
