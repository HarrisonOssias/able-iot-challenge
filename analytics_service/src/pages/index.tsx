import { useEffect, useState } from 'react';
import Link from 'next/link';
import QueryDialog from '../components/QueryDialog';

type Row = Record<string, any>;

async function fetchJson(path: string) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function Table({ rows }: { rows: Row[] }) {
  if (!rows || rows.length === 0) return <div className="text-sm text-gray-500">No data</div>;
  const cols = Object.keys(rows[0]);
  return (
    <div className="overflow-auto border rounded-md">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            {cols.map(c => (
              <th key={c} className="text-left px-3 py-2 font-medium text-gray-700 border-b">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="odd:bg-white even:bg-gray-50">
              {cols.map(c => (
                <td key={c} className="px-3 py-2 border-b align-top">{String(r[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Home() {
  const [avg, setAvg] = useState<Row[]>([]);
  const [exret, setExret] = useState<Row[]>([]);
  const [battery, setBattery] = useState<Row[]>([]);
  const [height, setHeight] = useState<Row[]>([]);
  const [open, setOpen] = useState(false);

  async function loadAll() {
    setAvg(await fetchJson('/api/metrics/avg-extension-mm'));
    setExret(await fetchJson('/api/metrics/extension-vs-retraction'));
    setBattery(await fetchJson('/api/metrics/battery-summary'));
    setHeight(await fetchJson('/api/metrics/platform-height'));
  }

  useEffect(() => { loadAll(); const t = setInterval(loadAll, 3000); return () => clearInterval(t); }, []);

  return (
    <div className="font-sans p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Able Analytics</h1>
        <div className="space-x-3">
          <Link href="/docs" className="underline">Documentation</Link>
          <button onClick={() => setOpen(true)} className="rounded-md bg-indigo-600 px-3 py-1.5 text-white">Run example query</button>
        </div>
      </div>
      <p className="mt-2 text-gray-700">This service is read-only and separate from ingest. It queries Postgres via Next.js API routes.</p>
      <div className="grid gap-4 mt-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))' }}>
        <section><h3>Avg Extension (mm)</h3><Table rows={avg} /></section>
        <section><h3>Extensions vs Retractions</h3><Table rows={exret} /></section>
        <section><h3>Battery Summary</h3><Table rows={battery} /></section>
        <section><h3>Platform Height</h3><Table rows={height} /></section>
      </div>
      <QueryDialog open={open} onClose={() => setOpen(false)} />
    </div>
  );
}


