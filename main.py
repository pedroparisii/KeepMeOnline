import os
import sys
import json
import asyncio
import platform
import requests
from colorama import init, Fore
from keep_alive import keep_alive

init(autoreset=True)

# ================== CONFIGURAÇÃO ==================
status = "idle"                    # online / dnd / idle

# Coloque seus tokens aqui (pode deixar vazio se for usar variável de ambiente)
TOKENS = {
    "TOKEN1": os.getenv("TOKEN1"),
    "TOKEN2": os.getenv("TOKEN2"),
    "TOKEN3": os.getenv("TOKEN3"),
    "TOKEN4": os.getenv("TOKEN4"),
}

# Remover tokens vazios ou None
TOKENS = {name: token for name, token in TOKENS.items() if token}

if not TOKENS:
    print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Nenhum token encontrado!")
    print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Adicione TOKEN1, TOKEN2, TOKEN3 ou TOKEN4 nas Secrets.")
    sys.exit()

# ================== VALIDAÇÃO DOS TOKENS ==================
valid_tokens = {}

for name, token in TOKENS.items():
    headers = {"Authorization": token, "Content-Type": "application/json"}
    
    try:
        validate = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers, timeout=10)
        
        if validate.status_code == 200:
            userinfo = validate.json()
            username = userinfo["username"]
            userid = userinfo["id"]
            discriminator = userinfo.get("discriminator", "0")
            
            valid_tokens[token] = {
                "name": name,
                "username": f"{username}#{discriminator}",
                "userid": userid,
                "display": f"{username} ({userid})"
            }
            
            print(f"{Fore.WHITE}[{Fore.LIGHTGREEN_EX}+{Fore.WHITE}] Token {name} válido → {Fore.LIGHTBLUE_EX}{username}#{discriminator}{Fore.WHITE}")
        else:
            print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Token {name} inválido (Status: {validate.status_code})")
            
    except Exception as e:
        print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Erro ao validar {name}: {e}")

if not valid_tokens:
    print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Nenhum token válido encontrado. Encerrando...")
    sys.exit()

print(f"\n{Fore.WHITE}[{Fore.LIGHTGREEN_EX}+{Fore.WHITE}] Iniciando {len(valid_tokens)} conta(s) online...\n")

# ================== FUNÇÃO PARA MANTER UMA CONTA ONLINE ==================
async def keep_online(token, user_info):
    while True:
        try:
            async with websockets.connect("wss://gateway.discord.gg/?v=9&encoding=json") as ws:
                start = json.loads(await ws.recv())
                heartbeat = start["d"]["heartbeat_interval"]

                # Login
                auth = {
                    "op": 2,
                    "d": {
                        "token": token,
                        "properties": {
                            "$os": "Windows 10",
                            "$browser": "Google Chrome",
                            "$device": "Windows",
                        },
                        "presence": {"status": status, "afk": False},
                    },
                }
                await ws.send(json.dumps(auth))

                # Custom Status
                cstatus = {
                    "op": 3,
                    "d": {
                        "since": 0,
                        "activities": [
                            {
                                "type": 4,
                                "state": custom_status,
                                "name": "Custom Status",
                                "id": "custom",
                            }
                        ],
                        "status": status,
                        "afk": False,
                    },
                }
                await ws.send(json.dumps(cstatus))

                print(f"{Fore.WHITE}[{Fore.LIGHTGREEN_EX}+{Fore.WHITE}] {user_info['display']} → Online com status customizado")

                # Heartbeat loop
                while True:
                    online = {"op": 1, "d": None}
                    await ws.send(json.dumps(online))
                    await asyncio.sleep(heartbeat / 1000)

        except Exception as e:
            print(f"{Fore.WHITE}[{Fore.YELLOW}-{Fore.WHITE}] {user_info['display']} desconectou. Reconectando em 10s... ({e})")
            await asyncio.sleep(10)


# ================== EXECUÇÃO ==================
async def main():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

    print(f"{Fore.WHITE}[{Fore.LIGHTGREEN_EX}+{Fore.WHITE}] Sistema de Multi-Contas Discord Iniciado!\n")

    tasks = []
    for token, info in valid_tokens.items():
        tasks.append(asyncio.create_task(keep_online(token, info)))

    await asyncio.gather(*tasks, return_exceptions=True)


keep_alive()
asyncio.run(main())
