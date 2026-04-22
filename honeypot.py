import socket
import logging
from datetime import datetime
import winsound  # Biblioteca para o sinal sonoro no Windows
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. CONFIGURAÇÃO DO LOG
logging.basicConfig(
    filename="honeypot_log.txt", 
    level=logging.INFO, 
    format='%(message)s',
)

def gerar_resposta_html():
    """Gera uma página HTML de alerta para o 'invasor' no navegador."""
    html = """HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8

<html>
<head><title>ACESSO RESTRITO</title></head>
<body style="background-color:black; color:red; text-align:center; font-family:sans-serif; padding-top:50px;">
    <h1>⚠️ SISTEMA DE SEGURANÇA CORPORATIVA ⚠️</h1>
    <p>Seu endereço IP e metadados foram registrados por razões de auditoria.</p>
    <hr style="border: 1px solid red; width: 50%;">
    <br>
    <form>
        Usuário: <input type="text" name="user" style="background: #222; color: white; border: 1px solid red;"><br><br>
        Senha: <input type="password" name="pass" style="background: #222; color: white; border: 1px solid red;"><br><br>
        <input type="button" value="Entrar" style="background: red; color: black; font-weight: bold; cursor: not-allowed;">
    </form>
    <p style="font-size: 12px; color: #555;">Aviso: Tentativas de acesso não autorizado são monitoradas.</p>
</body>
</html>
"""
    return html.encode('utf-8')

def iniciar_honeypot(ip, porta):
    # Cria o socket (IPv4 e TCP)
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permite reutilizar a porta imediatamente após fechar o script
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        servidor.bind((ip, porta))
        servidor.listen(5)
        
        # Define um timeout de 1 segundo para que o script verifique o Ctrl+C periodicamente
        servidor.settimeout(1.0)
        
        print("-" * 50)
        print(f"[*] HONEYPOT ATIVO EM: {ip}:{porta}")
        print(f"[*] LOGS SENDO SALVOS EM: honeypot_log.txt")
        print(f"[*] Pressione CTRL+C para encerrar com segurança.")
        print("-" * 50)

        while True:
            try:
                try:
                    cliente, endereco = servidor.accept()
                except socket.timeout:
                    # Ninguém conectou no último segundo, volta para o topo do loop e checa o teclado
                    continue
                
                # SUCESSO: Alguém caiu na armadilha!
                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                # Alerta sonoro no Desktop (Frequência 1000Hz por 500ms)
                winsound.Beep(1000, 500)
                
                msg_alerta = f"\n[!] ALERTA DE INTRUSÃO: {endereco[0]} às {data_hora}"
                print(msg_alerta)
                logging.info(msg_alerta)
                
                # Captura a requisição HTTP enviada pelo dispositivo
                requisicao = cliente.recv(1024).decode('utf-8', errors='ignore')
                if requisicao:
                    # Pega apenas a primeira linha (ex: GET / HTTP/1.1) para o terminal
                    primeira_linha = requisicao.splitlines()[0]
                    print(f"    [DADOS]: {primeira_linha}")
                    logging.info(f"    Requisição Completa:\n{requisicao}")
                
                # Envia a página falsa de login e encerra a conexão
                cliente.send(gerar_resposta_html())
                cliente.close()
                
            except KeyboardInterrupt:
                print("\n\n[!] Encerrando HoneyPot... Limpando portas e finalizando logs.")
                break
            except Exception as e:
                print(f"[-] Erro durante a conexão: {e}")
                
    except Exception as e:
        print(f"[-] Erro ao iniciar o servidor: {e}")
    finally:
        servidor.close()

if __name__ == "__main__":
    # '0.0.0.0' escuta em todas as interfaces (Ethernet e Wi-Fi)
    # Porta 8080 é ideal para simular serviços web alternativos
    iniciar_honeypot('0.0.0.0', 8080)