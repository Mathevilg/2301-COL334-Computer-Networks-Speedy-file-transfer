import socket
from socket import timeout as TimeoutException
import random
import hashlib

client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

send_size = "SendSize\n\n"

while True:
    client_socket.sendto(send_size.encode('utf-8'),('127.0.0.1',9801))
    client_socket.settimeout(0.1)
    try:
        data,addr = client_socket.recvfrom(8192)
        break
    except:
        continue
    
# print(data.decode('utf-8'))
size = int(data.decode('utf-8')[6:-2])
# print(size)
offset_list = [(1448*i,1448) for i in range(size//1448)]
if size % 1448 != 0 : offset_list.append(((size//1448)*1448,size % 1448))
# for x in offset_list : print(x)

lines_recv = 0
data_list = ["" for _ in range(len(offset_list))]

while offset_list:
    if len(offset_list)==0: break
    i = random.randint(0,len(offset_list)-1)
    off_sent,size_to_send = offset_list[i]
    message = f"Offset: {off_sent}\nNumBytes: {size_to_send}\n\n"
    client_socket.sendto(message.encode('utf-8'),('127.0.0.1',9801))
    client_socket.settimeout(0.1)

    try:
        data,addr = client_socket.recvfrom(8192)    
    except TimeoutException:
        continue
    
    message_recv = data.decode('utf-8')
    x = message_recv.find('\n')
    offset = int(message_recv[8:x])

    message_recv = message_recv[x+1:]
    y = message_recv.find('\n')
    num_bytes = int(message_recv[10:y])
    message_recv = message_recv[y+2:]

    if not ((offset,num_bytes) in offset_list) : continue
    offset_list.remove((offset,num_bytes))
    data_list[offset//1448] = message_recv
    lines_recv += 1
    # print("Length:",len(offset_list))

datastring = "".join(data_list)
bytestr = datastring.encode('utf-8')
hashval = hashlib.md5(bytestr)

submit = f"Submit: 2021CS10110@team\nMD5: {hashval.hexdigest()}\n\n"
# print()
# print(submit)

while True:
    client_socket.sendto(submit.encode('utf-8'),('127.0.0.1',9801))
    client_socket.settimeout(0.1)
    try:
        data,addr = client_socket.recvfrom(8192)
        break
    except:
        continue

feedback = data.decode('utf-8')
print(feedback)

client_socket.close()