# Quick Start Guide - 2Park Checker

## TL;DR

```bash
# 1. Install dependencies
uv sync
uv run playwright install chromium

# 2. Set up credentials
cp .env.example .env
nano .env  # Add your email and password

# 3. Run
./run.sh
```

That's it! 🎉

---

## What This Script Does

1. **Opens a browser** (visible, so you can see what's happening)
2. **Logs into 2park.nl** with your credentials
3. **Extracts your active reservations:**
   - Name
   - License plate
   - Start time
   - End time
4. **Shows your account balance**
5. **Displays everything nicely formatted**

## First Time Setup

### Step 1: Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install playwright
```

### Step 2: Install Chromium Browser

```bash
# Using uv
uv run playwright install chromium

# Or directly
playwright install chromium
```

### Step 3: Set Up Your Credentials

**Option A: Use .env file (Recommended)**

```bash
# Copy the example
cp .env.example .env

# Edit it
nano .env
```

Put your credentials in `.env`:
```
TWOPARK_EMAIL=your-email@example.com
TWOPARK_PASSWORD=your-password
```

**Option B: Export environment variables**

```bash
export TWOPARK_EMAIL="your-email@example.com"
export TWOPARK_PASSWORD="your-password"
```

## Running the Script

### Easy Way (Recommended)

```bash
./run.sh
```

The run script handles everything automatically:
- ✅ Loads credentials from `.env`
- ✅ Checks if browsers are installed
- ✅ Runs the script with proper error handling
- ✅ Shows colored output

### Manual Way

```bash
# Make sure credentials are set
export TWOPARK_EMAIL="your-email@example.com"
export TWOPARK_PASSWORD="your-password"

# Run with uv
uv run python main.py

# Or run directly
python main.py
```

## What You'll See

### Console Output

```
2025-12-19 22:40:44,845 - INFO - Launching browser...
2025-12-19 22:40:45,123 - INFO - Browser launched successfully
2025-12-19 22:40:45,234 - INFO - Navigating to login page...
2025-12-19 22:40:47,567 - INFO - Filling in email...
2025-12-19 22:40:48,123 - INFO - Filling in password...
2025-12-19 22:40:48,456 - INFO - Clicking login button...
2025-12-19 22:40:50,234 - INFO - Login successful
2025-12-19 22:40:51,123 - INFO - Found 2 reservation(s)

==================================================
ACTIVE RESERVATIONS
==================================================

Reservation 1:
  Name: John Doe
  License Plate: AB-123-CD
  Start Time: 09:00
  End Time: 17:00

Reservation 2:
  Name: Jane Smith
  License Plate: XY-456-ZZ
  Start Time: 10:00
  End Time: 18:00

==================================================
ACCOUNT BALANCE
==================================================
€ 25.50
==================================================
```

### Browser Window

You'll see a Chrome window open automatically and:
1. Navigate to mijn.2park.nl/login
2. Type in your email (slowly, so you can see)
3. Type in your password (slowly)
4. Click the login button
5. Navigate to the dashboard
6. Then close automatically

## Common Issues

### "Missing credentials" error

**Solution:** Set up your `.env` file or export environment variables

```bash
export TWOPARK_EMAIL="your-email@example.com"
export TWOPARK_PASSWORD="your-password"
```

### "playwright: not found" error

**Solution:** Install Playwright browsers

```bash
uv run playwright install chromium
```

### Browser crashes or fails to launch

**Solution:** Make sure Chromium is installed

```bash
uv run playwright install chromium
```

### Permission denied on run.sh

**Solution:** Make it executable

```bash
chmod +x run.sh
```

### Timeout errors

**Possible causes:**
- Slow internet connection
- Website is down or slow
- Firewall blocking the connection

**Solution:** Try again in a few minutes

## Customization

### Want to hide the browser?

Edit `main.py` line 39:

```python
# Change this:
headless=False,

# To this:
headless=True,
```

### Want to speed up the automation?

Edit `main.py` line 40:

```python
# Change this:
slow_mo=50,  # 50 milliseconds

# To this:
slow_mo=0,   # No delay
```

### Want to change the viewport size?

Edit `main.py` line 54:

```python
# Change this:
viewport={"width": 1920, "height": 1080}

# To whatever you want:
viewport={"width": 1280, "height": 720}
```

## Security Notes

🔒 **Your credentials are safe:**
- Never hardcoded in the script
- Stored only in `.env` (which is in `.gitignore`)
- Only sent to 2park.nl (nowhere else)
- Not logged or stored anywhere

⚠️ **Never commit `.env` to git!** It's already in `.gitignore`, but double-check:

```bash
git status  # Should NOT show .env
```

## Tips & Tricks

### Run without prompts

If you use `.env` file, you won't be prompted for credentials:

```bash
./run.sh  # Just runs, no questions asked
```

### Schedule it with cron

Check your balance every morning at 9 AM:

```bash
# Edit crontab
crontab -e

# Add this line (adjust path):
0 9 * * * cd /home/mark/Projects/2park_checker && ./run.sh >> /tmp/2park.log 2>&1
```

### Export data to file

```bash
./run.sh > output.txt 2>&1
```

## Need Help?

1. **Check the logs** - They show exactly what's happening
2. **Read README.md** - Comprehensive documentation
3. **Check CHANGES.md** - See what changed from the old version
4. **Look at the code** - It's well-commented!

## Files Overview

```
2park_checker/
├── main.py           # The main script
├── run.sh            # Easy run script
├── .env              # Your credentials (create this)
├── .env.example      # Template for credentials
├── README.md         # Full documentation
├── CHANGES.md        # What changed in the rewrite
├── QUICKSTART.md     # This file
└── pyproject.toml    # Python dependencies
```

## Next Steps

Now that you have it running:

1. ✅ Check your reservations regularly
2. ✅ Monitor your balance
3. ✅ Set up a cron job for automatic checks
4. ✅ Customize the output format if needed

Happy parking! 🚗