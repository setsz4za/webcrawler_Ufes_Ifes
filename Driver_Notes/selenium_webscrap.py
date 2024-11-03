from selenium import webdriver
import requests
from bs4 import BeautifulSoup


navegador = webdriver.Edge()

navegador.get('https://www.walissonsilva.com/blog')

elemento = navegador.find_element(By.TAG_NAME, 'tag_name')

input("Pressione Enter para fechar o navegador...")
navegador.quit()