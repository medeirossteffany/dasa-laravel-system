<?php

namespace App\Http\Controllers;

use Illuminate\Support\Facades\DB;
use Inertia\Inertia;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
use Carbon\Carbon;

class DashboardController extends Controller
{
    public function index()
    {
        $items = DB::table('PACIENTE')->orderBy('NOME_PACIENTE')->get();

        return Inertia::render('Dashboard', [
            'items' => $items,
        ]);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'nome' => 'required|string|max:255',
            'cpf' => ['required','string','size:11', Rule::unique('PACIENTE','CPF_PACIENTE')],
            'data_nascimento' => 'required|date|before_or_equal:today',
            'endereco' => 'nullable|string|max:255',
            'sexo' => 'required|in:M,F,O',
        ]);

        $id = DB::table('PACIENTE')->insertGetId([
            'NOME_PACIENTE' => $data['nome'],
            'CPF_PACIENTE' => $data['cpf'],
            'DATA_NASC_PACIENTE' => Carbon::parse($data['data_nascimento'])->format('Y-m-d'),
            'ENDERECO' => $data['endereco'],
            'SEXO' => $data['sexo'],
        ]);

        $newPatient = DB::table('PACIENTE')->where('ID_PACIENTE', $id)->first();

        return Inertia::render('Dashboard', [
            'newPatient' => $newPatient,
        ]);
    }
}
