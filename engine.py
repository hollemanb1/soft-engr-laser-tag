"""
engine.py - Photon Laser Tag Engine (2nd Edition) - 9/30/25

Protocols: 
- Start Code: "202" (must wait 3 seconds after start_game())
- Stop code: "221" (must send 3 times)
- Event format: "ATTACKER:TARGER" (str, no JSON)
    ** TARGET can be hardware_id OR special codes "43" or "53"
- Event Acknowledgement: Plain string response each event ("Okay", "    ")

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
import pygame

# | Scoring Rules |
STANDARD_HIT = 10 # 10 Points for P2P Combat
BASE_43_HIT = 100 # 100 Points for Hitting Base 43
BASE_53_HIT = 100 # 500 Points for Hitting Base 53

# | Music Engine |
pygame.init()
pygame.mixer.init()
mp3_file = "Photon_Audio.mp3"
pygame.mixer.music.load(mp3_file)
pygame.mixer.music.set_volume(1)

# | Player Object Initialization | 
class Player:
    def __init__(self, hw_id: str, username: str, team: str): # 3 Strings (Hardware ID, Username, and Team)
        self.hw_id    = hw_id # Key used for Event Handling
        self.username = username
        self.team     = team
        self.score    = 0 # Score initializes to 0 for game start
        self.has_icon = False
        
        
        
# | Main Game Engine |
class GameEngine:
    def __init__(self, ip="127.0.0.1", send_port=7500, recv_port=7501, game_time=300): #Initialized Values for Game Settings (Should NOT Change)
        self.players: dict[int, Player] = {} # Dictionary to hold the list of players
        
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
        
    def start_music(self):
        pygame.mixer.music.play()    
        
    def change_ip(self, new_ip: str):
        self.ip = new_ip
        print(f"[engine] send target ip =  {self.ip}")
        
    # | Public API |
    def start_game(self):
        
        self.send_code(202)
        
        if self.running:
            return
        self.running = True
        
        # Socket Setup
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Receiving Socket
        self.recv_sock.bind(("0.0.0.0", self.recv_port))
        self.recv_sock.settimeout(1.0)
        
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Initialize Listen, Send, Timer Threads
        self._start_thread(self._listen_loop, name="listen")
        self._start_thread(self._send_loop, name="send")
        
        print("[engine] Game Started!")
    
    # Stop Game Function    
    def stop_game(self):
        """Sends Stop Codes, halts threads, closes sockets"""
        if not self.running:
            return

        for _ in range(3):
            self.send_code("221")
            time.sleep(0.05)
        
        pygame.mixer.music.stop()
        pygame.quit()
        
        # Turn running marker off
        self.running = False
        
        # Buffer time
        time.sleep(0.2)
        
        # Close Sockets
        try:
            if self.recv_sock:
                self.recv_sock.close()
        finally:
            self.recv_sock = None
        try:
            if self.send_sock:
                self.send_sock.close()
        finally:
            self.send_sock = None
            
        print("[engine] Game stopped")
        
    def join_player(self, username: str, hw_id: int):
        team = "red" if hw_id % 2 == 0 else "green"
        
        if hw_id not in self.players:
            self.players[hw_id] = Player(hw_id, username, team)
            self.send_queue.put(f"Player joined: {username} ({hw_id}) [{team}]")
            return True
        else:
            print("HWID Dupe")
            return False
        
        # Register Broadcast
        self.send_text(f"REG: {hw_id}:{username}:{team}")
        
            
    # Clear Player List
    def clear_player_list(self):
        self.players: dict[str, Player] = {}
        # for hw_id in self.players:
        #     print(f"[engine] Player removed: {self.players[hw_id].username} ({hw_id})")
        #     del self.players[hw_id]  
            
    # | Network Help |
    def send_code(self, code: str):
        self.send_queue.put(str(code))
        
    def send_text(self, text: str):
        self.send_queue.put(str(text)) 
        
    # |Event Application (Internal) |
    def _apply_hit(self, attacker_hwid: int, target_code: int):
        """Apply the scoring/broadcast rules for incoming 'A:B' string"""
        print(f"applying hit: attacker_hwid={attacker_hwid} target_code={target_code}")
        
        print("DEBUG - players dict keys:", list(self.players.keys()))
        print("DEBUG - attacker_hwid     :", repr(attacker_hwid))

        attacker = self.players.get(attacker_hwid)
        if attacker is None:
            self.send_text("ERR:unknown-attacker")
            print(f"[engine] Ignored event: unknown attacker '{attacker_hwid}'")
            return
        
        # | Base Hits |
        if target_code == 43: # Green Base Hit: Red Team + 100
            if attacker.team == "red":
                attacker.score += BASE_43_HIT
                attacker.has_icon = True
                print(f"[engine] Red Base Score! {attacker.username} + {BASE_43_HIT}")
                self.send_code("43")
                return
            
        if target_code == 53: # Green Base Hit
            if attacker.team == "green":
                attacker.score += BASE_53_HIT
                attacker.has_icon = True
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
        print(f"[engine] Enemy hit: {attacker.username} ({attacker.hw_id})"
              f"hit {target.username} ({target.hw_id}), +{STANDARD_HIT}")
        
        # Broadcast Target's Equipment ID
        self.send_code(f"Okay, {target.hw_id}")
        print("\n")
                  
    # | Necessary Threads |
    def _listen_loop(self):
        """Recieves plain strings; expects each packet formatted as 'ATTACKER:TARGET"""
        while self.running:
            try: #Try-Catch block cause things be getting freaky
                data, _ = self.recv_sock.recvfrom(2048)
                msg = data.decode(errors="ignore").strip()
                if not msg:
                    continue
                print("\n")
                print(f"recieved packet: {msg}")
                
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
                
                print(f"attacker = {attacker}")
                print(f"target = {target}")

                try:
                    attacker_id = int(attacker)
                    target_id   = int(target)
                except ValueError:
                    self.send_text("ERR: bad-format")
                    print(f"[engine] Bad packet (non-numeric IDs): {msg}")
                    return

                self.event_queue.put((attacker_id, target_id))
                    
            except socket.timeout: #In case something goes wrong
                continue
            except OSError:
                break
            except Exception as e:
                print(f"[engine] Listen error: {e}") # Catch-All Statement for random errors
                print("bruh")
                
    def _send_loop(self):
        """Takes data from send queue and transmits strings to generator through ip and send port"""
        address  = (self.ip, self.send_port)
        while self.running or not self.send_queue.empty():
            try:
                msg = self.send_queue.get(timeout=0.1)
                line = msg if isinstance(msg, str) else str(msg)
            except queue.Empty:
                continue
            try:
                line = msg if isinstance(msg, str) else str(msg)
                self.send_sock.sendto(line.encode("utf-8", errors="ignore"), address)
            except OSError:
                break
            except Exception as e:
                print(f"[engine] Send error: {e}")
        

                
    # | Thread Helper |
    def _start_thread(self, target, name: str = ""): # Helps Initialize New Threads
        th = threading.Thread(target=target, daemon=True, name=f"engine-{name}" if name else None)
        self._threads.append(th)
        th.start() 
    
    def process_pending_events(self):
        """Drain queued (attacker, target) tuples and apply to game state."""
        while not self.event_queue.empty():
            attacker, target = self.event_queue.get()
            self._apply_hit(attacker, target)
