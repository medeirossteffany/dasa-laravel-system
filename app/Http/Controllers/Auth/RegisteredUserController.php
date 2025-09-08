<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Auth\Events\Registered;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules;
use Illuminate\Validation\Rule; // <-- importa Rule
use Inertia\Inertia;
use Inertia\Response;

class RegisteredUserController extends Controller
{
    public function create(): Response
    {
        return Inertia::render('Auth/Register');
    }

    public function store(Request $request): RedirectResponse
    {
        $request->validate([
            // continua usando os nomes do form
            'name'     => ['required','string','max:255'],
            'email'    => [
                'required','string','lowercase','email','max:255',
                // unique para TABELA USUARIO e COLUNA EMAIL_USUARIO
                Rule::unique('USUARIO', 'EMAIL_USUARIO'),
            ],
            'password' => ['required','confirmed', Rules\Password::defaults()],
        ]);

        // mapeia campos do form para as colunas reais
        $user = User::create([
            'NOME_USUARIO'  => $request->name,
            'EMAIL_USUARIO' => $request->email,
            'SENHA_USUARIO' => Hash::make($request->password),
            // 'CARGO_ID_CARGO' => $request->cargo_id ?? null, // se tiver
        ]);

        event(new Registered($user));
        Auth::login($user);

        return redirect()->route('dashboard');
    }
}
