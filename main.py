from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import json
from json import JSONEncoder
import tkinter as tk
from tkinter import messagebox
import subprocess

class DateTimeEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return JSONEncoder.default(self, o)

# Mileage data
mileage_data = {
    ("Tallahassee", "Crawfordville"): 20,
    ("Crawfordville", "Tallahassee"): 20,
    ("Tallahassee", "Quincy"): 23,
    ("Quincy", "Tallahassee"): 23,
    ("Tallahassee", "Apalachicola"): 77,
    ("Apalachicola", "Tallahassee"): 77,
    ("Tallahassee", "Bristol"): 44,
    ("Bristol", "Tallahassee"): 44
}

reasons = {
    1: "Support of State/Circuit Equipment",
    2: "Return",
    3: "Mandatory Meeting",
    4: "Pick Up Parts",
    5: "Delivering Parts & Equipment",
    6: "Other"
}

reimbursement_rate = 0.655  # cents per mile
total_miles = 0
trips = []
unique_city_pairs = set()

# Initialize logged_in_user variable
logged_in_user = None

# File to store user profiles
USER_PROFILES_FILE = "user_profiles.json"

# Load user profiles from file or create an empty dictionary if the file doesn't exist
try:
    with open(USER_PROFILES_FILE, 'r') as file:
        user_profiles = json.load(file)
except FileNotFoundError:
    user_profiles = {}

# Function to save user profiles to a file
def save_user_profiles():
    with open(USER_PROFILES_FILE, 'w') as file:
        json.dump(user_profiles, file)

# Add 'Madison' to user_profiles with a password 'Freeman' if not already added
if 'Madison' not in user_profiles:
    user_profiles['Madison'] = {'password': 'Freeman', 'trips': []}
    # Save the updated user_profiles dictionary to the file
    with open(USER_PROFILES_FILE, 'w') as file:
        json.dump(user_profiles, file)

# Save the updated user_profiles dictionary to the file
save_user_profiles()

# Function to save the state of the program
def save_program_state():
    program_state = {
        'total_miles': total_miles,
        'trips': trips,
        'unique_city_pairs': list(unique_city_pairs)
    }

    try:
        with open(f"{logged_in_user}_program_state.json", 'r') as file:
            data = json.load(file)

        # Append new trip data to the existing data
        data['total_miles'] += program_state['total_miles']
        data['trips'].extend(program_state['trips'])
        data['unique_city_pairs'].extend(program_state['unique_city_pairs'])

        with open(f"{logged_in_user}_program_state.json", 'w') as file:
            json.dump(data, file, cls=DateTimeEncoder)
    except FileNotFoundError:
        # If file doesn't exist, create it and write the program state
        with open(f"{logged_in_user}_program_state.json", 'w') as file:
            json.dump(program_state, file, cls=DateTimeEncoder)

# Function to load the state of the program
def load_program_state():
    global total_miles
    global trips
    global unique_city_pairs

    try:
        with open(f"{logged_in_user}_program_state.json", 'r') as file:
            program_state = json.load(file)
            total_miles = program_state['total_miles']
            trips = program_state['trips']
            unique_city_pairs = set(program_state['unique_city_pairs'])
    except FileNotFoundError:
        pass  # Continue with default values if the file is not found

# Load the program state if available
load_program_state()

# Function to handle user login
def validate_login():
    global logged_in_user
    username = username_entry.get()
    password = password_entry.get()

    # Check if username exists and passwords match
    if username in user_profiles and user_profiles[username]["password"] == password:
        logged_in_user = username
        messagebox.showinfo("Login", "Login Successful!")
        login_window.destroy()  # Close the login window after successful login
    else:
        messagebox.showerror("Login", "Invalid username or password")

# Function to handle closing the login window
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        login_window.destroy()
        exit()  # Exit the program when the window is closed

# Create Tkinter window for login
login_window = tk.Tk()
login_window.geometry("300x200")
login_window.title("Login")

# Create labels and entry fields for login
username_label = tk.Label(login_window, text="Username:")
username_label.pack()
username_entry = tk.Entry(login_window)
username_entry.pack()

password_label = tk.Label(login_window, text="Password:")
password_label.pack()
password_entry = tk.Entry(login_window, show="*")  # Show * for password input
password_entry.pack()

login_button = tk.Button(login_window, text="Login", command=validate_login)
login_button.pack()

login_window.protocol("WM_DELETE_WINDOW", on_closing)

# Start the GUI main loop for login window
login_window.mainloop()

# Continue with the rest of your existing code after successful login
if not logged_in_user:
    exit()  # Exit the program if login fails

# Function to record trip for a user
def record_user_trip(username, departure, destination, miles, reason):
    global total_miles
    global trips
    global unique_city_pairs

    if username in user_profiles:
        user_data = user_profiles[username]
    else:
        user_data = {"trips": []}

    if reason == 6:  # If "Other" is selected, prompt for custom reason
        custom_reason = input("Enter the reason for travel: ")
        reason_text = custom_reason[:40]  # Limit the length of the reason text
    else:
        reason_text = reasons.get(reason, "Unknown Reason")

    total_miles += miles
    trips.append((datetime.now(), departure, destination, miles, reason_text))

    # Check if the reversed direction of the trip is already recorded
    if (destination, departure) not in unique_city_pairs:
        unique_city_pairs.add((departure, destination))

    # Record trip details under user profile
    user_data["trips"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "departure": departure,
        "destination": destination,
        "miles": miles,
        "reason": reason_text
    })

    # Update user profile
    user_profiles[username] = user_data
    save_user_profiles()

def calculate_reimbursement(miles):
    return miles * reimbursement_rate

# Define the base city
base_city = "Tallahassee"

# Function to record trips, considering base city and Crawfordville exclusion
def record_trip(departure, destination, miles, reason, custom_reason=""):
    global total_miles
    global trips
    global unique_city_pairs

    # Skip recording trips between base city and Crawfordville
    if (departure == base_city and destination == "Crawfordville") or \
       (departure == "Crawfordville" and destination == base_city):
        return

    if reason == 6:  # If "Other" is selected, use the custom reason provided
        reason_text = custom_reason[:40]  # Limit the length of the reason text
    else:
        reason_text = reasons.get(reason, "Unknown Reason")

    total_miles += miles
    trips.append((datetime.now(), departure, destination, miles, reason_text))

    # Check if the reversed direction of the trip is already recorded
    if (destination, departure) not in unique_city_pairs:
        unique_city_pairs.add((departure, destination))

    # Save program state after each trip recording
    save_program_state()

def generate_report():
    current_month = datetime.now().strftime("%Y-%m")
    filename = f"travel_report_{current_month}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)

    # Add the government seal image
    c.drawImage("2ndJudC_logo.jpg", 30, 650, width=100, height=100)

    # Add text for reimbursement request
    c.setFont("Courier", 16)
    c.drawString(150, 700, "Wakulla County Voucher for Reimbursement")
    c.drawString(150, 670, "of Travel Expenses")

    # Write trips and mileage information
    c.setFont("Courier", 12)
    y = 580
    for trip in trips:
        timestamp, departure, destination, miles, reason = trip
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")  # Format timestamp to show only hours and minutes
        if miles != 20:  # Check if the trip isn't Tallahassee to Crawfordville
            c.drawString(100, y, f"{formatted_time}: {departure} to {destination} - {miles} miles")
            c.drawString(100, y - 15, f"Reason: {reason}")  # Place reason below trip details
        else:
            c.drawString(100, y, f"{formatted_time}: {departure} to {destination} (unpaid) - {miles}")
            c.drawString(100, y - 15, f"Reason: {reason}")  # Place reason below trip details
        y -= 40 # increase the gap between trips

    # Calculate and write reimbursement information
    total_reimbursement_str = f"Total reimbursement amount: ${total_reimbursement:.2f}"
    c.drawString(100, y - 30, f"Total miles traveled this month: {total_miles}")
    c.drawString(100, y - 50, total_reimbursement_str)

    # Add images at the end of the report for unique city pairs
    c.showPage()  # Add a new page
    for idx, (start, end) in enumerate(unique_city_pairs, start=1):
        path = f"{start}to{end}.png"
        c.drawImage(path, 30, 650 - (idx * 100), width=400, height=100)

    c.save()

def generate_pdf_report():
    # Load the entire history of trips from Madison_program_state.json
    try:
        with open(f"{logged_in_user}_program_state.json", 'r') as file:
            program_state = json.load(file)
            trips = program_state.get('trips', [])
            total_miles = program_state.get('total_miles', 0)
            unique_city_pairs = {
                tuple(pair) for pair in program_state.get('unique_city_pairs', [])
            }
            # Convert timestamps in trips back to datetime objects
            for trip in trips:
                trip[0] = datetime.fromisoformat(trip[0])
    except FileNotFoundError:
        # If the file doesn't exist, set default values
        trips = []
        total_miles = 0
        unique_city_pairs = set()

    # Calculate reimbursement within the function scope
    total_reimbursement = calculate_reimbursement(total_miles)

    current_month = datetime.now().strftime("%Y-%m")
    filename = f"travel_report_{current_month}.pdf"
    max_lines_per_page = 12
    c = canvas.Canvas(filename, pagesize=letter)

    # Add the government seal image
    c.drawImage("2ndJudC_logo.jpg", 30, 650, width=100, height=100)

    # Add text for reimbursement request
    c.setFont("Courier", 16)
    c.drawString(150, 700, "Wakulla County Voucher for Reimbursement")
    c.drawString(150, 670, "of Travel Expenses")

    # Write trips and mileage information
    c.setFont("Courier", 12)
    line_count = 0
    y = 580
    for trip in trips:
        timestamp, departure, destination, miles, reason = trip
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")  # Format timestamp to show only hours and minutes
        if miles != 20:  # Check if the trip isn't Tallahassee to Crawfordville
            c.drawString(100, y, f"{formatted_time}: {departure} to {destination} - {miles} miles")
            c.drawString(100, y - 15, f"Reason: {reason}")  # Place reason below trip details
        else:
            c.drawString(100, y, f"{formatted_time}: {departure} to {destination} (unpaid) - {miles}")
            c.drawString(100, y - 15, f"Reason: {reason}")  # Place reason below trip details
        y -= 40  # increase the gap between trips

        line_count += 1
        if line_count >= max_lines_per_page:
            # If remaining space is not enough for another trip, create a new page
            c.showPage()
            # Reset line_count and y-coordinate for the new page
            c.setFont("Courier", 12)
            line_count = 0
            y = 750  # Set to a suitable starting position on the new page

    # Calculate and write reimbursement information
    total_reimbursement_str = f"Total reimbursement amount: ${total_reimbursement:.2f}"
    c.drawString(100, y - 30, f"Total miles traveled this month: {total_miles}")
    c.drawString(100, y - 50, total_reimbursement_str)

    # Add images at the end of the report for unique city pairs
    added_maps = set()  # Maintain a set to track added maps

    c.showPage()  # Add a new page
    for idx, (start, end) in enumerate(unique_city_pairs, start=1):
        path = f"{start}to{end}.png"

        # Check if the map has already been added to avoid duplicates
        if path not in added_maps:
            c.drawImage(path, 30, 650 - (idx * 100), width=400, height=100)
            added_maps.add(path)  # Add the path to the set of added maps

    c.save()
    messagebox.showinfo("Report Generated", f"PDF report generated: {filename}")

    # Open the generated PDF file in the default PDF viewer
    try:
        subprocess.run([filename], shell=True)
    except FileNotFoundError:
        messagebox.showerror("Error", "Could not open the PDF file.")

    # Terminate the program
    exit()

# Function to handle GUI form submission
# Function to handle GUI form submission
def submit_form():
    departure = departure_var.get()
    destination = destination_var.get()
    miles = mileage_data.get((departure, destination), 0)

    if miles != 0:
        reason_choice = reason_var.get()
        if reason_choice == 6:  # 'Other' was selected
            custom_reason = custom_reason_entry.get()  # Get the custom reason text
            record_trip(departure, destination, miles, reason_choice, custom_reason)
        else:
            record_trip(departure, destination, miles, reason_choice, "")
        messagebox.showinfo("Success", f"Recorded {miles} miles for {departure} to {destination}")
    else:
        messagebox.showerror("Error", "Invalid cities entered or route not available.")

# Create Tkinter window
root = tk.Tk()
root.title("Travel Reimbursement Program")

# Create labels and entry fields
departure_label = tk.Label(root, text="Departure city:")
departure_label.pack()
departure_var = tk.StringVar()
departure_entry = tk.Entry(root, textvariable=departure_var)
departure_entry.pack()

destination_label = tk.Label(root, text="Destination city:")
destination_label.pack()
destination_var = tk.StringVar()
destination_entry = tk.Entry(root, textvariable=destination_var)
destination_entry.pack()

reason_label = tk.Label(root, text="Reason for travel:")
reason_label.pack()
reason_var = tk.IntVar()
for num, reason in reasons.items():
    rb = tk.Radiobutton(root, text=reason, variable=reason_var, value=num)
    rb.pack()

# Create labels and entry fields for custom reason in the GUI
custom_reason_label = tk.Label(root, text="Custom Reason:")
custom_reason_label.pack()
custom_reason_entry = tk.Entry(root)
custom_reason_entry.pack()

submit_button = tk.Button(root, text="Submit", command=submit_form)
submit_button.pack()

generate_report_button = tk.Button(root, text="Generate Report", command=generate_pdf_report)
generate_report_button.pack()

# Start the GUI main loop
root.mainloop()

# Sample usage and data collection
while True:
    username = logged_in_user # Use the logged_in_user variable for recording trips

    print("Available cities: Tallahassee, Crawfordville, Quincy, Apalachicola, Bristol")
    departure = input("Enter departure city: ")
    destination = input("Enter destination city: ")

    if (departure, destination) in mileage_data:
        miles = mileage_data[(departure, destination)]
        if miles != 20:  # Exclude Tallahassee to Crawfordville
            print("Select the reason for travel:")
            for num, reason in reasons.items():
                print(f"{num}: {reason}")
            reason_choice = int(input("Enter the corresponding number for the reason: "))
            record_trip(departure, destination, miles, reason_choice)
            print(f"Recorded {miles} miles for {departure} to {destination}")
        else:
            print("Excluded miles between Tallahassee and Crawfordville.")
    else:
        print("Invalid cities entered or route not available.")

    more_trips = input("Do you have more trips today? (y/n): ")
    if more_trips.lower() != 'y':
        break

# Flag to indicate if the month's data collection is complete
data_collection_complete = False

while not data_collection_complete:
    print("Available cities: Tallahassee, Crawfordville, Quincy, Apalachicola, Bristol")
    departure = input("Enter departure city (or 'end' to finish for today): ")

    # Check if the user wants to end data collection for the month
    if departure.lower() == 'end':
        more_days = input("Do you have more trips this month? (y/n): ")
        if more_days.lower() != 'y':
            data_collection_complete = True
        continue

    destination = input("Enter destination city: ")

    if (departure, destination) in mileage_data:
        miles = mileage_data[(departure, destination)]
        if miles != 20:  # Exclude Tallahassee to Crawfordville
            print("Select the reason for travel:")
            for num, reason in reasons.items():
                print(f"{num}: {reason}")
            reason_choice = int(input("Enter the corresponding number for the reason: "))
            record_trip(departure, destination, miles, reason_choice)
            print(f"Recorded {miles} miles for {departure} to {destination}")
        else:
            print("Excluded miles between Tallahassee and Crawfordville.")
    else:
        print("Invalid cities entered or route not available.")

total_reimbursement = calculate_reimbursement(total_miles)

print(f"Total miles traveled this month: {total_miles}")
print(f"Total reimbursement amount: ${total_reimbursement:.2f}")

generate_pdf_report()  # Generate PDF report with all recorded trips
exit()