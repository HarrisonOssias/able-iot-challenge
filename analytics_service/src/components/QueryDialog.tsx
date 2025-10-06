import { Fragment, useState } from 'react';
import { Dialog, Transition, Listbox } from '@headlessui/react';
import { ChevronUpDownIcon } from '@heroicons/react/24/outline';

type Option = { key: string; name: string; description: string };

const OPTIONS: Option[] = [
  { key: 'counts_by_type', name: 'Counts by type', description: 'Legacy vs New counts' },
  { key: 'devices_both_formats', name: 'Devices with both formats', description: 'Devices that reported both mm and ticks' },
  { key: 'unified_recent', name: 'Unified recent values', description: 'Recent rows with ticks→mm conversion' },
  { key: 'side_switches', name: 'Left↔Right switches', description: 'Counts of sign switches per device' },
];

export default function QueryDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [selected, setSelected] = useState<Option>(OPTIONS[0]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ sql: string; rows: any[] } | null>(null);

  async function run() {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`/api/examples/run?key=${encodeURIComponent(selected.key)}`);
      const data = await res.json();
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200" enterFrom="opacity-0" enterTo="opacity-100"
          leave="ease-in duration-150" leaveFrom="opacity-100" leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/30" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-200" enterFrom="opacity-0 translate-y-2" enterTo="opacity-100 translate-y-0"
              leave="ease-in duration-150" leaveFrom="opacity-100 translate-y-0" leaveTo="opacity-0 translate-y-2"
            >
              <Dialog.Panel className="w-full max-w-3xl transform rounded-lg bg-white p-6 shadow-xl ring-1 ring-gray-200">
                <Dialog.Title className="text-lg font-semibold mb-4">Run Example Query</Dialog.Title>
                <div className="space-y-4">
                  <Listbox value={selected} onChange={setSelected}>
                    <div className="relative">
                      <Listbox.Button className="relative w-full cursor-pointer rounded-md border border-gray-300 bg-white py-2 pl-3 pr-10 text-left shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500">
                        <span className="block truncate">{selected.name}</span>
                        <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                          <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                        </span>
                      </Listbox.Button>
                      <Transition as={Fragment} leave="transition ease-in duration-100" leaveFrom="opacity-100" leaveTo="opacity-0">
                        <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                          {OPTIONS.map(o => (
                            <Listbox.Option key={o.key} value={o} className={({ active }) => `relative cursor-pointer select-none py-2 pl-3 pr-4 ${active ? 'bg-indigo-50' : ''}`}>
                              <div>
                                <div className="font-medium">{o.name}</div>
                                <div className="text-xs text-gray-500">{o.description}</div>
                              </div>
                            </Listbox.Option>
                          ))}
                        </Listbox.Options>
                      </Transition>
                    </div>
                  </Listbox>

                  <div className="flex gap-2">
                    <button onClick={run} disabled={loading} className="rounded-md bg-indigo-600 px-4 py-2 text-white disabled:opacity-50">{loading ? 'Running…' : 'Run'}</button>
                    <button onClick={onClose} className="rounded-md border px-4 py-2">Close</button>
                  </div>

                  {result && (
                    <div className="mt-4 space-y-3">
                      <div>
                        <div className="text-sm font-semibold mb-1">SQL</div>
                        <pre className="whitespace-pre-wrap rounded-md bg-gray-50 p-2 text-sm border overflow-x-auto">
{result.sql}
                        </pre>
                      </div>
                      <div>
                        <div className="text-sm font-semibold mb-1">Results</div>
                        <div className="overflow-auto border rounded-md">
                          <table className="min-w-full text-sm">
                            <tbody>
                              {result.rows && result.rows.length > 0 ? (
                                result.rows.map((row, idx) => (
                                  <tr key={idx} className="odd:bg-white even:bg-gray-50">
                                    <td className="p-2 align-top">
                                      <pre className="whitespace-pre-wrap">{JSON.stringify(row, null, 2)}</pre>
                                    </td>
                                  </tr>
                                ))
                              ) : (
                                <tr><td className="p-2">No rows</td></tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
}


