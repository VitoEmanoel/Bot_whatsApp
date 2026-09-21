"""Envia um texto (uma mensagem por linha) pelo WhatsApp Web, devagar e com pausas.

Uso:
    python enviar.py 5511999999999            # para uma pessoa (DDI + DDD + numero)
    python enviar.py --grupo "Nome do Grupo"  # para um grupo (nome exato)

Ctrl+C para parar. O progresso fica em progresso.json e a execução continua de onde parou.
"""
import argparse
import json
import random
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
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
LIMITE_DIARIO_PADRAO = 150             # vale para a conta inteira, somando todos os destinos

CAIXA_MENSAGEM = 'footer div[contenteditable="true"]'
# a caixa de busca já foi um div editável e hoje é um input; aceita os dois
CAIXA_BUSCA = '#side input[role="textbox"], #side input[type="text"], #side div[contenteditable="true"]'


def carregar_progresso():
    """Formato: {"dia": ..., "enviadas_hoje": N, "destinos": {"<destino>": indice}}."""
    dados = {"dia": str(date.today()), "enviadas_hoje": 0, "destinos": {}}
    if PROGRESSO.exists():
        lido = json.loads(PROGRESSO.read_text(encoding="utf-8"))
        if "destinos" in lido:
            dados = lido
        else:  # formato antigo (um único destino, sem nome guardado)
            dados["dia"] = lido.get("dia", dados["dia"])
            dados["enviadas_hoje"] = lido.get("enviadas_hoje", 0)
            dados["destinos"] = {"_legado": lido.get("indice", 0)}
    if dados["dia"] != str(date.today()):
        dados["dia"], dados["enviadas_hoje"] = str(date.today()), 0
    return dados


def salvar_progresso(dados):
    PROGRESSO.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def limpar(texto):
    # chromedriver não digita caracteres fora do BMP (ex.: emojis)
    return "".join(c for c in texto if ord(c) <= 0xFFFF)


def sem_emoji(texto):
    """Remove emojis e símbolos invisíveis (seletores de variação, ZWJ) e normaliza os espaços."""
    manter = []
    for c in unicodedata.normalize("NFC", texto):  # junta letra + acento em um só caractere
        if ord(c) > 0xFFFF or unicodedata.category(c) in ("So", "Sk", "Cf", "Cs", "Mn", "Co", "Cn"):
            continue
        manter.append(c)
    return " ".join("".join(manter).split())


def normalizar(texto):
    """Forma usada para comparar nomes de grupo: sem emojis, sem espaços extras, sem caixa."""
    return sem_emoji(texto).casefold()


def abrir_pessoa(driver, numero):
    driver.get(f"https://web.whatsapp.com/send?phone={numero}")
    print("Se aparecer o QR code, escaneie com o celular. Aguardando a conversa abrir...")
    WebDriverWait(driver, 180).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CAIXA_MENSAGEM))
    )


def abrir_grupo(driver, nome):
    driver.get("https://web.whatsapp.com/")
    print("Se aparecer o QR code, escaneie com o celular. Aguardando o WhatsApp carregar...")
    busca = WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, CAIXA_BUSCA))
    )
    termo = sem_emoji(nome)  # o Chrome não digita emojis; a busca do WhatsApp acha pelo resto do nome
    if not termo:
        sys.exit("O nome do grupo precisa ter pelo menos uma letra ou número além de emojis.")
    busca.click()
    busca.send_keys(termo)

    # O WhatsApp redesenha a lista enquanto a busca carrega, então os títulos são lidos de uma vez
    # (um único comando JS) em vez de guardar elementos que podem ficar obsoletos no meio da leitura.
    def titulos_atuais():
        return driver.execute_script(
            "return Array.from(document.querySelectorAll('#pane-side span[title]'))"
            ".map(e => e.getAttribute('title') || '')"
        )

    # só aceita um resultado cujo título, ignorando emojis e maiúsculas, seja igual ao nome informado
    alvo = normalizar(nome)
    try:
        WebDriverWait(driver, 30).until(lambda d: any(normalizar(t) == alvo for t in titulos_atuais()))
    except TimeoutException:
        vistos = list(dict.fromkeys(titulos_atuais()))
        dica = f" Resultados da busca: {vistos[:10]}" if vistos else " A busca não retornou nenhum resultado."
        sys.exit(f'Grupo "{nome}" não encontrado. Confira o nome (o script ignora emojis e maiúsculas).{dica}')

    for _ in range(5):
        titulos = titulos_atuais()
        indices = [i for i, t in enumerate(titulos) if normalizar(t) == alvo]
        if not indices:
            time.sleep(0.5)
            continue
        distintos = list(dict.fromkeys(titulos[i] for i in indices))
        if len(distintos) > 1:
            # grupos diferentes só nos emojis: exige o título idêntico ao informado
            if nome not in distintos:
                lista = ", ".join(f'"{t}"' for t in distintos)
                sys.exit(f"Mais de um grupo combina com esse nome: {lista}. Nada foi enviado.")
            escolhido = nome
        else:
            escolhido = distintos[0]
        posicao = next(i for i in indices if titulos[i] == escolhido)
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, "#pane-side span[title]")
            if elementos[posicao].get_attribute("title") != escolhido:
                raise IndexError  # a lista mudou de ordem; tenta de novo
            elementos[posicao].click()
            break
        except (StaleElementReferenceException, IndexError):
            time.sleep(0.5)
    else:
        sys.exit("A lista de resultados ficou mudando e não consegui abrir o grupo. Tente de novo.")

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CAIXA_MENSAGEM))
    )


def main():
    ap = argparse.ArgumentParser(description="Envia o roteiro.txt pelo WhatsApp Web.")
    destino = ap.add_mutually_exclusive_group(required=True)
    destino.add_argument("numero", nargs="?", help="número com DDI e DDD, ex.: 5511999999999")
    destino.add_argument("--grupo", help="nome exato do grupo")
    ap.add_argument("--limite", type=int, default=LIMITE_DIARIO_PADRAO,
                    help=f"máximo de mensagens por dia, somando todos os destinos (padrão {LIMITE_DIARIO_PADRAO})")
    args = ap.parse_args()

    chave = f"grupo:{args.grupo}" if args.grupo else args.numero

    linhas = [l.strip() for l in ROTEIRO.read_text(encoding="utf-8").splitlines() if l.strip()]
    dados = carregar_progresso()
    if "_legado" in dados["destinos"] and args.numero:  # progresso do formato antigo era de um número
        dados["destinos"].setdefault(chave, dados["destinos"].pop("_legado"))
    indice = dados["destinos"].get(chave, 0)

    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument(f"--user-data-dir={PERFIL}")
    driver = webdriver.Chrome(options=opcoes)

    try:
        if args.grupo:
            abrir_grupo(driver, args.grupo)
        else:
            abrir_pessoa(driver, args.numero)

        while indice < len(linhas):
            if dados["enviadas_hoje"] >= args.limite:
                print(f"Limite diário ({args.limite}) atingido. Rode de novo amanhã.")
                break

            texto = limpar(linhas[indice])
            if texto:
                caixa = driver.find_element(By.CSS_SELECTOR, CAIXA_MENSAGEM)
                caixa.click()
                caixa.send_keys(texto)
                caixa.send_keys(Keys.ENTER)

            indice += 1
            dados["enviadas_hoje"] += 1
            dados["destinos"][chave] = indice
            salvar_progresso(dados)
            print(f"[{indice}/{len(linhas)}] {texto[:60]}")

            if indice % LOTE == 0:
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
