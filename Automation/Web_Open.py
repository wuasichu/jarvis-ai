import webbrowser
from Automation.Web_Data import websites


def openweb(webname: str):
    key = webname.lower().strip()

    # 1. Coincidencia exacta en el diccionario
    if key in websites:
        url = websites[key]
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return

    # 2. Ya es una URL completa
    if key.startswith("http://") or key.startswith("https://"):
        webbrowser.open(key)
        return

    # 3. Parece un dominio (contiene punto, sin espacios)
    if "." in key and " " not in key:
        webbrowser.open("https://" + key)
        return

    # 4. Búsqueda en Google como fallback
    query = webname.replace(" ", "+")
    webbrowser.open(f"https://www.google.com/search?q={query}")
