import { useMemo, useState } from 'react';
import { router } from '@inertiajs/react';
import NewPatientModal from './NewPatientModal';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

function classNames(...c) { return c.filter(Boolean).join(' ') }

function formatDate(d) {
  if (!d) return '';
  const date = typeof d === 'string' ? new Date(d) : d;
  if (Number.isNaN(date.getTime())) return d;
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' }).format(date);
}

export default function PatientsTable({ rows = [], onPatientCreated }) {
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState({ key: 'NOME_PACIENTE', dir: 'asc' });
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [newPatientOpen, setNewPatientOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState("");

  const headers = [
    { key: 'NOME_PACIENTE', label: 'Nome' },
    { key: 'CPF_PACIENTE', label: 'CPF' },
    { key: 'DATA_NASC_PACIENTE', label: 'Nascimento' },
    { key: 'ENDERECO', label: 'Endereço' },
    { key: 'SEXO', label: 'Sexo' },
  ];

  function toggleSort(key) {
    setPage(1);
    setSort((s) => s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' });
  }

  const filtered = useMemo(() => {
    if (!query) return rows;
    const q = query.toLowerCase();
    return rows.filter(r =>
      (r.NOME_PACIENTE || '').toLowerCase().includes(q) ||
      (r.CPF_PACIENTE || '').includes(q)
    );
  }, [rows, query]);

  const sorted = useMemo(() => {
    const { key, dir } = sort;
    const copy = [...filtered];
    copy.sort((a, b) => {
      const va = a[key]; const vb = b[key];
      if (va == null && vb == null) return 0;
      if (va == null) return dir === 'asc' ? -1 : 1;
      if (vb == null) return dir === 'asc' ? 1 : -1;

      if (key.includes('DATA')) {
        const da = new Date(va); const db = new Date(vb);
        return dir === 'asc' ? da - db : db - da;
      }

      return dir === 'asc'
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });
    return copy;
  }, [filtered, sort]);

  const total = sorted.length;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const visible = sorted.slice((page - 1) * pageSize, page * pageSize);

  const exportExcel = () => {
    const wsData = [
      headers.map(h => h.label),
      ...sorted.map(r => headers.map(h => h.key.includes('DATA') ? formatDate(r[h.key]) : r[h.key] ?? ''))
    ];
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(wsData);
    XLSX.utils.book_append_sheet(wb, ws, 'Pacientes');
    const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    saveAs(new Blob([wbout], { type: 'application/octet-stream' }), `pacientes_${new Date().toISOString().slice(0,10)}.xlsx`);
  };

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(""), 5000);
  };

  return (
    <div className="p-6">
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex gap-2">
          <button onClick={() => setNewPatientOpen(true)} className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
            + Novo Paciente
          </button>
          <button onClick={exportExcel} className="rounded-lg border px-4 py-2 text-gray-700 hover:bg-gray-50">
            Exportar Excel
          </button>
        </div>

        <input type="text" placeholder="Pesquisar" value={query} onChange={e => { setPage(1); setQuery(e.target.value); }}
          className="w-50 rounded-lg border px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="overflow-x-auto rounded-xl border">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {headers.map(h => (
                <th key={h.key} onClick={() => toggleSort(h.key)}
                    className="cursor-pointer px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">
                  <div className="flex items-center gap-1">
                    {h.label}
                    {sort.key === h.key && <span className="text-gray-400">{sort.dir === 'asc' ? '▲' : '▼'}</span>}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {visible.length === 0 && (
              <tr><td colSpan={headers.length} className="px-4 py-6 text-center text-sm text-gray-500">Nenhum registro</td></tr>
            )}
            {visible.map(r => (
              <tr key={r.ID_PACIENTE}>
                <td className="px-4 py-3">{r.NOME_PACIENTE}</td>
                <td className="px-4 py-3">{r.CPF_PACIENTE}</td>
                <td className="px-4 py-3">{formatDate(r.DATA_NASC_PACIENTE)}</td>
                <td className="px-4 py-3">{r.ENDERECO}</td>
                <td className="px-4 py-3">{r.SEXO}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
        <span>Total: {total}</span>
        <div className="flex items-center gap-2">
          <button className={classNames("rounded-md border px-3 py-1", page === 1 && "opacity-50")} onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Anterior</button>
          <span>Página {page} de {pages}</span>
          <button className={classNames("rounded-md border px-3 py-1", page === pages && "opacity-50")} onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages}>Próxima</button>
        </div>
      </div>

      <NewPatientModal
        open={newPatientOpen}
        onClose={() => setNewPatientOpen(false)}
        onCreated={(p) => { showToast('Paciente criado com sucesso!'); if (onPatientCreated) onPatientCreated(p); }}
      />

      {toastMessage && (
        <div className="fixed top-5 right-5 bg-green-500 text-white px-4 py-2 rounded shadow-lg">{toastMessage}</div>
      )}
    </div>
  );
}
