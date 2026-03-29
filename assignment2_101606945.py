"""
Author: Hayden Markusich
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

import socket
import threading
import sqlite3
import os
import platform
import datetime

print("Python Version:", platform.python_version())
print("Operating System:", os.name)

common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}

class NetworkTool:
    def __init__(self, target):
        self.__target = target

# Q3: What is the benefit of using @property and @target.setter?
# @property lets us use target like a normal variable while still keeping it private.
# The setter lets us check the value before changing it like stopping empty input.
# This helps prevent mistakes and keeps the program working properly.
    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value == "":
            print("Error: Target cannot be empty")
        else:
            self.__target = value

    def __del__(self):
        print("NetworkTool instance destroyed")

# Q1: How does PortScanner reuse code from NetworkTool?
# PortScanner inherits from NetworkTool so it can reuse the code for storing the target.
# For example it calls super().__init__(target) instead of writing that code again.
# This saves time and keeps things organized.
class PortScanner(NetworkTool):

    def __init__(self, target):
        super().__init__(target)
        self.results_list = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

    def scan_port(self, port):
        # Q4: What would happen without try-except here?
        # Without try-except the program could crash if there is a connection error.
        # This would stop the scan before it finishes.
        # Using try-except allows it to keep going even if something fails. 
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            result = sock.connect_ex((self.target, port))

            if result == 0:
                status = "Open"
            else:
                status = "Closed"

            service = common_ports.get(port, "Unknown")

            self.lock.acquire()
            self.results_list.append((port, status, service))
            self.lock.release()

        except socket.error as e:
            print(f"Error scanning port {port}: {e}")

        finally:
            sock.close()

    def get_open_ports(self):
        return [r for r in self.results_list if r[1] == "Open"]

# Q2: Why do we use threading instead of scanning one port at a time?
# Threading lets the program check multple ports at the same time.
# If we did it one by one scanning a lot of ports would take much longer.
# Using threads makes the scan faster overall.
    def scan_range(self, start_port, end_port):
        threads = []

        for port in range(start_port, end_port + 1):
            t = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            port INTEGER,
            status TEXT,
            service TEXT,
            scan_date TEXT
        )
        """)

        for port, status, service in results:
            cursor.execute(
                "INSERT INTO scans (target, port, status, service, scan_date) VALUES (?, ?, ?, ?, ?)",
                (target, port, status, service, str(datetime.datetime.now()))
            )

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print("Database error:", e)

def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM scans")
        rows = cursor.fetchall()

        for row in rows:
            print(f"[{row[5]}] {row[1]} : Port {row[2]} ({row[4]}) - {row[3]}")

        conn.close()

    except:
        print("No past scans found.")

if __name__ == "__main__":
    try:
        target = input("Enter target IP (default 127.0.0.1): ") or "127.0.0.1"

        start_port = int(input("Enter start port: "))
        end_port = int(input("Enter end port: "))

        if start_port < 1 or end_port > 1024:
            print("Port must be between 1 and 1024.")
            exit()

        if end_port < start_port:
            print("End port must be >= start port.")
            exit()

    except ValueError:
        print("Invalid input. Please enter a valid integer.")
        exit()

    scanner = PortScanner(target)

    print(f"Scanning {target} from port {start_port} to {end_port}...")

    scanner.scan_range(start_port, end_port)

    open_ports = scanner.get_open_ports()

    print(f"\n--- Scan Results for {target} ---")
    for port, status, service in open_ports:
        print(f"Port {port}: {status} ({service})")

    print("------")
    print(f"Total open ports found: {len(open_ports)}")

    save_results(target, scanner.results_list)

    choice = input("Would you like to see past scan history? (yes/no): ")

    if choice.lower() == "yes":
        load_past_scans()

# Q5: New Feature Proposal
# One feature I would add is filtering results to show only certain services like HTTP or SSH.
# This could be done using a list comprehension to check the service name.
# It would make the results easier to read and more useful.
# Diagram: See diagram_studentID.png in the repository root