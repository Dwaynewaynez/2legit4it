import sqlite3
import hashlib
import hmac
import json
import os
import zipfile
from datetime import datetime
from getpass import getuser

DBPATH = "codingdemon.db"
HMACKEY = b"CHANGETHISTOASTRONGSECRETKEY"
OWNER = "Dwayne Anthony Brian Galloway"

def initdb():
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY, name TEXT, createdts TEXT, owner TEXT
    );
    CREATE TABLE IF NOT EXISTS facts (
        id INTEGER PRIMARY KEY, projectid INTEGER, date TEXT, description TEXT,
        evidencelink TEXT, hash TEXT,
        FOREIGN KEY(projectid) REFERENCES projects(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS auditlog (
        id INTEGER PRIMARY KEY, ts TEXT, actor TEXT, action TEXT, details TEXT
    );
    CREATE TABLE IF NOT EXISTS collaborators (
        id INTEGER PRIMARY KEY, projectid INTEGER, user TEXT,
        FOREIGN KEY(projectid) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()

def getinput(prompt, required=True):
    while True:
        value = input(prompt).strip()
        if not value and required:
            print("Required. Please enter a value.")
        else:
            return value

def filehashsha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def manifesthmac(data, key=HMACKEY):
    return hmac.new(key, data, hashlib.sha256).hexdigest()

def logaudit(action, actor, details):
    ts = datetime.utcnow().isoformat() + "Z"
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO auditlog(ts, actor, action, details) VALUES (?, ?, ?, ?)",
        (ts, actor, action, details)
    )
    conn.commit()
    conn.close()

def createproject():
    name = getinput("Enter new project name: ")
    ts = datetime.utcnow().isoformat() + "Z"
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects(name, createdts, owner) VALUES (?, ?, ?)",
        (name, ts, OWNER)
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    logaudit("create_project", getuser(), f"project_id={pid}, name={name}")
    print(f"OK. Project created. ID {pid}")
    return pid

def listprojects():
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, createdts FROM projects")
    rows = cur.fetchall()
    conn.close()
    return rows

def addcollaborator(pid):
    user = getinput("Enter collaborator username: ")
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO collaborators(projectid, user) VALUES (?, ?)",
        (pid, user)
    )
    conn.commit()
    conn.close()
    logaudit("add_collaborator", getuser(), f"project_id={pid}, collaborator={user}")
    print("Collaborator added.")

def addfact(pid):
    desc = getinput("Describe the fact, issue, or piece of code: ")
    ev = getinput("Attach an evidence file path (leave blank for none): ", required=False)
    h = None
    evidencelink = None
    if ev:
        if not os.path.exists(ev):
            print("File not found. Skipping attachment.")
        else:
            h = filehashsha256(ev)
            evidencelink = os.path.abspath(ev)
    ts = datetime.utcnow().isoformat() + "Z"
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO facts(projectid, date, description, evidencelink, hash) VALUES (?, ?, ?, ?, ?)",
        (pid, ts, desc, evidencelink, h)
    )
    fid = cur.lastrowid
    conn.commit()
    conn.close()
    logaudit("add_fact", getuser(), f"project_id={pid}, fact_id={fid}")
    print(f"OK. Fact added. ID {fid}")

def listfacts(pid):
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute("SELECT id, date, description FROM facts WHERE projectid = ?", (pid,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("No facts recorded for this project.")
    for fid, date, desc in rows:
        print(f"- {fid} | {date} | {desc[:70]}...")

def exportevidencepack(pid):
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM projects WHERE id = ?", (pid,))
    project = cur.fetchone()
    if not project:
        print("No such project.")
        return
    pname = project[0]
    cur.execute("SELECT * FROM facts WHERE projectid = ?", (pid,))
    facts = cur.fetchall()
    exportzip = f"{pname}_evidencepack.zip"
    manifest = {
        "owner": OWNER,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project": pname,
        "facts": []
    }
    z = zipfile.ZipFile(exportzip, "w", zipfile.ZIP_DEFLATED)
    for fact in facts:
        fid, _, date, desc, link, filehash = fact
        item = {
            "id": fid, "date": date, "description": desc,
            "evidence_link": link, "hash": filehash
        }
        manifest["facts"].append(item)
        # Embed watermark to every description
        descwm = f"{desc}
---C 2025 Dwayne Anthony Brian Galloway. All Rights Reserved."
        z.writestr(f"fact_{fid}.txt", descwm)
        if link and os.path.exists(link):
            z.write(link, arcname=os.path.basename(link))
    manifestbytes = json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8")
    z.writestr("manifest.json", json.dumps(manifest, indent=2))
    z.writestr("manifest.sig", manifesthmac(manifestbytes))
    z.close()
    logaudit("export_evidence_pack", getuser(), f"project_id={pid}, output={exportzip}")
    print(f"OK. Exported {exportzip}")

def onboarding():
    print("Coding Demon Protocol")
    print(f"C 2025 {OWNER}. All Rights Reserved.
")
    print("Before you use this tool, you must acknowledge and agree to the following:")
    print("- 10% of all revenues generated via Coding Demon, its code, or derivative outputs are contractually owed to Dwayne Anthony Brian Galloway as royalty, in perpetuity.")
    print("- You accept that every output will be watermarked and cryptographically attributed.")
    print("- Use of this platform constitutes irrevocable acceptance of these terms.")
    ans = input("Type I AGREE to continue: ").strip()
    if ans.lower() != "i agree":
        print("Agreement not accepted. Exiting.")
        exit(1)

def mainmenu():
    onboarding()
    initdb()
    print("
Menu")
    while True:
        print("
1. Create a new project/session")
        print("2. List projects")
        print("3. Add collaborator to project")
        print("4. Add fact/evidence/issue to project")
        print("5. List project facts")
        print("6. Export evidence/compliance package (.zip)")
        print("0. Exit")
        try:
            sel = int(getinput("Select: "))
        except ValueError:
            print("Enter a number.")
            continue
        if sel == 1:
            createproject()
        elif sel == 2:
            projects = listprojects()
            for pid, name, ts in projects:
                print(f"- {pid} | {name} | Created {ts}")
        elif sel == 3:
            pid = int(getinput("Enter Project ID: "))
            addcollaborator(pid)
        elif sel == 4:
            pid = int(getinput("Enter Project ID: "))
            addfact(pid)
        elif sel == 5:
            pid = int(getinput("Enter Project ID: "))
            listfacts(pid)
        elif sel == 6:
            pid = int(getinput("Enter Project ID: "))
            exportevidencepack(pid)
        elif sel == 0:
            print("Goodbye.")
            break
        else:
            print("Invalid selection.")

if __name__ == "__main__":
    mainmenu()