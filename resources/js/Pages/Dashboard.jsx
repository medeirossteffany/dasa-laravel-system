import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';
import PatientsSamplesTable from '@/Components/PatientsSamplesTable';
import { Head, router } from '@inertiajs/react';

export default function Dashboard({ items = [] }) {

  function handleNewSample() {
    router.visit(route('amostras.create'));
  }

  return (
    <AuthenticatedLayout
      header={<h2 className="text-xl font-semibold leading-tight text-gray-800">Pacientes</h2>}
    >
      <Head title="Dashboard" />
      <div className="py-8">
        <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
          <div className="overflow-hidden bg-white shadow sm:rounded-xl">
            <PatientsSamplesTable rows={items} onNewSample={handleNewSample} />
          </div>
        </div>
      </div>
    </AuthenticatedLayout>
  );
}
