import socket 
from _thread import *
import sys
from collections import defaultdict as df
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer, TfidfTransformer
import time
import re
from deep_translator import MyMemoryTranslator

# print(msg)
model = pickle.load(open("LinearSVC.pkl", 'rb'))

class Server:
    def __init__(self):
        self.rooms = df(list)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    def accept_connections(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.server.bind((self.ip_address, int(self.port)))
        self.server.listen(100)

        while True:
            connection, address = self.server.accept()
            print(str(address[0]) + ":" + str(address[1]) + " Connected")

            start_new_thread(self.clientThread, (connection,))

        self.server.close()

    
    def clientThread(self, connection):
        user_id = connection.recv(1024).decode().replace("User ", "")
        room_id = connection.recv(1024).decode().replace("Join ", "")

        if room_id not in self.rooms:
            connection.send("New Group created".encode())
        else:
            connection.send("Welcome to chat room".encode())

        self.rooms[room_id].append(connection)

        while True:
            try:
                message = connection.recv(1024)
                pred=0
                if message:
                    if str(message.decode()) == "FILE":
                        self.broadcastFile(connection, room_id, user_id)

                    else:
                        # print('Am I fucking here')
                        pred=self.prettyPrinter(str(message.decode()))
                        message_to_send = "<" + str(user_id) + "> " + message.decode()
                        self.broadcast(message_to_send, connection, room_id,pred)

                else:
                    self.remove(connection, room_id)
            except Exception as e:
                print(repr(e))
                print("Client disconnected earlier")
                break
    
    
    def broadcastFile(self, connection, room_id, user_id):
        file_name = connection.recv(1024).decode()
        lenOfFile = connection.recv(1024).decode()
        for client in self.rooms[room_id]:
            if client != connection:
                try: 
                    client.send("FILE".encode())
                    time.sleep(0.1)
                    client.send(file_name.encode())
                    time.sleep(0.1)
                    client.send(lenOfFile.encode())
                    time.sleep(0.1)
                    client.send(user_id.encode())
                except:
                    client.close()
                    self.remove(client, room_id)

        total = 0
        print(file_name, lenOfFile)
        while str(total) != lenOfFile:
            data = connection.recv(1024)
            total = total + len(data)
            for client in self.rooms[room_id]:
                if client != connection:
                    try: 

                        # prettyPrinter(data_1)
                        client.send(data)
                        time.sleep(0.1)
                    except:
                        client.close()
                        self.remove(client, room_id)
        # print("Sent")

    def prettyPrinter(self,data_1):
        # Normalize text to catch evasions
        replacements = {'@': 'a', '$': 's', '1': 'i', '0': 'o', '!': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b'}
        for symbol, letter in replacements.items():
            data_1 = data_1.replace(symbol, letter)
            
        # Translate Devanagari to English to map correctly to ML model vocabulary
        if re.search(r'[\u0900-\u097F]', data_1):
            try:
                data_1 = MyMemoryTranslator(source='hi-IN', target='en-GB').translate(data_1)
            except:
                pass
        data_1 = data_1.lower()
        
         # List of stopwords 
        my_file = open("stopwords.txt", "r")
        content = my_file.read()
        content_list = content.split("\n")
        my_file.close()
        tfidf_vector =  TfidfVectorizer(stop_words = content_list, lowercase = True,vocabulary=pickle.load(open("tfidf_vector_vocabulary.pkl", "rb")))
        data_2=tfidf_vector.fit_transform([data_1])
        print(data_2)
        pred = model.predict(data_2)
        print(pred)
        if pred==0:
            print('Non bullying')
            return pred
        else: 
            print("Stop bullying people and behave decently.")
            return pred

    def broadcast(self, message_to_send, connection, room_id,pred):
        for client in self.rooms[room_id]:
            if client != connection:
                try:
                    if pred==0:
                        client.send(message_to_send.encode())
                    else :
                        client.send("Bullying message detected it has been hidden".encode())
                except:
                    client.close()
                    self.remove(client, room_id)

    
    def remove(self, connection, room_id):
        if connection in self.rooms[room_id]:
            self.rooms[room_id].remove(connection)


if __name__ == "__main__":
    ip_address = "127.0.0.1"
    port = 12345

    s = Server()
    s.accept_connections(ip_address, port)
