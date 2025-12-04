# ELC Parking App - Stage 2: Code Implementation and Testing
# Author: Jie Liang
# Course: CS2450 - Software Engineering
# Instructor: Dr. Gang Liu
#
# Real-time parking availability system for SUU Electronic Learning Center
# (Lots 14, 17, 18, 19)
#
# OOP PRINCIPLES:
# - Encapsulation: Private attributes with @property decorators
# - Singleton: Single ParkingSystem instance for data consistency
#
# CLASSES: UserType, ParkingStatus, ParkingLot, User, ParkingSystem, ParkingAppGUI


# Import required libraries for GUI, datetime handling, networking (requests),
# and multithreading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from enum import Enum
import random
import requests
import threading
import time

# Server configuration to connect to parking_server.py
SERVER_URL = "http://localhost:5000"
API_BASE = f"{SERVER_URL}/api"


# Enum: Limit user type to prevent invalid values
class UserType(Enum):
    """User type enumeration for permit-based access"""
    STUDENT = "Student"
    STAFF = "Staff"
    VISITOR = "Visitor"

# Enum: Regulates parking lot status to only AVAILABLE, LIMITED, or FULL
class ParkingStatus(Enum):
    """Parking lot status indicators"""
    AVAILABLE = "Available"
    LIMITED = "Limited"
    FULL = "Full"


# DOMAIN MODEL CLASSES

# Represents a parking lot with capacity tracking
# Encapsulation: parkinglot data and behavior together
class ParkingLot:

    def __init__(self, lot_id, name, total_spaces, permit_type, drive_time):
        self._lot_id = lot_id
        self._name = name
        self._total_spaces = total_spaces
        self._occupied_spaces = 0
        self._permit_type = permit_type  # "Student", "Staff", "Both", "Open"
        self._drive_time = drive_time
    
    @property
    def lot_id(self):
        return self._lot_id
    
    @property
    def name(self):
        return self._name
    
    @property
    def available_spaces(self):
        return self._total_spaces - self._occupied_spaces
    
    @property
    def total_spaces(self):
        return self._total_spaces
    
    @property
    def permit_type(self):
        return self._permit_type
    
    @property
    def drive_time(self):
        return self._drive_time
    
    # Determine lot status based on availability
    def get_status(self):
        availability_ratio = self.available_spaces / self._total_spaces
        if availability_ratio >= 0.3:
            return ParkingStatus.AVAILABLE
        elif availability_ratio > 0:
            return ParkingStatus.LIMITED
        else:
            return ParkingStatus.FULL
    
    # **The header color shows availability status:**
    # - 🟢 **Green** = AVAILABLE (≥30% free)
    # - 🟠 **Orange** = LIMITED (1-29% free)
    # - 🔴 **Red** = FULL (0% free)
    def get_status_color(self):
        """Get color code for status"""
        status = self.get_status()
        if status == ParkingStatus.AVAILABLE:
            return "#4CAF50"  # Green
        elif status == ParkingStatus.LIMITED:
            return "#FFA726"  # Orange
        else:
            return "#EF5350"  # Red
    # Update occupied spaces
    def update_occupancy(self, occupied):
        self._occupied_spaces = max(0, min(occupied, self._total_spaces))
    # Check if user can park based on permit type
    def can_user_park(self, user_type):
        if self._permit_type == "Open":
            return True
        elif self._permit_type == "Both":
            return user_type in [UserType.STUDENT, UserType.STAFF]
        elif self._permit_type == "Student":
            return user_type == UserType.STUDENT
        elif self._permit_type == "Staff":
            return user_type == UserType.STAFF
        return False

# Represents a user with a specific type of parking permit 
class User:   
    def __init__(self, user_id, name, user_type):
        self._user_id = user_id
        self._name = name
        self._user_type = user_type
    
    @property
    def name(self):
        return self._name
    
    @property
    def user_type(self):
        return self._user_type
    
    # Based on the user's parking permit,shows the lots they can access
    def get_permitted_lots(self, all_lots):
        return [lot for lot in all_lots if lot.can_user_park(self._user_type)]

# be a clients side of the parking system to communicate
# with parking lots availability for user
# OOP PRINCIPLE: Singleton pattern - single instance for data consistency
class ParkingSystem:
    _instance = None
    # Singleton: make sure only one ParkingSystem instance work at a time
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    # Initialize parking system
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lots = []
        self._server_connected = False
        self._initialize_lots()
    # Initialize the 4 parking lots near ELC
    def _initialize_lots(self):
        self._lots = [
            ParkingLot("17", "Lot 17", 35, "Student", 2),
            ParkingLot("18", "Lot 18", 45, "Staff", 1),
            ParkingLot("19", "Lot 19", 60, "Both", 2),
            ParkingLot("14", "Lot 14", 50, "Open", 3)
        ]
    # Get all parking lots
    def get_all_lots(self):
        return self._lots
    # Get specific lot by ID
    def get_lot_by_id(self, lot_id):
        for lot in self._lots:
            if lot.lot_id == lot_id:
                return lot
        return None
    # Check if server is available
    def check_server_connection(self):
        try:
            response = requests.get(f"{API_BASE}/lots", timeout=2)
            self._server_connected = response.status_code == 200
            return self._server_connected
        except:
            self._server_connected = False
            return False
    # Refresh parking data from server or simulate
    def refresh_data(self):
        try:
            response = requests.get(f"{API_BASE}/lots", timeout=2)
            if response.status_code == 200:
                lots_data = response.json()
                for lot_data in lots_data:
                    lot = self.get_lot_by_id(lot_data['lot_id'])
                    if lot:
                        lot.update_occupancy(lot_data['occupied_spaces'])
                self._server_connected = True
                return True
        except:
            # Simulate data if server unavailable
            for lot in self._lots:
                if lot.lot_id == "17":
                    lot.update_occupancy(random.randint(28, 35))
                elif lot.lot_id == "18":
                    lot.update_occupancy(random.randint(40, 45))
                elif lot.lot_id == "19":
                    lot.update_occupancy(random.randint(45, 60))
                else:  # Lot 14
                    lot.update_occupancy(random.randint(15, 40))
            self._server_connected = False
            return False
    # Check if currently connected to server
    def is_server_connected(self):
        return self._server_connected
    # Get lots user is permitted to park in
    def get_recommended_lots(self, user_type):
        return [lot for lot in self._lots if lot.can_user_park(user_type)]



# Interface CLASSES
#
# Main GUI application
# OOP PRINCIPLE: Separation of concerns - 
# GUI separate user interface from data model
class ParkingAppGUI:
    """

    """
    def __init__(self, root):
        self.root = root
        self.root.title("ELC Parking App - SUU")
        self.root.geometry("900x700")
        self.root.configure(bg="#f5f5f5")
        
        # Initialize parking system (Singleton)
        self.parking_system = ParkingSystem()
        
        # Current user
        self.current_user = None
        self.user_type = UserType.STUDENT  # Default
        
        # Auto-refresh
        self.auto_refresh_enabled = True
        self.refresh_thread = None
        
        # Check server on startup
        server_available = self.parking_system.check_server_connection()
        if not server_available:
            messagebox.showwarning(
                "Server Not Available",
                "Cannot connect to parking server.\n\n"
                "The app will work with simulated data.\n\n"
                "To use real-time data:\n"
                "1. Start parking_server.py first\n"
                "2. then Restart this app"
            )
        
        # Create UI
        self.create_header()
        self.create_user_selection()
        self.create_main_dashboard()
        self.create_footer()
        
        # Initial load
        self.refresh_parking_data()
        
        # Start auto-refresh
        self.start_auto_refresh()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    # Create application header
    def create_header(self):
        header_frame = tk.Frame(self.root, bg="#2196F3", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🚗 ELC Parking App",
            font=("Arial", 24, "bold"),
            bg="#2196F3",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Southern Utah University - Real-time Parking Availability",
            font=("Arial", 10),
            bg="#2196F3",
            fg="white"
        )
        subtitle_label.pack(side=tk.LEFT, padx=(0, 20))
    # Create user type selection
    def create_user_selection(self):
        selection_frame = tk.Frame(self.root, bg="white", height=70)
        selection_frame.pack(fill=tk.X, padx=20, pady=10)
        selection_frame.pack_propagate(False)
        
        label = tk.Label(
            selection_frame,
            text="I am a:",
            font=("Arial", 12, "bold"),
            bg="white"
        )
        label.pack(side=tk.LEFT, padx=20)
        
        # User type buttons:student, staff, visitor
        self.user_buttons = {}
        for user_type in [UserType.STUDENT, UserType.STAFF, UserType.VISITOR]:
            btn = tk.Button(
                selection_frame,
                text=user_type.value,
                font=("Arial", 11),
                width=12,
                height=1,
                command=lambda ut=user_type: self.set_user_type(ut),
                relief=tk.RAISED,
                bd=2
            )
            btn.pack(side=tk.LEFT, padx=5)
            self.user_buttons[user_type] = btn
        
        # Highlight default to indicate which user type is selected
        self.user_buttons[UserType.STUDENT].configure(bg="#2196F3", fg="white", relief=tk.SUNKEN)
    
    def create_main_dashboard(self):
        """Create main dashboard"""
        self.dashboard_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Update time
        self.update_label = tk.Label(
            self.dashboard_frame,
            text="",
            font=("Arial", 9),
            bg="#f5f5f5",
            fg="#666"
        )
        self.update_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Lots grid
        self.lots_container = tk.Frame(self.dashboard_frame, bg="#f5f5f5")
        self.lots_container.pack(fill=tk.BOTH, expand=True)
    
    def create_footer(self):
        """Create footer with refresh button"""
        footer_frame = tk.Frame(self.root, bg="#f5f5f5", height=60)
        footer_frame.pack(fill=tk.X, pady=10)
        
        refresh_btn = tk.Button(
            footer_frame,
            text="🔄 Refresh Data",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2,
            command=self.refresh_parking_data,
            relief=tk.RAISED,
            bd=2
        )
        refresh_btn.pack()
    
    def set_user_type(self, user_type):
        """Set user type and refresh display"""
        self.user_type = user_type
        
        # Update button highlights
        for ut, btn in self.user_buttons.items():
            if ut == user_type:
                btn.configure(bg="#2196F3", fg="white", relief=tk.SUNKEN)
            else:
                btn.configure(bg="white", fg="black", relief=tk.RAISED)
        
        # Refresh display
        self.display_lots()
    
    def refresh_parking_data(self):
        """Refresh parking data from system"""
        # Fetch data (from server or simulate)
        server_used = self.parking_system.refresh_data()
        
        # Update display
        self.display_lots()
        
        # Update timestamp
        now = datetime.now().strftime("%I:%M:%S %p")
        source = "server" if server_used else "simulated"
        self.update_label.configure(text=f"Last updated: {now} ({source})")
    
    def display_lots(self):
        """Display parking lot cards"""
        # Clear existing
        for widget in self.lots_container.winfo_children():
            widget.destroy()
        
        # Get recommended lots for current user
        recommended_lots = self.parking_system.get_recommended_lots(self.user_type)
        
        # Display each lot
        row = 0
        col = 0
        for idx, lot in enumerate(recommended_lots):
            card = self.create_lot_card(self.lots_container, lot, idx + 1)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
        
        # Configure grid weights
        self.lots_container.columnconfigure(0, weight=1)
        self.lots_container.columnconfigure(1, weight=1)
    
    def create_lot_card(self, parent, lot, priority):
        """Create a card for a parking lot"""
        # Card frame
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2)
        
        # Header with priority
        header_frame = tk.Frame(card, bg=lot.get_status_color(), height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        priority_label = tk.Label(
            header_frame,
            text=f"#{priority} PRIORITY" if priority == 1 else f"Option #{priority}",
            font=("Arial", 9, "bold"),
            bg=lot.get_status_color(),
            fg="white"
        )
        priority_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        status_label = tk.Label(
            header_frame,
            text=f"● {lot.get_status().value.upper()}",
            font=("Arial", 9, "bold"),
            bg=lot.get_status_color(),
            fg="white"
        )
        status_label.pack(side=tk.RIGHT, padx=10, pady=8)
        
        # Content
        content = tk.Frame(card, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Lot name
        tk.Label(
            content,
            text=f"LOT {lot.lot_id}",
            font=("Arial", 20, "bold"),
            bg="white"
        ).pack(anchor=tk.W)
        
        tk.Label(
            content,
            text=lot.permit_type.upper() + " PARKING",
            font=("Arial", 9),
            bg="white",
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Availability
        avail_frame = tk.Frame(content, bg="white")
        avail_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            avail_frame,
            text=f"{lot.available_spaces} / {lot.total_spaces}",
            font=("Arial", 24, "bold"),
            bg="white",
            fg=lot.get_status_color()
        ).pack(side=tk.LEFT)
        
        tk.Label(
            avail_frame,
            text="spaces\navailable",
            font=("Arial", 9),
            bg="white",
            fg="#666",
            justify=tk.LEFT
        ).pack(side=tk.LEFT, padx=10)
        
        # Progress bar
        progress_frame = tk.Frame(content, bg="#e0e0e0", height=20)
        progress_frame.pack(fill=tk.X, pady=10)
        progress_frame.pack_propagate(False)
        
        fill_width = int((lot.available_spaces / lot.total_spaces) * 300)
        fill = tk.Frame(progress_frame, bg=lot.get_status_color(), width=fill_width)
        fill.pack(side=tk.LEFT, fill=tk.Y)
        
        # Dshows the drive time TO the parking lot
        details_frame = tk.Frame(content, bg="white")
        details_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            details_frame,
            text=f"🚗 {lot.drive_time} min drive",
            font=("Arial", 10),
            bg="white",
            fg="#666"
        ).pack(side=tk.LEFT, padx=5)
        
        return card
    
    # updates parking data every 10 seconds
    def start_auto_refresh(self):
        """Start auto-refresh thread"""
        if self.refresh_thread and self.refresh_thread.is_alive():
            return
        
        def refresh_loop():
            while self.auto_refresh_enabled:
                time.sleep(10)  # 10 seconds
                if self.auto_refresh_enabled:
                    try:
                        self.refresh_parking_data()
                    except:
                        pass
        
        self.refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.refresh_thread.start()
    
    def on_closing(self):
        """Handle window close"""
        self.auto_refresh_enabled = False
        self.root.destroy()


# MAIN function
def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = ParkingAppGUI(root)
    root.mainloop()
if __name__ == "__main__":
    main()
