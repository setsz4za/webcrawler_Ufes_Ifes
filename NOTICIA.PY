from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
import pandas as pd
import json

# Configurações do Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Executar em modo headless
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# URLs dos sites
url_ufes = "https://www.ufes.br/noticias"
url_ifes = "https://www.ifes.edu.br/noticias"

# Função para coletar eventos da UFES
def coletar_eventos_ufes():
    eventos_ufes = []
    driver.get(url_ufes)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'views-field-title')))

    eventos_html = driver.find_elements(By.CLASS_NAME, 'views-field-title')
    for evento in eventos_html:
        try:
            titulo = evento.find_element(By.TAG_NAME, 'a').text
            data_elemento = evento.find_element(By.XPATH, ".//preceding::time[@class='datetime'][1]")
            data = data_elemento.get_attribute("datetime")  # Usando o atributo 'datetime' para maior precisão
            data_formatada = datetime.fromisoformat(data).replace(tzinfo=None)  # Removendo o fuso horário
            
            eventos_ufes.append({
                'Título': titulo,
                'Data': data_formatada,
                'Fonte': 'Ufes Notícias',
                'Data de Coleta': datetime.now().replace(tzinfo=None).isoformat()  # Removendo o fuso horário
            })
        except Exception as e:
            print("Erro ao coletar um evento da UFES:", e)
            continue
    return eventos_ufes

# Função para coletar eventos do IFES, agora incluindo o horário
def coletar_eventos_ifes():
    eventos_ifes = []
    driver.get(url_ifes)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'tileHeadline')))

    datas_html = driver.find_elements(By.XPATH, "//li[contains(text(), '/')]")
    horarios_html = driver.find_elements(By.XPATH, "//li[contains(text(), 'h')]")  # Seleciona o horário em formato HHhMM
    titulos_html = driver.find_elements(By.CLASS_NAME, "tileHeadline")

    for data_elem, horario_elem, titulo_elem in zip(datas_html, horarios_html, titulos_html):
        try:
            data_texto = data_elem.text.strip()  # Exemplo esperado: "30/10/24"
            horario_texto = horario_elem.text.strip()  # Exemplo esperado: "13h09"

            # Formatar data
            if data_texto:
                data_formatada = datetime.strptime(data_texto, "%d/%m/%y")
            else:
                print("Data vazia encontrada, pulando este evento.")
                continue  # Ignora eventos sem data válida

            # Formatar horário
            if horario_texto:
                # Extrai as horas e os minutos do texto de horário
                hora = int(horario_texto[:2])  # Extrai as horas
                minuto = int(horario_texto[3:])  # Extrai os minutos
                data_formatada = data_formatada.replace(hour=hora, minute=minuto)
            else:
                print("Horário vazio encontrado, pulando este evento.")
                continue  # Ignora eventos sem horário válido

            titulo = titulo_elem.find_element(By.TAG_NAME, 'a').text
            
            eventos_ifes.append({
                'Título': titulo,
                'Data': data_formatada,
                'Fonte': 'Ifes Notícias',
                'Data de Coleta': datetime.now().replace(tzinfo=None).isoformat()  # Removendo o fuso horário
            })
        except Exception as e:
            print("Erro ao coletar um evento do IFES:", e)
            continue
    return eventos_ifes

# Defina o intervalo em segundos para a coleta periódica
# Por exemplo, para executar a cada hora, use 3600 segundos (60 minutos * 60 segundos)
INTERVALO_COLETA = 3600  # 1 hora

# Loop de execução contínua para capturar eventos periodicamente
try:
    while True:
        print(f"Iniciando coleta de eventos às {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Coletar eventos de ambos os sites
        eventos_ufes = coletar_eventos_ufes()
        eventos_ifes = coletar_eventos_ifes()

        # Combinar e ordenar os eventos por data (do mais recente para o mais antigo)
        eventos_combinados = eventos_ufes + eventos_ifes
        eventos_ordenados = sorted(eventos_combinados, key=lambda x: x['Data'], reverse=True)

        # Converter os dados para um DataFrame
        df = pd.DataFrame(eventos_ordenados)

        # Nome do arquivo com timestamp para não sobrescrever
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo_csv = f"eventos_vitoria_intercalados_{timestamp}.csv"
        nome_arquivo_json = f"eventos_vitoria_intercalados_{timestamp}.json"

        # Salvar os dados em CSV
        df.to_csv(nome_arquivo_csv, index=False)
        print(f"Dados coletados e salvos com sucesso em '{nome_arquivo_csv}'!")

        # Converter datas para string para salvar em JSON
        for evento in eventos_ordenados:
            evento['Data'] = evento['Data'].isoformat()

        # Salvar em JSON
        with open(nome_arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(eventos_ordenados, f, ensure_ascii=False, indent=4)
        print(f"Dados coletados e salvos com sucesso em '{nome_arquivo_json}'!")

        print(f"Total de eventos coletados: {len(eventos_ordenados)}")
        
        # Aguardar pelo próximo intervalo de coleta
        print(f"Aguardando {INTERVALO_COLETA // 3600} hora(s) para a próxima coleta...\n")
        time.sleep(INTERVALO_COLETA)  # Pausa o programa pelo tempo definido em INTERVALO_COLETA

except KeyboardInterrupt:
    print("Rotina de coleta interrompida pelo usuário.")
finally:
    driver.quit()