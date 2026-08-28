import { useState, useEffect, useRef } from 'react';
import { fetchQueues, fetchUpNext, fetchRecentRecalls, fetchOfficeMessages } from '../services/api';
import { announceCalled, announceServing, announceRecall } from '../services/voice';

export default function useQueueData() {
  const [queues, setQueues] = useState([]);
  const [upNext, setUpNext] = useState([]);
  const [recalls, setRecalls] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isIdle, setIsIdle] = useState(true);
  const [stats, setStats] = useState({ totalWaiting: 0, totalCalled: 0, totalServing: 0 });
  const [activeTokens, setActiveTokens] = useState([]);
  const announcedRecalls = useRef(new Set());

  useEffect(() => {
    syncQueueData();
    const qTimer = setInterval(syncQueueData, 2000);
    const unTimer = setInterval(syncUpNext, 2000);
    const rTimer = setInterval(syncRecalls, 3000);
    const mTimer = setInterval(syncMessages, 10000);
    return () => {
      clearInterval(qTimer);
      clearInterval(unTimer);
      clearInterval(rTimer);
      clearInterval(mTimer);
    };
  }, []);

  async function syncQueueData() {
    const data = await fetchQueues();
    if (!data || !data.success) return;
    const q = data.queues || [];
    setQueues(q);

    let totalWaiting = 0;
    let totalCalled = 0;
    let totalServing = 0;
    const tokens = [];

    for (const office of q) {
      totalWaiting += office.waiting_count || 0;
      const called = (office.called_tokens || []).filter((t) => t.token_number);
      const serving = (office.serving_tokens || []).filter((t) => t.token_number);
      totalCalled += called.length;
      totalServing += serving.length;

      for (const t of called) {
        tokens.push({ ...t, office_name: office.office_name, type: 'called' });
        announceCalled(t.token_number, t.student_name, office.office_name);
      }
      for (const t of serving) {
        tokens.push({ ...t, office_name: office.office_name, type: 'serving' });
        announceServing(t.token_number, t.student_name, office.office_name);
      }
    }

    setActiveTokens(tokens);
    setIsIdle(totalCalled === 0 && totalServing === 0);
    setStats({ totalWaiting, totalCalled, totalServing });
  }

  async function syncUpNext() {
    const data = await fetchUpNext();
    if (!data || !data.success) return;
    const items = [];
    for (const office of data.queues || []) {
      for (const t of office.next_up || []) {
        items.push({ ...t, office_name: office.office_name });
      }
    }
    setUpNext(items);
  }

  async function syncRecalls() {
    const data = await fetchRecentRecalls();
    if (!data || !data.success) return;
    for (const r of data.recalls || []) {
      if (!announcedRecalls.current.has(r.id)) {
        announcedRecalls.current.add(r.id);
        if (announcedRecalls.current.size > 50) {
          const arr = [...announcedRecalls.current];
          announcedRecalls.current = new Set(arr.slice(-25));
        }
        announceRecall(r.token_number, r.student_name, r.office_name);
      }
    }
    setRecalls(data.recalls || []);
  }

  async function syncMessages() {
    const data = await fetchOfficeMessages();
    if (!data || !data.success) return;
    setMessages(data.messages || []);
  }

  const currentUnavailNotices = queues
    .filter(
      (o) =>
        (o.availability_status || '').toLowerCase() === 'unavailable' &&
        (o.unavailability_notice || '').trim()
    )
    .map((o) => ({
      office_name: o.office_name,
      office_code: o.office_code,
      message: `Warning: ${o.office_name} is currently closed: ${o.unavailability_notice}`,
      is_unavailability: true,
    }));

  const allNotices = [...currentUnavailNotices, ...messages];

  return {
    queues,
    upNext,
    recalls,
    messages,
    isIdle,
    stats,
    activeTokens,
    allNotices,
  };
}
