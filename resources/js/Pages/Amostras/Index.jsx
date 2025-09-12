import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';
import { Head } from '@inertiajs/react';
import SamplesTable from '@/Components/SamplesTable';

export default function AmostrasIndex({ items = [] }) {
  return (
    <AuthenticatedLayout
      header={<h2 className="text-xl font-semibold leading-tight text-gray-800">Amostras</h2>}
    >
      <Head title="Amostras" />
      <div className="py-8">
        <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
          <div className="overflow-hidden bg-white shadow sm:rounded-xl">
            <SamplesTable rows={items} />
          </div>
        </div>
      </div>
    </AuthenticatedLayout>
  );
}
