import os
import re
import subprocess
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)

load_dotenv()

TOKEN         = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER  = int(os.getenv("ALLOWED_USER_ID"))
REPO_PATH     = os.getenv("REPO_PATH")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "codellama")
OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434")

# ── helpers ───────────────────────────────────────────────────────────────────

def run_git(command: list) -> str:
    try:
        result = subprocess.run(
            command, cwd=REPO_PATH,
            capture_output=True, text=True
        )
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)

def auth(update: Update) -> bool:
    return update.effective_user.id == ALLOWED_USER

def get_repo_structure() -> str:
    try:
        result = subprocess.run(
            ["find", ".", 
             "-not", "-path", "./.git/*",
             "-not", "-path", "./node_modules/*",
             "-not", "-path", "./__pycache__/*",
             "-not", "-path", "./.venv/*",
             "-type", "f"],
            cwd=REPO_PATH, capture_output=True, text=True
        )
        return result.stdout[:3000]
    except:
        return "Unable to read repo structure"

def slugify(text: str) -> str:
    words = re.sub(r'[^a-z0-9 ]', '', text.lower()).split()[:6]
    return "-".join(words)

# ── Ollama API call ───────────────────────────────────────────────────────────

def ask_ollama(prompt: str, system: str = "") -> str:
    """
    Call local Ollama model and return the response text.
    Uses /api/generate endpoint (works with all Ollama versions).
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": 0.2,      # low temp = more deterministic code
            "num_predict": 8192,     # max tokens to generate
        }
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=300             # local models can be slow
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        return "ERROR: Ollama is not running. Start it with: ollama serve"
    except Exception as e:
        return f"ERROR: {str(e)}"

# ── parse Ollama response ─────────────────────────────────────────────────────

def parse_ollama_response(raw: str) -> dict:
    """
    Parse the structured response from Ollama into:
    { branch_name, files: [{path, content}], summary }
    """
    result = {"branch_name": "", "files": [], "summary": ""}

    # Extract BRANCH_NAME
    for line in raw.splitlines():
        if line.strip().startswith("BRANCH_NAME:"):
            result["branch_name"] = line.replace("BRANCH_NAME:", "").strip()
            break

    # Extract FILE blocks  →  FILE: path\n```\ncontent\n```
    file_blocks = re.findall(
        r'FILE:\s*(.+?)\n```(?:\w*\n)?(.*?)```',
        raw, re.DOTALL
    )
    for filepath, content in file_blocks:
        result["files"].append({
            "path": filepath.strip(),
            "content": content.strip()
        })

    # Extract SUMMARY
    if "SUMMARY:" in raw:
        result["summary"] = raw.split("SUMMARY:")[-1].strip()[:1000]

    return result

# ── feature implementation core ───────────────────────────────────────────────

def build_prompt(feature_description: str) -> tuple[str, str]:
    repo_structure = get_repo_structure()

    system = """You are an expert software engineer. You generate complete working code based on feature descriptions.

You MUST respond in EXACTLY this format — no extra explanation before or after:

BRANCH_NAME: feature/<short-kebab-case-name>

FILE: <relative/path/to/file.ext>
```
<complete file content>
```

FILE: <relative/path/to/another/file.ext>
```
<complete file content>
```

SUMMARY: <short paragraph of what was implemented>

Rules:
- Always include BRANCH_NAME:, at least one FILE:, and SUMMARY:
- Write COMPLETE file contents, never partial snippets
- If editing existing files, rewrite the whole file
- Follow the code style of the existing project
- Create any needed config, helper, or test files too"""

    prompt = f"""Repository file structure:
{repo_structure}

Feature request:
{feature_description}

Generate the full implementation now following the exact format."""

    return system, prompt

async def implement_feature(update: Update, description: str):
    # Step 1 — notify user
    await update.message.reply_text(
        f"🤖 Asking `{OLLAMA_MODEL}` to implement your feature...\n"
        f"_(This may take 30–120 seconds depending on your hardware)_",
        parse_mode="Markdown"
    )

    # Step 2 — call Ollama
    system, prompt = build_prompt(description)
    raw = ask_ollama(prompt, system)

    if raw.startswith("ERROR:"):
        await update.message.reply_text(f"❌ {raw}")
        return

    # Step 3 — parse response
    impl = parse_ollama_response(raw)

    if not impl["files"]:
        await update.message.reply_text(
            "❌ The model didn't return files in the expected format.\n"
            "Try rephrasing your feature or use a better model like `deepseek-coder`.\n\n"
            f"Raw response:\n```\n{raw[:1000]}\n```",
            parse_mode="Markdown"
        )
        return

    # Step 4 — create git branch
    branch = impl["branch_name"] or f"feature/{slugify(description)}"
    await update.message.reply_text(f"🌿 Creating branch: `{branch}`", parse_mode="Markdown")

    # Go to default branch and pull latest
    default_branch = run_git(["git", "symbolic-ref", "--short", "HEAD"]).strip()
    for base in ["main", "master", default_branch]:
        out = run_git(["git", "checkout", base])
        if "error" not in out.lower() and "fatal" not in out.lower():
            break
    run_git(["git", "pull"])

    # Create new branch
    out = run_git(["git", "checkout", "-b", branch])
    if "fatal" in out.lower():
        await update.message.reply_text(f"❌ Git error:\n```\n{out}\n```", parse_mode="Markdown")
        return

    # Step 5 — write files to disk
    written = []
    errors = []
    for file_info in impl["files"]:
        rel_path = file_info["path"]
        content  = file_info["content"]
        full_path = os.path.join(REPO_PATH, rel_path)

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            written.append(rel_path)
        except Exception as e:
            errors.append(f"{rel_path}: {e}")

    if errors:
        await update.message.reply_text(
            "⚠️ Some files had errors:\n" + "\n".join(errors)
        )

    await update.message.reply_text(
        "📝 Files written:\n" + "\n".join(f"  • `{f}`" for f in written),
        parse_mode="Markdown"
    )

    # Step 6 — git add + commit + push
    run_git(["git", "add", "-A"])
    commit_msg = f"feat: {description[:72]}"
    commit_out = run_git(["git", "commit", "-m", commit_msg])
    push_out   = run_git(["git", "push", "-u", "origin", branch])

    push_status = "✅ Pushed!" if "branch" in push_out.lower() or "upstream" in push_out.lower() else f"⚠️ Push output:\n```\n{push_out[:300]}\n```"

    await update.message.reply_text(
        f"🎉 *Feature implemented!*\n\n"
        f"🌿 Branch: `{branch}`\n\n"
        f"📋 *Summary:*\n{impl['summary']}\n\n"
        f"📁 Files: {', '.join(f'`{f}`' for f in written)}\n\n"
        f"{push_status}\n\n"
        f"👉 Go to GitHub and open a Pull Request!",
        parse_mode="Markdown"
    )

# ── standard git commands ─────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    await update.message.reply_text(
        f"🤖 *ClawBot* — Git + AI assistant\n"
        f"Model: `{OLLAMA_MODEL}`\n\n"
        "*Git Commands:*\n"
        "/status — git status\n"
        "/pull — git pull\n"
        "/log — last 10 commits\n"
        "/branch — list branches\n"
        "/checkout `<branch>` — switch branch\n"
        "/commit `<msg>` — stage all & commit\n"
        "/push — push to remote\n"
        "/run `<shell cmd>` — run any shell command\n\n"
        "*AI Feature:*\n"
        "Just *send any message* describing a feature and the bot will:\n"
        "  1. Ask the local AI to generate code\n"
        "  2. Create a new git branch\n"
        "  3. Write the files\n"
        "  4. Commit & push\n",
        parse_mode="Markdown"
    )

async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    out = run_git(["git", "status"])
    await update.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def pull(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    out = run_git(["git", "pull"])
    await update.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def log(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    out = run_git(["git", "log", "--oneline", "-10"])
    await update.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def branch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    out = run_git(["git", "branch", "-a"])
    await update.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def checkout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    if not ctx.args:
        await update.message.reply_text("Usage: /checkout <branch>")
        return
    out = run_git(["git", "checkout", ctx.args[0]])
    await update.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def commit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    if not ctx.args:
        await update.message.reply_text("Usage: /commit <message>")
        return
    run_git(["git", "add", "-A"])
    out = run_git(["git", "commit", "-m", " ".join(ctx.args)])
    await update.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def push(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    out = run_git(["git", "push"])
    await update.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def run_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    if not ctx.args:
        await update.message.reply_text("Usage: /run <command>")
        return
    try:
        result = subprocess.run(
            " ".join(ctx.args), shell=True,
            cwd=REPO_PATH, capture_output=True,
            text=True, timeout=30
        )
        out = result.stdout or result.stderr or "No output"
    except subprocess.TimeoutExpired:
        out = "Command timed out after 30s"
    except Exception as e:
        out = str(e)
    await update.message.reply_text(f"```\n{out[:3500]}\n```", parse_mode="Markdown")

# ── message handler: plain text = feature request ─────────────────────────────

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    description = update.message.text.strip()
    if len(description) < 10:
        await update.message.reply_text("Please describe your feature in more detail.")
        return
    await implement_feature(update, description)

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    # Verify Ollama is reachable before starting
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"✅ Ollama connected. Available models: {models}")
        if OLLAMA_MODEL not in " ".join(models):
            print(f"⚠️  Warning: '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}")
    except:
        print("⚠️  Warning: Ollama not reachable at", OLLAMA_URL)
        print("   Start it with: ollama serve")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("status",   status))
    app.add_handler(CommandHandler("pull",     pull))
    app.add_handler(CommandHandler("log",      log))
    app.add_handler(CommandHandler("branch",   branch))
    app.add_handler(CommandHandler("checkout", checkout))
    app.add_handler(CommandHandler("commit",   commit))
    app.add_handler(CommandHandler("push",     push))
    app.add_handler(CommandHandler("run",      run_cmd))

    # Any plain text message → AI feature implementation
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 ClawBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()