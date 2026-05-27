import re
import webbrowser
import subprocess
import requests
import qrcode
import customtkinter as ctk
import json
import os
import sys
import threading  # Added for non-blocking UI

# Load settings from JSON file
if os.path.exists("settings.json"):
    with open("settings.json", "r") as f:
        settings = json.load(f)
else:
    settings = {"api_username": "", "api_auth_token": "", "theme": "dark"}

API_USERNAME = settings["api_username"]
API_AUTH_TOKEN = settings["api_auth_token"]
MATCHES_PER_QR = 20  

ctk.set_appearance_mode(settings["theme"])
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScoutingAppRebuilt Hub")
        self.geometry("600x620") # Slightly taller to comfortably fit status messages
        self.resizable(False, False)
        self.iconbitmap("src/icon.ico")
        
        tabview = ctk.CTkTabview(self, width=560, height=580)
        tabview.grid(column=0, row=0, padx=20, pady=20)

        # --- Home Tab ---
        tabview.add("Home")
        tabview.tab("Home").grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        home_title = ctk.CTkLabel(master=tabview.tab("Home"), text="Welcome to the Scouting App Hub!", font=ctk.CTkFont(size=20, weight="bold"))
        home_title.grid(column=0, row=0, padx=20, pady=20, columnspan=4)
        
        self.qr_code_switch_button = ctk.CTkButton(master=tabview.tab("Home"), text="Generate QR Codes", command=lambda: tabview.set("QR Code Schedules"))
        self.qr_code_switch_button.grid(column=0, row=1, padx=0, pady=20, columnspan=2)
        
        self.pull_data_switch_button = ctk.CTkButton(master=tabview.tab("Home"), text="Pull Tablet Scouting Data", command=lambda: tabview.set("Pull Data"))
        self.pull_data_switch_button.grid(column=2, row=1, padx=0, pady=20, columnspan=2)
        
        self.settings_switch_button = ctk.CTkButton(master=tabview.tab("Home"), text="Settings", command=lambda: tabview.set("Settings"))
        self.settings_switch_button.grid(column=0, row=2, padx=0, pady=20, columnspan=4, sticky="n")
        
        docs_label = ctk.CTkLabel(master=tabview.tab("Home"), text="Documentation", font=ctk.CTkFont(size=16, weight="bold"))
        docs_label.grid(column=0, row=3, padx=20, pady=10, columnspan=4)
        docs_button = ctk.CTkButton(master=tabview.tab("Home"), text="Open Docs", command=self.open_docs)
        docs_button.grid(column=0, row=4, padx=20, pady=10, columnspan=4)

        # --- QR Code Schedules Tab ---
        tabview.add("QR Code Schedules")
        tabview.tab("QR Code Schedules").grid_columnconfigure(0, weight=1)
        
        qr_title = ctk.CTkLabel(master=tabview.tab("QR Code Schedules"), text="QR Schedule Generator", font=ctk.CTkFont(size=20, weight="bold"))
        qr_title.grid(column=0, row=0, padx=20, pady=20, sticky="nwe")
        
        ctk.CTkLabel(master=tabview.tab("QR Code Schedules"), text="Year").grid(column=0, row=1, pady=5)
        self.year_entry = ctk.CTkEntry(master=tabview.tab("QR Code Schedules"), placeholder_text="2024")
        self.year_entry.grid(column=0, row=2, padx=20, pady=5)

        ctk.CTkLabel(master=tabview.tab("QR Code Schedules"), text="Event Code").grid(column=0, row=3, pady=5)
        self.event_entry = ctk.CTkEntry(master=tabview.tab("QR Code Schedules"), placeholder_text="WAKNO")
        self.event_entry.grid(column=0, row=4, padx=20, pady=5)
        
        self.qr_status_label = ctk.CTkLabel(master=tabview.tab("QR Code Schedules"), text="", font=ctk.CTkFont(size=12))
        self.qr_status_label.grid(column=0, row=6, padx=20, pady=10)

        self.go_button = ctk.CTkButton(master=tabview.tab("QR Code Schedules"), text="Generate QRs", 
                                  command=self.start_qr_generation_thread)
        self.go_button.grid(column=0, row=8, padx=20, pady=20)

        # --- Pull Data Tab ---
        tabview.add("Pull Data")
        tabview.tab("Pull Data").grid_columnconfigure((0, 1, 2), weight=1)
        
        pull_data_label = ctk.CTkLabel(master=tabview.tab("Pull Data"), text="Tablet Data Pull", font=ctk.CTkFont(size=20, weight="bold"))
        pull_data_label.grid(column=0, row=0, padx=20, pady=20, columnspan=3)
        
        self.tablet_number = ctk.CTkEntry(master=tabview.tab("Pull Data"), placeholder_text="Tablet Number")
        self.tablet_number.grid(column=0, row=1, padx=20, pady=20, columnspan=3)
        
        self.output_label = ctk.CTkLabel(master=tabview.tab("Pull Data"), text="", font=ctk.CTkFont(size=12), wraplength=450)
        self.output_label.grid(column=0, row=3, padx=20, pady=20, columnspan=3)
        
        self.pull_button = ctk.CTkButton(master=tabview.tab("Pull Data"), text="Pull Data", command=self.start_pull_data_thread)
        self.pull_button.grid(column=0, row=2, padx=20, pady=20, columnspan=3)
        
        self.merge_button = ctk.CTkButton(master=tabview.tab("Pull Data"), text="Merge CSV Data", command=self.start_merge_data_thread)
        self.merge_button.grid(column=0, row=4, padx=20, pady=10, columnspan=3)
        
        self.merge_status_label = ctk.CTkLabel(master=tabview.tab("Pull Data"), text="", font=ctk.CTkFont(size=12), wraplength=450)
        self.merge_status_label.grid(column=0, row=5, padx=20, pady=10, columnspan=3)

        # --- Settings Tab ---
        tabview.add("Settings")
        self.setup_settings_tab(tabview.tab("Settings"))

    def setup_settings_tab(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1)
        api_label = ctk.CTkLabel(master=tab, text="API Login", font=ctk.CTkFont(size=20, weight="bold"))
        api_label.grid(column=0, row=0, padx=20, pady=20, columnspan=2)
        
        self.username_entry = ctk.CTkEntry(master=tab, placeholder_text="API Username")
        self.username_entry.grid(column=0, row=1, padx=20, pady=20, sticky="ew")
        self.username_entry.insert(0, settings["api_username"])
        
        self.auth_token_entry = ctk.CTkEntry(master=tab, placeholder_text="API Auth Token")
        self.auth_token_entry.grid(column=1, row=1, padx=20, pady=20, sticky="ew")
        self.auth_token_entry.insert(0, settings["api_auth_token"])
        
        self.settings_status_label = ctk.CTkLabel(master=tab, text="", font=ctk.CTkFont(size=12))
        self.settings_status_label.grid(column=0, row=3, padx=20, pady=10, columnspan=2)
        
        ctk.CTkButton(master=tab, text="Save Settings", command=self.save_settings).grid(column=0, row=5, padx=20, pady=20, columnspan=2)

    def save_settings(self):
        settings["api_username"] = self.username_entry.get()
        settings["api_auth_token"] = self.auth_token_entry.get()
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
            self.settings_status_label.configure(text="Settings saved successfully!", text_color="green")
        except Exception as e:
            self.settings_status_label.configure(text=f"Error saving settings: {e}", text_color="red")

    # --- Threading Wrappers ---
    def start_qr_generation_thread(self):
        year = self.year_entry.get().strip()
        event = self.event_entry.get().strip()
        if not year or not event:
            self.qr_status_label.configure(text="Please enter both Year and Event Code.", text_color="red")
            return
            
        self.go_button.configure(state="disabled")
        self.qr_status_label.configure(text="Fetching data from FIRST API...", text_color="orange")
        
        # Offload logic to a background thread so UI stays interactive
        threading.Thread(target=self.do_qr_code_generation, args=(year, event), daemon=True).start()

    def start_pull_data_thread(self):
        tab_num = self.tablet_number.get().strip()
        if not tab_num:
            self.output_label.configure(text="Please enter a tablet number.", text_color="red")
            return
            
        self.pull_button.configure(state="disabled")
        self.output_label.configure(text=f"Pulling data from Tablet {tab_num}...", text_color="orange")
        
        threading.Thread(target=self.pull_tablet_data, args=(tab_num,), daemon=True).start()

    # --- Core Logic Functions ---
    def do_qr_code_generation(self, year, event_code):
        match_data = self.pull_api_data(year, event_code, self.username_entry.get(), self.auth_token_entry.get())
        
        if match_data:
            try:
                for i in range(0, len(match_data), MATCHES_PER_QR):
                    chunk = match_data[i : i + MATCHES_PER_QR]
                    chunk_str = self.generate_compact_string(chunk)
                    
                    start_m = chunk[0].get('matchNumber')
                    end_m = chunk[-1].get('matchNumber')
                    filename = f"master_schedule_{start_m}_to_{end_m}.png"
                    self.create_qr(chunk_str, filename)
                
                self.qr_status_label.configure(text=f"Success! Master QRs Generated ({len(match_data)} matches).", text_color="green")
            except Exception as e:
                self.qr_status_label.configure(text=f"Error processing QR data: {e}", text_color="red")
        else:
            self.qr_status_label.configure(text="Failed to fetch matches. Check API credentials or Event Code.", text_color="red")
        
        self.go_button.configure(state="normal")

    def pull_api_data(self, year, event_code, api_username, api_auth_token):
        url = f"https://frc-api.firstinspires.org/v3.0/{year}/schedule/{event_code}?tournamentLevel=qual"
        try:
            response = requests.get(url, auth=(api_username, api_auth_token), timeout=10)
            response.raise_for_status()
            return response.json().get('Schedule', [])
        except Exception as e:
            print(f"API Error: {e}")
            return None

    def generate_compact_string(self, matches):
        match_list = []
        for m in matches:
            m_num = m.get('matchNumber')
            team_nums = [str(t.get('teamNumber')) for t in m.get('teams', [])]
            row = f"{m_num}," + ",".join(team_nums)
            match_list.append(row)
        return ";".join(match_list)

    def create_qr(self, data_string, filename):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=4,
        )
        qr.add_data(data_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filename)

    def open_docs(self):
        base = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base, "src", "docs", "index.html")

        if not os.path.exists(file_path):
            return

        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", file_path])
        else:
            subprocess.run(["xdg-open", file_path])
    
    def pull_tablet_data(self, tablet_number):
        command = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', 'tablets.ps1', tablet_number]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                out_text = result.stdout if result.stdout.strip() else "Script executed with no output."
                self.output_label.configure(text=f"Success:\n{out_text}", text_color="green")
            else:
                self.output_label.configure(text=f"PowerShell Error:\n{result.stderr}", text_color="red")
        except subprocess.TimeoutExpired:
            self.output_label.configure(text="Error: PowerShell script timed out.", text_color="red")
        except Exception as e:
            self.output_label.configure(text=f"Execution Failed: {e}", text_color="red")
        finally:
            self.pull_button.configure(state="normal")
            
    def merge_data(self):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merge.ps1")
        
        if not os.path.exists(script_path):
            self.output_label.configure(text="Error: merge.ps1 not found next to this script.", text_color="red")
            self.merge_button.configure(state="normal")
            return

        command = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', script_path]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                out_text = result.stdout.strip() or "Merge completed with no output."
                self.output_label.configure(text=f"Success:\n{out_text}", text_color="green")
            else:
                self.output_label.configure(text=f"PowerShell Error:\n{result.stderr.strip()}", text_color="red")
        except subprocess.TimeoutExpired:
            self.output_label.configure(text="Error: Merge script timed out.", text_color="red")
        except Exception as e:
            self.output_label.configure(text=f"Execution Failed: {e}", text_color="red")
        finally:
            self.merge_button.configure(state="normal")
    
    def start_merge_data_thread(self):
        self.merge_button.configure(state="disabled")
        self.output_label.configure(text="Merging CSV files...", text_color="orange")
        threading.Thread(target=self.merge_data, daemon=True).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()