import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

name = input()
name = name + '\a' + '\b'

s.connect(('localhost', 55554)) # Подключаемся к нашему серверу.
s.sendall(bytes(name, 'utf-8')) # Отправляем фразу.
data = s.recv(1024)
print(data.decode())

code = "0" + '\a' + '\b'
s.sendall(bytes(code, 'utf-8'))
data = s.recv(1024)
print(data.decode())

code = "8389 " + '\a' + '\b'
s.sendall(bytes(code, 'utf-8'))
data = s.recv(1024)
print(data.decode())

#time.sleep(1.5)


# code = "RECHARGING\a\b"
# s.sendall(bytes(code, 'utf-8'))
#
# time.sleep(6)
#
# code = "FULL POWER\a\b"
# s.sendall(bytes(code, 'utf-8'))

s.close()
