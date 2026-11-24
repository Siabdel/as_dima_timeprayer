// ===========================================================================
// Appels API « Coran » — contrat backend /api/v1/quran/.
// ---------------------------------------------------------------------------
// Endpoints (tous publics sauf la progression) :
//   - GET  /quran/surahs/                    → liste des 114 sourates
//   - GET  /quran/surahs/{number}/           → versets + traductions
//   - GET  /quran/reciters/                  → récitateurs (chapter / verse)
//   - GET  /quran/audio/chapter/{surah}/     → URL audio chapitre
//   - GET  /quran/audio/verse/               → URL audio verset + timings
//   - GET  /quran/progress/                  → dernière position (Bearer)
//   - PUT  /quran/progress/                  → enregistre la position (Bearer)
// ===========================================================================
import client from './client';

/**
 * GET /quran/surahs/ — liste des 114 sourates.
 * @returns {Promise<Array>} [{ number, name_arabic, name_transliterated,
 *   verses_count, revelation_place }, ...]
 */
export function getSurahs() {
  return client.get('/quran/surahs/');
}

/**
 * GET /quran/surahs/{number}/ — versets d'une sourate avec traductions.
 * @param {number|string} surah numéro de sourate (1-114)
 * @param {Array<string>} [translations] codes de traduction, ex. ['fr','en']
 * @param {Object} [options] options de requête
 * @param {boolean} [options.words] ajoute `words: true` (lecture mot à mot)
 * @returns {Promise<Array>} [{ ayah_number, text_uthmani, translations: [...],
 *   words?: [{ position, text_uthmani, translation_fr, translation_en,
 *   transliteration, audio_url, is_end }] }]
 */
export function getVerses(surah, translations = [], options = {}) {
  const params = { translations: (translations ?? []).join(',') };
  // Lecture mot à mot : le backend ajoute alors le tableau `words` à chaque
  // verset (mots isolés + traduction + audio dédié).
  if (options && options.words) params.words = 'true';
  return client.get(`/quran/surahs/${surah}/`, { params });
}

/**
 * GET /quran/words/{surah}/{ayah}/ — mots isolés d'un seul verset.
 * @param {number|string} surah numéro de sourate (1-114)
 * @param {number|string} ayah numéro de verset
 * @returns {Promise<Object>} { verse_key, words: [{ position, text_uthmani,
 *   translation_fr, translation_en, transliteration, audio_url, is_end }] }
 */
export function getVerseWords(surah, ayah) {
  return client.get(`/quran/words/${surah}/${ayah}/`);
}

/**
 * GET /quran/reciters/ — récitateurs disponibles.
 * @returns {Promise<Object>} { chapter: [{ id, name, style }], verse: [...] }
 */
export function getReciters() {
  return client.get('/quran/reciters/');
}

/**
 * GET /quran/audio/chapter/{surah}/ — URL audio complète d'une sourate.
 * @param {number|string} surah numéro de sourate
 * @param {number|string} [reciterId] identifiant du récitateur (chapitre)
 * @returns {Promise<Object>} { audio_url }
 */
export function getChapterAudio(surah, reciterId) {
  return client.get(`/quran/audio/chapter/${surah}/`, {
    params: reciterId ? { reciter_id: reciterId } : {},
  });
}

/**
 * GET /quran/audio/verse/ — URL audio d'un verset (+ timings optionnels).
 * @param {number|string} surah numéro de sourate
 * @param {number|string} ayah numéro de verset
 * @param {number|string} [reciterId] identifiant du récitateur (verset)
 * @returns {Promise<Object>} { audio_url, timings?: { segments } }
 */
export function getVerseAudio(surah, ayah, reciterId) {
  return client.get('/quran/audio/verse/', {
    params: { surah, ayah, ...(reciterId ? { reciter_id: reciterId } : {}) },
  });
}

/**
 * GET /quran/progress/ — dernière position de lecture de l'utilisateur.
 * (Nécessite un Bearer token : géré par l'intercepteur du client.)
 * @returns {Promise<Object>} { last_surah_number, last_ayah_number, updated_at }
 */
export function getProgress() {
  return client.get('/quran/progress/');
}

/**
 * PUT /quran/progress/ — enregistre la dernière position de lecture.
 * @param {{ last_surah_number: number, last_ayah_number: number }} payload
 * @returns {Promise<Object>} position enregistrée (même format que GET)
 */
export function updateProgress(payload) {
  return client.put('/quran/progress/', payload);
}
