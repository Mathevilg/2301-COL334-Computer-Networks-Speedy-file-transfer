import socket
from socket import timeout as TimeoutException
# import random
import hashlib
import threading
import time
from matplotlib import pyplot as plt

client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
send_size = "SendSize\nReset\n\n"
rtt = 0
while True:
    t1 = time.time()
    client_socket.sendto(send_size.encode('utf-8'),('127.0.0.1',9801))
    client_socket.settimeout(0.1)
    try:
        data,addr = client_socket.recvfrom(8192)
        rtt = time.time() - t1
        break
    except:
        continue
print("RTT:",rtt)
# print(data.decode('utf-8'))
size = int(data.decode('utf-8')[6:-2])
print(size)
offset_list = [(1448*i,1448) for i in range(size//1448)]
if size % 1448 != 0 : offset_list.append(((size//1448)*1448,size % 1448))
# for x in offset_list : print(x)

lines_recv = 0
data_list = ["" for _ in range(len(offset_list))]
received = [False for _ in range(len(offset_list))]

print(len(data_list))
n = len(offset_list)
sleep_time = 0.036
line_num_list = [i for i in range (len(data_list))]
received_lines = [False for _ in range (len(offset_list))]

start_time = time.time()
squished = 0
burst_size = 12
current = 0
lock = threading.Lock()
can_reduce = True
sending_time_list = [0 for _ in range (len(offset_list))]
receiving_time_list = [0 for _ in range (len(offset_list))]
rtt_time_list = [0 for _ in range (len(offset_list))]
burst_size_list = [0 for _ in range (len(offset_list))]

def sending_process() :
    global offset_list
    global lines_recv
    global current
    global rtt_time_list
    req_sent = 0
    while True:
        if len(offset_list)==lines_recv: break
        with lock :
            for j in range (round(burst_size)) :
                try : i = line_num_list[j]
                except : continue
                off_sent,size_to_send = offset_list[i]
                message = f"Offset: {off_sent}\nNumBytes: {size_to_send}\n\n"
                # rtt_time_list[i] = time.time()
                sending_time_list[i] = time.time()
                client_socket.sendto(message.encode('utf-8'),('127.0.0.1',9801))
                req_sent += 1
                # print("req_send : ", req_sent)
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
    prev_good = True
    while True:
        if len(offset_list)==lines_recv: break
        # with lock :
        #     for j in range (burst_size) :
        try: data,addr = client_socket.recvfrom(8192)    
        except TimeoutException: continue

        message_recv = data.decode('utf-8')
        x = message_recv.find('\n')
        offset = int(message_recv[8:x])
        receiving_time_list[offset//1448] = time.time()
        rtt_time_list[offset//1448] = receiving_time_list[offset//1448] - sending_time_list[offset//1448]

        message_recv = message_recv[x+1:]
        y = message_recv.find('\n')
        num_bytes = int(message_recv[10:y])
        message_recv = message_recv[y+2:]


        # if (message_recv[0:7]=="quished") : 
        #     if prev_good == True : 
        #         burst_size /= 2
        #         sleep_time += 0.01
        #         prev_good = False
        #     squished += 1
        #     print(burst_size)
        #     print(prev_good)
        #     continue

        received_lines[offset//1448] = True
        # if lines_recv <= 1000 :
        #     rtt_sum = 0
        #     count = 0
        #     for i in range (len(received_lines)) :
        #         if received_lines[i] : 
        #             rtt_sum += rtt_time_list[i]
        #             count += 1
        #     # print("rttsum/count :", rtt_sum/count)
        #     sleep_time = max(0.05,((rtt_sum/count)+0.005)*round(burst_size))
        
        burst_size_list[lines_recv] = burst_size
        # burst_size += 1/burst_size
        prev_good = True
        if received[offset//1448]: continue
        data_list[offset//1448] = message_recv
        line_num_list.remove(offset//1448)
        received[offset//1448] = True
        lines_recv += 1
        # print("Length:",len(offset_list))
        print(lines_recv)
        print("Squished :", squished)
        print("sleep time : ", sleep_time)
        print("Burst size :", burst_size)
        print()


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
    client_socket.sendto(submit.encode('utf-8'),('127.0.0.1',9801))
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
# print(rtt_time_list)
print(sum(rtt_time_list)/len(rtt_time_list))

y = [i for i in range (len(offset_list))]
plt.figure(figsize=(20,15))
plt.scatter(sending_time_list,y,label = "Offset sent",c="blue")
plt.scatter(receiving_time_list,y,label = "Offset received",c="red")
plt.xlabel('Time (in ms)',fontsize = 18)
plt.ylabel('Offset', fontsize = 18)
plt.xticks(fontsize = 18)
plt.yticks(fontsize = 18)
plt.legend()
plt.savefig("seq_trace.jpg")
plt.close()


plt.figure(figsize=(20,15))
plt.plot(y, burst_size_list, linestyle='-', marker='o')
plt.xlabel('Lines received',fontsize = 18)
plt.ylabel('Burst size', fontsize = 18)
plt.xticks(fontsize = 18)
plt.yticks(fontsize = 18)
plt.savefig("burst.jpg")
plt.close()