import GuestLayout from '@/Layouts/GuestLayout';
import { Head, Link, useForm } from '@inertiajs/react';

export default function VerifyEmail({ status }) {
    const { post, processing } = useForm({});

    const submit = (e) => {
        e.preventDefault();

        post(route('verification.send'));
    };

    return (
        <GuestLayout>
            <Head title="Verificação de E-mail" />

            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
                Obrigado por se cadastrar! Antes de começar, você poderia verificar seu endereço de e-mail 
                clicando no link que acabamos de enviar para você? Se você não recebeu o e-mail, 
                ficaremos felizes em enviar outro.
            </div>

            {status === 'verification-link-sent' && (
                <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                    Um novo link de verificação foi enviado para o endereço de e-mail que você 
                    forneceu durante o cadastro.
                </div>
            )}

            <form onSubmit={submit} className="space-y-6">
                <div className="flex flex-col space-y-4">
                    <button 
                        type="submit"
                        className="w-full inline-flex items-center justify-center px-4 py-3 bg-blue-600 border border-transparent rounded-lg font-medium text-sm text-white uppercase tracking-widest hover:bg-blue-700 focus:bg-blue-700 active:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed" 
                        disabled={processing}
                    >
                        {processing ? 'Enviando...' : 'Reenviar E-mail de Verificação'}
                    </button>

                    <div className="text-center">
                        <Link
                            href={route('logout')}
                            method="post"
                            as="button"
                            className="text-sm text-blue-600 hover:text-blue-700 underline transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                        >
                            Sair
                        </Link>
                    </div>
                </div>
            </form>
        </GuestLayout>
    );
}

