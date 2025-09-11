<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

class MicroscopioController extends Controller
{
    public function run(Request $request)
    {
        try {
            $user = Auth::user();

            Log::channel('stderr')->debug('[Microscopio] Auth user', ['user' => $user]);
            Log::debug('[Microscopio] Auth user', ['user' => $user]);

            if (!$user) {
                return back()->withErrors('Você precisa estar logado.');
            }

            $userId   = $user->id ?? $user->ID_USUARIO ?? null;
            $userName = $user->name ?? $user->NOME_USUARIO ?? 'Usuário';

            Log::channel('stderr')->debug('[Microscopio] Resolved user', [
                'userId' => $userId,
                'userName' => $userName,
            ]);

            if (!$userId) {
                return back()->withErrors('Não foi possível determinar o ID do usuário autenticado.');
            }

            $script = base_path('app/Http/Scripts/microscopio.py');
            if (!file_exists($script)) {
                Log::error("[Microscopio] Script não encontrado: {$script}");
                return back()->withErrors("Script não encontrado em {$script}");
            }

            $python = $this->resolvePythonPath();
            if (!$python) {
                return back()->withErrors('Python 3 não encontrado. Ajuste o caminho no controller.');
            }

            $env = array_merge($_ENV, [
                'AUTH_USER_ID'   => (string) $userId,
                'AUTH_USER_NAME' => (string) $userName,
            ]);

            $cmd = [$python, $script];
            $workdir = base_path();

            if ($request->boolean('diag')) {
                $process = new Process($cmd, $workdir, $env);
                $process->setTimeout(null);
                $process->setIdleTimeout(null);
                $process->run();

                $out = $process->getOutput();
                $err = $process->getErrorOutput();

                Log::channel('stderr')->debug('[Microscopio][DIAG] stdout', ['out' => $out]);
                Log::channel('stderr')->debug('[Microscopio][DIAG] stderr', ['err' => $err]);

                if (!$process->isSuccessful()) {
                    return back()->withErrors("Falha ao iniciar Python (diag):\n$err\n$out");
                }

                return back()->with('success', "Python OK (diag):\n$out");
            }

            $logDir = storage_path('logs');
            if (!is_dir($logDir)) {
                @mkdir($logDir, 0775, true);
            }
            $logFile = storage_path('logs/microscopio.out.log');
            $errFile = storage_path('logs/microscopio.err.log');

            $cmdline = sprintf(
                'nohup %s %s >> %s 2>> %s & echo $!',
                escapeshellarg($python),
                escapeshellarg($script),
                escapeshellarg($logFile),
                escapeshellarg($errFile)
            );

            $process = Process::fromShellCommandline($cmdline, $workdir, $env);
            $process->setTimeout(10);
            $process->setIdleTimeout(null);
            $process->run();

            if (!$process->isSuccessful()) {
                $err = $process->getErrorOutput();
                $out = $process->getOutput();
                Log::error("[Microscopio] Falha ao spawnar nohup", ['err' => $err, 'out' => $out]);
                return back()->withErrors("Falha ao iniciar em background: \n$err\n$out");
            }

            $pid = trim($process->getOutput());
            Log::info("[Microscopio] Disparado em background (nohup) com PID {$pid} para usuário {$userId} - {$userName}");

            return back()->with('success', 'Microscópio iniciado em background. Veja os logs em storage/logs/microscopio.*.log');

        } catch (ProcessFailedException $e) {
            Log::error('[Microscopio] Falha no processo: '.$e->getMessage());
            return back()->withErrors('Falha ao iniciar o microscópio. Verifique os logs.');
        } catch (\Throwable $e) {
            Log::error('[Microscopio] Erro: '.$e->getMessage(), ['trace' => $e->getTraceAsString()]);
            return back()->withErrors('Erro ao iniciar o microscópio. Verifique os logs.');
        }
    }

    private function resolvePythonPath(): ?string
    {
        $venvPython = base_path('.venv/bin/python');
        if (is_executable($venvPython)) {
            return $venvPython;
        }

        $candidates = [
            '/opt/homebrew/bin/python3', 
            '/usr/local/bin/python3',    
            '/usr/bin/python3',          
            'python3',                  
        ];

        foreach ($candidates as $p) {
            if ($p === 'python3') {
                return $p; 
            }
            if (is_executable($p)) {
                return $p;
            }
        }
        return null;
    }
}
