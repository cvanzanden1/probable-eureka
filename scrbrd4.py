import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog, colorchooser
import time
import json
from datetime import datetime
import os
import threading
import winsound
import random
from PIL import Image, ImageTk

class FootballScoreboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Electric Football Scoreboard - Control")
        self.root.geometry("1400x900")
        self.root.configure(bg="#006E33")

        # Game state variables
        self.team1_score = 0
        self.team2_score = 0
        self.team1_name = ""
        self.team2_name = ""
        self.seconds_remaining = 900
        self.clock_running = False
        self.quarter = 1
        self.down = 1
        self.yards_to_go = 10
        self.ball_on = 35
        self.box_score = []
        self.game_log = []
        self.team1_timeouts = 3
        self.team2_timeouts = 3
        self.team1_color = "#FF0000"
        self.team2_color = "#0000FF"
        self.possession = 1
        self.team1_stats = {"first_downs": 0, "total_yards": 0, "pass_yards": 0, "rush_yards": 0, "penalties": 0}
        self.team2_stats = {"first_downs": 0, "total_yards": 0, "pass_yards": 0, "rush_yards": 0, "penalties": 0}
        self.weather = "Clear"
        self.replay_active = False
        self.team1_logo = None
        self.team2_logo = None
        self.vibration_on = False
        self.play_seconds = 10

        # Audio files
        self.sounds = {
            "touchdown": "touchdown.wav",
            "field_goal": "field_goal.wav",
            "game_over": "game_over.wav",
            "kickoff": "kickoff.wav",
            "vibration": "vibration.wav"
        }

        # Initial setup
        self.get_team_names()
        self.setup_gui()
        self.setup_display_window()
        self.load_default_logos()
        self.start_kickoff()

    def setup_gui(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Game", command=self.save_game)
        file_menu.add_command(label="Load Game", command=self.load_game)
        file_menu.add_command(label="Export Log", command=self.export_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(expand=True, fill="both")

        # Top frame
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(pady=10)

        # Clock frame with weather
        self.clock_frame = ttk.LabelFrame(self.top_frame, text="Game Clock", padding=10)
        self.clock_frame.pack(side="left", padx=10)
        self.clock_label = ttk.Label(self.clock_frame, text=self.format_time(self.seconds_remaining), 
                                   font=("Arial", 36))
        self.clock_label.pack()
        self.weather_label = ttk.Label(self.clock_frame, text=f"Weather: {self.weather}", 
                                     font=("Arial", 12))
        self.weather_label.pack()
        clock_btn_frame = ttk.Frame(self.clock_frame)
        clock_btn_frame.pack(pady=5)
        ttk.Button(clock_btn_frame, text="Start", command=self.start_clock).pack(side="left", padx=2)
        ttk.Button(clock_btn_frame, text="Pause", command=self.pause_clock).pack(side="left", padx=2)
        ttk.Button(clock_btn_frame, text="Set Time", command=self.set_quarter_time).pack(side="left", padx=2)
        self.timeout_frame = ttk.Frame(self.clock_frame)
        self.timeout_frame.pack(pady=5)
        self.team1_timeout_label = ttk.Label(self.timeout_frame, 
                                           text=f"{self.team1_name} TO: {self.team1_timeouts}")
        self.team1_timeout_label.pack(side="left", padx=5)
        self.team2_timeout_label = ttk.Label(self.timeout_frame, 
                                           text=f"{self.team2_name} TO: {self.team2_timeouts}")
        self.team2_timeout_label.pack(side="left", padx=5)

        # Game info frame
        self.info_frame = ttk.LabelFrame(self.top_frame, text="Game Situation", padding=10)
        self.info_frame.pack(side="left", padx=10)
        self.quarter_label = ttk.Label(self.info_frame, text=f"Quarter: {self.quarter}", 
                                     font=("Arial", 16))
        self.quarter_label.pack()
        self.field_label = ttk.Label(self.info_frame, 
                                   text=f"Ball on: {self.format_yard_line(self.ball_on)}", 
                                   font=("Arial", 16))
        self.field_label.pack()
        self.down_label = ttk.Label(self.info_frame, 
                                  text=f"Down: {self.down} & {self.yards_to_go}", 
                                  font=("Arial", 16))
        self.down_label.pack()
        self.possession_label = ttk.Label(self.info_frame, 
                                        text=f"Possession: {self.team1_name if self.possession == 1 else self.team2_name}",
                                        font=("Arial", 16))
        self.possession_label.pack()
        
        # Play control frame
        play_frame = ttk.Frame(self.info_frame)
        play_frame.pack(pady=5)
        ttk.Button(play_frame, text="Next Play", command=self.next_play).pack(side="left", padx=2)
        ttk.Button(play_frame, text="Switch Possession", command=self.switch_possession).pack(side="left", padx=2)
        ttk.Button(play_frame, text="Penalty", command=self.add_penalty).pack(side="left", padx=2)
        ttk.Button(play_frame, text="Replay Review", command=self.start_replay).pack(side="left", padx=2)
        ttk.Button(play_frame, text="Set Ball Position", command=self.set_ball_position).pack(side="left", padx=2)
        ttk.Button(play_frame, text="Start Play Timer", command=self.start_play_timer).pack(side="left", padx=2)

        # Preset play buttons frame
        preset_frame = ttk.Frame(self.info_frame)
        preset_frame.pack(pady=5)
        ttk.Button(preset_frame, text="Gain 5", command=lambda: self.preset_play("rush", 5)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="Gain 10", command=lambda: self.preset_play("rush", 10)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="Loss 2", command=lambda: self.preset_play("rush", -2)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="Touchdown", command=lambda: self.preset_play("rush", None)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="Turnover", command=self.switch_possession).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="Stop Play", command=lambda: self.preset_play("stop", 0)).pack(side="left", padx=2)

        # Team frames with logos
        self.teams_frame = ttk.Frame(self.main_frame)
        self.teams_frame.pack(pady=10)
        
        self.team1_frame = ttk.LabelFrame(self.teams_frame, text=self.team1_name, padding=10)
        self.team1_frame.pack(side="left", padx=20)
        self.team1_logo_label = ttk.Label(self.team1_frame)
        self.team1_logo_label.pack(pady=5)
        self.team1_label = ttk.Label(self.team1_frame, text="0", font=("Arial", 48), 
                                   foreground=self.team1_color)
        self.team1_label.pack(pady=10)
        self.create_score_buttons(self.team1_frame, 1)
        self.team1_stats_label = ttk.Label(self.team1_frame, 
                                         text=self.format_stats(self.team1_stats))
        self.team1_stats_label.pack(pady=5)
        ttk.Button(self.team1_frame, text="Timeout", command=lambda: self.use_timeout(1)).pack(pady=2)
        ttk.Button(self.team1_frame, text="Change Color", 
                  command=lambda: self.change_team_color(1)).pack(pady=2)
        ttk.Button(self.team1_frame, text="Load Logo", 
                  command=lambda: self.load_team_logo(1)).pack(pady=2)

        self.team2_frame = ttk.LabelFrame(self.teams_frame, text=self.team2_name, padding=10)
        self.team2_frame.pack(side="right", padx=20)
        self.team2_logo_label = ttk.Label(self.team2_frame)
        self.team2_logo_label.pack(pady=5)
        self.team2_label = ttk.Label(self.team2_frame, text="0", font=("Arial", 48), 
                                   foreground=self.team2_color)
        self.team2_label.pack(pady=10)
        self.create_score_buttons(self.team2_frame, 2)
        self.team2_stats_label = ttk.Label(self.team2_frame, 
                                         text=self.format_stats(self.team2_stats))
        self.team2_stats_label.pack(pady=5)
        ttk.Button(self.team2_frame, text="Timeout", command=lambda: self.use_timeout(2)).pack(pady=2)
        ttk.Button(self.team2_frame, text="Change Color", 
                  command=lambda: self.change_team_color(2)).pack(pady=2)
        ttk.Button(self.team2_frame, text="Load Logo", 
                  command=lambda: self.load_team_logo(2)).pack(pady=2)

        # Bottom frame
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(pady=10, fill="both", expand=True)
        
        self.box_frame = ttk.LabelFrame(self.bottom_frame, text="Box Score & Play Log", padding=10)
        self.box_frame.pack(side="left", padx=10, fill="both", expand=True)
        self.box_text = tk.Text(self.box_frame, height=18, width=70, font=("Arial", 12))
        self.box_text.pack()
        box_btn_frame = ttk.Frame(self.box_frame)
        box_btn_frame.pack(pady=5)
        ttk.Button(box_btn_frame, text="Undo Last", command=self.undo_score).pack(side="left", padx=2)
        ttk.Button(box_btn_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=2)

        # Field visualization
        self.field_frame = ttk.LabelFrame(self.bottom_frame, text="Field View", padding=10)
        self.field_frame.pack(side="right", padx=10)
        self.field_canvas = tk.Canvas(self.field_frame, width=300, height=200, bg="green")
        self.field_canvas.pack()
        self.draw_field()

        # Control frame
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(pady=10)
        ttk.Button(self.control_frame, text="Reset Game", command=self.reset_game).pack(side="left", padx=5)
        ttk.Button(self.control_frame, text="Simulate Play", command=self.simulate_play).pack(side="left", padx=5)
        ttk.Button(self.control_frame, text="Change Weather", command=self.change_weather).pack(side="left", padx=5)
        ttk.Button(self.control_frame, text="Toggle Overtime", command=self.toggle_overtime).pack(side="left", padx=5)
        ttk.Button(self.control_frame, text="Toggle Vibration", command=self.toggle_vibration).pack(side="left", padx=5)
        ttk.Button(self.control_frame, text="Set Play Time", command=self.set_play_time).pack(side="left", padx=5)

        self.overtime_active = tk.BooleanVar(value=False)
        self.update_clock()

    def setup_display_window(self):
        self.display_window = tk.Toplevel(self.root)
        self.display_window.title("Electric Football Scoreboard - Display")
        self.display_window.geometry("800x400")
        self.display_window.configure(bg="#006E33")
        self.display_window.protocol("WM_DELETE_WINDOW", lambda: None)

        display_frame = ttk.Frame(self.display_window, padding=20)
        display_frame.pack(expand=True, fill="both")

        self.display_clock_label = ttk.Label(display_frame, text=self.format_time(self.seconds_remaining), 
                                           font=("Arial", 72), background="#006E33", foreground="white")
        self.display_clock_label.pack(pady=20)

        score_frame = ttk.Frame(display_frame, style="Display.TFrame")
        score_frame.pack(pady=20)
        self.display_team1_label = ttk.Label(score_frame, text=f"{self.team1_name}: 0", 
                                           font=("Arial", 48), foreground=self.team1_color, 
                                           background="#006E33")
        self.display_team1_label.pack(side="left", padx=50)
        self.display_team2_label = ttk.Label(score_frame, text=f"{self.team2_name}: 0", 
                                           font=("Arial", 48), foreground=self.team2_color, 
                                           background="#006E33")
        self.display_team2_label.pack(side="right", padx=50)

        self.display_field_label = ttk.Label(display_frame, 
                                           text=f"Ball on: {self.format_yard_line(self.ball_on)}", 
                                           font=("Arial", 36), background="#006E33", foreground="white")
        self.display_field_label.pack(pady=20)

        style = ttk.Style()
        style.configure("Display.TFrame", background="#006E33")

    def create_score_buttons(self, frame, team):
        buttons = [
            ("Touchdown (6)", 6),
            ("Field Goal (3)", 3),
            ("Extra Point (1)", 1),
            ("Two-Point Conv (2)", 2),
            ("Safety (2)", 2)
        ]
        for text, points in buttons:
            ttk.Button(frame, text=text, 
                      command=lambda p=points: self.add_score(team, p)).pack(pady=2)

    def get_team_names(self):
        self.team1_name = simpledialog.askstring("Input", "Enter Team 1 Name:", parent=self.root) or "Team 1"
        self.team2_name = simpledialog.askstring("Input", "Enter Team 2 Name:", parent=self.root) or "Team 2"

    def format_time(self, seconds):
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def format_yard_line(self, yard):
        if yard == 50:
            return "50"
        elif yard < 50:
            return f"{self.team2_name} {yard}"
        else:
            return f"{self.team1_name} {100 - yard}"

    def format_stats(self, stats):
        return (f"FD: {stats['first_downs']} | Tot: {stats['total_yards']} | "
                f"Pass: {stats['pass_yards']} | Rush: {stats['rush_yards']} | Pen: {stats['penalties']}")

    def start_kickoff(self):
        kicking_team = simpledialog.askinteger("Kickoff", "Which team kicks off? (1 or 2):", 
                                             minvalue=1, maxvalue=2) or 1
        self.possession = 2 if kicking_team == 1 else 1
        kick_distance = simpledialog.askinteger("Kickoff", "Enter kickoff distance (yards):", 
                                              minvalue=20, maxvalue=80) or 65
        return_yards = simpledialog.askinteger("Kickoff", "Enter return yards:", 
                                             minvalue=0, maxvalue=100) or 20
        
        self.ball_on = 100 - kick_distance + return_yards
        self.ball_on = max(1, min(99, self.ball_on))
        
        self.update_play_display()
        self.update_display_window()
        self.possession_label.config(text=f"Possession: {self.team1_name if self.possession == 1 else self.team2_name}")
        self.box_score.append(f"Q{self.quarter} {self.format_time(self.seconds_remaining)} - "
                            f"Kickoff: {self.team1_name if kicking_team == 1 else self.team2_name} "
                            f"to {self.format_yard_line(self.ball_on)}")
        self.update_box_score()
        self.draw_field()
        self.play_sound("kickoff")

    def set_ball_position(self):
        side = simpledialog.askinteger("Field Side", "Which side? (1 for Team 1, 2 for Team 2):", 
                                     minvalue=1, maxvalue=2)
        yard_line = simpledialog.askinteger("Yard Line", "Enter yard line (1-50):", 
                                          minvalue=1, maxvalue=50)
        if side and yard_line:
            if side == 1:
                self.ball_on = 100 - yard_line
            else:
                self.ball_on = yard_line
            self.update_play_display()
            self.update_display_window()
            self.draw_field()
            self.box_score.append(f"Q{self.quarter} {self.format_time(self.seconds_remaining)} - "
                                f"Ball moved to {self.format_yard_line(self.ball_on)}")
            self.update_box_score()

    def start_clock(self):
        self.clock_running = True

    def pause_clock(self):
        self.clock_running = False

    def update_clock(self):
        if self.clock_running and self.seconds_remaining > 0:
            self.seconds_remaining -= 1
            self.clock_label.config(text=self.format_time(self.seconds_remaining))
            self.display_clock_label.config(text=self.format_time(self.seconds_remaining))
            if self.seconds_remaining == 0:
                self.clock_running = False
                self.next_quarter()
        self.root.after(1000, self.update_clock)

    def next_quarter(self):
        if self.quarter < 4:
            self.quarter += 1
            self.seconds_remaining = 900
            if self.quarter == 3:
                self.team1_timeouts = 3
                self.team2_timeouts = 3
                self.update_timeout_labels()
            self.quarter_label.config(text=f"Quarter: {self.quarter}")
            messagebox.showinfo("Quarter Ended", f"Starting Quarter {self.quarter}")
            self.start_kickoff()
        elif not self.overtime_active.get() or self.team1_score != self.team2_score:
            self.end_game()
        else:
            self.start_overtime()

    def start_overtime(self):
        self.quarter = "OT"
        self.seconds_remaining = 300
        self.quarter_label.config(text="Quarter: OT")
        self.team1_timeouts = 1
        self.team2_timeouts = 1
        self.update_timeout_labels()
        messagebox.showinfo("Overtime", "Starting Overtime Period")
        self.start_kickoff()

    def end_game(self):
        winner = (self.team1_name if self.team1_score > self.team2_score 
                 else self.team2_name if self.team2_score > self.team1_score else "Tie")
        messagebox.showinfo("Game Over", f"Final Score:\n"
                          f"{self.team1_name}: {self.team1_score}\n"
                          f"{self.team2_name}: {self.team2_score}\n"
                          f"Winner: {winner}")
        self.play_sound("game_over")

    def next_play(self):
        self.start_play_timer()
        play_type = simpledialog.askstring("Play Type", "Enter play type (pass/rush/stop):", 
                                        parent=self.root) or "rush"
        yards = simpledialog.askinteger("Yards", "Yards gained this play:", 
                                      minvalue=-99, maxvalue=99) or 0
        self.update_field_position(yards)
        
        current_stats = self.team1_stats if self.possession == 1 else self.team2_stats
        current_stats["total_yards"] += yards
        if play_type.lower() == "pass":
            current_stats["pass_yards"] += yards
        elif play_type.lower() == "rush":
            current_stats["rush_yards"] += yards

        self.down += 1
        if self.down > 4:
            self.down = 1
            self.yards_to_go = 10
            self.switch_possession()
        else:
            self.yards_to_go -= yards
            if self.yards_to_go <= 0:
                self.down = 1
                self.yards_to_go = 10
                current_stats["first_downs"] += 1
        
        self.update_play_display()
        self.update_display_window()
        self.update_stats_labels()
        self.box_score.append(f"Q{self.quarter} {self.format_time(self.seconds_remaining)} - "
                            f"{play_type.capitalize()} Play: {yards} yds to {self.format_yard_line(self.ball_on)}")
        self.update_box_score()

    def preset_play(self, play_type, yards):
        self.start_play_timer()
        
        if play_type == "rush" and yards is not None:  # Gain/Loss
            self.update_field_position(yards)
            current_stats = self.team1_stats if self.possession == 1 else self.team2_stats
            current_stats["total_yards"] += yards
            current_stats["rush_yards"] += yards
            self.down += 1
            if self.down > 4:
                self.down = 1
                self.yards_to_go = 10
                self.switch_possession()
            else:
                self.yards_to_go -= yards
                if self.yards_to_go <= 0:
                    self.down = 1
                    self.yards_to_go = 10
                    current_stats["first_downs"] += 1
            log_entry = f"Q{self.quarter} {self.format_time(self.seconds_remaining)} - Rush Play: {yards} yds to {self.format_yard_line(self.ball_on)}"
        
        elif play_type == "rush" and yards is None:  # Touchdown
            self.add_score(self.possession, 6)
            log_entry = f"Q{self.quarter} {self.format_time(self.seconds_remaining)} - Touchdown via Rush"
        
        elif play_type == "stop":  # Stop Play
            self.update_field_position(0)
            self.down += 1
            if self.down > 4:
                self.down = 1
                self.yards_to_go = 10
                self.switch_possession()
            log_entry = f"Q{self.quarter} {self.format_time(self.seconds_remaining)} - Stop Play at {self.format_yard_line(self.ball_on)}"

        self.update_play_display()
        self.update_display_window()
        self.update_stats_labels()
        self.box_score.append(log_entry)
        self.update_box_score()

    def update_field_position(self, yards):
        self.ball_on -= yards if self.possession == 1 else -yards
        self.ball_on = max(1, min(99, self.ball_on))
        if self.ball_on <= 0 or self.ball_on >= 100:
            self.add_score(self.possession, 6)
            self.ball_on = 35
            self.switch_possession()
        self.field_label.config(text=f"Ball on: {self.format_yard_line(self.ball_on)}")
        self.display_field_label.config(text=f"Ball on: {self.format_yard_line(self.ball_on)}")
        self.draw_field()

    def draw_field(self):
        self.field_canvas.delete("all")
        self.field_canvas.create_rectangle(0, 0, 300, 200, fill="green")
        for i in range(0, 300, 30):
            self.field_canvas.create_line(i, 0, i, 200, fill="white")
        x_pos = (self.ball_on / 100) * 300
        self.field_canvas.create_oval(x_pos-5, 95, x_pos+5, 105, fill="brown")

    def switch_possession(self):
        self.possession = 2 if self.possession == 1 else 1
        self.possession_label.config(text=f"Possession: {self.team1_name if self.possession == 1 else self.team2_name}")
        self.box_score.append(f"Q{self.quarter} {self.format_time(self.seconds_remaining)} - Turnover: Possession to {self.team1_name if self.possession == 1 else self.team2_name}")
        self.update_box_score()

    def add_score(self, team, points):
        current_time = self.format_time(self.seconds_remaining)
        score_type = {6: "TD", 3: "FG", 1: "XP", 2: "2PT/Safety"}[points]
        if team == 1:
            self.team1_score += points
            self.team1_label.config(text=str(self.team1_score))
            self.display_team1_label.config(text=f"{self.team1_name}: {self.team1_score}")
            score_entry = f"Q{self.quarter} {current_time} - {self.team1_name} {score_type} ({points} pts)"
        else:
            self.team2_score += points
            self.team2_label.config(text=str(self.team2_score))
            self.display_team2_label.config(text=f"{self.team2_name}: {self.team2_score}")
            score_entry = f"Q{self.quarter} {current_time} - {self.team2_name} {score_type} ({points} pts)"
        
        self.box_score.append(score_entry)
        self.game_log.append({"time": time.time(), "team": team, "points": points, 
                            "quarter": self.quarter, "clock": current_time, 
                            "possession": self.possession, "ball_on": self.ball_on})
        self.update_box_score()
        self.play_sound("touchdown" if points == 6 else "field_goal")
        self.animate_score(team)
        if points == 6:
            self.handle_post_touchdown(team)

    def handle_post_touchdown(self, team):
        choice = simpledialog.askinteger("After TD", "1 for PAT, 2 for Two-Point, 3 for Kickoff:", 
                                       minvalue=1, maxvalue=3)
        if choice == 1:
            self.add_score(team, 1)
        elif choice == 2:
            self.add_score(team, 2)
        elif choice == 3:
            self.start_kickoff()

    def animate_score(self, team):
        label = self.team1_label if team == 1 else self.team2_label
        original_font = ("Arial", 48)
        for i in range(5):
            label.config(font=("Arial", 48 + i*2))
            self.root.update()
            time.sleep(0.1)
        label.config(font=original_font)

    def update_box_score(self):
        self.box_text.delete(1.0, tk.END)
        for entry in self.box_score:
            self.box_text.insert(tk.END, entry + "\n")

    def update_display_window(self):
        self.display_clock_label.config(text=self.format_time(self.seconds_remaining))
        self.display_team1_label.config(text=f"{self.team1_name}: {self.team1_score}")
        self.display_team2_label.config(text=f"{self.team2_name}: {self.team2_score}")
        self.display_field_label.config(text=f"Ball on: {self.format_yard_line(self.ball_on)}")

    def use_timeout(self, team):
        if team == 1 and self.team1_timeouts > 0:
            self.team1_timeouts -= 1
            self.pause_clock()
            self.update_timeout_labels()
        elif team == 2 and self.team2_timeouts > 0:
            self.team2_timeouts -= 1
            self.pause_clock()
            self.update_timeout_labels()

    def update_timeout_labels(self):
        self.team1_timeout_label.config(text=f"{self.team1_name} TO: {self.team1_timeouts}")
        self.team2_timeout_label.config(text=f"{self.team2_name} TO: {self.team2_timeouts}")

    def change_team_color(self, team):
        color = colorchooser.askcolor(title=f"Choose color for {self.team1_name if team == 1 else self.team2_name}")[1]
        if color:
            if team == 1:
                self.team1_color = color
                self.team1_label.config(foreground=color)
                self.display_team1_label.config(foreground=color)
            else:
                self.team2_color = color
                self.team2_label.config(foreground=color)
                self.display_team2_label.config(foreground=color)

    def load_team_logo(self, team):
        filename = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if filename:
            img = Image.open(filename).resize((100, 100), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            if team == 1:
                self.team1_logo = photo
                self.team1_logo_label.config(image=photo)
            else:
                self.team2_logo = photo
                self.team2_logo_label.config(image=photo)

    def load_default_logos(self):
        if os.path.exists("team1_default.png"):
            self.load_team_logo(1)
        if os.path.exists("team2_default.png"):
            self.load_team_logo(2)

    def undo_score(self):
        if self.game_log:
            last_score = self.game_log.pop()
            if last_score["team"] == 1:
                self.team1_score -= last_score["points"]
                self.team1_label.config(text=str(self.team1_score))
                self.display_team1_label.config(text=f"{self.team1_name}: {self.team1_score}")
            else:
                self.team2_score -= last_score["points"]
                self.team2_label.config(text=str(self.team2_score))
                self.display_team2_label.config(text=f"{self.team2_name}: {self.team2_score}")
            self.box_score.pop()
            self.ball_on = last_score["ball_on"]
            self.update_play_display()
            self.update_display_window()
            self.update_box_score()
            self.draw_field()

    def update_stats_labels(self):
        self.team1_stats_label.config(text=self.format_stats(self.team1_stats))
        self.team2_stats_label.config(text=self.format_stats(self.team2_stats))

    def update_play_display(self):
        self.down_label.config(text=f"Down: {self.down} & {self.yards_to_go}")
        self.field_label.config(text=f"Ball on: {self.format_yard_line(self.ball_on)}")

    def add_penalty(self):
        team = simpledialog.askinteger("Penalty", "Penalty on (1 or 2):", minvalue=1, maxvalue=2)
        yards = simpledialog.askinteger("Penalty Yards", "Penalty yards:", minvalue=1, maxvalue=15) or 5
        current_stats = self.team1_stats if team == 1 else self.team2_stats
        current_stats["penalties"] += 1
        self.ball_on += yards if team == self.possession else -yards
        self.ball_on = max(1, min(99, self.ball_on))
        self.update_play_display()
        self.update_display_window()
        self.update_stats_labels()
        self.box_score.append(f"Q{self.quarter} {self.format_time(self.seconds_remaining)} - "
                            f"Penalty on {self.team1_name if team == 1 else self.team2_name}: {yards} yds")
        self.update_box_score()
        self.draw_field()

    def start_replay(self):
        if not self.replay_active:
            self.replay_active = True
            self.pause_clock()
            result = messagebox.askyesno("Replay Review", "Overturn the call?")
            if result:
                self.undo_score()
            self.replay_active = False
            messagebox.showinfo("Replay", "Review complete")

    def simulate_play(self):
        self.start_play_timer()
        yards = random.randint(-10, 30)
        play_type = random.choice(["pass", "rush", "stop"])
        self.next_play_auto(yards, play_type)
        self.box_score.append(f"Q{self.quarter} {self.format_time(self.seconds_remaining)} - "
                            f"Simulated {play_type}: {yards} yds to {self.format_yard_line(self.ball_on)}")
        self.update_box_score()

    def next_play_auto(self, yards, play_type):
        current_stats = self.team1_stats if self.possession == 1 else self.team2_stats
        current_stats["total_yards"] += yards
        if play_type == "pass":
            current_stats["pass_yards"] += yards
        elif play_type == "rush":
            current_stats["rush_yards"] += yards
        self.update_field_position(yards)
        self.update_stats_labels()

    def change_weather(self):
        weather_options = ["Clear", "Rain", "Snow", "Fog", "Windy"]
        self.weather = simpledialog.askstring("Weather", "Enter weather condition:", 
                                            initialvalue=self.weather, 
                                            parent=self.root) or random.choice(weather_options)
        self.weather_label.config(text=f"Weather: {self.weather}")

    def toggle_overtime(self):
        self.overtime_active.set(not self.overtime_active.get())
        messagebox.showinfo("Overtime", f"Overtime {'enabled' if self.overtime_active.get() else 'disabled'}")

    def toggle_vibration(self):
        self.vibration_on = not self.vibration_on
        messagebox.showinfo("Vibration", f"Vibration {'ON' if self.vibration_on else 'OFF'}")
        if self.vibration_on:
            self.play_sound("vibration")

    def set_play_time(self):
        seconds = simpledialog.askinteger("Play Time", "Enter play duration (seconds):", 
                                        minvalue=5, maxvalue=30)
        if seconds:
            self.play_seconds = seconds
            messagebox.showinfo("Play Time", f"Play timer set to {seconds} seconds")

    def start_play_timer(self):
        if self.vibration_on:
            self.play_sound("vibration")
        threading.Thread(target=self.run_play_timer).start()

    def run_play_timer(self):
        for _ in range(self.play_seconds):
            if not self.clock_running:
                break
            time.sleep(1)
        if self.vibration_on and self.clock_running:
            self.play_sound("vibration")

    def play_sound(self, sound_key):
        if sound_key in self.sounds and os.path.exists(self.sounds[sound_key]):
            threading.Thread(target=lambda: winsound.PlaySound(self.sounds[sound_key], 
                                                            winsound.SND_FILENAME)).start()

    def reset_game(self):
        if messagebox.askyesno("Reset", "Reset the game?"):
            self.team1_score = 0
            self.team2_score = 0
            self.team1_label.config(text="0")
            self.team2_label.config(text="0")
            self.display_team1_label.config(text=f"{self.team1_name}: 0")
            self.display_team2_label.config(text=f"{self.team2_name}: 0")
            self.seconds_remaining = 900
            self.clock_label.config(text=self.format_time(self.seconds_remaining))
            self.display_clock_label.config(text=self.format_time(self.seconds_remaining))
            self.clock_running = False
            self.quarter = 1
            self.quarter_label.config(text="Quarter: 1")
            self.down = 1
            self.yards_to_go = 10
            self.ball_on = 35
            self.team1_timeouts = 3
            self.team2_timeouts = 3
            self.update_timeout_labels()
            self.possession = 1
            self.possession_label.config(text=f"Possession: {self.team1_name}")
            self.team1_stats = {"first_downs": 0, "total_yards": 0, "pass_yards": 0, "rush_yards": 0, "penalties": 0}
            self.team2_stats = {"first_downs": 0, "total_yards": 0, "pass_yards": 0, "rush_yards": 0, "penalties": 0}
            self.update_stats_labels()
            self.box_score = []
            self.game_log = []
            self.weather = "Clear"
            self.weather_label.config(text="Weather: Clear")
            self.vibration_on = False
            self.update_play_display()
            self.update_display_window()
            self.update_box_score()
            self.draw_field()
            self.start_kickoff()

    def save_game(self):
        data = {
            "team1": {"name": self.team1_name, "score": self.team1_score, "color": self.team1_color, 
                     "timeouts": self.team1_timeouts, "stats": self.team1_stats},
            "team2": {"name": self.team2_name, "score": self.team2_score, "color": self.team2_color, 
                     "timeouts": self.team2_timeouts, "stats": self.team2_stats},
            "quarter": self.quarter,
            "time": self.seconds_remaining,
            "down": self.down,
            "yards": self.yards_to_go,
            "ball_on": self.ball_on,
            "possession": self.possession,
            "weather": self.weather,
            "overtime": self.overtime_active.get(),
            "vibration": self.vibration_on,
            "play_seconds": self.play_seconds,
            "box_score": self.box_score,
            "game_log": self.game_log
        }
        filename = filedialog.asksaveasfilename(defaultextension=".json")
        if filename:
            with open(filename, 'w') as f:
                json.dump(data, f)
            messagebox.showinfo("Saved", "Game saved successfully!")

    def load_game(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.team1_name = data["team1"]["name"]
            self.team1_score = data["team1"]["score"]
            self.team1_color = data["team1"]["color"]
            self.team1_timeouts = data["team1"]["timeouts"]
            self.team1_stats = data["team1"]["stats"]
            self.team2_name = data["team2"]["name"]
            self.team2_score = data["team2"]["score"]
            self.team2_color = data["team2"]["color"]
            self.team2_timeouts = data["team2"]["timeouts"]
            self.team2_stats = data["team2"]["stats"]
            self.quarter = data["quarter"]
            self.seconds_remaining = data["time"]
            self.down = data["down"]
            self.yards_to_go = data["yards"]
            self.ball_on = data["ball_on"]
            self.possession = data["possession"]
            self.weather = data["weather"]
            self.overtime_active.set(data["overtime"])
            self.vibration_on = data["vibration"]
            self.play_seconds = data["play_seconds"]
            self.box_score = data["box_score"]
            self.game_log = data["game_log"]
            
            self.team1_frame.config(text=self.team1_name)
            self.team2_frame.config(text=self.team2_name)
            self.team1_label.config(text=str(self.team1_score), foreground=self.team1_color)
            self.team2_label.config(text=str(self.team2_score), foreground=self.team2_color)
            self.display_team1_label.config(text=f"{self.team1_name}: {self.team1_score}", foreground=self.team1_color)
            self.display_team2_label.config(text=f"{self.team2_name}: {self.team2_score}", foreground=self.team2_color)
            self.quarter_label.config(text=f"Quarter: {self.quarter}")
            self.clock_label.config(text=self.format_time(self.seconds_remaining))
            self.update_play_display()
            self.update_display_window()
            self.possession_label.config(text=f"Possession: {self.team1_name if self.possession == 1 else self.team2_name}")
            self.update_timeout_labels()
            self.update_stats_labels()
            self.weather_label.config(text=f"Weather: {self.weather}")
            self.update_box_score()
            self.draw_field()
            messagebox.showinfo("Loaded", "Game loaded successfully!")

    def export_log(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", 
                                              filetypes=[("Text files", "*.txt")])
        if filename:
            with open(filename, 'w') as f:
                f.write(f"Electric Football Game Log - {self.team1_name} vs {self.team2_name}\n")
                f.write(f"Final Score: {self.team1_score} - {self.team2_score}\n")
                f.write(f"Weather: {self.weather}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for entry in self.box_score:
                    f.write(entry + "\n")
            messagebox.showinfo("Exported", "Game log exported successfully!")

    def set_quarter_time(self):
        minutes = simpledialog.askinteger("Quarter Length", "Enter quarter length (minutes):", 
                                       minvalue=1, maxvalue=60)
        if minutes:
            self.seconds_remaining = minutes * 60
            self.clock_label.config(text=self.format_time(self.seconds_remaining))
            self.display_clock_label.config(text=self.format_time(self.seconds_remaining))

    def clear_log(self):
        if messagebox.askyesno("Clear Log", "Clear the play log?"):
            self.box_score = []
            self.game_log = []
            self.update_box_score()

    def on_closing(self):
        if messagebox.askyesno("Quit", "Do you want to save before quitting?"):
            self.save_game()
        self.display_window.destroy()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = FootballScoreboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()