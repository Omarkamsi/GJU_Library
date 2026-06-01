export default function About() {
  return (
    <main className="p-8 max-w-3xl">
      <h1 className="text-3xl font-bold">About HydroLoop</h1>
      <p className="mt-4 text-slate-300">
        HydroLoop turns water and energy usage at GJU into a measurable, public,
        data-driven system. Funded by the IEEE Region 8 Sustainable Universities
        Program 2026.
      </p>
      <p className="mt-4 text-slate-300">
        Hardware: ESP32 + PZEM-004T + JSN-SR04T + BME280 + Hall-effect flow sensors.
        Software: FastAPI, TimescaleDB, Mosquitto, Next.js. All open-source on
        <a className="text-water mx-1" href="https://github.com/">GitHub</a>.
      </p>
    </main>
  );
}
