<?php

namespace App\Http\Controllers;

use Illuminate\Support\Facades\DB;
use Inertia\Inertia;

class DashboardController extends Controller
{
    public function index()
    {
        $items = DB::table('PACIENTE as p')
            ->leftJoin('AMOSTRA as a', 'a.PACIENTE_ID_PACIENTE', '=', 'p.ID_PACIENTE')
            ->selectRaw("
                p.ID_PACIENTE,
                p.NOME_PACIENTE,
                p.CPF_PACIENTE,
                a.ID_AMOSTRA,
                a.DATA_AMOSTRA,
                a.ALTURA_AMOSTRA,
                a.LARGURA_AMOSTRA,
                a.ESPESSURA,
                a.ANOTACAO_MEDICO_AMOSTRA,
                a.ANOTACAO_IA_AMOSTRA
            ")
            ->orderByDesc('a.DATA_AMOSTRA')
            ->get();

        return Inertia::render('Dashboard', [
            'items' => $items,
        ]);
    }
}
