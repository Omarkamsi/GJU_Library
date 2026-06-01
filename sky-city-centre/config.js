// Sky City Centre — Booking System Configuration
// Replace the placeholders below with your actual values from Supabase.
// See SETUP-BOOKING.md for step-by-step instructions.

window.SKY_CITY_CONFIG = {
  // Your Supabase project URL (Settings → API → Project URL)
  SUPABASE_URL: 'https://cxqraanhftwhggwqsooy.supabase.co',

  // Your Supabase anon/public key (Settings → API → anon public key)
  // TODO: paste the 'anon public' key here — it's safe to put in this file
  SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4cXJhYW5oZnR3aGdnd3Fzb295Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU4OTQzODgsImV4cCI6MjA5MTQ3MDM4OH0.0-hqykPy0pvoW2HCGlSuFh77C_E96UuAA5CNks4_b1U',

  // Your Edge Function URL (automatic — matches the project URL above)
  ADMIN_FUNCTION_URL: 'https://cxqraanhftwhggwqsooy.supabase.co/functions/v1/admin-api',

  // Booking configuration
  SLOT_DURATION_MIN: 60,
  OPEN_HOUR: 10,   // first slot at 10:00
  CLOSE_HOUR: 21,  // last slot starts at 20:00 (clinic closes at 21:00)
  BOOKING_DAYS_AHEAD: 14,
};
