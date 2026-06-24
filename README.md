# 🎮 GTA 6 Tracker — Fnac.com

Get an **automatic email alert** the moment **GTA 6** (*Grand Theft Auto VI*)
shows up in the search results of **Fnac.com** (the French retailer).

The script checks Fnac every 15 minutes (configurable) and emails you as soon
as the game is spotted. No more refreshing the page yourself!

```
==========================================
            GTA 6 TRACKER - FNAC
==========================================
  Email: configured
  Alert to  : you@gmail.com
  Frequency : 15 min
------------------------------------------
  1) Start monitoring
  2) Check once (test)
  3) Configure / edit settings
  4) Send a test email
  5) Quit
==========================================
```

---

## ✨ Features

- 🔔 **Email alert** as soon as the game appears in Fnac search
- 🎯 **Smart filtering**: alerts **only** for the **GTA 6 PS5 game** (or a
  bundle that includes the game) — books, guides and merch are ignored
- 🧭 **Interactive menu**: drive everything without knowing any commands
- 🪄 **Setup wizard**: it asks you the questions, nothing to edit by hand
- 🛡️ **Bypasses the DataDome anti-bot** by driving a real Chrome browser
- 🪟 **Persistent Chrome window**: stays open during monitoring; closing it
  stops the script
- 🚫 **No spam**: one alert per product (remembered)
- ⏰ **Automatable** at Windows startup

---

## 📥 Download

From the [**Releases**](../../releases) page, pick one:

- **`GTA6-Tracker-Setup.exe`** — recommended for most people. A real Windows
  installer: no Python needed, creates shortcuts and a proper entry in
  *Add/Remove Programs*. **Requires Google Chrome.**
- **`GTA6-Tracker.zip`** — for users who prefer the Python route (run
  `Installer.bat` / `Start.bat`). Needs Python installed.

> ℹ️ The installer is **not code-signed**, so Windows SmartScreen may show an
> "unknown publisher" warning — click *More info → Run anyway*. Your antivirus
> may also flag it (a common false positive for this kind of tool).

---

## 📦 Requirements

| Software | Detail |
|---|---|
| **Windows** | The project targets Windows |
| **Google Chrome** | Required for the installer (.exe); recommended for the zip too |
| **Python 3.10+** | Only for the **zip** route — install from [python.org](https://www.python.org/downloads/) and **tick "Add python.exe to PATH"** |
| **An email account** | Gmail (or another provider) to receive the alerts |

---

## 🚀 Installation (2 steps)

1. **Double-click `Installer.bat`**
   → creates the Python environment and installs everything automatically.
   *(Only needed once.)*

2. **Double-click `Start.bat`**
   → opens the tracker menu.

> 💡 First time? The script detects there is no configuration yet and launches
> the setup wizard directly (see below).

---

## ⚙️ Email configuration (wizard)

On first launch (or via menu option **3**), the wizard asks the questions one
by one:

```
SMTP server [smtp.gmail.com] :
SMTP port (465=SSL, 587=STARTTLS) [465] :
Your email address (sender) :
App password :          (input hidden)
Address that receives the alert [...] :
Check frequency (minutes) [15] :
```

👉 Just press **Enter** to accept the value shown in [brackets].

### 🔑 Get a Gmail "App password"

Gmail refuses your normal password in scripts. You need an app password (free):

1. Enable **2-Step Verification** on your Google account.
2. Go to **https://myaccount.google.com/apppasswords**
3. Create a password (16 characters) and enter it when the wizard asks.

> **Another provider?** The wizard also asks for the SMTP server/port
> (`465` = SSL, `587` = STARTTLS).

---

## ▶️ Usage (via the menu)

Run `Start.bat`, then choose:

| Option | Effect |
|---|---|
| **1** | Start continuous monitoring (close the Chrome window to stop) |
| **2** | Run a single check — handy for testing |
| **3** | (Re)configure email and settings |
| **4** | Send a test email to verify the config |
| **5** | Quit |

### ⚠️ On the very first real check
A **Chrome window opens** (this is normal and required to bypass the anti-bot).
If a **captcha / DataDome** page appears, **solve it once by hand** in that
window. The cookie is saved in `browser_profile/`, so later checks are
automatic.

### 🪟 During monitoring (option 1)
- The **Chrome window stays open** between checks (it is no longer reopened
  every cycle).
- **To stop**: simply close the Chrome window → the script stops.
  *(Ctrl+C in the console works too.)*

### 🎯 What triggers (or not) the alert
You get an email **only** if the result is:
- ✅ the **Grand Theft Auto VI game on PS5**, or
- ✅ a **bundle/pack that includes the PS5 game** (e.g. *PS5 Console + GTA VI*).

**Ignored**: books, game guides, novels, mugs, figurines, posters and other
merch, as well as non-PS5 versions (Xbox, PC) and other GTA titles.

---

## 🤖 Automate at Windows startup

To start monitoring on its own when you log in, use the **Windows Task
Scheduler**:

1. Open **Task Scheduler** → *Create Task*.
2. **General** tab: tick **"Run only when user is logged on"**
   *(required so the Chrome window can be shown).*
3. **Triggers** tab: *At log on*.
4. **Actions** tab: *Start a program*
   - **Program**: `<path>\GTA6-Tracker\.venv\Scripts\python.exe`
   - **Arguments**: `gta6_tracker.py --watch`
   - **Start in**: `<path>\GTA6-Tracker`

> Replace `<path>` with the real folder location on your machine.

---

## ⌨️ Command line options (advanced)

| Command | Effect |
|---|---|
| `gta6_tracker.py` | Open the interactive menu |
| `gta6_tracker.py --watch` | Continuous monitoring (for automation) |
| `gta6_tracker.py --once` | Single check then exit |
| `gta6_tracker.py --config` | Re-run the setup wizard |
| `gta6_tracker.py --test-email` | Send a test email |
| `gta6_tracker.py --help` | Show help |

---

## 🔧 Settings (`.env`)

These are created by the wizard, but you can edit them by hand:

| Variable | Purpose |
|---|---|
| `SMTP_HOST` / `SMTP_PORT` | Outgoing mail server (Gmail by default) |
| `SMTP_USER` / `SMTP_PASSWORD` | Your email + app password |
| `EMAIL_TO` | Address that receives the alert |
| `CHECK_INTERVAL_MINUTES` | Check frequency (default 15) |
| `HEADLESS` | `false` = visible Chrome (recommended) / `true` = hidden (often blocked) |
| `PAGE_WAIT_MS` | Wait time per page (default 5000 ms) |

---

## 🆘 Troubleshooting

| Problem | Fix |
|---|---|
| `Python not found` | Install Python and tick "Add to PATH", then re-run `Installer.bat` |
| Lots of `HTTP 403` / captchas | Run in visible mode and solve the captcha once (cookie saved) |
| No email received | Test with option **4**; make sure you used an *app password* |
| Still blocked by Fnac | Keep the interval at ≥ 15 min; as a last resort a paid anti-bot service is possible |

---

## 🗑️ Uninstall

**Installed with the `.exe`?** Uninstall it like any program: *Settings →
Apps → GTA 6 Tracker → Uninstall* (or the Start Menu "Uninstall" shortcut).
Your data in `%APPDATA%\GTA6-Tracker` can be deleted manually afterwards.

**Used the `.zip`?** Double-click **`Uninstaller.bat`**. It removes the locally
installed components (`.venv`, `browser_profile/`, `state.json`, `__pycache__`,
the build zip) after a confirmation, and asks separately before deleting your
`.env` (email/password).

Two things neither method deletes automatically:
- the shared Chromium downloaded by Playwright, in `%LOCALAPPDATA%\ms-playwright`;
- any Windows scheduled task you created — remove it from Task Scheduler.

---

## 🛠️ For developers

Build the distributable zip locally:

```powershell
py build_zip.py     # creates GTA6-Tracker.zip
```

Build the Windows installer locally (needs [Inno Setup](https://jrsoftware.org/isdl.php)):

```powershell
py -m pip install pyinstaller
pyinstaller --noconfirm GTA6-Tracker.spec
ISCC.exe /DMyAppVersion=1.1.0 installer.iss   # creates installer_output\GTA6-Tracker-Setup.exe
```

Releases are built automatically by GitHub Actions. **Pushing a tag** like
`v1.1.0` triggers both workflows:

- [`release.yml`](.github/workflows/release.yml) → attaches `GTA6-Tracker.zip`
- [`installer.yml`](.github/workflows/installer.yml) → attaches
  `GTA6-Tracker-Setup.exe`

Both also run on demand from the **Actions** tab (uploading build artifacts).

```bash
git tag v1.1.0
git push origin v1.1.0   # triggers the release builds
```

---

## 📁 Project contents

| File | Purpose |
|---|---|
| `Installer.bat` | One-click installation |
| `Start.bat` | One-click launch |
| `Uninstaller.bat` | One-click uninstall |
| `gta6_tracker.py` | The main script |
| `build_zip.py` | Builds the distributable zip |
| `GTA6-Tracker.spec` | PyInstaller build spec (the `.exe`) |
| `installer.iss` | Inno Setup script (the `Setup.exe`) |
| `.env.example` | Configuration template |
| `requirements.txt` | Python dependencies |
| `.github/workflows/release.yml` | Automatic zip/release workflow |
| `.github/workflows/installer.yml` | Automatic installer build workflow |

---

## ⚖️ Note

Personal, educational project. Please respect Fnac.com's terms of service: the
check frequency is intentionally moderate (15 min) to avoid overloading the
site.

## 📄 License

[MIT](LICENSE) © 2026 Loris
