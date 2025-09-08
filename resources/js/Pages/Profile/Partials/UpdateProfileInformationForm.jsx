import InputError from '@/Components/InputError';
import InputLabel from '@/Components/InputLabel';
import PrimaryButton from '@/Components/PrimaryButton';
import TextInput from '@/Components/TextInput';
import { Transition } from '@headlessui/react';
import { Link, useForm, usePage } from '@inertiajs/react';

const cargoLabel = (id) => {
  switch (Number(id)) {
    case 1: return 'CRM';
    case 2: return 'CRBM';
    case 3: return 'COREN';
    default: return 'Registro';
  }
};

export default function UpdateProfileInformation({ mustVerifyEmail, status, className = '' }) {
  const { auth, cargos } = usePage().props;
  const user = auth.user;

  const { data, setData, patch, errors, processing, recentlySuccessful } = useForm({
    name: user.name ?? user.NOME_USUARIO,
    email: user.email ?? user.EMAIL_USUARIO,
    cargo_id: user.CARGO_ID_CARGO ?? '',  // se já existir
    license_number: '',
    license_state: '',
  });

  const submit = (e) => {
    e.preventDefault();
    patch(route('profile.update'), { preserveScroll: true });
  };

  return (
    <section className={className}>
      <header>
        <h2 className="text-lg font-medium text-gray-900">Profile Information</h2>
        <p className="mt-1 text-sm text-gray-600">Atualize seus dados e seu registro profissional.</p>
      </header>

      <form onSubmit={submit} className="mt-6 space-y-6">
        {/* Nome */}
        <div>
          <InputLabel htmlFor="name" value="Nome" />
          <TextInput id="name" className="mt-1 block w-full"
            value={data.name} onChange={(e) => setData('name', e.target.value)} required autoComplete="name" />
          <InputError className="mt-2" message={errors.name} />
        </div>

        {/* Email */}
        <div>
          <InputLabel htmlFor="email" value="Email" />
          <TextInput id="email" type="email" className="mt-1 block w-full"
            value={data.email} onChange={(e) => setData('email', e.target.value)} required autoComplete="username" />
          <InputError className="mt-2" message={errors.email} />
        </div>

        {/* Cargo */}
        <div>
          <InputLabel htmlFor="cargo_id" value="Cargo" />
          <select
            id="cargo_id"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            value={data.cargo_id}
            onChange={(e) => setData('cargo_id', e.target.value)}
            required
          >
            <option value="" disabled>Selecione um cargo</option>
            {cargos?.map(c => (
              <option key={c.ID_CARGO} value={c.ID_CARGO}>{c.TITULO_CARGO}</option>
            ))}
          </select>
          <InputError className="mt-2" message={errors.cargo_id} />
        </div>

        {/* Número do registro (CRM/CRBM/COREN) */}
        <div>
          <InputLabel htmlFor="license_number" value={`${cargoLabel(data.cargo_id)} - Número`} />
          <TextInput
            id="license_number"
            className="mt-1 block w-full"
            value={data.license_number}
            onChange={(e) => setData('license_number', e.target.value)}
            required
            placeholder={`Ex: 123456`}
          />
          <InputError className="mt-2" message={errors.license_number} />
        </div>

        {/* UF do registro */}
        <div>
          <InputLabel htmlFor="license_state" value="UF do registro" />
          <TextInput
            id="license_state"
            className="mt-1 block w-24 uppercase"
            value={data.license_state}
            onChange={(e) => setData('license_state', e.target.value.toUpperCase())}
            required
            maxLength={2}
            placeholder="SP"
          />
          <InputError className="mt-2" message={errors.license_state} />
        </div>

        {/* Verificação de email (sem mudanças) */}
        {mustVerifyEmail && user.email_verified_at === null && (
          <div>
            <p className="mt-2 text-sm text-gray-800">
              Seu email não está verificado.
              <Link href={route('verification.send')} method="post" as="button"
                className="rounded-md text-sm text-gray-600 underline hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
                Reenviar verificação.
              </Link>
            </p>
            {status === 'verification-link-sent' && (
              <div className="mt-2 text-sm font-medium text-green-600">
                Um novo link de verificação foi enviado.
              </div>
            )}
          </div>
        )}

        <div className="flex items-center gap-4">
          <PrimaryButton disabled={processing}>Salvar</PrimaryButton>
          <Transition show={recentlySuccessful} enter="transition ease-in-out" enterFrom="opacity-0" leave="transition ease-in-out" leaveTo="opacity-0">
            <p className="text-sm text-gray-600">Salvo.</p>
          </Transition>
        </div>
      </form>
    </section>
  );
}
