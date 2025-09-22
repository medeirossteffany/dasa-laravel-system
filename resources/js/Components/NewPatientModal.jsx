import { useState } from 'react';
import { router } from '@inertiajs/react';

export default function NewPatientModal({ open, onClose, onCreated }) {
  const [nome, setNome] = useState('');
  const [cpf, setCpf] = useState('');
  const [dataNascimento, setDataNascimento] = useState('');
  const [endereco, setEndereco] = useState('');
  const [sexo, setSexo] = useState('O');
  const [errors, setErrors] = useState({});

  if (!open) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrors({});

    const cpfRegex = /^\d{11}$/;
    if (!cpfRegex.test(cpf)) {
      setErrors({ cpf: 'CPF deve ter 11 números sem pontos' });
      return;
    }
    const hoje = new Date().toISOString().split("T")[0]; 
    if (dataNascimento > hoje) {
      setErrors({ data_nascimento: 'Data de nascimento não pode ser futura' });
      return;
    }
    
    router.post('/dashboard', {
      nome,
      cpf,
      data_nascimento: dataNascimento,
      endereco,
      sexo
    }, {
      onSuccess: (page) => {
        if (onCreated) onCreated(page.props.newPatient);
        onClose();
        setNome(''); setCpf(''); setDataNascimento(''); setEndereco(''); setSexo('O');
      },
      onError: (err) => setErrors(err),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
        {/* Header com linha fina */}
        <div className="flex justify-between items-center px-5 py-3 border-b">
          <h2 className="text-lg font-semibold">Novo Paciente</h2>
          <button onClick={onClose} className="text-gray-600 hover:text-gray-800">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 p-5">
          <div>
            <label className="block text-sm font-medium">Nome</label>
            <input
              type="text"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              className="mt-1 w-full rounded border px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.nome && <p className="mt-1 text-sm text-red-500">{errors.nome}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium">CPF (11 dígitos, sem pontos)</label>
            <input
              type="text"
              value={cpf}
              onChange={(e) => setCpf(e.target.value.replace(/\D/g, ''))} // remove não dígitos
              maxLength={11}
              className="mt-1 w-full rounded border px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.cpf && <p className="mt-1 text-sm text-red-500">{errors.cpf}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium">Data de Nascimento</label>
            <input
              type="date"
              value={dataNascimento}
              onChange={(e) => setDataNascimento(e.target.value)}
              className="mt-1 w-full rounded border px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.data_nascimento && <p className="mt-1 text-sm text-red-500">{errors.data_nascimento}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium">Endereço</label>
            <input
              type="text"
              value={endereco}
              onChange={(e) => setEndereco(e.target.value)}
              className="mt-1 w-full rounded border px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.endereco && <p className="mt-1 text-sm text-red-500">{errors.endereco}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium">Sexo</label>
            <select
              value={sexo}
              onChange={(e) => setSexo(e.target.value)}
              className="mt-1 w-full rounded border px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="M">Masculino</option>
              <option value="F">Feminino</option>
              <option value="O">Outro</option>
            </select>
            {errors.sexo && <p className="mt-1 text-sm text-red-500">{errors.sexo}</p>}
          </div>

          <div className="mt-4 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded border px-4 py-2 hover:bg-gray-100">Cancelar</button>
            <button type="submit" className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">Criar</button>
          </div>
        </form>
      </div>
    </div>
  );
}
