#!/usr/bin/env python3

import socket
#import mysql.connector
import pymysql
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk import download
from nltk.corpus import wordnet
from nltk.tokenize.treebank import TreebankWordDetokenizer
from collections import Counter
import math

# Baixar os recursos necessários do NLTK
download('punkt')
download('stopwords')
download('wordnet')

# Definindo variáveis globais
PORT = 8098
SIMILARITY_CUT_OFF = 0.7  # Valor de corte para a similaridade

def preprocess_text(text):
    # Tokenizar o texto
    tokens = word_tokenize(text.lower())
    # Remover palavras de parada
    tokens = [word for word in tokens if word.isalnum()]
    stop_words = set(stopwords.words('portuguese'))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    return filtered_tokens

def get_wordnet_pos(word):
    # Obter a parte do discurso do wordnet para a lematização
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ, "N": wordnet.NOUN, "V": wordnet.VERB, "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

def text_to_vector(text):
    # Lematizar o texto
    tokens = preprocess_text(text)
    lemmatizer = nltk.WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(token, get_wordnet_pos(token)) for token in tokens]
    return Counter(lemmatized_tokens)

def cosine_similarity(vec1, vec2):
    # Calcular a similaridade do cosseno entre dois vetores de texto
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
    sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

def find_most_similar_text(client_text):
    # Conecta ao banco de dados MySQL
    conn = pymysql.connect(
        host='localhost',
        user='mmm',
        password='226468',
        database='doctordb'
    )
    cursor = conn.cursor()
    
    # Executa uma consulta para obter todos os textos da tabela logouve
    cursor.execute("SELECT id, texto FROM logouve WHERE not idComando is null")
    rows = cursor.fetchall()

    # Converte o texto do cliente para vetor de texto
    client_vector = text_to_vector(client_text)
    
    most_similar_id = -1
    highest_similarity = 0

    # Itera sobre os resultados do banco de dados
    for row in rows:
        logouve_id, logouve_text = row
        logouve_vector = text_to_vector(logouve_text)
        
        # Calcula a similaridade
        similarity = cosine_similarity(client_vector, logouve_vector)
        
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
    while True:
        # Recebe o texto do cliente
        data = client_socket.recv(1024).decode('utf-8')
        print(f"Recebido: {data}")

        # Encontra o id com maior similaridade
        result_id = find_most_similar_text(data)
        
        # Envia o id de volta ao cliente, ou -1 se não houver similaridade suficiente
        response = str(result_id) if result_id != -1 else '-1'
        client_socket.send(response.encode('utf-8'))

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
