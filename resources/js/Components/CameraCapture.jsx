import { useRef, useEffect, useState} from 'react';
import { usePage } from '@inertiajs/react';

export default function CameraCapture({ onClose }) {
  const { auth } = usePage().props;
  const userId = auth?.user?.id;
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [toastMessage, setToastMessage] = useState("");
  const [anotacao, setAnotacao] = useState('');
  const [geminiObs, setGeminiObs] = useState('');
  const [amostraRetirada, setAmostraRetirada] = useState(false);
  const [cpf, setCpf] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function startCamera() {
      try {
        const s = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
        if (!mounted) {
          s.getTracks().forEach(t => t.stop());
          return;
        }
        setStream(s);
        if (videoRef.current) videoRef.current.srcObject = s;
      } catch (err) {
        console.error("Erro ao acessar a câmera:", err);
        alert("Não foi possível acessar a câmera.");
      }
    }
    startCamera();

    const onKey = (e) => {
      if (e.key === 'Escape') handleClose();
    };
    window.addEventListener('keydown', onKey);

    return () => {
      mounted = false;
      window.removeEventListener('keydown', onKey);
      stopStream();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, []);

  const stopStream = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    setStream(null);
    if (videoRef.current) videoRef.current.srcObject = null;
  };

  const handleClose = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    setStream(null);
  
    setCapturedBlob(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }

    if (onClose) onClose(null);
  };
  

  const capture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const url = URL.createObjectURL(blob);
      setCapturedBlob(blob);
      setPreviewUrl(url);
    }, 'image/png', 0.95);
  };

  const send = async () => {
    if (!capturedBlob) { showToast("Capture uma imagem primeiro!"); return; }
    if (amostraRetirada && !cpf) { showToast("Informe CPF!"); return; }
  
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('imagem', capturedBlob, `amostra_${Date.now()}.png`);
      formData.append('anotacao', anotacao || '');
      formData.append('gemini_obs', geminiObs || '');
      formData.append('amostra_retirada', amostraRetirada ? '1' : '0');
      formData.append('cpf', cpf || '');
      formData.append('user_id', userId || '');
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
  
      const res = await fetch('/microscopio/upload', {
        method: 'POST',
        body: formData,
        headers: { 'Accept': 'application/json', 'X-CSRF-TOKEN': csrf },
        credentials: 'same-origin'
      });
  
      const payload = await res.json();
  
      if (!res.ok) {
        alert(payload?.message || 'Erro no upload');
        setLoading(false);
        return;
      }
  
      setCapturedBlob(null);
      if (previewUrl) { URL.revokeObjectURL(previewUrl); setPreviewUrl(null); }
      stopStream();
      if (onClose) onClose(payload);
  
    } catch (err) {
      console.error(err);
      alert('Erro ao enviar/processar.');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(""), 5000); 
  };
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-4xl overflow-hidden">
        <div className="flex justify-between items-center px-5 py-3 border-b">
          <h2 className="text-lg font-semibold">Nova Amostra</h2>
          <button onClick={handleClose} className="text-gray-600 hover:text-gray-800">
            ✕
          </button>
        </div>

        <div className="flex flex-col lg:flex-row gap-4 p-5">
          <div className="lg:flex-1 flex flex-col items-center gap-3">
            <div className="bg-black w-full h-96 rounded-md flex items-center justify-center overflow-hidden">
              {!previewUrl ? (
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
              ) : (
                <img src={previewUrl} alt="preview" className="w-full h-full object-cover" />
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={capture}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md"
              >
                Capturar
              </button>
              <button
                onClick={send}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
              >
                {loading ? 'Enviando...' : 'Salvar e Processar'}
              </button>
            </div>
          </div>

          <div className="lg:flex-1 flex flex-col gap-3">
            <label className="text-sm font-medium text-gray-700">Observação</label>
            <input value={anotacao} onChange={(e) => setAnotacao(e.target.value)} className="w-full rounded border px-3 py-2" />
            <label className="text-sm font-medium text-gray-700">Informações adicionais (Gemini)</label>
            <input value={geminiObs} onChange={(e) => setGeminiObs(e.target.value)} className="w-full rounded border px-3 py-2" />
            <label className="flex items-center gap-2 mt-2">
              <input type="checkbox" checked={amostraRetirada} onChange={(e) => setAmostraRetirada(e.target.checked)} className="h-4 w-4" />
              <span className="text-gray-700 text-sm">A amostra já foi retirada</span>
            </label>
            {amostraRetirada && (
              <input value={cpf} onChange={(e) => setCpf(e.target.value)} className="w-full rounded border px-3 py-2" placeholder="CPF do paciente" />
            )}
          </div>
        </div>
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>
    {/* Toast */}
    {toastMessage && (
    <div
        className="fixed top-5 right-5 px-4 py-2 rounded shadow-lg text-white bg-red-500 transition-transform transform"
    >
        {toastMessage}
    </div>
    )}
    </div>
  );
}
