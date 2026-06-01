// Sky City Centre — Customer manage/cancel page

(function () {
  const CFG = window.SKY_CITY_CONFIG;
  if (!CFG) { alert('config.js missing'); return; }

  let current = null;
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
        else if (k.startsWith('on') && typeof v === 'function') {
          node.addEventListener(k.slice(2).toLowerCase(), v);
        } else node.setAttribute(k, String(v));
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
  function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); }

  // Language: match main site's stored preference
  function applyLang() {
    let lang = 'en';
    try { if (localStorage.getItem('skycity_lang') === 'ar') lang = 'ar'; } catch (_) {}
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
    document.querySelectorAll('[data-en]').forEach(node => {
      const text = node.getAttribute(lang === 'ar' ? 'data-ar' : 'data-en');
      if (text) node.textContent = text;
    });
    return lang;
  }
  const lang = applyLang();
  const localeStr = lang === 'ar' ? 'ar-JO' : 'en-US';

  const MSG = {
    en: {
      notFound: 'No booking found with those details.',
      missing: 'Please enter both phone and code.',
      error: 'Something went wrong. Please try again.',
      confirmCancel: 'Are you sure you want to cancel this booking?',
      cancelFailed: 'Could not cancel. Please call the clinic.',
      savedLabel: 'Your recent booking:',
      statusBooked: 'Booked',
      statusCancelled: 'Cancelled',
    },
    ar: {
      notFound: 'لا يوجد حجز بهذه البيانات.',
      missing: 'الرجاء إدخال الهاتف والرمز.',
      error: 'حدث خطأ. حاول مرة أخرى.',
      confirmCancel: 'هل أنت متأكد أنك تريد إلغاء هذا الحجز؟',
      cancelFailed: 'تعذّر الإلغاء. يرجى الاتصال بالعيادة.',
      savedLabel: 'حجزك الأخير:',
      statusBooked: 'محجوز',
      statusCancelled: 'ملغى',
    },
  }[lang];

  // ---------- RPC ----------
  async function rpc(fn, body) {
    const res = await fetch(`${CFG.SUPABASE_URL}/rest/v1/rpc/${fn}`, {
      method: 'POST',
      headers: {
        'apikey': CFG.SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${CFG.SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok) {
      const msg = (json && (json.message || json.error)) || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return json;
  }

  // ---------- Flow ----------
  async function lookup() {
    const phone = $('phone-input').value.trim();
    const code = $('code-input').value.trim().toUpperCase();
    const err = $('lookup-err');
    err.textContent = '';
    if (!phone || !code) { err.textContent = MSG.missing; return; }
    try {
      const data = await rpc('lookup_booking', { p_phone: phone, p_cancel_code: code });
      if (!data || !data.length) { err.textContent = MSG.notFound; return; }
      current = data[0];
      current._code = code;
      showResult();
    } catch (e) {
      err.textContent = MSG.error;
    }
  }

  function showResult() {
    const info = $('info');
    clear(info);
    const d = new Date(current.start_at);
    const dateStr = d.toLocaleDateString(localeStr, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    const timeStr = pad2(d.getHours()) + ':00';
    const isBooked = current.status === 'booked';

    info.appendChild(el('div', { class: 'name', text: current.name || '' }));
    info.appendChild(el('div', { class: 'when', text: `${dateStr} · ${timeStr}` }));
    info.appendChild(el('span', {
      class: 'status ' + current.status,
      text: isBooked ? MSG.statusBooked : MSG.statusCancelled,
    }));

    $('cancel-btn').style.display = isBooked ? 'flex' : 'none';
    $('lookup-view').style.display = 'none';
    $('result-view').style.display = 'block';
  }

  async function doCancel() {
    if (!confirm(MSG.confirmCancel)) return;
    try {
      const result = await rpc('cancel_booking', { p_id: current.id, p_cancel_code: current._code });
      if (result === true) {
        current.status = 'cancelled';
        showResult();
        // Remove from localStorage saved list
        try {
          const saved = JSON.parse(localStorage.getItem('sky_bookings') || '[]');
          localStorage.setItem('sky_bookings', JSON.stringify(saved.filter(x => x.id !== current.id)));
        } catch (_) {}
      } else {
        alert(MSG.cancelFailed);
      }
    } catch (e) {
      alert(MSG.cancelFailed);
    }
  }

  function backToLookup() {
    $('result-view').style.display = 'none';
    $('lookup-view').style.display = 'block';
    $('phone-input').value = '';
    $('code-input').value = '';
    $('lookup-err').textContent = '';
    current = null;
    loadSaved();
  }

  // ---------- Saved bookings hint from localStorage ----------
  function loadSaved() {
    const container = $('saved-list');
    clear(container);
    let saved = [];
    try { saved = JSON.parse(localStorage.getItem('sky_bookings') || '[]'); } catch (_) {}
    // Only future, non-cancelled bookings
    const now = new Date();
    const upcoming = saved.filter(x => new Date(x.start_at) > now);
    if (upcoming.length === 0) return;
    upcoming.forEach(x => {
      const d = new Date(x.start_at);
      const dateStr = d.toLocaleDateString(localeStr, { month: 'short', day: 'numeric' });
      const timeStr = pad2(d.getHours()) + ':00';
      const hint = el('div', {
        class: 'saved-hint',
        onClick: () => {
          $('code-input').value = x.code;
          $('code-input').focus();
        },
      }, [
        MSG.savedLabel + ' ',
        el('strong', { text: `${dateStr} · ${timeStr}` }),
        ' — code ',
        el('strong', { text: x.code }),
      ]);
      container.appendChild(hint);
    });
  }

  function wire() {
    $('lookup-btn').addEventListener('click', lookup);
    $('phone-input').addEventListener('keypress', e => { if (e.key === 'Enter') lookup(); });
    $('code-input').addEventListener('keypress', e => { if (e.key === 'Enter') lookup(); });
    $('cancel-btn').addEventListener('click', doCancel);
    $('back-btn').addEventListener('click', backToLookup);
    loadSaved();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire);
  else wire();
})();
