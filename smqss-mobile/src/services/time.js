import { fetchServerTime } from './api';

let serverTimeMs = Date.now();
let lastSyncLocal = Date.now();
let serverSynced = false;

export async function syncServerTime() {
  try {
    const data = await fetchServerTime();
    if (data && data.timestamp) {
      lastSyncLocal = Date.now();
      serverTimeMs = new Date(data.timestamp).getTime();
      serverSynced = true;
    }
  } catch (e) {}
}

export function now() {
  if (serverSynced) {
    return new Date(serverTimeMs + (Date.now() - lastSyncLocal));
  }
  return new Date();
}

export function getEATDate() {
  return now().toLocaleDateString('en-UG', {
    timeZone: 'Africa/Nairobi',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function getEATTime() {
  return now()
    .toLocaleTimeString('en-UG', {
      timeZone: 'Africa/Nairobi',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    })
    .replace(/^0/, '');
}

export function getEATShortTime() {
  return now()
    .toLocaleTimeString('en-UG', {
      timeZone: 'Africa/Nairobi',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    })
    .replace(/^0/, '');
}
