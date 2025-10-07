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
        
        # Turn running marker off
        self.running = False
        
        # Buffer time
        time.sleep(0.2)
        
        # Close Sockets
        try:
            if self.recv_sock:
                self.recv_sock.accept
        finally:
            self.recv_sock = None
            
        try:
            if self.send_sock:
                self.send_sock.close()
        finally:
            self.send_sock = None
            
        print("[engine] Game stopped")
        
    def join_player(self, username: str):
        """Add new player with auto-gen hardware ID/team"""
        
        # Generate a random 4-digit hex hardware ID
        rand_num = random.randint(1, 9999)
        hw_id = f"hw0x{rand_num:04x}"
        
        #Assign team (Even = Red, Odd = Green)
        team = "red" if rand_num % 2 == 0 else "green"
        
        # Add new player to Player List
        if hw_id not in self.players:
            self.players[hw_id] = Player(hw_id, username, team)
            print(f"[engine] Player joined: {username} ({hw_id}) [{team}]")
        else:
            # If collision (unlikely), regenrate player
            print(f"[engine] Player joined: {username} ({hw_id}) [{team}]")
            return self.join_player(username)
        
        # Register Broadcast
        self.send_text(f"REG: {hw_id}:{username}:{team}")
        
    # Remove Specific Player    
    def remove_player(self, hw_id: str):
        if hw_id in self.players:
            print(f"[engine] Player removed: {self.players[hw_id].username} ({hw_id})")
            del self.players[hw_id]
            
    # Clear Player List
    def clear_player_list(self):
        for hw_id in self.players:
            print(f"[engine] Player removed: {self.players[hw_id].username} ({hw_id})")
            del self.players[hw_id]  
            
    # | Network Help |
    def send_code(self, code: str):
        """Queue code to be sent ('202', '221')"""
        self.send_queue.put(str(code))
        
    def send_text(self, text: str):
        """Queue a string message to be sent"""
        self.send_queue.put(str(text)) 
        
    # |Event Application (Internal) |
    def _apply_hit(self, attacker_hwid: str, target_code: str):
        """Apply the scoring/broadcast rules for incoming 'A:B' string"""
        attacker = self.players.get(attacker_hwid)
        if attacker is None:
            self.send_text("ERR:unknown-attacker")
            print(f"[engine] Ignored event: unknown attacker '{attacker_hwid}'")
            return
        
        # | Base Hits |
        if target_code == "43": # Green Base Hit: Red Team + 100
            if attacker.team == "red":
                attacker.score += BASE_43_HIT
                print(f"[engine] Red Base Score! {attacker.username} + {BASE_43_HIT}")
                self.send_code("43")
                return
            
        if target_code == "53": # Green Base Hit: Red Team + 100
            if attacker.team == "green":
                attacker.score += BASE_53_HIT
                print(f"[engine] Green Base Score! {attacker.username} + {BASE_53_HIT}")
                self.send_code("53")
                return
            
        # | Player Hits |
        target = self.players.get(target_code)
        if target is None:
            self.send_text("ERR:unknown-target")
            print(f"[engine] Ignored event: unknown target '{target_code}")
            return
        
        if attacker.team == target.team: # Friendly Fire (-10 Points)
            attacker.score -= 10
            target.score -= 10
            print(f"[engine] Friendly Fire: {attacker.username} ({attacker.hw_id})"
                  f"hit {target.username} ({target.hw_id}), -10 each")
            
            # Broadcast Equipment IDs
            self.send_code(attacker.hw_id)
            self.send_code(target.hw_id)
            return
            
        # Enemy Hit (Attacker +10 Points)
        attacker.score += STANDARD_HIT
        print(f"[engine] Ebemy hit: {attacker.username} ({attacker.hw_id})"
              f"hit {target.username} ({target.hw_id}), -{STANDARD_HIT}")
        
        # Broadcast Target's Equipment ID
        self.send_code(target.hw_id)
                  
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