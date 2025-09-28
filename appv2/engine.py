"""
engine.py
----------
Handles ALL game logic and (optional) network transport.

Responsibilities:
- Hold the current game state (players, scores, health, timer).
- Provide functions: join_player, hit_player, remove_player.
- Optionally spin up UDP listener/sender threads.
- Maintain a queue of incoming events (from network OR test client).
- Provide process_event() to apply events to the game state.

Why keep this separate?
- Keeps logic + networking away from the UI.
- Makes it testable (you can feed fake events in without Qt).
"""


"""
engine.py
---------
Minimal game engine for the Photon scoreboard project.

- Holds game state (players, scores, health, timer).
- Provides actions: join_player, hit_player, remove_player.
- Manages an event queue (from UDP/test client).
- Can start/stop UDP networking threads.
"""

import threading
import socket
import json
import queue
import time


# --- Basic player object ---
class Player:
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username
        self.score = 0

# --- Main game engine ---
class GameEngine:
    def __init__(self, ip="127.0.0.1", send_port=7500, recv_port=7501, game_time=30):
        self.players = {}             # dict of user_id -> Player
        self.time_left = game_time
        self.running = False

        # Networking setup
        self.ip = ip
        self.send_port = send_port
        self.recv_port = recv_port

        self.event_queue = queue.Queue()
        self.send_queue = queue.Queue()

        self.recv_sock = None
        self.send_sock = None

    # --- Change IP Addr ---
    def change_ip(self, new_ip):
        self.ip = new_ip
        print(f"ip = {self.ip}")

    # ---------------------------
    # Public API
    # ---------------------------
    def start_game(self):
        """Start networking + game timer."""
        if self.running:
            return
        self.running = True

        time.sleep(3)
        self.send_queue.put("202")

        # setup sockets
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(("0.0.0.0", self.recv_port))
        self.recv_sock.settimeout(1.0)

        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # start listener + sender + timer threads
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._send_loop, daemon=True).start()
        threading.Thread(target=self._game_loop, daemon=True).start()

        print("Game started.")

    def stop_game(self):
        """Stop networking + cleanup."""
        self.running = False
        time.sleep(0.5)
        if self.recv_sock:
            self.recv_sock.close()
        if self.send_sock:
            self.send_sock.close()
        print("Game stopped.")

    def process_pending_events(self):
        """Drain queued events and apply to game state."""
        while not self.event_queue.empty():
            event = self.event_queue.get()
            self._process_event(event)

    # ---------------------------
    # Event handling
    # ---------------------------
    def _process_event(self, event):
        action = event.get("action")

        if action == "hit":
            id1, id2 = event["ID1"], event["ID2"]
            score = event["scoreUpdate"]
            self.hit_player(id1, id2, score)

        else:
            print(f"Unknown event: {event}")

    def join_player(self, user_id, username):
        if user_id not in self.players:
            self.players[user_id] = Player(user_id, username)
            print(f"Player joined: {username} ({user_id})")

    def hit_player(self, id1, id2, score_update, health_update):
        if id1 in self.players:
            self.players[id1].score += score_update
        if id2 in self.players:
            self.players[id2].score -= score_update
        print(f"Hit: {id1} -> {id2} (+{score_update})")

    def remove_player(self, user_id):
        if user_id in self.players:
            print(f"Player removed: {self.players[user_id].username}")
            del self.players[user_id]

    # ---------------------------
    # Threads
    # ---------------------------
    def _listen_loop(self):
        while self.running:
            try:
                data, _ = self.recv_sock.recvfrom(2048)
                event = json.loads(data.decode())
                self.event_queue.put(event)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Listen error: {e}")

    def _send_loop(self):
        while self.running:
            try:
                msg = self.send_queue.get(timeout=0.5)
                self.send_sock.sendto(msg.encode(), (self.ip, self.send_port))
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Send error: {e}")

    def _game_loop(self):
        while self.running and self.time_left > 0:
            time.sleep(1)
            self.time_left -= 1
        # notify game over
        for _ in range(3):
            self.send_queue.put("221")
            time.sleep(0.1)
        self.stop_game()

