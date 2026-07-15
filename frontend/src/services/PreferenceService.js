/**
 * PreferenceService
 * Static service to get, set, and reset user preferences (e.g. layout order, hidden cards)
 * persisted in localStorage. Safely handles SSR context.
 */
const PreferenceService = {
  get(key, defaultValue) {
    if (typeof window === "undefined") return defaultValue;
    try {
      const item = localStorage.getItem(`gc_pref_${key}`);
      return item ? JSON.parse(item) : defaultValue;
    } catch (err) {
      console.error(`Error reading preference "${key}":`, err);
      return defaultValue;
    }
  },

  set(key, value) {
    if (typeof window === "undefined") return;
    try {
      localStorage.setItem(`gc_pref_${key}`, JSON.stringify(value));
    } catch (err) {
      console.error(`Error writing preference "${key}":`, err);
    }
  },

  reset(key) {
    if (typeof window === "undefined") return;
    try {
      localStorage.removeItem(`gc_pref_${key}`);
    } catch (err) {
      console.error(`Error removing preference "${key}":`, err);
    }
  }
};

export default PreferenceService;
