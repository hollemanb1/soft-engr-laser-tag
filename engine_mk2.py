"""
engine.py mk2 - Photon Laser Tag Engine (2nd Edition) - 9/30/25

Protocols: 
- Start Code: "202" (must wait 3 seconds after start_game())
- Stop code: "221" (must send 3 times)
- Event format: "ATTACKER:TARGER" (str, no JSON)
    ** TARGET can be hardware_id OR special codes "43" or "53"
- Event Acknowledgement: Plain string response each event ("Okay", "Acknowledged")

Data Model (memory only):
- Player keyed by hardware_id; tracks username, team, score

Networking Defaults:
- Receiving Port (Hits): 7501
- Sending Port (Attacks, Start/Stop, Join Broadcasts): 7500 (self.ip)

"""

# Import Statements
import threading # Cause we multitask around here
import socket # UDP sockets
import queue # Data Structure of choice
import time # For clock
import random # random hardware IDs

# | Scoring Rules |
STANDARD_HIT = 10 # 10 Points for P2P Combat
BASE_43_HIT = 100 # 100 Points for Hitting Base 43
BASE_53_HIT = 500 # 500 Points for Hitting Base 53


# | Player Object Initialization | 
class Player:
    def __init__(self, hw_id: str, username: str, team: str): # 3 Strings (Hardware ID, Username, and Team)
        self.hw_id    = hw_id # Key used for Event Handling
        self.username = username
        self.team     = team
        self.score    = 0 # Score initializes to 0 for game start
        
# | Main Game Engine |
class GameEngine:
    def __init__(self, ip="127.0.0.1", send_port=7500, recv_port=7501, game_time=300): #Initialized Values for Game Settings (Should NOT Change)
        self.players: dict[str, Player] = {} # Dictionary to hold the list of players
        
        self.time_left = game_time
        self.running = False
        
        #Networking
        self.ip = ip # Location where the Traffic Generator is Located (127.0.0.1)
        self.send_port = send_port # We send signals TO port 7500 (The Generator)
        self.recv_port = recv_port # We receive signals INTO port 7501
        
        self.event_queue: queue.Queue[tuple[str,str]] = queue.Queue() # Event Queue holds tuples (attacker, target)
        self.send_queue: queue.Queue[str]             = queue.Queue() # Send Queue holds strings
        
        # UDP Sockets
        self.recv_sock = None
        self.send_sock = None
        
        self._threads: list[threading.Thread] = [] # Threads if desired
        
    # Function to Change the Target IP for outgoing messages (before game start)
    def change_ip(self, new_ip: str):
        self.ip = new_ip
        print(f"[engine] send target ip =  {self.ip}")
        
    # | Public API |
    def start_game(self):
        """Start the Network and Game timer, wait 3 seconds --> send Start Code '202'"""
        if self.running:
            return
        self.running = True
        
        # Socket Setup
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Receiving Socket
        self.recv_sock.bind(("0.0.0.0", self.recv_sock))
        self.recv_sock.settimeout(1.0)
        
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Initialize Listen, Send, Timer Threads
        self._start_thread(self._listen_loop, name="listen")
        self._start_thread(self._send_loop, name="send")
        self._start_thread(self._game_loop, name="game")
        
        # Start Thread (On own delayed thread so UI not blocked)
        self._start_thread(self._delayed_start_code, name="start_code")
        
        print("[engine] Game Started!")
    
    # Stop Game Function    
    def stop_game(self):
        """Sends Stop Codes, halts threads, closes sockets"""
        if not self.running:
            return
        
    # | Necessary Threads |
    def _listen_loop(self):
        """Recieves plain strings; expects each packet formatted as 'ATTACKER:TARGET"""
        while self.running:
            try: #Try-Catch block cause things be getting freaky
                data, _ = self.recv_sock.recvfrom(2048)
                msg = data.decode(errors="ignore").strip()
                if not msg:
                    continue
                
                # EXACTLY ONE COLON
                if ":" not in msg:
                    #Not a Valid Hit Log
                    print(f"[engine] Unknown Packet (ignored): {msg}")
                    # Reply so generator isn't left haning
                    self.send_text("OK")
                    continue
                
                attacker, target = msg.split(":", 1) # Parse each message by splitting at the colon
                attacker = attacker.strip() # Removes whitespace
                target = target.strip()
                
                if attacker and target:
                    self.event_queue.put((attacker, target)) #If receives a valid attacker and target, send message
                else:
                    self.send_text("ERR: bad-format") #Error Message: Incorrect Format for message (missing target, missing attacker, extra info, etc...)
                    print(f"[engine] Bad packet (ignored): {msg}")
                    
            except socket.timeout: #In case something goes wrong
                continue
            except OSError:
                break
            except Exception as e:
                print(f"[engine] Listen error: {e}") # Catch-All Statement for random errors
                print("bruh")
                
    def _send_loop(self):
        """Takes data from send queue and transmits strings to generator through ip and send port"""
        while self.running or not self.send_queue.empty():
            try:
                msg = self.send_queue.get(timeout=0.5)
                line = msg if isinstance(msg, str) else str(msg)
            except queue.Empty:
                continue
            except OSError:
                break
            except Exception as e:
                print(f"[engine] Send error: {e}")
                    
    def _game_loop(self):
        """Game Countdown; on zero, send stop code and halt program"""
        while self.running and self.time_left > 0:
            time.sleep(1) # Wait 1 milisecond
            self.time_left -= 1 # Decremement Time Remaining
            
        if not self.running: # Don't double start
            return
        
        # Game Over
        self.stop_game()
        
    def _delayed_start_code(self):
        """Sleep for 3 seconds and start game AFTER (emit start code '202' One time)"""
        t0 = time.time()
        while self.running and (time.time() - t0) < 3.0: # 3 Second Wait before game start
            time.sleep(0.05)
            if self.running:
                self.send_code("202")
                
    # | Thread Helper |
    def _start_thread(self, target, name: str = ""): # Helps Initialize New Threads
        th = threading.Thread(target=target, daemon=True, name=f"engine-{name}" if name else None)
        self.threads.append(th)
        th.start() 