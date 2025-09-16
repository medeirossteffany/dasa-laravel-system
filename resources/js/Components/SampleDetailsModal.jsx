import React from 'react';

/**
 * SampleDetailsModal
 * - mantém todos os campos originais (em grid 2 colunas)
 * - Anotação IA ocupa 2 colunas (mais larga)
 * - Imagem ocupa 2 colunas abaixo (mesma largura da anotação IA)
 * - tenta usar sample.IMAGEM_URL (data URL) ou fallback para /amostras/{id}/imagem
 * - se você usar Ziggy, substitua getImageRoute por route('amostras.imagem', sample.ID_AMOSTRA)
 */

function getImageRoute(id) {
  // Se você tiver Ziggy e helper route disponível no window:
  if (typeof route === 'function') {
    try {
      return route('amostras.imagem', id);
    } catch (e) {
      // fallback
    }
  }
  return `/amostras/${id}/imagem`;
}

export default function SampleDetailsModal({ open, onClose, sample = {} }) {
  if (!open) return null;

  // mantemos os campos exceto ANOTACAO_IA para renderizar separado
  const fields = [
    ['ID Amostra', 'ID_AMOSTRA'],
    ['Data', 'DATA_AMOSTRA'],
    ['Altura', 'ALTURA_AMOSTRA'],
    ['Largura', 'LARGURA_AMOSTRA'],
    ['Espessura', 'ESPESSURA'],
    ['Anotação Médico', 'ANOTACAO_MEDICO_AMOSTRA'],
    ['ID Paciente', 'ID_PACIENTE'],
    ['Paciente', 'NOME_PACIENTE'],
    ['CPF', 'CPF_PACIENTE'],
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
        <div className="max-h-[80vh] overflow-y-auto px-6 py-4">
          <div className="grid gap-4 sm:grid-cols-2">
            {fields.map(([label, key]) => (
              <div key={key} className="space-y-1">
                <div className="text-xs font-medium text-gray-500">{label}</div>
                <div className="whitespace-pre-wrap break-words text-sm text-gray-800 border rounded p-2 bg-gray-50">
                  {sample[key] ?? '—'}
                </div>
              </div>
            ))}

            {/* Anotação IA ocupa as duas colunas e é mais larga */}
            <div className="sm:col-span-2 space-y-1">
              <div className="text-xs font-medium text-gray-500">Anotação IA</div>
              <div className="whitespace-pre-wrap break-words text-sm text-gray-800 border rounded p-3 bg-gray-50 min-h-[4rem]">
                {sample.ANOTACAO_IA_AMOSTRA ?? '—'}
              </div>
            </div>

            {/* Imagem ocupa as duas colunas, mesma largura */}
            <div className="sm:col-span-2 space-y-1">
              <div className="text-xs font-medium text-gray-500">Imagem da amostra</div>

              {imageSrc ? (
                <div className="mt-2 flex justify-center">
                  <img
                    src={imageSrc}
                    alt={`Amostra ${sample.ID_AMOSTRA || ''}`}
                    className="w-full rounded border object-contain"
                    style={{ maxHeight: '520px' }}
                    // adiciona loading lazy para performance
                    loading="lazy"
                  />
                </div>
              ) : (
                <div className="mt-2 text-sm text-gray-600">Nenhuma imagem disponível</div>
              )}
            </div>
          </div>
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
