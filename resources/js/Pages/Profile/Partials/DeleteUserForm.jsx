import DangerButton from '@/Components/DangerButton';
import InputError from '@/Components/InputError';
import InputLabel from '@/Components/InputLabel';
import Modal from '@/Components/Modal';
import SecondaryButton from '@/Components/SecondaryButton';
import TextInput from '@/Components/TextInput';
import { useForm } from '@inertiajs/react';
import { useRef, useState } from 'react';

export default function DeleteUserForm({ className = '' }) {
    const [confirmandoExclusao, setConfirmandoExclusao] = useState(false);
    const passwordInput = useRef();

    const {
        data,
        setData,
        delete: destroy,
        processing,
        reset,
        errors,
        clearErrors,
    } = useForm({
        password: '',
    });

    const confirmarExclusao = () => {
        setConfirmandoExclusao(true);
    };

    const excluirUsuario = (e) => {
        e.preventDefault();

        destroy(route('profile.destroy'), {
            preserveScroll: true,
            onSuccess: () => fecharModal(),
            onError: () => passwordInput.current.focus(),
            onFinish: () => reset(),
        });
    };

    const fecharModal = () => {
        setConfirmandoExclusao(false);

        clearErrors();
        reset();
    };

    return (
        <section className={`space-y-6 ${className}`}>
            <header>
                <h2 className="text-lg font-medium text-gray-900">
                    Excluir Conta
                </h2>

                <p className="mt-1 text-sm text-gray-600">
                    Uma vez excluída, todos os recursos e dados da sua conta serão permanentemente apagados. 
                    Antes de excluir sua conta, baixe quaisquer dados ou informações que deseja manter.
                </p>
            </header>

            <DangerButton onClick={confirmarExclusao}>
                Excluir Conta
            </DangerButton>

            <Modal show={confirmandoExclusao} onClose={fecharModal}>
                <form onSubmit={excluirUsuario} className="p-6">
                    <h2 className="text-lg font-medium text-gray-900">
                        Tem certeza de que deseja excluir sua conta?
                    </h2>

                    <p className="mt-1 text-sm text-gray-600">
                        Uma vez excluída, todos os recursos e dados da sua conta serão permanentemente apagados. 
                        Por favor, digite sua senha para confirmar que deseja excluir sua conta.
                    </p>

                    <div className="mt-6">
                        <InputLabel
                            htmlFor="password"
                            value="Senha"
                            className="sr-only"
                        />

                        <TextInput
                            id="password"
                            type="password"
                            name="password"
                            ref={passwordInput}
                            value={data.password}
                            onChange={(e) =>
                                setData('password', e.target.value)
                            }
                            className="mt-1 block w-3/4"
                            isFocused
                            placeholder="Senha"
                        />

                        <InputError
                            message={errors.password}
                            className="mt-2"
                        />
                    </div>

                    <div className="mt-6 flex justify-end">
                        <SecondaryButton onClick={fecharModal}>
                            Cancelar
                        </SecondaryButton>

                        <DangerButton className="ms-3" disabled={processing}>
                            Excluir Conta
                        </DangerButton>
                    </div>
                </form>
            </Modal>
        </section>
    );
}
