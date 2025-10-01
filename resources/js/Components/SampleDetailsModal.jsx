import React, { useRef, useEffect, useState } from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

function getImageRoute(id) {
  if (typeof route === 'function') {
    try {
      return route('amostras.imagem', id);
    } catch (e) {}
  }
  return `/amostras/${id}/imagem`;
}

export default function SampleDetailsModal({ open, onClose, sample = {} }) {
  const modalRef = useRef(null);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const [lines, setLines] = useState([]);
  const [currentLine, setCurrentLine] = useState(null);
    useEffect(() => {
    if (canvasRef.current && imageRef.current) {
      canvasRef.current.width = imageRef.current.width;
      canvasRef.current.height = imageRef.current.height;
      drawLines(lines);
    }
  }, [lines, imageRef.current]);

  if (!open) return null;

  const patientFields = [
    ['ID Paciente', 'ID_PACIENTE'],
    ['Paciente', 'NOME_PACIENTE'],
    ['CPF', 'CPF_PACIENTE'],
    ['DATA NASCIMENTO', 'DATA_NASC_PACIENTE'],
  ];

  const sampleFields = [
    ['ID Amostra', 'ID_AMOSTRA'],
    ['Data', 'DATA_AMOSTRA'],
    ['Altura', 'ALTURA_AMOSTRA'],
    ['Largura', 'LARGURA_AMOSTRA'],
    ['Espessura', 'ESPESSURA'],
    ['Profissional', 'NOME_MEDICO'],
    ['Anotação Profissional', 'ANOTACAO_MEDICO_AMOSTRA'],
  ];

  const imageSrc = sample.IMAGEM_URL
    ? sample.IMAGEM_URL
    : (sample.ID_AMOSTRA ? getImageRoute(sample.ID_AMOSTRA) : null);

  // ------------------- Funções do Canvas -------------------
  const startLine = (e) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setCurrentLine({ x1: x, y1: y, x2: x, y2: y });
  };

  const updateLine = (e) => {
    if (!currentLine || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setCurrentLine({ ...currentLine, x2: x, y2: y });
    drawLines([...lines, { ...currentLine, x2: x, y2: y }]);
  };

  const endLine = () => {
    if (currentLine) {
      setLines([...lines, currentLine]);
      setCurrentLine(null);
    }
  };

  const drawLines = (allLines) => {
    if (!canvasRef.current || !imageRef.current) return;
    const ctx = canvasRef.current.getContext('2d');
    const img = imageRef.current;
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    ctx.drawImage(img, 0, 0, canvasRef.current.width, canvasRef.current.height);

    ctx.strokeStyle = 'yellow';
    ctx.fillStyle = 'yellow';
    ctx.lineWidth = 2;
    ctx.font = '14px Arial';

    allLines.forEach((line) => {
      ctx.beginPath();
      ctx.moveTo(line.x1, line.y1);
      ctx.lineTo(line.x2, line.y2);
      ctx.stroke();

      // extremidades
      ctx.beginPath();
      ctx.arc(line.x1, line.y1, 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(line.x2, line.y2, 4, 0, 2 * Math.PI);
      ctx.fill();

      // distância
      const dx = line.x2 - line.x1;
      const dy = line.y2 - line.y1;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const scale = 1.85/461;
      
      // -------- Aqui você pode calibrar a medição convertendo px para mm/cm
      const calibratedDist = dist * scale; // <- ajuste conforme necessário
      ctx.fillText(calibratedDist.toFixed(2) + ' mm', (line.x1 + line.x2) / 2, (line.y1 + line.y2) / 2 - 5);
    });
  };

  const clearLines = () => {
    setLines([]);
    drawLines([]);
  };


  const exportPDF = async () => {
    if (!modalRef.current) return;
    const canvas = await html2canvas(modalRef.current, { scale: 2 });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pdfWidth = 210;
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
    pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
    pdf.save(`amostra_${sample.ID_AMOSTRA || 'relatorio'}.pdf`);
  };

  const imageOnLoad = () => {
    if (canvasRef.current && imageRef.current) {
      canvasRef.current.width = imageRef.current.width;
      canvasRef.current.height = imageRef.current.height;
      drawLines(lines);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div ref={modalRef} className="relative z-10 w-full max-w-4xl rounded-lg bg-white shadow-lg">
        {/* Cabeçalho fixo */}
        <div className="flex items-center justify-between border-b px-6 py-3">
          <h3 className="text-lg font-semibold">Detalhes da Amostra</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-xl" title="Fechar">✕</button>
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
                  <div className="text-sm text-gray-800 border rounded p-2 bg-gray-50 whitespace-pre-wrap break-words">{sample[key] ?? '—'}</div>
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
                    {sample[key] !== '' && sample[key] != null ? sample[key] : '—'}
                  </div>
                </div>
              ))}

              {/* Anotação IA */}
              <div className="sm:col-span-2 space-y-1">
                <div className="text-xs font-medium text-gray-500">Anotação IA</div>
                <div className="text-sm text-gray-800 border rounded p-3 bg-gray-50 whitespace-pre-wrap break-words min-h-[4rem]">
                  {sample.ANOTACAO_IA_AMOSTRA !== '' && sample.ANOTACAO_IA_AMOSTRA != null ? sample.ANOTACAO_IA_AMOSTRA : '—'}
                </div>
              </div>

              {/* Imagem da Amostra com Canvas para medições */}
              <div className="sm:col-span-2 space-y-1">
                <div className="flex justify-between items-center">
                  <div className="text-xs font-medium text-gray-500">Imagem da amostra</div>
                  <div className="flex gap-2">
                    <button onClick={clearLines} className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">Limpar Medições</button>
                    <button onClick={exportPDF} className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">Exportar PDF</button>
                  </div>
                </div>
                {imageSrc ? (
                  <div className="mt-2 relative flex justify-center">
                    <img ref={imageRef} src={imageSrc} alt={`Amostra ${sample.ID_AMOSTRA || ''}`} className="w-full rounded border object-contain" style={{ maxHeight: '520px' }} onLoad={imageOnLoad}/>
                    <canvas
                      ref={canvasRef}
                      className="absolute top-0 left-0"
                      style={{ width: '100%', height: '100%', cursor: 'crosshair' }}
                      onMouseDown={startLine}
                      onMouseMove={updateLine}
                      onMouseUp={endLine}
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
          <button onClick={onClose} className="rounded bg-gray-200 px-4 py-2 text-sm hover:bg-gray-300">Fechar</button>
        </div>
      </div>
    </div>
  );
}
