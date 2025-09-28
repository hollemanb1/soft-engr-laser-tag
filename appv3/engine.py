"""
engine.py
---------
Photon game engine aligned to the teacher's traffic generator.

Protocol alignment:
- Start code: plain "202" sent ~3s after start_game()
- Stop code: plain "221" sent 3x at game end
- Event format from generator: "ATTACKER:TARGET" (plain string, no JSON)
  * TARGET may be another hardware_id OR special codes "43" or "53"
- Per-event acknowledgement: send a short plain string back each time (e.g., "OK")

Data model (in-memory only):
- Player keyed by hardware_id; tracks username, team, score

Networking defaults (match generator v2):
- Receive (hits) on port 7501
- Send (acks / start / stop / join broadcasts) to port 7500 at self.ip
"""

import threading
import socket
import queue
import time


# ---- Scoring rules ----
NORMAL_HIT_POINTS = 10
BASE_43_POINTS    = 100
BASE_53_POINTS    = 500


# --- Basic player object ---
class Player:
    def __init__(self, hw_id: str, username: str, team: str):
        self.hw_id   = hw_id       # hardware ID is the canonical in-game key
        self.username = username
        self.team     = team       # "red" or "green" (free-form string)
        self.score    = 0


# --- Main game engine ---
class GameEngine:
    def __init__(self, ip="127.0.0.1", send_port=7500, recv_port=7501, game_time=30):
        # Active roster for the current match (keyed by hardware_id)
        self.players: dict[str, Player] = {}

        # Game control
        self.time_left = game_time
        self.running   = False

        # Networking setup
        self.ip         = ip          # where we SEND (generator is listening on this host)
        self.send_port  = send_port   # generator receives on 7500
        self.recv_port  = recv_port   # we receive on 7501

        # Queues (strings in send_queue; tuples (attacker, target) in event_queue)
        self.event_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.send_queue:  queue.Queue[str]             = queue.Queue()

        # Sockets
        self.recv_sock = None
        self.send_sock = None

        # Internal thread refs (optional)
        self._threads: list[threading.Thread] = []

    # --- Change target IP for outgoing messages (before start) ---
    def change_ip(self, new_ip: str):
        self.ip = new_ip
        print(f"[engine] send target ip = {self.ip}")

    # ---------------------------
    # Public API
    # ---------------------------
    def start_game(self):
        """Start networking + game timer; emit start code '202' after ~3s."""
        if self.running:
            return
        self.running = True

        # setup sockets
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(("0.0.0.0", self.recv_port))
        self.recv_sock.settimeout(1.0)

        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Broadcast not required for local generator, but harmless to keep:
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # start listener + sender + timer threads
        self._start_thread(self._listen_loop, name="listen")
        self._start_thread(self._send_loop,   name="send")
        self._start_thread(self._game_loop,   name="game")

        # delayed start code on its own thread to avoid blocking UI
        self._start_thread(self._delayed_start_code, name="start_code")

        print("[engine] Game started.")

    def stop_game(self):
        """Send stop codes, halt threads, close sockets."""
        if not self.running:
            return

        # Send stop code (221) three times quickly
        for _ in range(3):
            self.send_code("221")
            time.sleep(0.1)

        # Flip running off; loops will end
        self.running = False

        # Give loops a moment to exit gracefully
        time.sleep(0.2)

        # Close sockets
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

        print("[engine] Game stopped.")

    def process_pending_events(self):
        """Drain queued (attacker, target) tuples and apply to game state."""
        while not self.event_queue.empty():
            attacker, target = self.event_queue.get()
            self._apply_hit(attacker, target)

    # ---------------------------
    # Player management
    # ---------------------------
    def join_player(self, username: str):
        """Add a new active player with auto-generated hardware ID and team."""

        # Generate a random 4-digit hex hardware ID
        rand_num = random.randint(1, 9999)
        hw_id = f"hw0x{rand_num:04x}"

        # Assign team based on odd/even rule
        team = "red" if rand_num % 2 == 1 else "green"

        # Add to active players
        if hw_id not in self.players:
            self.players[hw_id] = Player(hw_id, username, team)
            print(f"[engine] Player joined: {username} ({hw_id}) [{team}]")
        else:
            # Very unlikely collision; regenerate
            print(f"[engine] Collision on {hw_id}, regenerating...")
            return self.join_player(username)

        # Broadcast registration
        self.send_text(f"REG:{hw_id}:{username}:{team}")


    def remove_player(self, hw_id: str):
        if hw_id in self.players:
            print(f"[engine] Player removed: {self.players[hw_id].username} ({hw_id})")
            del self.players[hw_id]

    # ---------------------------
    # Networking helpers
    # ---------------------------
    def send_code(self, code: str):
        """Queue a plain control code to be sent (e.g., '202', '221')."""
        self.send_queue.put(str(code))

    def send_text(self, text: str):
        """Queue an arbitrary plain text line to be sent."""
        self.send_queue.put(str(text))

    # ---------------------------
    # Internal: event application
    # ---------------------------
    def _apply_hit(self, attacker_hwid: str, target_code: str):
        """Apply scoring for an incoming 'A:B' string event."""
        # Validate attacker exists
        attacker = self.players.get(attacker_hwid)
        if attacker is None:
            self.send_text("ERR:unknown-attacker")
            print(f"[engine] Ignored event: unknown attacker '{attacker_hwid}'")
            return

        # Special targets: 43 / 53
        if target_code == "43":
            attacker.score += BASE_43_POINTS
            self.send_text("OK")
            return
        if target_code == "53":
            attacker.score += BASE_53_POINTS
            self.send_text("OK")
            return

        # Normal hit on another hardware ID
        target = self.players.get(target_code)
        if target is None:
            self.send_text("ERR:unknown-target")
            print(f"[engine] Ignored event: unknown target '{target_code}'")
            return

        # Friendly fire? (same team)
        if attacker.team == target.team:
            # No points awarded (neutral handling)
            self.send_text("OK")  # acknowledge anyway
            print(f"[engine] Friendly fire: {attacker_hwid} -> {target_code} (no score)")
            return

        # Enemy hit → award normal points to attacker
        attacker.score += NORMAL_HIT_POINTS
        self.send_text("OK")

    # ---------------------------
    # Threads
    # ---------------------------
    def _listen_loop(self):
        """Receive plain strings; expect 'ATTACKER:TARGET' per packet."""
        while self.running:
            try:
                data, _ = self.recv_sock.recvfrom(2048)
                msg = data.decode(errors="ignore").strip()
                if not msg:
                    continue

                # Expect exactly one colon
                if ":" not in msg:
                    # Not a hit packet; ignore quietly or log
                    print(f"[engine] Unknown packet (ignored): {msg}")
                    # Still reply something so generator doesn't hang
                    self.send_text("OK")
                    continue

                attacker, target = msg.split(":", 1)
                attacker = attacker.strip()
                target   = target.strip()

                if attacker and target:
                    self.event_queue.put((attacker, target))
                else:
                    self.send_text("ERR:bad-format")
                    print(f"[engine] Bad packet (ignored): {msg}")

            except socket.timeout:
                continue
            except OSError:
                # Likely socket closed during shutdown
                break
            except Exception as e:
                print(f"[engine] Listen error: {e}")

    def _send_loop(self):
        """Drains send_queue and transmits plain strings to (self.ip, self.send_port)."""
        while self.running or not self.send_queue.empty():
            try:
                msg = self.send_queue.get(timeout=0.5)
                line = msg if isinstance(msg, str) else str(msg)
                self.send_sock.sendto(line.encode(), (self.ip, self.send_port))
            except queue.Empty:
                continue
            except OSError:
                # Socket likely closed; exit loop
                break
            except Exception as e:
                print(f"[engine] Send error: {e}")

    def _game_loop(self):
        """Simple countdown; on zero, send stop code and halt."""
        while self.running and self.time_left > 0:
            time.sleep(1)
            self.time_left -= 1

        # If we exited because running flipped False elsewhere, don't double-stop
        if not self.running:
            return

        # Game over path
        self.stop_game()

    def _delayed_start_code(self):
        """Sleep ~3s after start and emit the start code '202' once."""
        # Small guard so a very quick stop doesn't still send 202
        t0 = time.time()
        while self.running and (time.time() - t0) < 3.0:
            time.sleep(0.05)
        if self.running:
            self.send_code("202")

    # ---------------------------
    # Thread helper
    # ---------------------------
    def _start_thread(self, target, name: str = ""):
        th = threading.Thread(target=target, daemon=True, name=f"engine-{name}" if name else None)
        self._threads.append(th)
        th.start()
