<?php


namespace App\Http\Controllers;


use Illuminate\Support\Facades\DB;
use Inertia\Inertia;


class AmostraController extends Controller
{
    /**
    * Lista TODAS as amostras, inclusive sem paciente vinculado
    */
    public function index()
        {
            $items = DB::table('AMOSTRA as a')
            ->leftJoin('PACIENTE as p', 'p.ID_PACIENTE', '=', 'a.PACIENTE_ID_PACIENTE')
            ->selectRaw("
            a.ID_AMOSTRA,
            a.DATA_AMOSTRA,
            a.ALTURA_AMOSTRA,
            a.LARGURA_AMOSTRA,
            a.ESPESSURA,
            a.ANOTACAO_MEDICO_AMOSTRA,
            a.ANOTACAO_IA_AMOSTRA,
            p.ID_PACIENTE,
            p.NOME_PACIENTE,
            p.CPF_PACIENTE
            ")
            ->orderByDesc('a.DATA_AMOSTRA')
            ->get();


            return Inertia::render('Amostras/Index', [
            'items' => $items,
            ]);
        }
}