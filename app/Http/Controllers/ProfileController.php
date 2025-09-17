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

        $u = $request->user();

        $licenseNumber = null;
        $licenseState  = null;

        switch ((int) $u->CARGO_ID_CARGO) {
            case 1: // MÉDICO
                $row = DB::table('MEDICO')
                    ->select('NUMERO_CRM_MEDICO as num', 'ESTADO_CRM_MEDICO as uf')
                    ->where('USUARIO_ID_USUARIO', $u->ID_USUARIO)
                    ->first();
                break;

            case 2: // BIOMÉDICO
                $row = DB::table('BIOMEDICO')
                    ->select('NUMERO_CRBM_BIOMEDICO as num', 'ESTADO_CRBM_BIOMEDICO as uf')
                    ->where('USUARIO_ID_USUARIO', $u->ID_USUARIO)
                    ->first();
                break;

            case 3: // ENFERMEIRO
                $row = DB::table('ENFERMEIRO')
                    ->select('NUMERO_COREN_ENFERMEIRO as num', 'ESTADO_COREN_ENFERMEIRO as uf')
                    ->where('USUARIO_ID_USUARIO', $u->ID_USUARIO)
                    ->first();
                break;

            default:
                $row = null;
        }

        if ($row) {
            $licenseNumber = $row->num;
            $licenseState  = $row->uf;
        }

        return inertia('Profile/Edit', [
            'mustVerifyEmail' => false,
            'status'          => session('status'),
            'cargos'          => $cargos,

            // injeta o usuário completo já com os campos que o front espera
            'auth' => [
                'user' => [
                    'id'               => $u->ID_USUARIO,
                    'name'             => $u->NOME_USUARIO,
                    'email'            => $u->EMAIL_USUARIO,
                    'CARGO_ID_CARGO'   => $u->CARGO_ID_CARGO,
                    'license_number'   => $licenseNumber,
                    'license_state'    => $licenseState,
                    'email_verified_at'=> null, // se não usa verificação
                ],
            ],
        ]);
    }


    /**
     * Update the user's profile information.
     */
    public function update(Request $request)
    {
        $user = $request->user();
    
        $data = $request->validate([
            'name'            => ['required','string','max:255'],
            'email'           => ['required','email','max:255'],
            'cargo_id'        => ['required','integer','in:1,2,3'], // 1=MEDICO,2=BIOMEDICO,3=ENFERMEIRO
            'license_number'  => ['required','string','max:100'],
            'license_state'   => ['required','string','size:2'],
        ]);
    
        DB::transaction(function () use ($user, $data) {
    
            // Checa o cargo antigo
            $oldCargo = $user->CARGO_ID_CARGO;
    
            // Atualiza dados do usuário
            $user->NOME_USUARIO   = $data['name'];
            $user->EMAIL_USUARIO  = $data['email'];
            $user->CARGO_ID_CARGO = $data['cargo_id'];
            $user->save();
    
            // Se era médico antes e mudou de cargo, desassocia as amostras
            if ($oldCargo == 1 && $data['cargo_id'] != 1) {
                DB::table('AMOSTRA')
                    ->where('MEDICO_USUARIO_ID_USUARIO', $user->ID_USUARIO)
                    ->update(['MEDICO_USUARIO_ID_USUARIO' => null]);
            }
    
            // Atualiza ou cria registro do cargo atual
            switch ((int)$data['cargo_id']) {
                case 1: // MEDICO
                    DB::table('MEDICO')->updateOrInsert(
                        ['USUARIO_ID_USUARIO' => $user->ID_USUARIO],
                        [
                            'NUMERO_CRM_MEDICO' => $data['license_number'],
                            'ESTADO_CRM_MEDICO' => strtoupper($data['license_state']),
                        ]
                    );
                    break;
    
                case 2: // BIOMEDICO
                    DB::table('BIOMEDICO')->updateOrInsert(
                        ['USUARIO_ID_USUARIO' => $user->ID_USUARIO],
                        [
                            'NUMERO_CRBM_BIOMEDICO' => $data['license_number'],
                            'ESTADO_CRBM_BIOMEDICO' => strtoupper($data['license_state']),
                        ]
                    );
                    break;
    
                case 3: // ENFERMEIRO
                    DB::table('ENFERMEIRO')->updateOrInsert(
                        ['USUARIO_ID_USUARIO' => $user->ID_USUARIO],
                        [
                            'NUMERO_COREN_ENFERMEIRO' => $data['license_number'],
                            'ESTADO_COREN_ENFERMEIRO' => strtoupper($data['license_state']),
                        ]
                    );
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
