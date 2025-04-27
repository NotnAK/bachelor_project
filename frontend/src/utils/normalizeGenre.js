// src/utils/normalizeGenre.js
export function normalizeGenre(raw) {
  if (!raw) return [];
  // если это уже массив
  if (Array.isArray(raw)) return raw;
  // если строка-представление массива: "['A','B']"
  const trimmed = raw.trim();
  if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
    try {
      // заменяем одинарные на двойные кавычки и парсим JSON
      const json = trimmed.replace(/'/g, '"');
      const arr  = JSON.parse(json);
      return Array.isArray(arr) ? arr : [];
    } catch {
      // fallthrough
    }
  }
  // обычная CSV-строка
  return raw.split(',').map(s => s.trim()).filter(Boolean);
}
