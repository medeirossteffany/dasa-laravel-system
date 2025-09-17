<?php

use App\Http\Controllers\ProfileController;
use Illuminate\Foundation\Application;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\DashboardController;
use App\Http\Controllers\MicroscopioController;
use App\Http\Controllers\AmostraController;
use Inertia\Inertia;

Route::get('/', function () {
    return Inertia::render('Welcome', [
        'canLogin' => Route::has('login'),
        'canRegister' => Route::has('register'),
        'laravelVersion' => Application::VERSION,
        'phpVersion' => PHP_VERSION,
    ]);
});

Route::get('/dashboard', function () {
    return Inertia::render('Dashboard');
})->middleware(['auth', 'verified'])->name('dashboard');

Route::middleware('auth')->group(function () {
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');

    Route::get('/dashboard', [DashboardController::class, 'index'])->name('dashboard');

    Route::get('/amostras', [AmostraController::class, 'index'])->name('amostras.index');
    Route::get('/amostras/{id}', [AmostraController::class, 'show'])->name('amostras.show');
    Route::get('/amostras/{id}/imagem', [AmostraController::class, 'imagem'])->name('amostras.imagem');
    
    Route::post('/microscopio/upload', [MicroscopioController::class, 'upload']);
});


require __DIR__.'/auth.php';
