import socket
from socket import timeout as TimeoutException
import hashlib
import threading
import time
from matplotlib import pyplot as plt

client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

send_size = "SendSize\nReset\n\n"

while True:
    client_socket.sendto(send_size.encode('utf-8'),('127.0.0.1',9801))
    client_socket.settimeout(0.1)
    try:
        data,addr = client_socket.recvfrom(8192)
        break
    except:
        continue
    
size = int(data.decode('utf-8')[6:-2])
print(size)
offset_list = [(1448*i,1448) for i in range(size//1448)]
if size % 1448 != 0 : offset_list.append(((size//1448)*1448,size % 1448))
# for x in offset_list : print(x)

lines_recv = 0
data_list = ["" for _ in range(len(offset_list))]
received = [False for _ in range(len(offset_list))]

index = 0
print(len(data_list))
n = len(offset_list)
sleep_time = 0.005

start_time = time.time()
sent_time_list = []
recv_time_dict = {}

def sending_process() :
    global offset_list
    global index
    global lines_recv
    while True:
        if len(offset_list)==lines_recv: break
        while received[index]==True: index = (index+1)%n
        i = index
        index = (index+1)%n
        off_sent,size_to_send = offset_list[i]
        message = f"Offset: {off_sent}\nNumBytes: {size_to_send}\n\n"
        client_socket.sendto(message.encode('utf-8'),('127.0.0.1',9801))
        sent_time_list.append((off_sent,(time.time() - start_time)*1000))
        time.sleep(sleep_time)

        
def receiving_process() :
    global offset_list
    global data_list
    global sleep_time
    global lines_recv
    while True:
        if len(offset_list)==lines_recv: break
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

        if (message_recv[0:7]=="quished") : 
            sleep_time += 0.005
            continue

        if received[offset//1448]: continue
        recv_time_dict[offset] = (time.time() - start_time)*1000
        data_list[offset//1448] = message_recv
        received[offset//1448] = True
        lines_recv += 1


sending_thread = threading.Thread(target=sending_process, args=())
receiving_thread = threading.Thread(target=receiving_process, args=())
sending_thread.start()
receiving_thread.start()

receiving_thread.join()
sending_thread.join()


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

# Graph plotting
# xr = list(recv_time_dict.values())
# yr = list(recv_time_dict.keys())

# xs = [e[1] for e in sent_time_list]
# ys = [e[0] for e in sent_time_list]

# plt.style.use('seaborn')

# plt.figure(figsize=(20,15))
# plt.scatter(xs,ys,label = "Offset sent",c="blue")
# plt.scatter(xr,yr,label = "Offset received",c="red")
# plt.xlabel('Time (in ms)',fontsize = 18)
# plt.ylabel('Offset', fontsize = 18)
# plt.xticks(fontsize = 18)
# plt.yticks(fontsize = 18)
# plt.legend()
# plt.savefig("seq_trace.jpg")

# for i in range(len(xr)):
#     xr[i] *= 1000

# for i in range(len(xs)):
#     xs[i] *= 1000
    
# plt.figure(figsize=(14,10))
# plt.scatter(xs[:20],ys[:20],label = "Offset sent",c="blue")
# plt.scatter(xr[:15],yr[:15],label = "Offset received",c="red")
# plt.xlabel('Time (in μs)',fontsize = 16)
# plt.ylabel('Offset', fontsize = 16)
# plt.xticks(fontsize = 14)
# plt.yticks(fontsize = 14)
# plt.legend()
# plt.savefig("zoom_seq_trace.jpg")