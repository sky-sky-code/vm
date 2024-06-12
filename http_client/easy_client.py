import socket

HOST = 'localhost'
PORT = 8000

client = socket.socket()
client.connect((HOST, PORT))
message = "GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
print("Connecting...")
client.send(message.encode())
data = client.recv(1024)
print("Server sent: ", data.decode())
client.close()

