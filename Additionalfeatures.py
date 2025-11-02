#"""
================================================================================
 PRIVATE COMPLIANCE REPOSITORY: 2Legit4It / Coding Demon Suite
================================================================================

This repository and all contained files are PRIVATE and PROTECTED.

- Do NOT upload, deploy, or share on public GitHub, Hugging Face Space, or any public platform unless you explicitly consent.
- Hugging Face Spaces must be set to "Private" (Subscription required).
- GitHub repos must be "Private" and restricted to trusted collaborators.
- All compliance modules, the 3,600 Boris Loops, magnets, escalation logic, and trade-secret sauce are strictly for private/internal use.

>>> By running, deploying, or sharing this code, you agree to KEEP IT LOCKED DOWN. 
>>> Shade is forbidden here—this code runs in the sun, but never in public!

================================================================================
"""

import sqlite3
import hashlib
import hmac
import json
import os
import zipfile
from datetime import datetime
from getpass import getuser

DBPATH = "codingdemon.db"
HMACKEY = b'CHANGETHISTOASTRONGSECRETKEY'
OWNER = "Dwayne Anthony Brian Galloway"

def initdb():
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY, 
            name TEXT, createdts TEXT, owner TEXT
        );
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY,
            projectid INTEGER,
            date TEXT,
            description TEXT,
            evidencelink TEXT,
            hash TEXT,
            FOREIGN KEY(projectid) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS auditlog (
            id INTEGER PRIMARY KEY,
            ts TEXT, actor TEXT, action TEXT, details TEXT
        );
        CREATE TABLE IF NOT EXISTS collaborators (
            id INTEGER PRIMARY KEY,
            projectid INTEGER, 
            user TEXT,
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
    ts = datetime.utcnow().isoformat("T") + "Z"
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
    ts = datetime.utcnow().isoformat("T") + "Z"
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects(name, createdts, owner) VALUES (?, ?, ?)",
        (name, ts, OWNER)
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    logaudit("createproject", getuser(), f"projectid={pid},name={name}")
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
        "INSERT INTO collaborators(projectid, user) VALUES (?, ?)", (pid, user)
    )
    conn.commit()
    conn.close()
    logaudit("addcollaborator", getuser(), f"projectid={pid},collaborator={user}")
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
    ts = datetime.utcnow().isoformat("T") + "Z"
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO facts(projectid, date, description, evidencelink, hash) VALUES (?, ?, ?, ?, ?)",
        (pid, ts, desc, evidencelink, h)
    )
    fid = cur.lastrowid
    conn.commit()
    conn.close()
    logaudit("addfact", getuser(), f"projectid={pid},factid={fid}")
    print(f"OK. Fact added. ID {fid}")

def listfacts(pid):
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, date, description FROM facts WHERE projectid = ?", (pid,)
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("No facts recorded for this project.")
    for fid, date, desc in rows:
        print(f"- {fid} {date} {desc[:70]}...")

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
        "generatedat": datetime.utcnow().isoformat("T") + "Z",
        "project": pname,
        "facts": []
    }
    z = zipfile.ZipFile(exportzip, "w", zipfile.ZIP_DEFLATED)
    for fact in facts:
        fid, _, date, desc, link, filehash = fact
        item = {
            "id": fid, "date": date, "description": desc,
            "evidencelink": link, "hash": filehash
        }
        manifest["facts"].append(item)
        # Embed watermark to description
        descwm = f"{desc}
---© 2025 Dwayne Anthony Brian Galloway. All Rights Reserved."
        z.writestr(f"fact_{fid}.txt", descwm)
        if link and os.path.exists(link):
            z.write(link, arcname=os.path.basename(link))
    manifestbytes = json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8")
    z.writestr("manifest.json", json.dumps(manifest, indent=2))
    z.writestr("manifest.sig", manifesthmac(manifestbytes))
    z.close()
    logaudit("exportevidencepack", getuser(), f"projectid={pid},output={exportzip}")
    print(f"OK. Exported {exportzip}")

def onboarding():
    print("
Coding Demon Protocol")
    print("© 2025", OWNER, ". All Rights Reserved.")
    print("Before you use this tool, you must acknowledge and agree to the following:")
    print("- 10% of all revenues generated via Coding Demon, its code, or derivative outputs are contractually owed to Dwayne Anthony Brian Galloway as royalty, in perpetuity.")
    print("- You accept that every output will be watermarked and cryptographically attributed.")
    print("- Use of this platform constitutes irrevocable acceptance of these terms.")
    ans = input("Type 'I AGREE' to continue: ").strip()
    if ans.lower() != 'i agree':
        print("Agreement not accepted. Exiting.")
        exit(1)

def mainmenu():
    onboarding()
    initdb()
    print("
Menu:")
    while True:
        print("""
  1. Create a new project/session
  2. List projects
  3. Add collaborator to project
  4. Add fact/evidence/issue to project
  5. List project facts
  6. Export evidence/compliance package
  0. Exit
        """)
        try:
            sel = int(getinput("Select: ", required=True))
        except ValueError:
            print("Enter a number.")
            continue
        if sel == 1:
            createproject()
        elif sel == 2:
            projects = listprojects()
            for pid, name, ts in projects:
                print(f"- {pid} {name} Created {ts}")
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
""" codingdemon_monster.py
# By order of the Coding Demon Court—here go ALL the magic, fire, and stress-proof features.

import datetime

class CodingDemonMonster:
    def __init__(self, jurisdiction="UK"):
        self.jurisdiction = jurisdiction
        self.audit_log = []
        self.user_profiles = {}
        self.bs_phrases = self.get_bs_phrases()
        self.incrim_phrases = self.get_incrim_phrases()
        self.transcripts = []
        self.incidents = []
        self.claims = []

    ### AUDIT & INCIDENT LOGGING
    def log_incident(self, description, user, profile=None):
        timestamp = datetime.datetime.now().isoformat()
        incident = {
            "time": timestamp,
            "user": user,
            "description": description,
            "profile": profile,
            "jurisdiction": self.jurisdiction
        }
        self.incidents.append(incident)
        self.audit_log.append(f"{timestamp} - INCIDENT by {user}: {description}")

    def add_audit(self, activity):
        entry = f"{datetime.datetime.now().isoformat()} - {activity}"
        self.audit_log.append(entry)

    ### BS DETECTION
    def get_bs_phrases(self):
        return {
            "going forward": "Move along, nothing to address.",
            "robust process": "Looks good on paper.",
            "industry standard": "If it breaks, blame everyone.",
            "escalated": "Can you wait two weeks?",
        }

    def detect_bs(self, text):
        flags = []
        for phrase, meaning in self.bs_phrases.items():
            if phrase in text.lower():
                flags.append((phrase, meaning))
        return flags

    ### INCRIMINATION DETECTOR
    def get_incrim_phrases(self):
        return {
            "i admit": "Warning: Self-incrimination detected.",
            "we failed": "Uh oh! Legal blunder.",
            "lost the file": "Lost evidence, very bad.",
        }

    def detect_incrimination(self, text):
        flags = []
        for phrase, meaning in self.incrim_phrases.items():
            if phrase in text.lower():
                flags.append((phrase, meaning))
        return flags

    ### TRANSCRIPTION (FAKE DEMO)
    def transcribe(self, file_stub):
        # Demo function—replace with real transcription API.
        fake_transcript = f"Transcript for {file_stub} at {datetime.datetime.now().isoformat()}"
        self.transcripts.append(fake_transcript)
        self.add_audit(f"Transcribed {file_stub}")
        return fake_transcript

    ### LEGAL CLAIMS & COMPLAINTS
    def add_claim(self, claimant, defendant, heads_of_claim, exhibits):
        claim = {
            "claimant": claimant,
            "defendant": defendant,
            "heads_of_claim": heads_of_claim,
            "exhibits": exhibits,
            "jurisdiction": self.jurisdiction,
            "filed": datetime.datetime.now().isoformat()
        }
        self.claims.append(claim)
        self.add_audit(f"Claim registered: {claimant} vs {defendant}")

    ### ACCESSIBILITY
    def add_user_profile(self, user, profile_details):
        self.user_profiles[user] = profile_details
        self.add_audit(f"Accessibility/User profile updated for {user}")

    ### JURISDICTION LOCK-IN / INTERNATIONAL MODE
    def set_jurisdiction(self, new_jurisdiction):
        self.add_audit(f"Jurisdiction change: {self.jurisdiction} -> {new_jurisdiction}")
        self.jurisdiction = new_jurisdiction

    ### PLUGINS / EXTENSIBILITY
    def add_bs_phrase(self, phrase, meaning):
        self.bs_phrases[phrase] = meaning
        self.add_audit(f"BS phrase added: {phrase}")

    ### OUTPUT/AUDIT SUMMARY
    def audit_report(self):
        return "
".join(self.audit_log)

    ### STRESS RELIEF: JOKE GENERATOR
    def demonic_joke(self):
        # Here’s some levity for the journey!
        return "Why did the legal bot refuse to take a bribe? Because it's programmed for justice with extra seasoning!"

### DEMONSTRATION

if __name__ == "__main__":
    monster = CodingDemonMonster(jurisdiction="Jamaica")
    monster.log_incident("Bank ignored escalation letter", user="clientA")
    monster.add_user_profile("clientA", {"needs": "read-aloud", "preferred_language": "patois"})
    monster.add_claim("clientA", "BigBank", ["Breach of Duty", "Data loss"], ["audio_file1", "scanned_letter.pdf"])
    print(monster.transcribe("court_audio.mp3"))
    print("BS Detector:", monster.detect_bs("Going forward, we will escalate per industry standard."))
    print("Incrimination Detector:", monster.detect_incrimination("I admit we failed to act robustly and lost the file."))
    print("Audit Trail:
", monster.audit_report())
    print("Joke:", monster.demonic_joke())
