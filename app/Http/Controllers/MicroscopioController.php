<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class MicroscopioController extends Controller
{
    public function upload(Request $request)
    {
        set_time_limit(0);
        try {
            $request->validate([
                'imagem' => 'required|image|max:10240',
                'anotacao' => 'nullable|string|max:2000',
                'gemini_obs' => 'nullable|string|max:2000',
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

            // Detectando o sistema operacional e definindo Python
            if (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') {
                $venvPython = base_path('.venv\\Scripts\\python.exe');
                if (!file_exists($venvPython)) {
                    $venvPython = 'python'; // fallback para Python global no Windows
                }
            } else {
                $venvPython = base_path('.venv/bin/python');
                if (!file_exists($venvPython)) {
                    $venvPython = 'python3'; // fallback para macOS/Linux
                }
            }

            $script = base_path('app/Http/Scripts/mensureScript/microscopio.py');

            // Montando o comando
            $cmd = sprintf(
                '%s %s --image %s --anotacao %s --gemini_obs %s --cpf %s --user-id %s --user-name %s',
                escapeshellarg($venvPython),
                escapeshellarg($script),
                escapeshellarg($path),
                escapeshellarg($request->input('anotacao', '')),
                escapeshellarg($request->input('gemini_obs', '')),
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
                Log::error('Microscopio script error', ['cmd' => $cmd, 'stdout' => $stdout, 'stderr' => $stderr]);
                return response()->json(['success' => false, 'message' => 'Python retornou erro', 'stdout' => $stdout, 'stderr' => $stderr], 500);
            }

            return response()->json(['success' => true, 'file' => $filename, 'stdout' => $stdout, 'stderr' => $stderr]);
        } catch (\Throwable $e) {
            Log::error('Upload erro interno: '.$e->getMessage(), ['trace' => $e->getTraceAsString()]);
            return response()->json(['success' => false, 'message' => 'Erro interno no servidor', 'exception' => $e->getMessage()], 500);
        }
    }
}
