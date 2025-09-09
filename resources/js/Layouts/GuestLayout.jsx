import ApplicationLogo from '@/Components/ApplicationLogo';
import { Link } from '@inertiajs/react';

export default function GuestLayout({ children }) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <Link href="/" className="group">
                        <ApplicationLogo className="h-16 w-16 text-blue-600 transition-transform duration-200 group-hover:scale-105" />
                    </Link>
                </div>
                <h2 className="mt-6 text-center text-2xl font-bold tracking-tight text-gray-900">
                    Bem-vindo de volta
                </h2>
                <p className="mt-2 text-center text-sm text-gray-600">
                    Acesse sua conta para continuar
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white/80 backdrop-blur-sm py-8 px-6 shadow-xl ring-1 ring-gray-900/5 sm:rounded-2xl sm:px-10">
                    {children}
                </div>
            </div>
        </div>
    );
}

