<?php

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    use Notifiable;

    protected $table = 'USUARIO';
    protected $primaryKey = 'ID_USUARIO';
    public $incrementing = true;
    protected $keyType = 'int';
    public $timestamps = false;

    protected $fillable = [
        'NOME_USUARIO',
        'EMAIL_USUARIO',
        'SENHA_USUARIO',
        'CARGO_ID_CARGO',
    ];

    protected $hidden = [
        'SENHA_USUARIO',
    ];

    // Faz com que 'id', 'name' e 'email' apareçam no JSON do user
    protected $appends = ['id', 'name', 'email'];

    // Laravel vai usar essa coluna para comparar a senha
    public function getAuthPassword()
    {
        return $this->SENHA_USUARIO;
    }

    // Laravel vai usar essa coluna como identificador de login
    public function username()
    {
        return 'EMAIL_USUARIO';
    }

    // Aliases para funcionar igual ao padrão do Breeze
    public function getIdAttribute()
    {
        return $this->attributes['ID_USUARIO'] ?? null;
    }

    public function getNameAttribute()
    {
        return $this->attributes['NOME_USUARIO'] ?? null;
    }

    public function getEmailAttribute()
    {
        return $this->attributes['EMAIL_USUARIO'] ?? null;
    }
}
