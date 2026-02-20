import sys
import os
import subprocess
import json
import urllib.request
from datetime import datetime

# ================= Configuration =================
REPO_DIR = "/Users/ankitkumarsingh/Code/Full-SDLC-AgenticAI"
LOG_FILE = "/Users/ankitkumarsingh/Code/Full-SDLC-AgenticAI/auto_git.log"
# Provide the name of the Qwen model you have locally in Ollama
OLLAMA_MODEL = "qwen2.5-coder:7b" 
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
# =================================================

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log(f"Error running {' '.join(cmd)}: {e.stderr.strip()}")
        return None

def generate_commit_message(diff):
    if not diff.strip():
        return None
        
    prompt = (
        "You are an expert developer. Write a concise, conventional git commit message "
        "for the following diff. Only output the commit message, no backticks, no markdown, "
        "no quotes, no conversational text.\n\n"
        f"Diff:\n{diff[:3000]}" # Limit diff length to prevent context explosion
    )
    
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(data).encode("utf-8"))
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("response", "").strip()
    except Exception as e:
        log(f"LLM Generation failed (Is Ollama running?): {e}")
        return None

def do_commit():
    status = run_cmd(["git", "status", "--porcelain"])
    if not status:
        log("No changes detected. Skipping commit.")
        return
        
    log("Changes detected. Adding files...")
    run_cmd(["git", "add", "."])
    
    log("Generating LLM commit message...")
    diff = run_cmd(["git", "diff", "--cached"])
    
    commit_msg = generate_commit_message(diff) if diff else None
    
    if not commit_msg:
        commit_msg = f"chore: auto-commit backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
    log(f"Committing with message: {commit_msg}")
    run_cmd(["git", "commit", "-m", commit_msg])

def do_push():
    log("Running scheduled push...")
    run_cmd(["git", "push"])

if __name__ == "__main__":
    os.chdir(REPO_DIR)
    action = sys.argv[1] if len(sys.argv) > 1 else None
    
    if action == "commit":
        do_commit()
    elif action == "push":
        do_push()
    else:
        log("Error: Must specify 'commit' or 'push' as argument.")
