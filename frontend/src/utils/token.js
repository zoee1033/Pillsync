export const saveToken = (token) => {
  localStorage.setItem("access_token", token);
  try {
    const request = indexedDB.open("pillsync_db", 1);
    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains("auth")) {
        db.createObjectStore("auth");
      }
    };
    request.onsuccess = (e) => {
      const db = e.target.result;
      if (db.objectStoreNames.contains("auth")) {
        const tx = db.transaction("auth", "readwrite");
        tx.objectStore("auth").put(token, "access_token");
      }
    };
  } catch (e) {
    console.error("IndexedDB store error:", e);
  }
};

export const getToken = () => {
  return localStorage.getItem("access_token");
};

export const removeToken = () => {
  localStorage.removeItem("access_token");
  try {
    const request = indexedDB.open("pillsync_db", 1);
    request.onsuccess = (e) => {
      const db = e.target.result;
      if (db.objectStoreNames.contains("auth")) {
        const tx = db.transaction("auth", "readwrite");
        tx.objectStore("auth").delete("access_token");
      }
    };
  } catch (e) {
    console.error("IndexedDB delete error:", e);
  }
};