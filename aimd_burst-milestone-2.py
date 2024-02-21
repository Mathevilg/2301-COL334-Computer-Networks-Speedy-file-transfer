import socket
from socket import timeout as TimeoutException
import hashlib
import threading
import time
from matplotlib import pyplot as plt

client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
send_size = "SendSize\nReset\n\n"
rtt = 0
while True:
    t1 = time.time()
    client_socket.sendto(send_size.encode('utf-8'),('10.17.7.134',9801))
    client_socket.settimeout(0.1)
    try:
        data,addr = client_socket.recvfrom(8192)
        rtt = time.time() - t1
        break
    except:
        continue
print("RTT:",rtt)
size = int(data.decode('utf-8')[6:-2])
print(size)
offset_list = [(1448*i,1448) for i in range(size//1448)]
if size % 1448 != 0 : offset_list.append(((size//1448)*1448,size % 1448))

lines_recv = 0
data_list = ["" for _ in range(len(offset_list))]
received = [False for _ in range(len(offset_list))]

print(len(data_list))
n = len(offset_list)
sleep_time = 0.02
line_num_list = [i for i in range (len(data_list))]

start_time = time.time()
squished = 0
burst_size = 8
current = 0
lock = threading.Lock()
can_reduce = True
sent_time_list = []
recv_time_dict = {}
rtt_time_list = [0 for _ in range (len(offset_list))]
burst_size_list = []
burst_time_list = []
squished_list = []
starting_time = time.time()

def sending_process() :
    global offset_list
    global lines_recv
    global current
    global rtt_time_list
    req_sent = 0
    while True:
        if len(offset_list)==lines_recv: break
        b = burst_size
        for j in range(round(b)) :
            try : i = line_num_list[j]
            except : continue
            off_sent,size_to_send = offset_list[i]
            message = f"Offset: {off_sent}\nNumBytes: {size_to_send}\n\n"
            sent_time_list.append((off_sent,(time.time() - start_time)*1000))
            client_socket.sendto(message.encode('utf-8'),('10.17.7.134',9801))
            req_sent += 1
        time.sleep(sleep_time)

        
def receiving_process() :
    global offset_list
    global data_list
    global sleep_time
    global lines_recv
    global squished
    global line_num_list
    global burst_size
    global can_reduce
    global rtt_time_list
    global received_lines
    while True:
        if len(offset_list)==lines_recv: break
        start = time.time()
        to_recv = 0
        while time.time()-start<sleep_time:
            client_socket.settimeout(0.001)
            try: data,addr = client_socket.recvfrom(8192)    
            except TimeoutException: continue

            message_recv = data.decode('utf-8')
            x = message_recv.find('\n')
            offset = int(message_recv[8:x])

            message_recv = message_recv[x+1:]
            y = message_recv.find('\n')
            message_recv = message_recv[y+2:]

            if (message_recv[0:7]=="quished") : 
                sleep_time += 0.001
                message_recv = message_recv[9:]
                squished += 1

            if received[offset//1448]: continue
            recv_time_dict[offset] = (time.time() - start_time)*1000
            data_list[offset//1448] = message_recv
            line_num_list.remove(offset//1448)
            received[offset//1448] = True
            lines_recv += 1
            to_recv += 1

        burst_size_list.append(burst_size)
        squished_list.append(squished)
        burst_time_list.append((time.time()-starting_time)*1000)

        with lock:
            if to_recv/burst_size >= 0.8: burst_size += 1
            else : burst_size = max(1,burst_size//2)


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

while True:
    client_socket.sendto(submit.encode('utf-8'),('10.17.7.134',9801))
    client_socket.settimeout(0.1)
    try:
        data,addr = client_socket.recvfrom(8192)
        break
    except:
        continue

feedback = data.decode('utf-8')
print(feedback)
print("Squished :", squished)
print("burst_size :", burst_size)
client_socket.close()
print("RTT:",rtt)

# Graph plotting
xr = list(recv_time_dict.values())
yr = list(recv_time_dict.keys())

xs = [e[1] for e in sent_time_list]
ys = [e[0] for e in sent_time_list]

plt.style.use('seaborn')

plt.figure(figsize=(20,15))
plt.scatter(xs,ys,label = "Offset sent",c="blue")
plt.scatter(xr,yr,label = "Offset received",c="red")
plt.xlabel('Time (in ms)',fontsize = 18)
plt.ylabel('Offset', fontsize = 18)
plt.xticks(fontsize = 18)
plt.yticks(fontsize = 18)
plt.legend()
plt.savefig("seq_trace.jpg")

for i in range(len(xr)):
    xr[i] *= 1000

for i in range(len(xs)):
    xs[i] *= 1000
    
plt.figure(figsize=(12,9))
plt.scatter(xs[:30],ys[:30],label = "Offset sent",c="blue")
plt.scatter(xr[:30],yr[:30],label = "Offset received",c="red")
plt.xlabel('Time (in μs)',fontsize = 16)
plt.ylabel('Offset', fontsize = 16)
plt.xticks(fontsize = 14)
plt.yticks(fontsize = 14)
plt.legend()
plt.savefig("zoom_seq_trace.jpg")

plt.figure(figsize=(16,12))
plt.plot(burst_time_list, burst_size_list, linestyle='-', marker='o',label = "Burst size")
plt.plot(burst_time_list, squished_list, linestyle='-', marker='o',label = "Total squished")
plt.xlabel('Time (in ms)',fontsize = 18)
plt.ylabel('Burst size', fontsize = 18)
plt.xticks(fontsize = 18)
plt.yticks(fontsize = 18)
plt.legend()
plt.savefig("burst.jpg")
plt.close()