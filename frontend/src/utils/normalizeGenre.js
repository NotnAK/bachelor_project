// src/utils/normalizeGenre.js
export function normalizeGenre(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  const trimmed = raw.trim();
  if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
    try {
      const json = trimmed.replace(/'/g, '"');
      const arr  = JSON.parse(json);
      return Array.isArray(arr) ? arr : [];
    } catch {
    }
  }
  return raw.split(',').map(s => s.trim()).filter(Boolean);
}
