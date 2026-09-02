import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { fetchTTS } from './api';

let audioQueue = [];
let isPlaying = false;
let recentAnnouncements = {};

function spellToken(token) {
  return token.split('').join(' ');
}

function dedupKey(token, office, action) {
  return `${token}|${office}|${action}`;
}

function canAnnounce(key, cooldownMs = 1000) {
  const now = Date.now();
  if (recentAnnouncements[key] && now - recentAnnouncements[key] < cooldownMs) {
    return false;
  }
  recentAnnouncements[key] = now;
  return true;
}

async function playNext() {
  if (isPlaying || !audioQueue.length) return;
  isPlaying = true;
  const { sound, onDone } = audioQueue[0];
  try {
    await sound.playAsync();
    sound.setOnPlaybackStatusUpdate((status) => {
      if (status.didJustFinish) {
        sound.unloadAsync();
        audioQueue.shift();
        isPlaying = false;
        if (onDone) onDone();
        playNext();
      }
    });
  } catch (e) {
    audioQueue.shift();
    isPlaying = false;
    playNext();
  }
}

export async function speakText(text, onDone) {
  try {
    const blob = await fetchTTS(text);
    if (!blob) return;
    const fileUri = FileSystem.cacheDirectory + `tts_${Date.now()}.mp3`;
    const arrayBuffer = await blob.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);
    await FileSystem.writeAsStringAsync(fileUri, uint8Array, {
      encoding: FileSystem.EncodingType.Base64,
    });
    const base64 = await FileSystem.readAsStringAsync(fileUri, {
      encoding: FileSystem.EncodingType.Base64,
    });
    const { sound } = await Audio.Sound.createAsync({ uri: `data:audio/mp3;base64,${base64}` });
    audioQueue.push({ sound, onDone });
    playNext();
  } catch (e) {
    console.error('TTS error:', e);
  }
}

export function announceCalled(tokenNumber, studentName, officeName) {
  const key = dedupKey(tokenNumber, officeName, 'called');
  if (!canAnnounce(key)) return;
  const spelled = spellToken(tokenNumber);
  const text = studentName
    ? `Now calling ${studentName} with token ${spelled}. Please proceed to ${officeName}.`
    : `Now calling token ${spelled}. Please proceed to ${officeName}.`;
  speakText(text);
}

export function announceServing(tokenNumber, studentName, officeName) {
  const key = dedupKey(tokenNumber, officeName, 'serving');
  if (!canAnnounce(key)) return;
  const spelled = spellToken(tokenNumber);
  const text = studentName
    ? `Now serving ${studentName} with token ${spelled} at ${officeName}.`
    : `Now serving token ${spelled} at ${officeName}.`;
  speakText(text);
}

export function announceRecall(tokenNumber, studentName, officeName) {
  const key = dedupKey(tokenNumber, officeName, 'recall');
  if (!canAnnounce(key)) return;
  const spelled = spellToken(tokenNumber);
  const text = studentName
    ? `Attention please, ${studentName}, token ${spelled} please proceed to ${officeName}.`
    : `Attention please, token ${spelled} please proceed to ${officeName}.`;
  speakText(text);
}

export function announceBatch(tokens, officeName) {
  if (!tokens.length) return;
  const key = dedupKey(tokens.map((t) => t.token_number).join(','), officeName, 'batch');
  if (!canAnnounce(key, 5000)) return;
  const list = tokens
    .map((t) => {
      const name = t.student_name || 'Student';
      return `${name} (${spellToken(t.token_number)})`;
    })
    .join(', ');
  const lastComma = list.lastIndexOf(',');
  const formatted = lastComma > -1 ? list.substring(0, lastComma) + ' and' + list.substring(lastComma + 1) : list;
  const text = `Attention please. The following people, including ${formatted}, are requested to proceed to ${officeName}.`;
  speakText(text);
}
