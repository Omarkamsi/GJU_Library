// Sky City Centre — Customer booking widget
// Renders into <div id="booking-widget"></div> and talks to Supabase RPC.

(function () {
  const CFG = window.SKY_CITY_CONFIG;
  if (!CFG) { console.error('[booking] SKY_CITY_CONFIG missing — did you load config.js first?'); return; }

  const T = {
    en: {
      title: 'Book your session',
      subtitle: 'Pick a date and time. All sessions are 60 minutes.',
      today: 'Today',
      tomorrow: 'Tomorrow',
      selectDate: "Select a date above to see available times.",
      noSlots: 'No times available for this day.',
      timesFor: 'Available times',
      yourName: 'Your name',
      yourPhone: 'Phone number',
      confirm: 'Confirm booking',
      booking: 'Booking...',
      success: 'Booking confirmed',
      successMsg: 'We look forward to seeing you.',
      yourCode: 'Your cancel code',
      saveCode: "Save this code. You will need it to cancel or reschedule.",
      another: 'Book another',
      manageLink: 'Manage my booking',
      errorBooked: 'Sorry, that slot was just taken. Please pick another time.',
      errorGeneric: 'Something went wrong. Please try again or call us.',
      errorFields: 'Please enter your name and phone number.',
      booked: 'Booked',
      monthNames: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
      dayShort: ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
    },
    ar: {
      title: 'احجز جلستك',
      subtitle: 'اختر التاريخ والوقت. جميع الجلسات 60 دقيقة.',
      today: 'اليوم',
      tomorrow: 'غدًا',
      selectDate: 'اختر تاريخًا من الأعلى لرؤية الأوقات المتاحة.',
      noSlots: 'لا تتوفر مواعيد في هذا اليوم.',
      timesFor: 'الأوقات المتاحة',
      yourName: 'اسمك',
      yourPhone: 'رقم الهاتف',
      confirm: 'تأكيد الحجز',
      booking: 'جاري الحجز...',
      success: 'تم تأكيد الحجز',
      successMsg: 'نتطلع لرؤيتك.',
      yourCode: 'رمز الإلغاء',
      saveCode: 'احتفظ بهذا الرمز. ستحتاجه للإلغاء أو تغيير الموعد.',
      another: 'احجز موعدًا آخر',
      manageLink: 'إدارة حجزي',
      errorBooked: 'عذرًا، تم حجز هذا الموعد للتو. يرجى اختيار وقت آخر.',
      errorGeneric: 'حدث خطأ. حاول مرة أخرى أو اتصل بنا.',
      errorFields: 'الرجاء إدخال الاسم ورقم الهاتف.',
      booked: 'محجوز',
      monthNames: ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'],
      dayShort: ['الأحد','الإثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت'],
    },
  };

  // ---------- State ----------
  let lang = document.documentElement.dir === 'rtl' ? 'ar' : 'en';
  let selectedDate = null;   // Date (midnight of selected day)
  let selectedSlot = null;   // Date (start of hour slot)
  let bookedSlots = new Set(); // ISO strings

  const t = (k) => T[lang][k];
  const pad2 = (n) => String(n).padStart(2, '0');

  // ---------- DOM helpers (safe, no innerHTML with untrusted data) ----------
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
        if (typeof c === 'string') node.appendChild(document.createTextNode(c));
        else node.appendChild(c);
      });
    }
    return node;
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  // ---------- RPC helpers ----------
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

  async function fetchBookedSlots() {
    const from = new Date(); from.setHours(0, 0, 0, 0);
    const to = new Date(from); to.setDate(to.getDate() + CFG.BOOKING_DAYS_AHEAD + 1);
    try {
      const data = await rpc('get_booked_slots', {
        p_from: from.toISOString(),
        p_to: to.toISOString(),
      });
      bookedSlots = new Set((data || []).map(r => new Date(r.start_at).toISOString()));
    } catch (e) {
      console.error('[booking] fetch booked slots failed', e);
    }
  }

  async function createBooking(name, phone, startAt) {
    const data = await rpc('create_booking', {
      p_name: name,
      p_phone: phone,
      p_start_at: startAt.toISOString(),
    });
    return Array.isArray(data) ? data[0] : data;
  }

  // ---------- Data helpers ----------
  function getDates() {
    const dates = [];
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    for (let i = 0; i < CFG.BOOKING_DAYS_AHEAD; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      dates.push(d);
    }
    return dates;
  }

  function getSlotsForDate(date) {
    const slots = [];
    const now = new Date();
    for (let h = CFG.OPEN_HOUR; h < CFG.CLOSE_HOUR; h++) {
      const d = new Date(date);
      d.setHours(h, 0, 0, 0);
      if (d > now) slots.push(d);
    }
    return slots;
  }

  function labelForDate(d) {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const diff = Math.round((d - today) / 86400000);
    if (diff === 0) return t('today');
    if (diff === 1) return t('tomorrow');
    return t('dayShort')[d.getDay()];
  }

  // ---------- Rendering (DOM builders, not innerHTML) ----------
  function buildDateButton(d) {
    const sel = selectedDate && d.getTime() === selectedDate.getTime();
    const btn = el('button', {
      type: 'button',
      class: 'bk-date' + (sel ? ' selected' : ''),
      dataset: { iso: d.toISOString() },
      onClick: () => { selectedDate = new Date(d); selectedSlot = null; render(); },
    }, [
      el('div', { class: 'bk-date-day', text: labelForDate(d) }),
      el('div', { class: 'bk-date-num', text: String(d.getDate()) }),
      el('div', { class: 'bk-date-month', text: t('monthNames')[d.getMonth()] }),
    ]);
    return btn;
  }

  function buildSlotsSection() {
    const section = el('div', { class: 'bk-section' });
    if (!selectedDate) {
      section.appendChild(el('p', { class: 'bk-hint', text: t('selectDate') }));
      return section;
    }
    const slots = getSlotsForDate(selectedDate);
    if (slots.length === 0) {
      section.appendChild(el('p', { class: 'bk-hint', text: t('noSlots') }));
      return section;
    }
    section.appendChild(el('div', { class: 'bk-section-label', text: t('timesFor') }));
    const grid = el('div', { class: 'bk-slots' });
    slots.forEach(s => {
      const iso = s.toISOString();
      const isBooked = bookedSlots.has(iso);
      const isSel = selectedSlot && selectedSlot.toISOString() === iso;
      const btnAttrs = {
        type: 'button',
        class: 'bk-slot' + (isSel ? ' selected' : ''),
        dataset: { iso },
      };
      if (isBooked) {
        btnAttrs.disabled = true;
        btnAttrs['aria-disabled'] = 'true';
      } else {
        btnAttrs.onClick = () => {
          selectedSlot = new Date(s);
          render();
          setTimeout(() => {
            const f = document.querySelector('.bk-form');
            if (f && f.scrollIntoView) f.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }, 60);
        };
      }
      const btn = el('button', btnAttrs, [
        el('span', { class: 'bk-slot-time', text: pad2(s.getHours()) + ':00' }),
      ]);
      if (isBooked) btn.appendChild(el('span', { class: 'bk-slot-label', text: t('booked') }));
      grid.appendChild(btn);
    });
    section.appendChild(grid);
    return section;
  }

  function buildForm() {
    const nameInput = el('input', { type: 'text', id: 'bk-name', placeholder: t('yourName'), autocomplete: 'name', required: true });
    const phoneInput = el('input', { type: 'tel', id: 'bk-phone', placeholder: t('yourPhone'), autocomplete: 'tel', required: true });
    const err = el('div', { class: 'bk-error', id: 'bk-error', 'aria-live': 'polite' });
    const submit = el('button', {
      type: 'button', class: 'bk-submit', id: 'bk-submit', text: t('confirm'),
      onClick: async () => {
        const name = nameInput.value.trim();
        const phone = phoneInput.value.trim();
        err.textContent = '';
        if (!name || !phone) { err.textContent = t('errorFields'); return; }
        submit.disabled = true;
        submit.textContent = t('booking');
        try {
          const result = await createBooking(name, phone, selectedSlot);
          renderSuccess(result, selectedSlot);
        } catch (e) {
          const msg = (e.message || '').toLowerCase();
          err.textContent = (msg.includes('booked') || msg.includes('duplicate') || msg.includes('unique'))
            ? t('errorBooked')
            : t('errorGeneric');
          submit.disabled = false;
          submit.textContent = t('confirm');
          fetchBookedSlots();
        }
      },
    });
    return el('div', { class: 'bk-form' }, [nameInput, phoneInput, submit, err]);
  }

  function render() {
    const container = document.getElementById('booking-widget');
    if (!container) return;
    clear(container);

    const wrap = el('div', { class: 'bk-wrap' });
    const head = el('div', { class: 'bk-head' }, [
      el('h3', { class: 'bk-title', text: t('title') }),
      el('p', { class: 'bk-sub', text: t('subtitle') }),
    ]);
    wrap.appendChild(head);

    const dates = el('div', { class: 'bk-dates' });
    getDates().forEach(d => dates.appendChild(buildDateButton(d)));
    wrap.appendChild(dates);

    wrap.appendChild(buildSlotsSection());

    if (selectedSlot) wrap.appendChild(buildForm());

    container.appendChild(wrap);
  }

  function renderSuccess(result, startAt) {
    const container = document.getElementById('booking-widget');
    if (!container) return;
    clear(container);

    const locale = lang === 'ar' ? 'ar-JO' : 'en-US';
    const dateStr = startAt.toLocaleDateString(locale, {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
    });
    const timeStr = pad2(startAt.getHours()) + ':00';

    const wrap = el('div', { class: 'bk-wrap' }, [
      el('div', { class: 'bk-success-wrap' }, [
        el('div', { class: 'bk-check', 'aria-hidden': 'true', text: '✓' }),
        el('h3', { class: 'bk-title', text: t('success') }),
        el('p', { class: 'bk-sub', text: t('successMsg') }),
        el('div', { class: 'bk-confirm-details' }, [
          el('div', { class: 'bk-confirm-date', text: dateStr }),
          el('div', { class: 'bk-confirm-time', text: timeStr }),
        ]),
        el('div', { class: 'bk-code-box' }, [
          el('div', { class: 'bk-code-label', text: t('yourCode') }),
          el('div', { class: 'bk-code', text: String(result.cancel_code || '') }),
          el('div', { class: 'bk-code-hint', text: t('saveCode') }),
        ]),
        el('div', { class: 'bk-actions' }, [
          el('button', {
            type: 'button', class: 'bk-restart', text: t('another'),
            onClick: () => {
              selectedDate = null; selectedSlot = null;
              fetchBookedSlots().then(render);
            },
          }),
          el('a', { href: 'manage.html', class: 'bk-manage', text: t('manageLink') + (lang === 'ar' ? ' ←' : ' →') }),
        ]),
      ]),
    ]);
    container.appendChild(wrap);

    // Save to localStorage so the manage page can pick it up
    try {
      const saved = JSON.parse(localStorage.getItem('sky_bookings') || '[]');
      saved.push({
        id: result.id,
        code: result.cancel_code,
        start_at: startAt.toISOString(),
      });
      localStorage.setItem('sky_bookings', JSON.stringify(saved));
    } catch (_) { /* ignore */ }
  }

  // Re-render on language toggle
  const observer = new MutationObserver(() => {
    const newLang = document.documentElement.dir === 'rtl' ? 'ar' : 'en';
    if (newLang !== lang) {
      lang = newLang;
      render();
    }
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['dir', 'lang'] });

  // Init
  function init() {
    if (!document.getElementById('booking-widget')) return;
    fetchBookedSlots().then(render);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
