import socket
import threading
import time
import queue
from queue import Queue


#Constant Values
DEFAULT_IP = "127.0.0.1"
SEND_PORT = 7500
RECEIVE_PORT = 7501

# Vars for making the addresses modifiable
current_ip = DEFAULT_IP
send_port = SEND_PORT
receive_port = RECEIVE_PORT

game_time = 30
running = True

time.sleep(0.1) # gives another program time to modify global vars

# ~~~~ Port Setup ~~~~

# Listening Socket:
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# AF_INET -> IPV4, SOCK_DGRAM -> UDP
recv_sock.bind(("0.0.0.0", receive_port)) # (network device, port)
recv_sock.settimeout(1.0) # gives max time to wait for input b4 restarting loop

# Sending Socket:
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Global Mailboxes
event_queue = Queue()
send_queue = Queue()

# ~~~~ end port setup ~~~~


# ~~~~ Thread Loops ~~~~

# ~~~Listening loop~~~
def Listen_Loop():
    global running
    while running:
        try:
            data, addr = recv_sock.recvfrom(2048)# 1024 is max bytes per packet
            msg = data.decode()
            event = {"name": msg}
            event_queue.put(event) # puts message in event queue
            print(f"Received message: {event}")
        except socket.timeout:
            pass  # nothing came in, just check running and loop again
# ~~~end loop~~~

# ~~~Sending Loop~~~
def Send_Loop():
    global running
    while running:
        try:
            msg = send_queue.get(timeout=0.5)  # wait up to 0.5s for message
            send_sock.sendto(msg.encode(), (current_ip, send_port))
            print(f"Sent message: {msg}")
        except queue.Empty:
            pass
# ~~~end loop~~~

# ~~~Game Tracker Loop~~~
def Game_Loop():
    global game_time, running
    while running and game_time > 0:
        time.sleep(1)
        game_time -=1
        # print(f"Time left: {game_time} seconds")  # optional for screen

    for i in range(3):
        send_queue.put("221")
        time.sleep(0.1)
    Times_Up()
# ~~~end loop~~~

# ~~~End Game Loop~~~
def Times_Up():
    global running
    running = False
    
    time.sleep(0.5)

    recv_sock.close()
    send_sock.close()
# ~~~end loop~~~


# Setup Threads:
listener_thread = threading.Thread(target = Listen_Loop)
sender_thread = threading.Thread(target = Send_Loop)
game_thread = threading.Thread(target = Game_Loop)

listener_thread.start()
sender_thread.start()
game_thread.start()

# Do stuff loop
def Mainloop():


    while running:
        if not event_queue.empty():
            event = event_queue.get()
            print(f"Received event: {event}")


            # if event = case1
            # else if event = case2
            # else if event = case3
            # else


