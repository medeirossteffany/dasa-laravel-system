// resources/js/Components/PatientsSamplesTable.jsx
import { router } from '@inertiajs/react';
import { useMemo, useState } from 'react';

function classNames(...c) { return c.filter(Boolean).join(' ') }

function formatDate(d) {
  if (!d) return '';
  // aceita 'YYYY-MM-DD' ou Date
  const date = typeof d === 'string' ? new Date(d) : d;
  if (Number.isNaN(date.getTime())) return d;
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' }).format(date);
}

function normalize(str = '') {
  return String(str).toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '');
}

export default function PatientsSamplesTable({ rows = [], onNewSample }) {
  // rows esperado: [{ ID_PACIENTE, NOME_PACIENTE, CPF_PACIENTE, ID_AMOSTRA, DATA_AMOSTRA, ALTURA_AMOSTRA, LARGURA_AMOSTRA, ESPESSURA, ANOTACAO_MEDICO_AMOSTRA, ANOTACAO_IA_AMOSTRA }]
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState({ key: 'DATA_AMOSTRA', dir: 'desc' });
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const headers = [
    { key: 'NOME_PACIENTE', label: 'Paciente' },
    { key: 'CPF_PACIENTE', label: 'CPF' },
    { key: 'DATA_AMOSTRA', label: 'Data' },
    { key: 'ALTURA_AMOSTRA', label: 'Altura' },
    { key: 'LARGURA_AMOSTRA', label: 'Largura' },
    { key: 'ESPESSURA', label: 'Espessura' },
    { key: 'ANOTACAO_MEDICO_AMOSTRA', label: 'Anotação Médico' },
    { key: 'ANOTACAO_IA_AMOSTRA', label: 'Anotação IA' },
    { key: 'DETALHES', label: 'Detalhes' },
  ];

  function toggleSort(key) {
    setPage(1);
    setSort((s) => s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' });
  }

  const filtered = useMemo(() => {
    if (!query) return rows;
    const q = normalize(query);
    return rows.filter(r =>
      normalize(r.NOME_PACIENTE).includes(q) ||
      String(r.CPF_PACIENTE || '').includes(query) ||
      normalize(r.ANOTACAO_MEDICO_AMOSTRA || '').includes(q) ||
      normalize(r.ANOTACAO_IA_AMOSTRA || '').includes(q)
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

      // tenta data/número, senão string
      const na = Number(va); const nb = Number(vb);
      if (!Number.isNaN(na) && !Number.isNaN(nb)) return dir === 'asc' ? na - nb : nb - na;

      const da = new Date(va); const db = new Date(vb);
      if (!Number.isNaN(da) && !Number.isNaN(db)) return dir === 'asc' ? da - db : db - da;

      return dir === 'asc'
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });
    return copy;
  }, [filtered, sort]);

  const total = sorted.length;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const visible = sorted.slice((page - 1) * pageSize, page * pageSize);

  function exportCSV() {
    const cols = ['Paciente','CPF','Data','Altura','Largura','Espessura','Anotação Médico','Anotação IA'];
    const lines = [cols.join(';')];
    sorted.forEach(r => {
      const line = [
        r.NOME_PACIENTE ?? '',
        r.CPF_PACIENTE ?? '',
        formatDate(r.DATA_AMOSTRA),
        r.ALTURA_AMOSTRA ?? '',
        r.LARGURA_AMOSTRA ?? '',
        r.ESPESSURA ?? '',
        (r.ANOTACAO_MEDICO_AMOSTRA ?? '').replace(/[\r\n]+/g,' '),
        (r.ANOTACAO_IA_AMOSTRA ?? '').replace(/[\r\n]+/g,' '),
      ].map(v => `"${String(v).replace(/"/g,'""')}"`).join(';');
      lines.push(line);
    });
    const blob = new Blob([`\ufeff${lines.join('\n')}`], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `pacientes_amostras_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-2"> 
        <button
          type="button"
          onClick={() => router.post(route('microscopio.run'))}
          className="rounded-lg bg-blue-600 px-4 py-2 text-white shadow hover:bg-blue-700"
        >
          + Nova amostra
        </button>
          <button
            type="button"
            onClick={exportCSV}
            className="rounded-lg border px-4 py-2 text-gray-700 hover:bg-gray-50"
          >
            Exportar Excel
          </button>
        </div>

        <div className="relative">
          <input
            type="text"
            placeholder="Pesquisar"
            value={query}
            onChange={(e) => { setPage(1); setQuery(e.target.value); }}
            className="w-50 rounded-lg border px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {headers.map(h => (
                <th key={h.key}
                    onClick={() => toggleSort(h.key)}
                    className="cursor-pointer px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600">
                  <div className="flex items-center gap-1">
                    {h.label}
                    {sort.key === h.key && (
                      <span className="text-gray-400">{sort.dir === 'asc' ? '▲' : '▼'}</span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {visible.length === 0 && (
              <tr>
                <td colSpan={headers.length} className="px-4 py-6 text-center text-sm text-gray-500">
                  Nenhum registro encontrado.
                </td>
              </tr>
            )}

            {visible.map((r) => (
              <tr key={`${r.ID_AMOSTRA ?? 'p'}-${r.ID_PACIENTE}`}>
                <td className="px-4 py-3">{r.NOME_PACIENTE}</td>
                <td className="px-4 py-3">{r.CPF_PACIENTE}</td>
                <td className="px-4 py-3">{formatDate(r.DATA_AMOSTRA)}</td>
                <td className="px-4 py-3">{r.ALTURA_AMOSTRA}</td>
                <td className="px-4 py-3">{r.LARGURA_AMOSTRA}</td>
                <td className="px-4 py-3">{r.ESPESSURA}</td>
                <td className="px-4 py-3 max-w-[28rem] truncate" title={r.ANOTACAO_MEDICO_AMOSTRA || ''}>
                  {r.ANOTACAO_MEDICO_AMOSTRA}
                </td>
                <td className="px-4 py-3 max-w-[28rem] truncate" title={r.ANOTACAO_IA_AMOSTRA || ''}>
                  {r.ANOTACAO_IA_AMOSTRA}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* paginação simples */}
      <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
        <span>Total: {total}</span>
        <div className="flex items-center gap-2">
          <button
            className={classNames("rounded-md border px-3 py-1", page === 1 && "opacity-50")}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Anterior
          </button>
          <span>Página {page} de {pages}</span>
          <button
            className={classNames("rounded-md border px-3 py-1", page === pages && "opacity-50")}
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
            disabled={page === pages}
          >
            Próxima
          </button>
        </div>
      </div>
    </div>
  );
}
