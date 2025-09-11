<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

class MicroscopioController extends Controller
{
    /**
     * Dispara o script Python do microscópio passando o usuário autenticado.
     * - Modo normal: assíncrono (não bloqueia a requisição).
     * - Modo diagnóstico: adicionar ?diag=1 para rodar sincronamente e retornar stdout/stderr.
     */
    public function run(Request $request)
    {
        try {
            // 1) Usuário autenticado
            $user = Auth::user();

            // Logs úteis no console (stderr) e no laravel.log
            Log::channel('stderr')->debug('[Microscopio] Auth user', ['user' => $user]);
            Log::debug('[Microscopio] Auth user', ['user' => $user]);

            if (!$user) {
                return back()->withErrors('Você precisa estar logado.');
            }

            // Ajuste aqui se seus campos têm outros nomes
            $userId   = $user->id ?? $user->ID_USUARIO ?? null;
            $userName = $user->name ?? $user->NOME_USUARIO ?? 'Usuário';

            Log::channel('stderr')->debug('[Microscopio] Resolved user', [
                'userId' => $userId,
                'userName' => $userName,
            ]);

            if (!$userId) {
                return back()->withErrors('Não foi possível determinar o ID do usuário autenticado.');
            }

            // 2) Caminho do script Python
            // Mova seu microscopio.py para esse local do projeto (ou ajuste a linha abaixo)
            $script = base_path('app/Http/Scripts/microscopio.py');
            if (!file_exists($script)) {
                Log::error("[Microscopio] Script não encontrado: {$script}");
                return back()->withErrors("Script não encontrado em {$script}");
            }

            // 3) Descobrir Python (ajuste se necessário)
            $python = $this->resolvePythonPath();
            if (!$python) {
                return back()->withErrors('Python 3 não encontrado. Ajuste o caminho no controller.');
            }

            // 4) Variáveis de ambiente pro Python
            $env = array_merge($_ENV, [
                'AUTH_USER_ID'   => (string) $userId,
                'AUTH_USER_NAME' => (string) $userName,
                // Se quiser sobrepor credenciais de DB aqui:
                // 'DB_HOST' => config('database.connections.mysql.host'),
                // 'DB_USER' => config('database.connections.mysql.username'),
                // 'DB_PASSWORD' => config('database.connections.mysql.password'),
                // 'DB_NAME' => config('database.connections.mysql.database'),
            ]);

            // 5) Comando
            $cmd = [$python, $script];
            $workdir = base_path();

            // Modo diagnóstico? (sincrono, mostra stdout/err no retorno)
            if ($request->boolean('diag')) {
                $process = new Process($cmd, $workdir, $env);
                $process->setTimeout(20); // 20s
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

            // 6) Modo normal (assíncrono) + logs em arquivo
            $logFile = storage_path('logs/microscopio.out.log');
            $errFile = storage_path('logs/microscopio.err.log');

            $process = new Process($cmd, $workdir, $env, null, null);
            $process->start();

            // Captura buffers iniciais para arquivo (não bloqueia)
            $process->waitUntil(function ($type, $buffer) use ($logFile, $errFile) {
                if ($type === Process::OUT) {
                    file_put_contents($logFile, $buffer, FILE_APPEND);
                } else {
                    file_put_contents($errFile, $buffer, FILE_APPEND);
                }
                // sempre continue (não bloqueia)
                return false;
            });

            Log::info("[Microscopio] Disparado com PID {$process->getPid()} para usuário {$userId} - {$userName}");

            return back()->with('success', 'Microscópio iniciado. Verifique a janela do app e os logs em storage/logs/microscopio.*.log');

        } catch (ProcessFailedException $e) {
            Log::error('[Microscopio] Falha no processo: '.$e->getMessage());
            return back()->withErrors('Falha ao iniciar o microscópio. Verifique os logs.');
        } catch (\Throwable $e) {
            Log::error('[Microscopio] Erro: '.$e->getMessage(), ['trace' => $e->getTraceAsString()]);
            return back()->withErrors('Erro ao iniciar o microscópio. Verifique os logs.');
        }
    }

    /**
     * Tenta resolver o caminho do python3 em ambientes comuns de macOS.
     */
    private function resolvePythonPath(): ?string
    {
        // 1) Prioriza o Python do venv do projeto
        $venvPython = base_path('.venv/bin/python');
        if (is_executable($venvPython)) {
            return $venvPython;
        }
    
        // 2) Demais caminhos comuns no macOS
        $candidates = [
            '/opt/homebrew/bin/python3', // Apple Silicon (Homebrew)
            '/usr/local/bin/python3',    // Intel (Homebrew)
            '/usr/bin/python3',          // Sistema
            'python3',                   // PATH (último recurso)
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
