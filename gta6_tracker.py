"""
GTA 6 Tracker - Fnac.com

Watches the Fnac search page and sends you an email as soon as the game
Grand Theft Auto VI shows up in the search results.

Fnac.com is protected by an anti-bot system (DataDome), so we drive a real
Chrome browser (via Playwright) in VISIBLE mode, with a persistent profile that
keeps the DataDome cookie between runs.

Run:
    py gta6_tracker.py                # interactive menu
    py gta6_tracker.py --watch        # continuous monitoring (automation)
    py gta6_tracker.py --once         # single check (for testing)
    py gta6_tracker.py --test-email   # send a test email and exit

Configuration (email credentials, interval...) lives in the .env file
(see .env.example). The setup wizard creates it for you on first run.
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import smtplib
import unicodedata
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlencode

from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
except ImportError:
    # python-dotenv is optional: real system environment variables also work.
    # We define a neutral fallback so the name always exists.
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False

load_dotenv()


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "state.json"
ENV_FILE = BASE_DIR / ".env"
# Persistent browser profile (keeps cookies, including DataDome's).
BROWSER_PROFILE_DIR = BASE_DIR / "browser_profile"

# Terms searched on Fnac. Several are tried to maximize the chances.
SEARCH_TERMS = ["GTA 6", "Grand Theft Auto VI", "GTA VI", "Grand Theft Auto 6"]


# Settings read dynamically so values entered through the setup wizard at
# launch are taken into account immediately.
def get_interval_minutes() -> int:
    try:
        return int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))
    except ValueError:
        return 15


def get_headless() -> bool:
    # Defaults to VISIBLE (False) because DataDome blocks headless mode.
    return os.getenv("HEADLESS", "false").strip().lower() in ("1", "true", "yes")


def get_page_wait_ms() -> int:
    try:
        return int(os.getenv("PAGE_WAIT_MS", "5000"))
    except ValueError:
        return 5000


# Patterns that REALLY identify the GTA 6 game (and not GTA 5, Vice City...).
# Word boundaries (\b) avoid matching "GTA Vice City" which contains "gta vi".
TITLE_PATTERNS = [
    re.compile(r"grand theft auto vi\b"),
    re.compile(r"grand theft auto 6\b"),
    re.compile(r"\bgta vi\b"),
    re.compile(r"\bgta 6\b"),
]

# The product must be a PS5 version (game alone or a bundle with the game).
PS5_PATTERN = re.compile(r"\bps5\b|play ?station ?5")

# Words that reveal a DERIVATIVE product (book, guide, merch...) to exclude.
# NOTE: these are intentionally in FRENCH because they match the actual text
# of fnac.com (a French website). Do not translate them, or filtering breaks.
DERIVATIVE_PATTERN = re.compile(
    r"\b("
    r"guide|soluce|livre|artbook|art book|comics?|bande dessinee|manga|"
    r"magazine|mook|roman|"
    r"mug|tasse|verre|t ?shirt|sweat|pull|casquette|vetement|chaussette|"
    r"figurine|statuette|poster|affiche|porte ?cles?|stylo|carnet|cahier|"
    r"calendrier|puzzle|peluche|sticker|autocollant|badge|pin ?s|lampe|"
    r"tapis|coque|etui|goodies?|cle usb|drapeau|plaque|sac"
    r")\b"
)

SEARCH_URL = "https://www.fnac.com/SearchResult/ResultList.aspx"
HOME_URL = "https://www.fnac.com/"


# --------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------
def log(message: str) -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}", flush=True)


def normalize(text: str) -> str:
    """Lowercase + strip accents + normalize whitespace."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().lower()


def title_matches_gta6(title: str) -> bool:
    norm = normalize(title)
    return any(p.search(norm) for p in TITLE_PATTERNS)


def build_search_url(term: str) -> str:
    return SEARCH_URL + "?" + urlencode({"Search": term, "sft": "1", "sa": "0"})


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log("state.json unreadable, resetting.")
    return {"alerted_keys": []}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                          encoding="utf-8")


# --------------------------------------------------------------------------
# Page fetching via Chrome browser (Playwright)
# --------------------------------------------------------------------------
def _launch_context(p):
    """Open a persistent browser context (real Chrome if available)."""
    launch_kwargs = dict(
        user_data_dir=str(BROWSER_PROFILE_DIR),
        headless=get_headless(),
        locale="fr-FR",
        viewport={"width": 1366, "height": 768},
        args=["--disable-blink-features=AutomationControlled"],
    )
    # Try to use the real installed Chrome (better fingerprint), otherwise
    # fall back to the Chromium bundled with Playwright.
    # noinspection PyBroadException
    try:
        ctx = p.chromium.launch_persistent_context(channel="chrome", **launch_kwargs)
    except Exception:
        log("  (Chrome not found, using Playwright's bundled Chromium.)")
        ctx = p.chromium.launch_persistent_context(**launch_kwargs)
    ctx.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
    )
    return ctx


def _warmup(page) -> None:
    """Visit the homepage to obtain/refresh the DataDome cookie."""
    # noinspection PyBroadException
    try:
        page.goto(HOME_URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(get_page_wait_ms())
    except Exception as exc:
        log(f"  [!] Homepage visit failed: {exc}")


def _fetch_terms(page, terms: list[str]) -> dict[str, str | None]:
    """Fetch the HTML of each search using an already-open page."""
    page_wait = get_page_wait_ms()
    results: dict[str, str | None] = {}
    for term in terms:
        log(f"  Searching: '{term}'...")
        # noinspection PyBroadException
        try:
            resp = page.goto(build_search_url(term),
                             wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(page_wait)
            status = resp.status if resp else None
            html = page.content()
            if status and status != 200:
                log(f"  [!] HTTP {status} for '{term}' (possible block).")
            results[term] = html
        except Exception as exc:
            log(f"  [!] Failed to load '{term}': {exc}")
            results[term] = None
        time.sleep(1)
    return results


def fetch_pages(terms: list[str]) -> dict[str, str | None]:
    """One-shot mode: open Chrome, fetch the HTML, then close.

    Returns {term: html} (html=None on failure).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("[!] Playwright is not installed. Run Installer.bat first, or:")
        log("    py -m pip install playwright")
        log("    py -m playwright install chromium")
        return {term: None for term in terms}

    with sync_playwright() as p:
        ctx = _launch_context(p)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            _warmup(page)
            return _fetch_terms(page, terms)
        finally:
            # noinspection PyBroadException
            try:
                ctx.close()
            except Exception:
                pass


def _container_text(link) -> str:
    """Text of the product card around the link (title + format + platform).

    We climb a few parents up to the product "card" to get the context (the
    PS5 platform or a "Livre" label is sometimes next to the title, not inside
    the link itself).
    """
    node = link
    for _ in range(4):
        parent = getattr(node, "parent", None)
        if parent is None:
            break
        node = parent
        classes = " ".join(node.get("class", []) or []).lower()
        if node.name in ("li", "article") or "article-item" in classes or "product" in classes:
            break
    return normalize(node.get_text(" ", strip=True))


def is_relevant_ps5_game(context: str) -> bool:
    """True only for the GTA 6 PS5 game (or a bundle), not a derivative."""
    if not PS5_PATTERN.search(context):
        return False                       # not a PS5 version
    if DERIVATIVE_PATTERN.search(context):
        return False                       # book / guide / merch...
    return True


def parse_products(html: str | None) -> list[dict]:
    """Extract only the products that are the GTA 6 PS5 game (or a bundle)."""
    if not html:
        return []

    low = html.lower()
    if "captcha" in low and "datadome" in low:
        log("  [!] DataDome captcha page detected. If it keeps happening, run "
            "the script once by hand and solve the captcha in the Chrome "
            "window (the cookie will be remembered).")

    soup = BeautifulSoup(html, "html.parser")
    found: dict[str, dict] = {}
    raw_matches = 0

    for link in soup.find_all("a"):
        text = link.get_text(" ", strip=True)
        if not text or not title_matches_gta6(text):
            continue
        raw_matches += 1
        context = _container_text(link)
        if not is_relevant_ps5_game(context):
            continue
        href = link.get("href", "")
        if href.startswith("/"):
            href = "https://www.fnac.com" + href
        key = href or normalize(text)
        found[key] = {"title": text, "url": href}

    if raw_matches and not found:
        log(f"  ({raw_matches} GTA6 result(s) ignored: no PS5 game, "
            f"only books/derivatives.)")

    return list(found.values())


def check_all_terms(page=None) -> list[dict]:
    """Fetch and filter the products. If 'page' is given, reuse the already-open
    browser (continuous monitoring mode)."""
    if page is not None:
        pages = _fetch_terms(page, SEARCH_TERMS)
    else:
        pages = fetch_pages(SEARCH_TERMS)
    merged: dict[str, dict] = {}
    for html in pages.values():
        for product in parse_products(html):
            key = product["url"] or normalize(product["title"])
            merged[key] = product
    return list(merged.values())


# --------------------------------------------------------------------------
# Email sending
# --------------------------------------------------------------------------
def send_email(subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "465"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    email_from = os.getenv("EMAIL_FROM", user)
    email_to = os.getenv("EMAIL_TO", user)

    if not user or not password:
        log("  [!] SMTP_USER / SMTP_PASSWORD missing in .env, "
            "cannot send the email.")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = email_to
    msg.set_content(body)

    # noinspection PyBroadException
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=30) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)
        log(f"  Email sent to {email_to}.")
        return True
    except Exception as exc:
        log(f"  [!] Failed to send email: {exc}")
        return False


# --------------------------------------------------------------------------
# Interactive setup wizard
# --------------------------------------------------------------------------
def email_config_complete() -> bool:
    return bool(os.getenv("SMTP_USER")) and bool(os.getenv("SMTP_PASSWORD"))


def _prompt(label: str, default: str = "", secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    if secret:
        import getpass
        value = getpass.getpass(f"{label}{suffix} : ").strip()
    else:
        value = input(f"{label}{suffix} : ").strip()
    return value or default


def save_env(values: dict[str, str]) -> None:
    lines = ["# Generated by the wizard (py gta6_tracker.py --config)\n",
             "# Do not share: this file contains your password.\n"]
    for key, val in values.items():
        lines.append(f"{key}={val}\n")
    ENV_FILE.write_text("".join(lines), encoding="utf-8")


def interactive_setup() -> None:
    print("\n========================================")
    print("   GTA 6 Tracker - Setup")
    print("========================================")
    print("(Press Enter to keep the value shown in [brackets].)\n")

    host = _prompt("SMTP server", os.getenv("SMTP_HOST", "smtp.gmail.com"))
    port = _prompt("SMTP port (465=SSL, 587=STARTTLS)", os.getenv("SMTP_PORT", "465"))

    user = _prompt("Your email address (sender)", os.getenv("SMTP_USER", ""))
    while not user:
        print("  -> The email address is required.")
        user = _prompt("Your email address (sender)", "")

    print("\n  APP PASSWORD (input is hidden).")
    print("  Gmail: create one at https://myaccount.google.com/apppasswords\n")
    password = _prompt("App password", os.getenv("SMTP_PASSWORD", ""), secret=True)
    while not password:
        print("  -> The password is required.")
        password = _prompt("App password", "", secret=True)

    email_to = _prompt("Address that receives the alert", os.getenv("EMAIL_TO", "") or user)
    interval = _prompt("Check frequency (minutes)",
                       os.getenv("CHECK_INTERVAL_MINUTES", "15"))

    values = {
        "SMTP_HOST": host,
        "SMTP_PORT": port,
        "SMTP_USER": user,
        "SMTP_PASSWORD": password,
        "EMAIL_FROM": user,
        "EMAIL_TO": email_to or user,
        "CHECK_INTERVAL_MINUTES": interval,
        "HEADLESS": os.getenv("HEADLESS", "false"),
        "PAGE_WAIT_MS": os.getenv("PAGE_WAIT_MS", "5000"),
    }
    save_env(values)
    # Apply immediately for the current session.
    for key, val in values.items():
        os.environ[key] = val

    print(f"\nConfiguration saved to {ENV_FILE}")

    answer = _prompt("Send a test email now? (y/n)", "y")
    if answer.lower().startswith("y"):
        send_email("[TEST] GTA 6 Tracker",
                   "Test email: your configuration works!")
    print()


# --------------------------------------------------------------------------
# Core logic
# --------------------------------------------------------------------------
def run_check(page=None) -> None:
    state = load_state()
    already_alerted = set(state.get("alerted_keys", []))

    products = check_all_terms(page=page)
    if not products:
        log("No GTA 6 PS5 game found for now.")
        return

    new_products = []
    for product in products:
        key = product["url"] or normalize(product["title"])
        if key not in already_alerted:
            new_products.append(product)
            already_alerted.add(key)

    log(f"GTA 6 PS5 GAME DETECTED: {len(products)} product(s), "
        f"including {len(new_products)} new.")

    if new_products:
        lines = [f"- {p['title']}\n  {p['url']}" for p in new_products]
        body = (
            "Good news: the GTA 6 (PS5) game just appeared on Fnac!\n\n"
            + "\n\n".join(lines)
            + "\n\nSearch: https://www.fnac.com/SearchResult/ResultList.aspx?Search=GTA+6"
        )
        if send_email("[ALERT] GTA 6 (PS5) available on Fnac!", body):
            state["alerted_keys"] = sorted(already_alerted)
            save_state(state)
    else:
        log("  (already reported earlier, no new email.)")


def _interruptible_wait(page, total_seconds: int) -> bool:
    """Wait while pumping the Playwright event loop.

    Returns False if the window/browser was closed during the wait, which lets
    monitoring stop immediately.
    """
    remaining_ms = total_seconds * 1000
    step_ms = 1000
    while remaining_ms > 0:
        if page.is_closed():
            return False
        # noinspection PyBroadException
        try:
            page.wait_for_timeout(min(step_ms, remaining_ms))
        except Exception:
            return False  # page / context closed
        remaining_ms -= step_ms
    return not page.is_closed()


def run_loop() -> None:
    """Continuous monitoring: open Chrome ONCE and keep it open.

    If you close the browser window, the script stops.
    Ctrl+C works too.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("[!] Playwright is not installed. Run Installer.bat first.")
        return

    interval = get_interval_minutes()
    log(f"Starting monitoring (checking every {interval} min).")
    log("Keep the Chrome window open. Closing it (or Ctrl+C) stops the script.")

    with sync_playwright() as p:
        ctx = _launch_context(p)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        _warmup(page)

        while not page.is_closed():
            # noinspection PyBroadException
            try:
                run_check(page=page)
            except Exception as exc:
                if page.is_closed() or "closed" in str(exc).lower():
                    break
                log(f"[!] Unexpected error: {exc}")

            interval = get_interval_minutes()
            log(f"Next check in {interval} min "
                "(close the Chrome window to stop).")
            if not _interruptible_wait(page, interval * 60):
                break

        log("Browser closed: monitoring stopped.")
        # noinspection PyBroadException
        try:
            ctx.close()
        except Exception:
            pass


def send_test_email() -> bool:
    log("Sending a test email...")
    return send_email(
        "[TEST] GTA 6 Tracker",
        "This is a test email from GTA 6 Tracker. Your email config works!",
    )


# --------------------------------------------------------------------------
# Interactive menu
# --------------------------------------------------------------------------
def show_menu() -> None:
    while True:
        configured = "configured" if email_config_complete() else "NOT configured"
        print("\n==========================================")
        print("            GTA 6 TRACKER - FNAC")
        print("==========================================")
        print(f"  Email: {configured}")
        if email_config_complete():
            print(f"  Alert to  : {os.getenv('EMAIL_TO', os.getenv('SMTP_USER',''))}")
            print(f"  Frequency : {get_interval_minutes()} min")
        print("------------------------------------------")
        print("  1) Start monitoring")
        print("  2) Check once (test)")
        print("  3) Configure / edit settings")
        print("  4) Send a test email")
        print("  5) Quit")
        print("==========================================")

        choice = input("Your choice [1-5]: ").strip()

        if choice == "1":
            if not email_config_complete():
                print("\n-> Configure the email first (option 3).")
                interactive_setup()
            try:
                run_loop()
            except KeyboardInterrupt:
                print("\nMonitoring interrupted, back to the menu.")
        elif choice == "2":
            if not email_config_complete():
                interactive_setup()
            run_check()
        elif choice == "3":
            interactive_setup()
        elif choice == "4":
            if not email_config_complete():
                interactive_setup()
            send_test_email()
        elif choice in ("5", "q", "Q"):
            print("Goodbye!")
            return
        else:
            print("Invalid choice, enter a number from 1 to 5.")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
HELP_TEXT = """\
Usage: py gta6_tracker.py [option]

No option        : open the interactive menu.
  --watch        : start continuous monitoring directly (automation).
  --once         : run a single check then exit.
  --config       : (re)run the setup wizard.
  --test-email   : send a test email then exit.
  --help, -h     : show this help.
"""


def main() -> None:
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(HELP_TEXT)
        return

    if "--config" in args:
        interactive_setup()
        return

    if "--test-email" in args:
        if not email_config_complete():
            interactive_setup()
        sys.exit(0 if send_test_email() else 1)

    if "--once" in args:
        if not email_config_complete():
            interactive_setup()
        log("Single check.")
        run_check()
        return

    if "--watch" in args:
        if not email_config_complete():
            interactive_setup()
        run_loop()
        return

    # No option: interactive menu.
    try:
        show_menu()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
