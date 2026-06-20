"""
AgentsFactory Daily Outreach Pipeline — direct execution, no LLM.
Builds queue from Google Sheet, validates emails, sends via Gmail SMTP.
Writes results to output/outreach_results_YYYY-MM-DD.json and updates DB.
"""
import json, os, re, smtplib, sqlite3, subprocess, sys, time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
# Use script-relative path so this works from any cwd or cron
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

PROJECT_ROOT = Path("C:/Users/Admin/Projects/AgentsFactory")

# Slack alerts
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from slack_alert import send_alert, format_error_alert
OUTPUT_DIR  = PROJECT_ROOT / "output"
DB_PATH     = PROJECT_ROOT / "agentsfactory_metrics.db"

SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", os.environ.get("SMTP_APP_PASSWORD", ""))

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BAD_DOMAINS  = {"example.com","test.com","mailinator.com","tempmail.com","guerrillamail.com","trashmail.com","yopmail.com","10minutemail.com","dispostable.com"}
ROLE_PREFIXES = {"admin","support","info","contact","sales","hello","enquiry","enquiries","care","press","billing","jobs","hr"}

def is_bad_email(email):
    e = email.strip().lower()
    if not EMAIL_RE.match(e): return True
    if "@" not in e: return True
    local, domain = e.split("@",1)
    if domain in BAD_DOMAINS: return True
    if local in ROLE_PREFIXES: return True
    return False

def send_one(to_email, subject, body):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return {"status": "error", "reason": "SMTP not configured"}
    last_err = None
    for attempt in range(1, 4):
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"]    = SMTP_EMAIL
            msg["To"]      = to_email
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, [to_email], msg.as_string())
            return {"status": "sent"}
        except (smtplib.SMTPException, OSError, TimeoutError) as ex:
            last_err = ex
            print(f"    ⚠️  SMTP attempt {attempt}/3 failed: {ex}")
            if attempt < 3:
                time.sleep(10)
    return {"status": "error", "reason": str(last_err)}

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS leads (email TEXT, company TEXT, outreach_status TEXT, last_outreach_at TEXT)")
    conn.commit()
    return conn

def build_queue():
    r = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "src/agents/outreach_queue_v3.py")],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=180
    )
    print(r.stdout[-500:] if r.stdout else "")
    if r.returncode != 0:
        print("Queue build stderr:", r.stderr[-500:] if r.stderr else "")
    # find queue file
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    files = sorted(OUTPUT_DIR.glob(f"outreach_queue_{today}*.json"))
    if not files:
        raise FileNotFoundError(f"No queue file for {today}")
    with open(files[-1]) as f:
        return json.load(f)

def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"=== AgentsFactory Outreach — {today} ===\n")

    try:
        conn = ensure_db()

        # Build or load queue
        try:
            queue = build_queue()
        except Exception as ex:
            print(f"Queue build failed: {ex}")
            conn.close()
            rf = OUTPUT_DIR / f"outreach_results_{today}.json"
            try:
                with open(rf, "w", encoding="utf-8") as f:
                    json.dump({"date": today, "fatal_error": str(ex)}, f, indent=2)
            except Exception:
                pass
            send_alert("C0BBP317H7G", format_error_alert("daily_outreach.py", str(ex), "Queue build failed"))
            sys.exit(1)

        leads = queue.get("actions", [])
        print(f"Queue size: {len(leads)}")

        # Exclude already-contacted
        cur = conn.cursor()
        cur.execute("SELECT LOWER(email) FROM leads WHERE outreach_status IN ('sent','bounced','skipped')")
        exclude = {r[0] for r in cur.fetchall()}

        to_send = [l for l in leads if l.get("email","").strip().lower() not in exclude]
        print(f"Already contacted: {len(exclude)}, To send: {len(to_send)}\n")

        results = []
        sent = failed = skipped = 0

        for lead in to_send:
            email = lead.get("email","").strip()
            company = lead.get("company","Unknown")

            if is_bad_email(email):
                print(f"  SKIP (bad): {email}")
                skipped += 1
                cur.execute("INSERT OR IGNORE INTO leads (email,company,outreach_status) VALUES (?,?,?)", (email, company, "skipped"))
                continue

            body = lead.get("lead_email_body", f"Hi {company},\n\nPhanindra here from AgentsFactory. We help agencies automate outreach, content, and reporting.\n\n—Phani")
            res = send_one(email, f"Quick question for {company}", body)

            status = res["status"]
            print(f"  {status.upper()}: {company} ({email})" + (f" — {res.get('reason','')}" if status=="error" else ""))

            if status == "sent":
                sent += 1
            else:
                failed += 1

            cur.execute(
                "INSERT OR REPLACE INTO leads (email,company,outreach_status,last_outreach_at) VALUES (?,?,?,datetime('now'))",
                (email, company, status)
            )
            results.append({"company": company, "email": email, "status": status})

        conn.commit()
        conn.close()

        # Save results
        rf = OUTPUT_DIR / f"outreach_results_{today}.json"
        summary = {"date": today, "total": len(leads), "sent": sent, "failed": failed, "skipped": skipped, "results": results}
        with open(rf, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n=== DONE: sent={sent} failed={failed} skipped={skipped} ===")
        print(f"Results: {rf}")

        # Slack alert
        status_emoji = "✅" if failed == 0 else "⚠️"
        alert_text = (
            f"{status_emoji} *Daily Outreach — {today}*\n"
            f"Sent: {sent} | Failed: {failed} | Skipped: {skipped}\n"
            f"Total in queue: {len(leads)}"
        )
        send_alert("C0BBP317H7G", alert_text)

    except Exception as e:
        rf = OUTPUT_DIR / f"outreach_results_{today}.json"
        try:
            with open(rf, "w", encoding="utf-8") as f:
                json.dump({"date": today, "fatal_error": str(e)}, f, indent=2)
        except Exception:
            pass
        send_alert("C0BBP317H7G", format_error_alert("daily_outreach.py", str(e), f"Date: {today}"))
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
