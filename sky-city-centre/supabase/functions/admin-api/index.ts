// Sky City Centre — Staff Admin API (Supabase Edge Function)
//
// Deploy:  supabase functions deploy admin-api
// Secret:  supabase secrets set STAFF_PIN=4821  (change 4821 to your PIN)
//
// Accepts POST with JSON body: { action, payload }
// Requires header: x-staff-pin: <STAFF_PIN>

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const STAFF_PIN = Deno.env.get('STAFF_PIN') ?? '';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? '';
const SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'content-type, x-staff-pin, authorization, apikey',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

function randomCode(): string {
  return Math.random().toString(36).substring(2, 8).toUpperCase();
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: cors });
  }

  const pin = req.headers.get('x-staff-pin');
  if (!STAFF_PIN || pin !== STAFF_PIN) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Unauthorized' }),
      { status: 401, headers: { ...cors, 'Content-Type': 'application/json' } },
    );
  }

  const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

  try {
    const { action, payload } = await req.json();
    let data: unknown;

    switch (action) {
      case 'list': {
        const { from, to } = payload ?? {};
        let q = supabase
          .from('appointments')
          .select('*')
          .order('start_at', { ascending: true });
        if (from) q = q.gte('start_at', from);
        if (to) q = q.lt('start_at', to);
        const { data: rows, error } = await q;
        if (error) throw error;
        data = rows;
        break;
      }

      case 'create': {
        const { name, phone, start_at, notes } = payload ?? {};
        if (!name || !phone || !start_at) {
          throw new Error('name, phone, start_at are required');
        }
        const { data: existing } = await supabase
          .from('appointments')
          .select('id')
          .eq('start_at', start_at)
          .eq('status', 'booked')
          .maybeSingle();
        if (existing) throw new Error('Slot already booked');

        const { data: row, error } = await supabase
          .from('appointments')
          .insert({
            name: String(name).trim(),
            phone: String(phone).trim(),
            start_at,
            cancel_code: randomCode(),
            created_by: 'staff',
            notes: notes || null,
          })
          .select()
          .single();
        if (error) throw error;
        data = row;
        break;
      }

      case 'cancel': {
        const { id } = payload ?? {};
        if (!id) throw new Error('id required');
        const { data: row, error } = await supabase
          .from('appointments')
          .update({ status: 'cancelled' })
          .eq('id', id)
          .select()
          .single();
        if (error) throw error;
        data = row;
        break;
      }

      case 'update_notes': {
        const { id, notes } = payload ?? {};
        if (!id) throw new Error('id required');
        const { data: row, error } = await supabase
          .from('appointments')
          .update({ notes: notes || null })
          .eq('id', id)
          .select()
          .single();
        if (error) throw error;
        data = row;
        break;
      }

      default:
        throw new Error('Unknown action');
    }

    return new Response(JSON.stringify({ ok: true, data }), {
      headers: { ...cors, 'Content-Type': 'application/json' },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ ok: false, error: (err as Error).message }),
      { status: 400, headers: { ...cors, 'Content-Type': 'application/json' } },
    );
  }
});
