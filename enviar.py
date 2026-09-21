"""Envia um texto (uma mensagem por linha) pelo WhatsApp Web, devagar e com pausas.

Uso:
    python enviar.py 5511999999999

Ctrl+C para parar. O progresso fica em progresso.json e a execução continua de onde parou.
"""
import json
import random
import sys
import time
from datetime import date
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

PASTA = Path(__file__).parent
ROTEIRO = PASTA / "roteiro.txt"
PROGRESSO = PASTA / "progresso.json"
PERFIL = PASTA / "perfil_chrome"  # guarda o login (QR code só na primeira vez)

DELAY_MIN, DELAY_MAX = 20, 45          # segundos entre mensagens (aleatório)
LOTE = 25                              # a cada N mensagens, pausa longa
PAUSA_LONGA_MIN, PAUSA_LONGA_MAX = 180, 300
LIMITE_DIARIO = 150


def carregar_progresso():
    if PROGRESSO.exists():
        dados = json.loads(PROGRESSO.read_text(encoding="utf-8"))
    else:
        dados = {"indice": 0, "dia": str(date.today()), "enviadas_hoje": 0}
    if dados["dia"] != str(date.today()):
        dados["dia"], dados["enviadas_hoje"] = str(date.today()), 0
    return dados


def salvar_progresso(dados):
    PROGRESSO.write_text(json.dumps(dados), encoding="utf-8")


def limpar(texto):
    # chromedriver não digita caracteres fora do BMP (ex.: emojis)
    return "".join(c for c in texto if ord(c) <= 0xFFFF)


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python enviar.py <numero com DDI e DDD, ex.: 5511999999999>")
    numero = sys.argv[1]

    linhas = [l.strip() for l in ROTEIRO.read_text(encoding="utf-8").splitlines() if l.strip()]
    dados = carregar_progresso()

    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument(f"--user-data-dir={PERFIL}")
    driver = webdriver.Chrome(options=opcoes)
    driver.get(f"https://web.whatsapp.com/send?phone={numero}")

    print("Se aparecer o QR code, escaneie com o celular. Aguardando a conversa abrir...")
    caixa = WebDriverWait(driver, 180).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'footer div[contenteditable="true"]'))
    )

    try:
        while dados["indice"] < len(linhas):
            if dados["enviadas_hoje"] >= LIMITE_DIARIO:
                print(f"Limite diário ({LIMITE_DIARIO}) atingido. Rode de novo amanhã.")
                break

            texto = limpar(linhas[dados["indice"]])
            if texto:
                caixa = driver.find_element(By.CSS_SELECTOR, 'footer div[contenteditable="true"]')
                caixa.click()
                caixa.send_keys(texto)
                caixa.send_keys(Keys.ENTER)

            dados["indice"] += 1
            dados["enviadas_hoje"] += 1
            salvar_progresso(dados)
            print(f"[{dados['indice']}/{len(linhas)}] {texto[:60]}")

            if dados["indice"] % LOTE == 0:
                pausa = random.uniform(PAUSA_LONGA_MIN, PAUSA_LONGA_MAX)
                print(f"Pausa longa de {pausa / 60:.1f} min...")
            else:
                pausa = random.uniform(DELAY_MIN, DELAY_MAX)
            time.sleep(pausa)
        else:
            print("Roteiro completo enviado!")
    except KeyboardInterrupt:
        print("\nParado. O progresso foi salvo.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
