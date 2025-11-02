"""
2legit4it Monster Suite
Unified engine - All main features, choose and run from simple menu
"""

import sqlite3
import hashlib
import json
import datetime

def forensic_audit():
    print("Log a specific action/user/details into the forensic audit database")
    action = input("Action: ")
    user = input("User: ")
    details = input("Details: ")
    conn = sqlite3.connect("2legit4itdb.sqlite")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS forensicaudit (
            id INTEGER PRIMARY KEY,
            action TEXT,
            user TEXT,
            details TEXT,
            timestamp TEXT
        )
    """)
    timestamp = datetime.datetime.utcnow().isoformat("T")
    cur.execute("INSERT INTO forensicaudit (action, user, details, timestamp) VALUES (?, ?, ?, ?)", 
                (action, user, details, timestamp))
    conn.commit()
    conn.close()
    print("Audit logged!")

def manifest_generator():
    print("Generate a manifest for tracked files with SHA256 hashes")
    project = input("Project name: ")
    contributors = input("Contributors (comma separated): ").split(",")
    files = input("File paths (comma separated): ").split(",")
    manifest = {
        "project": project,
        "contributors": contributors,
        "generated": datetime.datetime.utcnow().isoformat(),
        "files": []
    }
    for fpath in files:
        fpath = fpath.strip()
        try:
            with open(fpath, "rb") as f:
                content = f.read()
                fhash = hashlib.sha256(content).hexdigest()
                manifest["files"].append({
                    "name": fpath,
                    "sha256": fhash
                })
        except Exception as e:
            manifest["files"].append({
                "name": fpath,
                "error": str(e)
            })
    print(json.dumps(manifest, indent=2))

def multiuser_collaboration():
    print("Add a user to a project team for collaboration")
    project = input("Project: ")
    user = input("User: ")
    role = input("Role: ")
    conn = sqlite3.connect("2legit4itdb.sqlite")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS team (
            id INTEGER PRIMARY KEY,
            project TEXT,
            user TEXT,
            role TEXT
        )
    """)
    cur.execute("INSERT INTO team (project, user, role) VALUES (?, ?, ?)", (project, user, role))
    conn.commit()
    conn.close()
    print(f"{user} added to {project} as {role}")

def access_control():
    print("Grant a permission to a user")
    user = input("User: ")
    permission = input("Permission: ")
    conn = sqlite3.connect("2legit4itdb.sqlite")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY,
            user TEXT,
            permission TEXT
        )
    """)
    cur.execute("INSERT INTO permissions (user, permission) VALUES (?, ?)", (user, permission))
    conn.commit()
    conn.close()
    print(f"{user} now has permission: {permission}")

def menu():
    functions = [
        ("Forensic Audit", forensic_audit),
        ("Manifest Generator", manifest_generator),
        ("Multiuser Collaboration", multiuser_collaboration),
        ("Access Control", access_control)
    ]
    while True:
        print("
2legit4it Main Menu")
        for i, (name, _) in enumerate(functions):
            print(f"{i+1}. {name}")
        print("0. Exit")
        choice = input("Select action: ")
        if choice == "0":
            break
        try:
            index = int(choice) - 1
            if 0 <= index < len(functions):
                functions[index][1]()
            else:
                print("Invalid option!")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    menu()