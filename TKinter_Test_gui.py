import tkinter as tk
from tkinter import ttk
import random
import time

# --- Placeholder Data (will come from JSON later) ---
players = [
    {"name": "Player 1", "score": 100},
    {"name": "Player 2", "score": 90},
    {"name": "Player 3", "score": 80},
]

notifications = []  # list of recent events

# --- Setup Root Window ---
root = tk.Tk()
root.title("Laser Tag Scoreboard")
root.geometry("600x400")
root.configure(bg="black")

# --- Top Timer ---
timer_var = tk.StringVar(value="Time Left: 10")
timer_label = tk.Label(root, textvariable=timer_var, font=("Helvetica", 16), bg="black", fg="white")
timer_label.pack(pady=5)

# --- Main Frame with Two Columns ---
main_frame = tk.Frame(root, bg="black")
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# --- Scoreboard (Left Side) ---
scoreboard_frame = tk.Frame(main_frame, bg="black")
scoreboard_frame.pack(side="left", fill="y", padx=10)

score_labels = []  # store references so we can update later

header_score = tk.Label(scoreboard_frame, text="SCORE", font=("Helvetica", 14, "bold"), fg="yellow", bg="black")
header_name = tk.Label(scoreboard_frame, text="NAME", font=("Helvetica", 14, "bold"), fg="yellow", bg="black")
header_score.grid(row=0, column=0, padx=5, pady=2)
header_name.grid(row=0, column=1, padx=5, pady=2)

for i, p in enumerate(players, start=1):
    score_lbl = tk.Label(scoreboard_frame, text=p["score"], font=("Helvetica", 12), fg="white", bg="black")
    name_lbl = tk.Label(scoreboard_frame, text=p["name"], font=("Helvetica", 12), fg="white", bg="black")
    score_lbl.grid(row=i, column=0, padx=5, pady=2, sticky="w")
    name_lbl.grid(row=i, column=1, padx=5, pady=2, sticky="w")
    score_labels.append(score_lbl)

# --- Notifications Panel (Right Side) ---
notif_frame = tk.Frame(main_frame, bg="black")
notif_frame.pack(side="right", fill="both", expand=True, padx=10)

notif_label = tk.Label(notif_frame, text="Recent Actions", font=("Helvetica", 14, "bold"), fg="yellow", bg="black")
notif_label.pack(anchor="w")

notif_text = tk.Text(notif_frame, height=10, width=30, bg="gray10", fg="white", wrap="word")
notif_text.pack(fill="both", expand=True)

# --- Timer Countdown Logic ---
time_left = 10

def update_timer():
    global time_left
    if time_left > 0:
        time_left -= 1
        timer_var.set(f"Time Left: {time_left}")
        root.after(1000, update_timer)
    else:
        timer_var.set("GAME OVER")
        notif_text.insert("end", "Game Over!\n")
        notif_text.see("end")

# --- Fake Notifications for Testing ---
def add_fake_notification():
    p1, p2 = random.sample(players, 2)
    message = f"{p1['name']} shot {p2['name']}"
    notif_text.insert("end", message + "\n")
    notif_text.see("end")
    root.after(3000, add_fake_notification)

# --- Start Loops ---
root.after(1000, update_timer)
root.after(3000, add_fake_notification)

# --- Run Application ---
root.mainloop()
