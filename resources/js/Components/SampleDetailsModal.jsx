import React from 'react';

/**
 * SampleDetailsModal organizado em:
 *  - Seção: Informações do Paciente (somente campos do paciente)
 *  - Seção: Informações da Amostra (campos da amostra, anotação IA em largura total, imagem em largura total)
 *
 * Usa getImageRoute fallback para /amostras/{id}/imagem (substitua por Ziggy route() se usar).
 */

function getImageRoute(id) {
  if (typeof route === 'function') {
    try {
      return route('amostras.imagem', id);
    } catch (e) {}
  }
  return `/amostras/${id}/imagem`;
}

export default function SampleDetailsModal({ open, onClose, sample = {} }) {
  if (!open) return null;

  const patientFields = [
    ['ID Paciente', 'ID_PACIENTE'],
    ['Paciente', 'NOME_PACIENTE'],
    ['CPF', 'CPF_PACIENTE'],
  ];

  const sampleFields = [
    ['ID Amostra', 'ID_AMOSTRA'],
    ['Data', 'DATA_AMOSTRA'],
    ['Altura', 'ALTURA_AMOSTRA'],
    ['Largura', 'LARGURA_AMOSTRA'],
    ['Espessura', 'ESPESSURA'],
    ['Anotação Médico', 'ANOTACAO_MEDICO_AMOSTRA'],
  ];

  const imageSrc = sample.IMAGEM_URL
    ? sample.IMAGEM_URL
    : (sample.ID_AMOSTRA ? getImageRoute(sample.ID_AMOSTRA) : null);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="relative z-10 w-full max-w-4xl rounded-lg bg-white shadow-lg">
        {/* Cabeçalho fixo */}
        <div className="flex items-center justify-between border-b px-6 py-3">
          <h3 className="text-lg font-semibold">Detalhes da Amostra</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
            title="Fechar"
          >
            ✕
          </button>
        </div>

        {/* Conteúdo rolável */}
        <div className="max-h-[80vh] overflow-y-auto px-6 py-4 space-y-6">
          {/* Seção: Informações do Paciente */}
          <section>
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-700">Informações do Paciente</h4>
            </div>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              {patientFields.map(([label, key]) => (
                <div key={key} className="space-y-1">
                  <div className="text-xs font-medium text-gray-500">{label}</div>
                  <div className="text-sm text-gray-800 border rounded p-2 bg-gray-50 whitespace-pre-wrap break-words">
                    {sample[key] ?? '—'}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <hr className="border-gray-100" />

          {/* Seção: Informações da Amostra */}
          <section>
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-700">Informações da Amostra</h4>
            </div>

            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              {sampleFields.map(([label, key]) => (
                <div key={key} className="space-y-1">
                  <div className="text-xs font-medium text-gray-500">{label}</div>
                  <div className="text-sm text-gray-800 border rounded p-2 bg-gray-50 whitespace-pre-wrap break-words">
                    {sample[key] ?? '—'}
                  </div>
                </div>
              ))}

              {/* Anotação IA em largura total */}
              <div className="sm:col-span-2 space-y-1">
                <div className="text-xs font-medium text-gray-500">Anotação IA</div>
                <div className="text-sm text-gray-800 border rounded p-3 bg-gray-50 whitespace-pre-wrap break-words min-h-[4rem]">
                  {sample.ANOTACAO_IA_AMOSTRA ?? '—'}
                </div>
              </div>

              {/* Imagem em largura total, abaixo da anotação IA */}
              <div className="sm:col-span-2 space-y-1">
                <div className="text-xs font-medium text-gray-500">Imagem da amostra</div>
                {imageSrc ? (
                  <div className="mt-2 flex justify-center">
                    <img
                      src={imageSrc}
                      alt={`Amostra ${sample.ID_AMOSTRA || ''}`}
                      className="w-full rounded border object-contain"
                      style={{ maxHeight: '520px' }}
                      loading="lazy"
                    />
                  </div>
                ) : (
                  <div className="mt-2 text-sm text-gray-600">Nenhuma imagem disponível</div>
                )}
              </div>
            </div>
          </section>
        </div>

        {/* Rodapé fixo */}
        <div className="flex justify-end border-t px-6 py-3">
          <button
            onClick={onClose}
            className="rounded bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
