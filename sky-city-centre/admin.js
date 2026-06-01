// Sky City Centre — Staff admin
// Talks to the admin-api Edge Function with a PIN header.

(function () {
  const CFG = window.SKY_CITY_CONFIG;
  if (!CFG) { alert('config.js missing'); return; }

  let pin = sessionStorage.getItem('sky_admin_pin') || '';
  let bookings = [];
  let editingId = null;

  const $ = (id) => document.getElementById(id);
  const pad2 = (n) => String(n).padStart(2, '0');

  // Safe DOM builder
  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v == null || v === false) continue;
        if (k === 'class') node.className = v;
        else if (k === 'text') node.textContent = v;
        else if (k === 'dataset') {
          for (const [dk, dv] of Object.entries(v)) node.dataset[dk] = dv;
        } else if (k.startsWith('on') && typeof v === 'function') {
          node.addEventListener(k.slice(2).toLowerCase(), v);
        } else if (v === true) node.setAttribute(k, '');
        else node.setAttribute(k, String(v));
      }
    }
    if (children) {
      (Array.isArray(children) ? children : [children]).forEach(c => {
        if (c == null || c === false) return;
        node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
      });
    }
    return node;
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  // ---------- API ----------
  async function api(action, payload) {
    const res = await fetch(CFG.ADMIN_FUNCTION_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-staff-pin': pin },
      body: JSON.stringify({ action, payload: payload || {} }),
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok || !json.ok) throw new Error(json.error || `HTTP ${res.status}`);
    return json.data;
  }

  // ---------- Auth ----------
  async function login() {
    pin = $('pin-input').value.trim();
    $('pin-err').textContent = '';
    if (!pin) { $('pin-err').textContent = 'Enter a PIN'; return; }
    try {
      await api('list', {});
      sessionStorage.setItem('sky_admin_pin', pin);
      showMain();
      await refresh();
    } catch (e) {
      $('pin-err').textContent = e.message.includes('Unauthorized') ? 'Invalid PIN' : e.message;
    }
  }

  function logout() {
    sessionStorage.removeItem('sky_admin_pin');
    pin = '';
    location.reload();
  }

  function showMain() {
    $('pin-screen').style.display = 'none';
    $('main').style.display = 'block';
  }

  // ---------- List ----------
  async function refresh() {
    try {
      const payload = {};
      const from = $('filter-from').value;
      const to = $('filter-to').value;
      if (from) payload.from = new Date(from + 'T00:00:00').toISOString();
      if (to) {
        const t2 = new Date(to + 'T00:00:00');
        t2.setDate(t2.getDate() + 1);
        payload.to = t2.toISOString();
      }
      bookings = await api('list', payload);
      render();
    } catch (e) {
      alert('Could not load bookings: ' + e.message);
    }
  }

  function render() {
    const container = $('list');
    clear(container);

    const active = bookings.filter(b => b.status === 'booked');
    $('total-count').textContent = `${active.length} active · ${bookings.length} total`;

    if (!bookings.length) {
      container.appendChild(
        el('div', { class: 'empty' }, [
          el('h3', { text: 'No bookings yet' }),
          el('p', { text: 'New bookings will appear here automatically.' }),
        ])
      );
      return;
    }

    // Group by day
    const groups = new Map();
    bookings.forEach(b => {
      const d = new Date(b.start_at);
      const key = d.toDateString();
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(b);
    });

    for (const [key, items] of groups) {
      const dayDate = new Date(key);
      const dayLabel = dayDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
      const group = el('div', { class: 'day-group' });
      group.appendChild(
        el('div', { class: 'day-header' }, [
          dayLabel,
          el('span', { class: 'day-count', text: `${items.filter(x => x.status === 'booked').length} booked` }),
        ])
      );
      const list = el('div', { class: 'booking-list' });
      items.forEach(b => list.appendChild(buildBookingItem(b)));
      group.appendChild(list);
      container.appendChild(group);
    }
  }

  function buildBookingItem(b) {
    const d = new Date(b.start_at);
    const timeStr = pad2(d.getHours()) + ':00';
    const dateStr = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

    const nameWrap = el('div', { class: 'name' }, [b.name || '—']);
    if (b.created_by === 'staff') nameWrap.appendChild(el('span', { class: 'tag staff', text: 'Staff' }));
    if (b.status === 'cancelled') nameWrap.appendChild(el('span', { class: 'tag cancelled', text: 'Cancelled' }));

    const meta = el('div', { class: 'meta' }, [
      nameWrap,
      el('div', { class: 'phone' }, [el('a', { href: 'tel:' + (b.phone || ''), text: b.phone || '' })]),
    ]);
    if (b.notes) meta.appendChild(el('div', { class: 'notes', text: b.notes }));

    const actions = el('div', { class: 'actions' });
    if (b.status === 'booked') {
      actions.appendChild(el('button', {
        class: 'btn btn-ghost btn-sm',
        text: b.notes ? 'Edit notes' : 'Add notes',
        onClick: () => openNotesModal(b),
      }));
      actions.appendChild(el('button', {
        class: 'btn btn-danger btn-sm',
        text: 'Cancel',
        onClick: () => cancelBooking(b),
      }));
    }

    return el('div', { class: 'booking-item' + (b.status === 'cancelled' ? ' cancelled' : '') }, [
      el('div', { class: 'when' }, [
        el('div', { class: 'time', text: timeStr }),
        el('div', { class: 'date', text: dateStr }),
      ]),
      meta,
      actions,
    ]);
  }

  // ---------- New booking modal ----------
  function openNewModal() {
    $('nb-name').value = '';
    $('nb-phone').value = '';
    // Default to tomorrow 10:00 local time
    const d = new Date();
    d.setDate(d.getDate() + 1);
    d.setHours(CFG.OPEN_HOUR, 0, 0, 0);
    $('nb-datetime').value = localInputValue(d);
    $('nb-notes').value = '';
    $('nb-err').textContent = '';
    $('new-modal').classList.add('show');
    setTimeout(() => $('nb-name').focus(), 50);
  }

  function localInputValue(d) {
    return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
  }

  async function saveNew() {
    const name = $('nb-name').value.trim();
    const phone = $('nb-phone').value.trim();
    const dt = $('nb-datetime').value;
    const notes = $('nb-notes').value.trim();
    const err = $('nb-err');
    err.textContent = '';
    if (!name || !phone || !dt) { err.textContent = 'Name, phone and date/time are required'; return; }

    const d = new Date(dt);
    d.setMinutes(0, 0, 0); // snap to the hour
    if (d <= new Date()) { err.textContent = 'Cannot book in the past'; return; }

    try {
      await api('create', { name, phone, start_at: d.toISOString(), notes });
      $('new-modal').classList.remove('show');
      await refresh();
    } catch (e) {
      err.textContent = e.message;
    }
  }

  // ---------- Notes modal ----------
  function openNotesModal(b) {
    editingId = b.id;
    $('notes-text').value = b.notes || '';
    $('notes-err').textContent = '';
    $('notes-modal').classList.add('show');
    setTimeout(() => $('notes-text').focus(), 50);
  }

  async function saveNotes() {
    const notes = $('notes-text').value.trim();
    const err = $('notes-err');
    err.textContent = '';
    try {
      await api('update_notes', { id: editingId, notes });
      $('notes-modal').classList.remove('show');
      await refresh();
    } catch (e) {
      err.textContent = e.message;
    }
  }

  // ---------- Cancel ----------
  async function cancelBooking(b) {
    if (!confirm(`Cancel booking for ${b.name} at ${new Date(b.start_at).toLocaleString()}?`)) return;
    try {
      await api('cancel', { id: b.id });
      await refresh();
    } catch (e) {
      alert('Cancel failed: ' + e.message);
    }
  }

  // ---------- Wire up ----------
  function wire() {
    $('pin-btn').addEventListener('click', login);
    $('pin-input').addEventListener('keypress', e => { if (e.key === 'Enter') login(); });

    $('new-btn').addEventListener('click', openNewModal);
    $('refresh-btn').addEventListener('click', refresh);
    $('logout-btn').addEventListener('click', logout);

    $('filter-from').addEventListener('change', refresh);
    $('filter-to').addEventListener('change', refresh);
    $('filter-clear').addEventListener('click', () => {
      $('filter-from').value = '';
      $('filter-to').value = '';
      refresh();
    });

    $('nb-save').addEventListener('click', saveNew);
    $('nb-cancel').addEventListener('click', () => $('new-modal').classList.remove('show'));
    $('notes-save').addEventListener('click', saveNotes);
    $('notes-cancel').addEventListener('click', () => $('notes-modal').classList.remove('show'));

    // Close modals on backdrop click
    document.querySelectorAll('.modal-backdrop').forEach(bd => {
      bd.addEventListener('click', e => { if (e.target === bd) bd.classList.remove('show'); });
    });

    // Auto-login if a PIN is already in session storage
    if (pin) {
      api('list', {}).then(() => { showMain(); refresh(); })
        .catch(() => { sessionStorage.removeItem('sky_admin_pin'); pin = ''; });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire);
  else wire();
})();
