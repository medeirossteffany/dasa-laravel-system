<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

class MicroscopioController extends Controller
{
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
