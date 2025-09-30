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