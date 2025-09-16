def fazer_login(conexao, email, senha):
    with conexao.cursor() as cursor:
        query = "SELECT ID_USUARIO, NOME_USUARIO FROM USUARIO WHERE EMAIL_USUARIO = %s AND SENHA_USUARIO = %s"
        cursor.execute(query, (email, senha))
        resultado = cursor.fetchone()
    if resultado:
        id_usuario = resultado['ID_USUARIO']
        nome_usuario = resultado['NOME_USUARIO']
        return id_usuario, nome_usuario
    else:
        return None, None