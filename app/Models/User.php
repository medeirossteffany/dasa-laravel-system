<?php

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    use Notifiable;

    // Nome da tabela
    protected $table = 'USUARIO';

    // Nome da chave primária
    protected $primaryKey = 'ID_USUARIO';

    // Se a PK não for auto incremento inteiro
    public $incrementing = true;
    protected $keyType = 'int';

    // Se não tiver timestamps (created_at, updated_at)
    public $timestamps = false;

    // Campos que podem ser preenchidos
    protected $fillable = [
        'NOME_USUARIO',
        'EMAIL_USUARIO',
        'SENHA_USUARIO',
        'CARGO_ID_CARGO',
    ];

    // Mapeia a coluna de senha
    public function getAuthPassword()
    {
        return $this->SENHA_USUARIO;
    }

    public function username()
{
    return 'EMAIL_USUARIO';
}

}
