from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime
from pathlib import Path
from urllib import request, parse
import json
import csv
import sys
import traceback

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
LOG_DIR = BASE_DIR / "logs"
SCREENSHOT_DIR = BASE_DIR / "prints_erros"
LOG_DIR.mkdir(exist_ok=True)
SCREENSHOT_DIR.mkdir(exist_ok=True)

def agora_texto():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def agora_arquivo():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def carregar_config():
    if not CONFIG_PATH.exists():
        print("ERRO: arquivo config.json não encontrado.")
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)

def salvar_resultado(resultado):
    arquivo_csv = LOG_DIR / "resultado_monitoramento.csv"
    existe = arquivo_csv.exists()

    with open(arquivo_csv, "a", newline="", encoding="utf-8") as arquivo:
        campos = ["data_hora", "site", "url", "status", "detalhe"]
        writer = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")

        if not existe:
            writer.writeheader()

        writer.writerow(resultado)

def enviar_telegram(config, mensagem):
    telegram = config.get("telegram", {})
    ativo = telegram.get("ativo", False)
    token = telegram.get("bot_token", "").strip()
    chat_id = telegram.get("chat_id", "").strip()

    if not ativo:
        print("Telegram desativado no config.json.")
        return

    if not token or not chat_id or token == "PREENCHA_AQUI" or chat_id == "PREENCHA_AQUI":
        print("Telegram não configurado: preencha bot_token e chat_id no config.json.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    dados = parse.urlencode({
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "HTML"
    }).encode("utf-8")

    try:
        req = request.Request(url, data=dados, method="POST")
        with request.urlopen(req, timeout=15) as resposta:
            resposta.read()
        print("Mensagem enviada para o Telegram.")
    except Exception as erro:
        print(f"Falha ao enviar Telegram: {erro}")

def testar_site(page, site):
    nome = site["nome"]
    url = site["url"]
    data_hora = agora_texto()

    try:
        page.goto(url, timeout=site.get("timeout_ms", 20000), wait_until="domcontentloaded")

        if site.get("apenas_verificar_online", False):
            return {
                "data_hora": data_hora,
                "site": nome,
                "url": url,
                "status": "OK",
                "detalhe": "Site carregou corretamente."
            }

        campo_usuario = site.get("campo_usuario", "").strip()
        campo_senha = site.get("campo_senha", "").strip()
        botao_login = site.get("botao_login", "").strip()
        usuario = site.get("usuario", "")
        senha = site.get("senha", "")
        texto_sucesso = site.get("texto_sucesso", "").strip()

        if not campo_usuario or not campo_senha or not botao_login or not texto_sucesso:
            return {
                "data_hora": data_hora,
                "site": nome,
                "url": url,
                "status": "CONFIG_INCOMPLETA",
                "detalhe": "Preencha campo_usuario, campo_senha, botao_login e texto_sucesso no config.json."
            }

        page.fill(campo_usuario, usuario, timeout=10000)
        page.fill(campo_senha, senha, timeout=10000)
        page.click(botao_login, timeout=10000)

        page.wait_for_timeout(site.get("tempo_apos_login_ms", 4000))

        conteudo = page.content()
        url_atual = page.url

        if texto_sucesso.lower() in conteudo.lower() or texto_sucesso.lower() in url_atual.lower():
            return {
                "data_hora": data_hora,
                "site": nome,
                "url": url,
                "status": "OK",
                "detalhe": "Login realizado e validação encontrada."
            }

        nome_print = f"{nome.replace(' ', '_')}_{agora_arquivo()}.png"
        caminho_print = SCREENSHOT_DIR / nome_print
        page.screenshot(path=str(caminho_print), full_page=True)

        return {
            "data_hora": data_hora,
            "site": nome,
            "url": url,
            "status": "ERRO_LOGIN",
            "detalhe": f"O site abriu, mas a validação de sucesso não foi encontrada. Print salvo em: {caminho_print}"
        }

    except PlaywrightTimeoutError as erro:
        try:
            nome_print = f"{nome.replace(' ', '_')}_{agora_arquivo()}_timeout.png"
            caminho_print = SCREENSHOT_DIR / nome_print
            page.screenshot(path=str(caminho_print), full_page=True)
        except Exception:
            caminho_print = "Não foi possível salvar print."

        return {
            "data_hora": data_hora,
            "site": nome,
            "url": url,
            "status": "TIMEOUT",
            "detalhe": f"Demorou para carregar ou responder. Detalhe: {erro}. Print: {caminho_print}"
        }

    except Exception as erro:
        try:
            nome_print = f"{nome.replace(' ', '_')}_{agora_arquivo()}_erro.png"
            caminho_print = SCREENSHOT_DIR / nome_print
            page.screenshot(path=str(caminho_print), full_page=True)
        except Exception:
            caminho_print = "Não foi possível salvar print."

        return {
            "data_hora": data_hora,
            "site": nome,
            "url": url,
            "status": "ERRO",
            "detalhe": f"{erro}. Print: {caminho_print}"
        }

def montar_mensagem_telegram(resultados):
    erros = [r for r in resultados if r["status"] != "OK"]
    total = len(resultados)
    ok = total - len(erros)

    if erros:
        titulo = "⚠️ <b>Monitoramento Superbom - ATENÇÃO</b>"
    else:
        titulo = "✅ <b>Monitoramento Superbom - Tudo certo</b>"

    linhas = [
        titulo,
        "",
        f"🕒 <b>Data/Hora:</b> {agora_texto()}",
        f"📊 <b>Total testado:</b> {total}",
        f"✅ <b>OK:</b> {ok}",
        f"❌ <b>Problemas:</b> {len(erros)}",
        "",
        "<b>Detalhes:</b>"
    ]

    for r in resultados:
        icone = "✅" if r["status"] == "OK" else "❌"
        linhas.append(f"{icone} {r['site']} - {r['status']}")

    if erros:
        linhas.append("")
        linhas.append("<b>Erros encontrados:</b>")
        for r in erros:
            detalhe = r["detalhe"]
            if len(detalhe) > 250:
                detalhe = detalhe[:250] + "..."
            linhas.append(f"❌ <b>{r['site']}</b>: {detalhe}")

    return "\n".join(linhas)

def main():
    config = carregar_config()
    headless = config.get("headless", True)
    sites = config.get("sites", [])

    if not sites:
        print("Nenhum site cadastrado no config.json.")
        return

    resultados = []

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=headless)
        contexto = navegador.new_context(ignore_https_errors=True)

        for site in sites:
            page = contexto.new_page()
            resultado = testar_site(page, site)
            resultados.append(resultado)
            salvar_resultado(resultado)
            print(f"[{resultado['data_hora']}] {resultado['site']} - {resultado['status']} - {resultado['detalhe']}")
            page.close()

        navegador.close()

    erros = [r for r in resultados if r["status"] != "OK"]

    print("\nResumo:")
    print(f"Total testado: {len(resultados)}")
    print(f"OK: {len(resultados) - len(erros)}")
    print(f"Problemas: {len(erros)}")

    if erros:
        print("\nSites com problema:")
        for erro in erros:
            print(f"- {erro['site']}: {erro['status']}")

    mensagem = montar_mensagem_telegram(resultados)
    enviar_telegram(config, mensagem)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Erro inesperado na execução geral:")
        print(traceback.format_exc())
        sys.exit(1)



    

    

                                          # © 2026 João Frederico | Projeto: Monitoramento de Sistemas