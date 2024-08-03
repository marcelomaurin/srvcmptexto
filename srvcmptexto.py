#!/usr/bin/env python3

import socket
#import mysql.connector
import pymysql
import spacy
from spacy.util import is_package

# Carregando o modelo spaCy em português Brasil large
#nlp = spacy.load("pt_core_news_lg")
# Nome do modelo
model_name = "pt_core_news_lg"

try:
    # Verifica se o modelo está instalado
    if not is_package(model_name):
        # Se não estiver instalado, faz o download
        from spacy.cli import download
        print(f"Modelo {model_name} não encontrado. Instalando...")
        download(model_name)

    # Carrega o modelo
    nlp = spacy.load(model_name)
    print(f"Modelo {model_name} carregado com sucesso.")

    # Exemplo de uso
    doc = nlp("Este é um exemplo de frase.")
    for token in doc:
        print(token.text, token.pos_, token.dep_)

except Exception as e:
    print(f"Ocorreu um erro: {e}")


# Definindo variáveis globais
PORT = 8098
SIMILARITY_CUT_OFF = 0.7  # Valor de corte para a similaridade

def find_most_similar_text(client_text):
    # Conecta ao banco de dados MySQL
    conn = pymysql.connect(
        host='localhost',       # Altere para o seu host MySQL
        user='mmm',     # Altere para seu usuário MySQL
        password='226468',   # Altere para sua senha MySQL
        database='doctordb'     # Nome do banco de dados
    )
    cursor = conn.cursor()
    
    # Executa uma consulta para obter todos os textos da tabela logouve
    cursor.execute("SELECT id, texto FROM logouve where not idComando is null")
    rows = cursor.fetchall()

    # Converte o texto do cliente em um objeto spaCy
    client_doc = nlp(client_text)
    
    most_similar_id = -1
    highest_similarity = 0

    # Itera sobre os resultados do banco de dados
    for row in rows:
        logouve_id, logouve_text = row
        logouve_doc = nlp(logouve_text)
        
        # Calcula a similaridade
        similarity = client_doc.similarity(logouve_doc)
        
        # Atualiza o id com maior similaridade se a similaridade for maior que o valor de corte
        if similarity > highest_similarity:
            highest_similarity = similarity
            if similarity >= SIMILARITY_CUT_OFF:
                most_similar_id = logouve_id

    print(f"Chave encontrada:{most_similar_id}")

    # Fecha a conexão com o banco de dados
    conn.close()

    return most_similar_id

def handle_client(client_socket):
  while(1):  
    # Recebe o texto do cliente
    data = client_socket.recv(1024).decode('utf-8')
    print(f"Recebido:{data}")

    # Encontra o id com maior similaridade
    result_id = find_most_similar_text(data)
    
    # Envia o id de volta ao cliente, ou -1 se não houver similaridade suficiente
    response = str(result_id) if result_id != -1 else '-1'
    client_socket.send(response.encode('utf-8'))
    
    # Fecha a conexão com o cliente
    #client_socket.close()

def main():
    # Cria um socket TCP/IP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Define o endereço e a porta para o servidor
    server.bind(('0.0.0.0', PORT))
    
    # Escuta conexões
    server.listen(5)
    print(f'Servidor escutando na porta {PORT}...')

    while True:
        # Aceita uma nova conexão
        client_socket, addr = server.accept()
        print(f'Conectado a {addr}')
        
        # Lida com a conexão do cliente
        handle_client(client_socket)

if __name__ == '__main__':
    main()

