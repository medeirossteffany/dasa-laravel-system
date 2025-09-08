<?php

namespace App\Http\Controllers;

use App\Http\Requests\ProfileUpdateRequest;
use Illuminate\Contracts\Auth\MustVerifyEmail;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Redirect;
use Inertia\Inertia;
use Inertia\Response;
use App\Models\Cargo;  
use Illuminate\Support\Facades\DB;


class ProfileController extends Controller
{
    /**
     * Display the user's profile form.
     */
    public function edit(Request $request)
    {
        $cargos = Cargo::select('ID_CARGO','TITULO_CARGO')->orderBy('ID_CARGO')->get();
        return inertia('Profile/Edit', [
            'mustVerifyEmail' => false,
            'status' => session('status'),
            'cargos' => $cargos,
        ]);
    }

    /**
     * Update the user's profile information.
     */
    public function update(Request $request)
    {
        /** @var Usuario $user */
        $user = $request->user(); // seu guard pode ser diferente; ajuste se usar outro model

        $data = $request->validate([
            'name'            => ['required','string','max:255'],
            'email'           => ['required','email','max:255'],
            'cargo_id'        => ['required','integer','in:1,2,3'], // 1=MEDICO,2=BIOMEDICO,3=ENFERMEIRO
            'license_number'  => ['required','string','max:100'],
            'license_state'   => ['required','string','size:2'],    // UF
        ]);

        DB::transaction(function () use ($user, $data) {
            // Atualiza dados do usuário
            $user->NOME_USUARIO       = $data['name'];
            $user->EMAIL_USUARIO      = $data['email'];
            $user->CARGO_ID_CARGO     = $data['cargo_id'];
            $user->save();

            // Sincroniza a tabela específica do cargo
            switch ((int)$data['cargo_id']) {
                case 1: // MEDICO
                    DB::table('MEDICO')->updateOrInsert(
                        ['USUARIO_ID_USUARIO' => $user->ID_USUARIO],
                        [
                            'NUMERO_CRM_MEDICO'  => $data['license_number'],
                            'ESTADO_CRM_MEDICO'  => strtoupper($data['license_state']),
                        ]
                    );
                    // opcional: limpar outras tabelas para esse usuário
                    DB::table('BIOMEDICO')->where('USUARIO_ID_USUARIO',$user->ID_USUARIO)->delete();
                    DB::table('ENFERMEIRO')->where('USUARIO_ID_USUARIO',$user->ID_USUARIO)->delete();
                    break;

                case 2: // BIOMEDICO
                    DB::table('BIOMEDICO')->updateOrInsert(
                        ['USUARIO_ID_USUARIO' => $user->ID_USUARIO],
                        [
                            'NUMERO_CRBM_BIOMEDICO' => $data['license_number'],
                            'ESTADO_CRBM_BIOMEDICO' => strtoupper($data['license_state']),
                        ]
                    );
                    DB::table('MEDICO')->where('USUARIO_ID_USUARIO',$user->ID_USUARIO)->delete();
                    DB::table('ENFERMEIRO')->where('USUARIO_ID_USUARIO',$user->ID_USUARIO)->delete();
                    break;

                case 3: // ENFERMEIRO
                    DB::table('ENFERMEIRO')->updateOrInsert(
                        ['USUARIO_ID_USUARIO' => $user->ID_USUARIO],
                        [
                            'NUMERO_COREN_ENFERMEIRO' => $data['license_number'],
                            'ESTADO_COREN_ENFERMEIRO' => strtoupper($data['license_state']),
                        ]
                    );
                    DB::table('MEDICO')->where('USUARIO_ID_USUARIO',$user->ID_USUARIO)->delete();
                    DB::table('BIOMEDICO')->where('USUARIO_ID_USUARIO',$user->ID_USUARIO)->delete();
                    break;
            }
        });

        return back()->with('status','profile-updated');
    }

    /**
     * Delete the user's account.
     */
    public function destroy(Request $request): RedirectResponse
    {
        $request->validate([
            'password' => ['required', 'current_password'],
        ]);

        $user = $request->user();

        Auth::logout();

        $user->delete();

        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return Redirect::to('/');
    }
}
