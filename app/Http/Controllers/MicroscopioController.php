<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

class MicroscopioController extends Controller
{
    public function upload(Request $request)
    {
        try {
            $request->validate([
                'imagem' => 'required|image|max:10240', 
                'anotacao' => 'nullable|string|max:2000',
                'gemini_obs' => 'nullable|string|max:2000',
                'amostra_retirada' => 'nullable|in:0,1',
                'cpf' => 'nullable|string|max:20',
            ]);
        } catch (\Illuminate\Validation\ValidationException $e) {
            return response()->json(['success' => false, 'errors' => $e->errors()], 422);
        }

        try {
            $image = $request->file('imagem');
            $filename = 'amostra_' . time() . '.png';
            $destDir = storage_path('app/amostras');
            if (!is_dir($destDir)) @mkdir($destDir, 0775, true);
            $path = $image->move($destDir, $filename)->getPathname();

            $venvPython = base_path('.venv/bin/python');
            if (!file_exists($venvPython)) {
                $venvPython = 'python3';
            }

            $script = base_path('app/Http/Scripts/microscopio.py');

            $cmd = sprintf(
                '%s %s --image %s --anotacao %s --gemini_obs %s --amostra_retirada %s --cpf %s --user-id %s --user-name %s',
                escapeshellarg($venvPython),
                escapeshellarg($script),
                escapeshellarg($path),
                escapeshellarg($request->input('anotacao', '')),
                escapeshellarg($request->input('gemini_obs', '')),
                escapeshellarg($request->input('amostra_retirada', '0')),
                escapeshellarg($request->input('cpf', '')),
                escapeshellarg((string) optional($request->user())->id ?: ''),
                escapeshellarg((string) optional($request->user())->name ?: '')
            );

            $descriptors = [
                1 => ['pipe', 'w'],
                2 => ['pipe', 'w']
            ];
            $process = proc_open($cmd, $descriptors, $pipes, base_path());
            if (!is_resource($process)) {
                return response()->json(['success' => false, 'message' => 'Falha ao iniciar processo Python'], 500);
            }

            $stdout = stream_get_contents($pipes[1]); fclose($pipes[1]);
            $stderr = stream_get_contents($pipes[2]); fclose($pipes[2]);
            $return_value = proc_close($process);

            if ($return_value !== 0) {
                \Log::error('Microscopio script error', ['cmd' => $cmd, 'stdout' => $stdout, 'stderr' => $stderr]);
                return response()->json(['success' => false, 'message' => 'Python retornou erro', 'stdout' => $stdout, 'stderr' => $stderr], 500);
            }

            return response()->json(['success' => true, 'file' => $filename, 'stdout' => $stdout, 'stderr' => $stderr]);
        } catch (\Throwable $e) {
            \Log::error('Upload erro interno: '.$e->getMessage(), ['trace' => $e->getTraceAsString()]);
            return response()->json(['success' => false, 'message' => 'Erro interno no servidor', 'exception' => $e->getMessage()], 500);
        }
    }
}
