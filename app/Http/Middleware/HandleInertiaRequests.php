<?php

namespace App\Http\Middleware;

use Illuminate\Http\Request;
use Inertia\Middleware;

class HandleInertiaRequests extends Middleware
{
    /**
     * The root template that is loaded on the first page visit.
     *
     * @var string
     */
    protected $rootView = 'app';

    /**
     * Determine the current asset version.
     */
    public function version(Request $request): ?string
    {
        return parent::version($request);
    }

    /**
     * Define the props that are shared by default.
     *
     * @return array<string, mixed>
     */
    public function share(Request $request): array
    {
        $u = $request->user();
    
        return array_merge(parent::share($request), [
            'auth' => [
                'user' => $u ? [
                    'id'              => $u->ID_USUARIO,
                    'name'            => $u->NOME_USUARIO,
                    'email'           => $u->EMAIL_USUARIO,
                    'CARGO_ID_CARGO'  => $u->CARGO_ID_CARGO,
                    'email_verified_at' => $u->email_verified_at,
                    // se você já tiver buscado o registro profissional:
                    'license_number'  => $u->license_number ?? null,
                    'license_state'   => $u->license_state ?? null,
                ] : null,
            ],
            // já mande a lista de cargos também, se ainda não estiver
            'cargos' => fn () => \Illuminate\Support\Facades\DB::table('CARGO')
                ->select('ID_CARGO','TITULO_CARGO')->orderBy('ID_CARGO')->get(),
        ]);
    }
}
