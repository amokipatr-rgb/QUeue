const BASE_URL = 'https://queue-production-2a11.up.railway.app';

async function fetchJSON(url, timeout = 10000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    clearTimeout(timer);
    return null;
  }
}

export async function fetchQueues() {
  return fetchJSON(`${BASE_URL}/api/public/queues`);
}

export async function fetchUpNext() {
  return fetchJSON(`${BASE_URL}/api/public/queues/next`);
}

export async function fetchRecentRecalls() {
  return fetchJSON(`${BASE_URL}/api/queue/recent-recalls`);
}

export async function fetchOfficeMessages(officeCode) {
  let url = `${BASE_URL}/api/office/messages?limit=100`;
  if (officeCode) url += `&office_code=${encodeURIComponent(officeCode)}`;
  return fetchJSON(url);
}

export async function fetchTTS(text) {
  try {
    const res = await fetch(`${BASE_URL}/api/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) return null;
    return await res.blob();
  } catch (e) {
    return null;
  }
}

export async function fetchServerTime() {
  return fetchJSON(`${BASE_URL}/api/health`);
}
