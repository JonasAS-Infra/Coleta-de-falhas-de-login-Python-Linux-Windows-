# projeto3_login_fail.py

import paramiko
import winrm
from datetime import datetime
import os

# ---------------------------------------
# Função para carregar lista de hosts
# ---------------------------------------
def carregar_hosts(caminho_arquivo):
    with open(caminho_arquivo, "r") as f:
        linhas = f.readlines()
        return [linha.strip() for linha in linhas if linha.strip()]


# ---------------------------------------
# Coletar falhas de login - Linux
# ---------------------------------------
def coletar_linux(host):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(
            hostname=host,
            username="scv_account",
            password="senha1",
            timeout=5
        )
        # Primeiro, descobrir qual arquivo de log existe
        comando_detect = """
        if [ -f /var/log/secure ]; then
            echo SECURE
        elif [ -f /var/log/auth.log ]; then
            echo AUTHLOG
        else
            echo NONE
        fi
        """

        stdin, stdout, stderr = ssh.exec_command(comando_detect)
        log_tipo = stdout.read().decode().strip()
        
        # Escolher o comando correto
        if log_tipo == "SECURE":
            comando = 'grep "Failed password" /var/log/secure | tail -n 20'
        elif log_tipo == "AUTHLOG":
            comando = 'grep "Failed password" /var/log/auth.log | tail -n 20'
        else:
            ssh.close()
            return f"[LINUX] {host}\nArquivo de log de autenticação não encontrado.\n"
        
        # Executar comando final
        stdin, stdout, stderr = ssh.exec_command(comando)
        saida = stdout.read().decode().strip()

        ssh.close()

        if saida == "":
            saida = "Nenhum erro encontrado nos últimos 20 eventos."

        return f"[LINUX] {host}\n{saida}\n"
    
    except Exception as e:
        return f"[LINUX] {host}: ERRO -> {e}\n"


# ---------------------------------------
# Coletar falhas de login - Windows
# ---------------------------------------
def coletar_windows(host):
    try:
        sess = winrm.Session(
            target=host, 
            auth=("scv_account", "senha1")
        )

        comando = (
            "powershell -Command "
            "\"Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625} "
            "-MaxEvents 20 | Format-List\""
        )

        resposta = sess.run_cmd(comando)
        saida = resposta.std_out.decode().strip()

        if saida == "":
            saida = "Nenhum erro encontrado nos últimos 20 eventos."

        return f"[WINDOWS] {host}\n{saida}\n"

    except Exception as e:
        return f"[WINDOWS] {host}: ERRO -> {e}\n"


# ---------------------------------------
# Função Principal
# ---------------------------------------
def main():
    print("=== Coletando falhas de login... ===")

    hosts_linux = carregar_hosts("hosts_linux.txt")
    hosts_win   = carregar_hosts("hosts_win.txt")

    resultados = []

    # Linux
    for host in hosts_linux:
        print(f"Linux -> {host}")
        resultados.append(coletar_linux(host))

    # Windows
    for host in hosts_win:
        print(f"Windows -> {host}")
        resultados.append(coletar_windows(host))

    # Criar pasta LOG se não existir
    if not os.path.exists("log"):
        os.mkdir("log")

    nome_log = f"log/logins_falhos_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"

    with open(nome_log, "w") as f:
        f.write("\n\n".join(resultados))

    print(f"\n✔ Coleta finalizada! Arquivo salvo em: {nome_log}")


if __name__ == "__main__":
    main()

