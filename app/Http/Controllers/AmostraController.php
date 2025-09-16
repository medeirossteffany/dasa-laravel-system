<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Storage;
use Inertia\Inertia;

class AmostraController extends Controller
{
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

        public function show($id)
    {
        $row = DB::table('AMOSTRA as a')
            ->leftJoin('PACIENTE as p', 'p.ID_PACIENTE', '=', 'a.PACIENTE_ID_PACIENTE')
            ->selectRaw("
                a.ID_AMOSTRA,
                a.DATA_AMOSTRA,
                a.ALTURA_AMOSTRA,
                a.LARGURA_AMOSTRA,
                a.ESPESSURA,
                a.ANOTACAO_MEDICO_AMOSTRA,
                a.ANOTACAO_IA_AMOSTRA,
                a.IMAGEM_AMOSTRA,
                a.OUTROS_CAMPOS,
                p.ID_PACIENTE,
                p.NOME_PACIENTE,
                p.CPF_PACIENTE
            ")
            ->where('a.ID_AMOSTRA', $id)
            ->first();

        if (!$row) {
            return response()->json(['message' => 'Amostra não encontrada'], 404);
        }

        // Se não tiver imagem
        if (empty($row->IMAGEM_AMOSTRA)) {
            $row->IMAGEM_URL = null;
            // removemos o blob do payload se existir
            unset($row->IMAGEM_AMOSTRA);
            return response()->json($row);
        }

        // Lê o conteúdo do blob corretamente (resource ou string)
        $binary = null;
        if (is_resource($row->IMAGEM_AMOSTRA) || (is_object($row->IMAGEM_AMOSTRA) && method_exists($row->IMAGEM_AMOSTRA, 'stream'))) {
            try {
                $binary = stream_get_contents($row->IMAGEM_AMOSTRA);
            } catch (\Throwable $e) {
                $binary = null;
            }
        }

        if ($binary === null) {
            if (is_object($row->IMAGEM_AMOSTRA) && method_exists($row->IMAGEM_AMOSTRA, '__toString')) {
                $binary = (string) $row->IMAGEM_AMOSTRA;
            } else {
                $binary = $row->IMAGEM_AMOSTRA;
            }
        }

        // Detecta MIME se possível
        $mime = 'image/jpeg';
        if (!empty($binary) && function_exists('finfo_open')) {
            try {
                $finfo = finfo_open(FILEINFO_MIME_TYPE);
                $detected = finfo_buffer($finfo, $binary);
                if ($detected) $mime = $detected;
                finfo_close($finfo);
            } catch (\Throwable $e) {
                // fallback para default
            }
        }

        // Converte para data URL
        if (!empty($binary)) {
            $base64 = base64_encode($binary);
            $row->IMAGEM_URL = "data:{$mime};base64,{$base64}";
        } else {
            $row->IMAGEM_URL = null;
        }

        // remover blob original para não duplicar
        unset($row->IMAGEM_AMOSTRA);

        return response()->json($row);
    }

    /**
     * Serve a imagem diretamente (STREAM) — recomendado para produção.
     * GET /amostras/{id}/imagem
     */
    public function imagem($id)
    {
        $row = DB::table('AMOSTRA')->select('IMAGEM_AMOSTRA')->where('ID_AMOSTRA', $id)->first();

        if (!$row || empty($row->IMAGEM_AMOSTRA)) {
            return response('Imagem não encontrada', 404);
        }

        // lê blob
        $binary = null;
        if (is_resource($row->IMAGEM_AMOSTRA) || (is_object($row->IMAGEM_AMOSTRA) && method_exists($row->IMAGEM_AMOSTRA, 'stream'))) {
            try {
                $binary = stream_get_contents($row->IMAGEM_AMOSTRA);
            } catch (\Throwable $e) {
                $binary = null;
            }
        }

        if ($binary === null) {
            if (is_object($row->IMAGEM_AMOSTRA) && method_exists($row->IMAGEM_AMOSTRA, '__toString')) {
                $binary = (string) $row->IMAGEM_AMOSTRA;
            } else {
                $binary = $row->IMAGEM_AMOSTRA;
            }
        }

        if (empty($binary)) {
            return response('Imagem inválida', 404);
        }

        $mime = 'image/jpeg';
        if (function_exists('finfo_open')) {
            try {
                $finfo = finfo_open(FILEINFO_MIME_TYPE);
                $detected = finfo_buffer($finfo, $binary);
                if ($detected) $mime = $detected;
                finfo_close($finfo);
            } catch (\Throwable $e) {
                // ignore
            }
        }

        return response($binary, 200)
            ->header('Content-Type', $mime)
            ->header('Content-Length', strlen($binary));
    }
}
