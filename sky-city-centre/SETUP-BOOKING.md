# Sky City Centre — Booking System Setup

This guide walks you through wiring the booking system to your Supabase project.

Expected time: **15–20 minutes**. You only need a web browser.

---

## What you get

- **Customers** can book directly on your website (phone + name, no login).
- **Staff** can log into `/admin.html` with a PIN and create bookings from phone calls.
- **Customers** can cancel at `/manage.html` with their phone + cancel code.
- **One shared calendar** — one booking per 60-minute slot, no double-booking.
- **Bilingual** (English / Arabic) — matches the main site's toggle.

---

## 1. Open your Supabase project

Go to https://supabase.com/dashboard and sign in.

Your project should already exist. If not, click **New project**:
- Name: `sky-city`
- Password: pick a strong one, save it in a password manager
- Region: `Frankfurt` (closest to Jordan)

Wait ~2 minutes for it to provision.

---

## 2. Run the database schema

1. In your project, click **SQL Editor** in the left sidebar.
2. Click **New query**.
3. Open `supabase/schema.sql` from this project folder, copy the whole file.
4. Paste it into the SQL editor and click **Run** (bottom right).
5. You should see "Success. No rows returned."

This creates:
- The `appointments` table
- A unique index preventing double-booking
- Four secure functions: `get_booked_slots`, `create_booking`, `cancel_booking`, `lookup_booking`
- Grants for the public (`anon`) role to call those functions

---

## 3. Get your API keys and paste them into `config.js`

1. Go to **Settings → API** (left sidebar).
2. Copy:
   - **Project URL** — e.g. `https://cxqraanhftwhggwqsooy.supabase.co`
   - **Project API keys → `anon` `public`** — a long JWT starting with `eyJ...`
3. Open `config.js` in this project folder and paste them:

```js
window.SKY_CITY_CONFIG = {
  SUPABASE_URL: 'https://cxqraanhftwhggwqsooy.supabase.co',
  SUPABASE_ANON_KEY: 'eyJhbGciOi...',  // ← paste here
  ADMIN_FUNCTION_URL: 'https://cxqraanhftwhggwqsooy.supabase.co/functions/v1/admin-api',
  // ...
};
```

> The `anon public` key is **designed to be exposed** in client code. It's NOT the same as the `service_role` key — never expose that one.

---

## 4. Deploy the staff Edge Function

The admin page needs a secure backend function so staff can see patient names / phones. This runs on Supabase for free.

### Option A — via the Supabase dashboard (no CLI needed)

1. In your project, click **Edge Functions** (left sidebar).
2. Click **Deploy a new function**.
3. Name: `admin-api` (exactly this)
4. Copy the entire contents of `supabase/functions/admin-api/index.ts` from this folder.
5. Paste it into the editor and click **Deploy**.
6. After it deploys, click **Manage secrets** (or go to **Settings → Edge Functions → Secrets**).
7. Add a secret:
   - Name: `STAFF_PIN`
   - Value: any PIN you choose, e.g. `4821` (remember it — this is what staff will type to log in)
8. Save.

### Option B — via the Supabase CLI

```bash
# Install the CLI (Mac/Linux)
brew install supabase/tap/supabase
# or: npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref cxqraanhftwhggwqsooy

# Set the PIN secret
supabase secrets set STAFF_PIN=4821

# Deploy the function
supabase functions deploy admin-api
```

After deploying, the function URL is automatically:
`https://cxqraanhftwhggwqsooy.supabase.co/functions/v1/admin-api`

This is already set in `config.js` — nothing else to do.

---

## 5. Test locally

```bash
cd /root/sky-city-centre
python3 -m http.server 8766
```

Open these URLs in your browser:

- **http://localhost:8766/** — main site, scroll to "Ready to move again?" and try booking a session
- **http://localhost:8766/admin.html** — staff admin (enter your PIN)
- **http://localhost:8766/manage.html** — customer cancel page

### Test flow:
1. On the main site, book a session for tomorrow at 11:00 with a test name/phone
2. Copy the cancel code shown on the success screen
3. Open admin.html, log in with your PIN → you should see the booking
4. Open manage.html, enter the same phone + cancel code → cancel it
5. Refresh the main site → the 11:00 slot should be bookable again

---

## 6. Deploy the website to production

Easy option — **Netlify Drop**:

1. Right-click the `/root/sky-city-centre/` folder → compress to `sky-city-centre.zip`
2. Go to https://app.netlify.com/drop
3. Drag the zip onto the page
4. You get a free `*.netlify.app` URL immediately
5. In the Netlify dashboard, go to **Domain settings** and add your own domain (optional)

Or use **Vercel**:
```bash
npm i -g vercel
cd /root/sky-city-centre
vercel
```

---

## Changing things later

### Change hours or slot length
Edit `config.js`:
- `OPEN_HOUR: 10` — first slot
- `CLOSE_HOUR: 21` — last slot starts at (CLOSE_HOUR − 1):00
- `SLOT_DURATION_MIN: 60` — slot length
- `BOOKING_DAYS_AHEAD: 14` — how far ahead customers can book

### Change the staff PIN
Dashboard: **Settings → Edge Functions → Secrets → `STAFF_PIN`** → edit.
CLI: `supabase secrets set STAFF_PIN=new_pin`

### View all bookings directly in Supabase
Dashboard: **Table Editor → appointments**.
You can also export as CSV from there.

### Block a slot (lunch break, holiday)
Easiest: use the staff admin page and create a dummy booking with name "BLOCKED".
Or insert directly in the table editor.

---

## Troubleshooting

**"SKY_CITY_CONFIG missing" in console** — `config.js` isn't loading. Check the path, and that you didn't accidentally leave `PASTE-YOUR-ANON-PUBLIC-KEY-HERE` in there.

**Booking fails with "permission denied"** — the schema SQL didn't run fully, or the function grants are missing. Re-run `supabase/schema.sql` in the SQL Editor.

**Admin page says "Unauthorized"** — wrong PIN, OR the `STAFF_PIN` secret isn't set on the Edge Function, OR the function wasn't deployed.

**Slots don't show as booked** — check `get_booked_slots` is running by opening the Network tab in your browser and looking for the RPC call. The response should be an array.

**Times show in wrong timezone** — the system uses the browser's local time. As long as staff and customers are in Jordan (UTC+3), it works automatically.

---

## Security notes

- The `anon` key is safe in the browser — it can only call the four functions you explicitly granted.
- Row Level Security is **on** for the `appointments` table with no policies, which means **no one** can read the table directly. All access goes through the functions (limited access) or the admin Edge Function (full access, PIN-protected).
- The `service_role` key must NEVER leave Supabase — it's only used inside the Edge Function.
- The staff PIN is stored as an Edge Function secret, never in the frontend.
- **If you ever share screenshots or this project publicly, rotate the database password** via **Settings → Database → Reset database password**. The anon key can also be rotated via **Settings → API → Reset anon key** if needed.
