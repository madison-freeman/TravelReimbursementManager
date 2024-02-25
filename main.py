from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import json
from json import JSONEncoder
import tkinter as tk
from tkinter import messagebox
import subprocess
from tkinter import simpledialog

class DateTimeEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return JSONEncoder.default(self, o)

# Mileage data
mileage_data = {
    ("Tallahassee", "Crawfordville"): 20,
    ("Crawfordville", "Tallahassee"): 20,
    ("Tallahassee", "Quincy"): 19,
    ("Quincy", "Tallahassee"): 19,
    ("Crawfordville", "Apalachicola"): 57,
    ("Apalachicola", "Crawfordville"): 57,
    ("Crawfordville", "Monticello"): 46,
    ("Monticello", "Crawfordville"): 46,
    ("Tallahassee", "Monticello"): 26,
    ("Monticello", "Tallahassee"): 26,
    ("Tallahassee", "Apalachicola"): 77,
    ("Apalachicola", "Tallahassee"): 77,
    ("Tallahassee", "Bristol"): 44,
    ("Bristol", "Tallahassee"): 44,
    ("Crawfordville", "Bristol"): 46,
    ("Bristol", "Crawfordville"): 46
}

reasons = {
    1: "Support of Equipment",
    2: "Return",
    3: "Mandatory Meeting",
    4: "Pick Up Parts",
    5: "Delivering Equipment",
    6: "Other"
}

reimbursement_rate = 0.67  # cents per mile
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
            total_miles = program_state.get('total_miles', 0)
            trips = program_state.get('trips', [])
            unique_city_pairs = set(program_state.get('unique_city_pairs', []))
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

        # Check if it's the user's first login
        if 'base_city' not in user_profiles[username]:
            first_login = messagebox.askyesno("First Login", "Is this your first time logging in?")
            if first_login:
                base_city_window = tk.Toplevel()
                base_city_window.title("Set Base City")

                base_city_label = tk.Label(base_city_window, text="Select your base city:")
                base_city_label.pack()

                # Create a dropdown menu for base city selection
                base_city_var = tk.StringVar(base_city_window)
                base_city_var.set("Tallahassee")  # Set default base city
                cities = ["Tallahassee", "Crawfordville", "Quincy", "Apalachicola", "Bristol"]
                base_city_menu = tk.OptionMenu(base_city_window, base_city_var, *cities)
                base_city_menu.pack()

                # Function to save the selected base city and close the window
                def save_base_city():
                    selected_base_city = base_city_var.get()
                    user_profiles[logged_in_user]['base_city'] = selected_base_city

                    # Retrieve user information
                    tar_number = tar_number_entry.get()
                    employee_id = employee_id_entry.get()
                    traveler_name = traveler_name_entry.get()
                    agency = agency_entry.get()
                    headquarters = headquarters_entry.get()
                    account_number = account_number_entry.get()
                    base_city = base_city_var.get()

                    # Store user information in user_profiles
                    user_profiles[logged_in_user]['user_info'] = {
                        'TAR': tar_number,
                        'Employee ID / SSN': employee_id,
                        'Traveler Name': traveler_name,
                        'Agency': agency,
                        'Headquarters': headquarters,
                        'City of Residence': base_city,
                        'Account Number': account_number
                    }

                    save_user_profiles()
                    messagebox.showinfo("Base City", f"Base city set to {selected_base_city}")
                    base_city_window.destroy()
                    login_window.destroy()

                # Add labels and entry fields for user information
                tar_number_label = tk.Label(base_city_window, text="TAR #:")
                tar_number_label.pack()
                tar_number_entry = tk.Entry(base_city_window)
                tar_number_entry.pack()

                employee_id_label = tk.Label(base_city_window, text="Employee ID / SSN: ")
                employee_id_label.pack()
                employee_id_entry = tk.Entry(base_city_window)
                employee_id_entry.pack()

                traveler_name_label = tk.Label(base_city_window, text="Traveler Name: ")
                traveler_name_label.pack()
                traveler_name_entry = tk.Entry(base_city_window)
                traveler_name_entry.pack()

                agency_label = tk.Label(base_city_window, text="Agency: ")
                agency_label.pack()
                agency_entry = tk.Entry(base_city_window)
                agency_entry.pack()

                headquarters_label = tk.Label(base_city_window, text="Headquarters: ")
                headquarters_label.pack()
                headquarters_entry = tk.Entry(base_city_window)
                headquarters_entry.pack()

                account_number_label = tk.Label(base_city_window, text="Account Number: ")
                account_number_label.pack()
                account_number_entry = tk.Entry(base_city_window)
                account_number_entry.pack()

                save_button = tk.Button(base_city_window, text="Save", command=save_base_city)
                save_button.pack()
                return

        login_window.destroy()  # Close the login window after successful login
    else:
        messagebox.showerror("Login", "Invalid username or password")

# Function to handle closing the login window
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        login_window.destroy()
        exit()  # Exit the program when the window is closed


# Function to handle creating a new user profile
def create_user_profile():
    def save_new_user_profile():
        new_username = new_username_entry.get()
        new_password = new_password_entry.get()

        if new_username and new_password:
            user_profiles[new_username] = {'password': new_password, 'trips': []}
            save_user_profiles()
            messagebox.showinfo("Profile Created", "User profile created successfully!")
            new_user_window.destroy()
        else:
            messagebox.showerror("Error", "Username and password are required!")

    new_user_window = tk.Toplevel()
    new_user_window.title("Create User Profile")

    new_username_label = tk.Label(new_user_window, text="Enter Username:")
    new_username_label.pack()
    new_username_entry = tk.Entry(new_user_window)
    new_username_entry.pack()

    new_password_label = tk.Label(new_user_window, text="Enter Password:")
    new_password_label.pack()
    new_password_entry = tk.Entry(new_user_window, show="*")  # Show * for password input
    new_password_entry.pack()

    save_button = tk.Button(new_user_window, text="Save", command=save_new_user_profile)
    save_button.pack()


# Create Tkinter window for login
login_window = tk.Tk()
login_window.geometry("300x200")
login_window.title("Login")

# Function to handle hitting 'Enter' for login
def enter_pressed(event):
    validate_login()

# Binding the 'Return' key to the validate_login function
login_window.bind('<Return>', enter_pressed)

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

# Add a button for creating a new user profile
create_profile_button = tk.Button(login_window, text="Create User Profile", command=create_user_profile)
create_profile_button.pack()

# Start the GUI main loop for login window
login_window.mainloop()

# Continue with the rest of your existing code after successful login
if not logged_in_user:
    exit()  # Exit the program if login fails

# Function to record trip for a user
def record_user_trip(username, departure, destination, miles, reason, statement=""):
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
        "reason": reason_text,
        "statement": statement
    })

    # Update user profile
    user_profiles[username] = user_data
    save_user_profiles()

def calculate_reimbursement(miles):
    return miles * reimbursement_rate

# Define the base city
base_city = "Tallahassee"

# Function to record trips, considering base city and Crawfordville exclusion
def record_trip(departure, destination, miles, reason, custom_reason="", statement=""):
    global total_miles
    global trips
    global unique_city_pairs

    # Skip recording trips between base city and Crawfordville
    if (departure == base_city and destination == "Crawfordville") or \
       (departure == "Crawfordville" and destination == base_city):
        return

    # Check if the trip or its reverse is already recorded
    if (departure, destination) in unique_city_pairs or \
       (destination, departure) in unique_city_pairs:
        return

    if reason == 6:  # If "Other" is selected, use the custom reason provided
        reason_text = custom_reason[:40]  # Limit the length of the reason text
    else:
        reason_text = reasons.get(reason, "Unknown Reason")

    total_miles += miles
    trips.append((datetime.now(), departure, destination, miles, reason_text))

    # Add the trip and its reverse to the unique city pairs set
    unique_city_pairs.add((departure, destination))
    unique_city_pairs.add((destination, departure))

    # Save program state after each trip recording
    save_program_state()

def generate_pdf_report(statement=""):
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
    filename = f"{logged_in_user}_travel_report_{current_month}.pdf"
    max_lines_per_page = 30
    c = canvas.Canvas(filename, pagesize=letter)

    # Add the government seal image
    c.drawImage("2ndJudC_logo.jpg", 30, 650, width=100, height=100)

    # Add text for reimbursement request
    c.setFont("Courier", 12)
    c.drawString(150, 740, "Wakulla County Voucher for Reimbursement")
    c.drawString(150, 720, "of Travel Expenses")

    # Add user information at the top of the report
    c.setFont("Courier", 8)
    user_info = user_profiles.get(logged_in_user, {}).get('user_info', {})
    y_offset = 700
    for key, value in user_info.items():
        # Set color for the key (dark red)
        c.setFillColorRGB(0.5, 0, 0)  # Dark red color
        c.drawString(150, y_offset, f"{key}: ")
        # Set color for the value (black)
        c.setFillColorRGB(0, 0, 0)  # Black color
        c.drawString(270, y_offset, f"{value}")
        y_offset -= 10 # Adjust spacing between lines

    # Draw a long solid line to separate user_info from columns
    c.setStrokeColorRGB(0, 0, 0)  # Set stroke color to black
    c.setLineWidth(1)  # Set line width to 1 point
    c.line(30, 632, 575, 632)  # Draw a line from (50, 625) to (550, 625)

    # Write header for the table
    c.setFont("Courier-Bold", 8)
    # Date column
    c.drawString(40, 620, "Date")
    # Hour of Departure and Hour of Arrival column
    c.drawString(80, 620, "Time")
    # Travel Departure and Arrival column
    c.drawString(130, 620, "Travel from")
    c.drawString(130, 610, "Point of Origin")
    c.drawString(130, 600, "to Destination")
    # Purpose or Reason of travel column
    c.drawString(240, 620, "Purpose or")
    c.drawString(240, 610, "Reason")
    # Map/Vicinity Mileage Claimed column
    c.drawString(330, 620, "Vicinity")
    c.drawString(330, 610, "Mileage")
    c.drawString(330, 600, "Claimed")
    # Meals for Class A&B Travel expenses column
    c.drawString(400, 620, "Meals for")
    c.drawString(400, 610, "Class")
    c.drawString(400, 600, "A&B Travel")
    # Per Diem Lodging expenses column
    c.drawString(460, 620, "Per Diem")
    c.drawString(460, 610, "Lodging")
    c.drawString(460, 600, "Expenses")
    # Other expenses column
    c.drawString(520, 620, "Other")
    c.drawString(520, 610, "Expenses")

    # Write trips and mileage information
    c.setFont("Courier", 6)
    y = 580
    for trip in trips:
        timestamp, departure, destination, miles, reason = trip
        formatted_date = timestamp.strftime("%m-%d-%y")
        formatted_time = timestamp.strftime("%I:%M %p")  # Format timestamp to show 12-hour clock with AM/PM
        if miles != 20:  # Check if the trip isn't Tallahassee to Crawfordville
            c.drawString(40, y, formatted_date)
            c.drawString(80, y, formatted_time)
            c.drawString(130, y, f"{departure} to {destination}")
            c.drawString(240, y, reason)
            c.drawString(330, y, f"{miles}")
            c.drawString(750, y, f"{timestamp.hour} - {timestamp.hour + 1}")
        else:
            c.drawString(40, y, formatted_date)
            c.drawString(80, y, formatted_time)
            c.drawString(130, y, f"{departure} to {destination} (unpaid) - {miles}")
            c.drawString(240, y, reason)
            c.drawString(330, y, f"{miles}")
            c.drawString(750, y, f"{timestamp.hour} - {timestamp.hour + 1}")
        y -= 20  # Increase the gap between rows

    # Calculate and write reimbursement information
    total_reimbursement_str = f"Total reimbursement amount: ${total_reimbursement:.2f}"
    c.drawString(40, y - 30, f"Total miles paid at: $0.67")
    c.drawString(40, y - 40, f"Total miles traveled this month: {total_miles}")
    c.drawString(40, y - 50, total_reimbursement_str)

    # Print the statement of benefits
    if statement:
        # Get existing statement if available
        existing_statement = ""
        try:
            with open("statement_of_benefits.txt", "r") as file:
                existing_statement = file.read()
        except FileNotFoundError:
            pass

        # Append new statement to existing one
        combined_statement = existing_statement + reason + "-" + statement + "; "

        # Save the combined statement to file
        with open("statement_of_benefits.txt", "w") as file:
            file.write(combined_statement)

    # Add content from statement_of_benefits.txt if available
    try:
        with open("statement_of_benefits.txt", "r") as file:
            statement_content = file.read()
            c.drawString(40, y - 60, f"Statement of Benefits: {statement_content}")
    except FileNotFoundError:
        pass

    # Add images at the end of the report for unique city pairs
    added_city_pairs = set()  # Maintain a set to track added city pairs

    c.showPage()  # Add a new page
    for idx, (start, end) in enumerate(unique_city_pairs, start=1):
        city_pair = frozenset([start, end])

        # Check if the city pair or its reverse has already been added to avoid duplicates
        if city_pair not in added_city_pairs:
            path = f"Maps/{start}to{end}.png"
            c.drawImage(path, 30, 700 - (idx * 150), width=550, height=180)
            added_city_pairs.add(city_pair)  # Add the city pair to the set of added city pairs

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
def submit_form():
    departure = departure_var.get()
    destination = destination_var.get()
    miles = mileage_data.get((departure, destination), 0)

    if miles != 0:
        reason_choice = reason_var.get()
        if reason_choice == 6:  # 'Other' was selected
            custom_reason = custom_reason_entry.get()
            # Prompt the user for the statement of benefits
            statement = simpledialog.askstring("Statement of Benefits",
                                               "Please provide a statement of benefits to the state:")
            if statement is not None:  # Check if a statement is provided
                # Record the trip with both purpose/reason and statement of benefits
                record_trip(departure, destination, miles, reason_choice, custom_reason, statement)
                messagebox.showinfo("Success", f"Recorded {miles} miles for {departure} to {destination}")
                generate_pdf_report(statement)  # Pass the statement to generate PDF report
            else:
                messagebox.showinfo("Information", "Trip recording canceled.")  # Notify user of cancellation
        else:
            # For other reasons, directly record the trip without requiring a statement
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

exit()