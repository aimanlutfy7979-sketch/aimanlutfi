# Smart File Protector (Windows)

## Overview
**Smart File Protector** is a Tkinter-based Windows desktop application that:
- Detects **removable USB drives**.
- Lets you **add protected files/folders** to a local list.
- Provides **“Protect Now”** to **hide** the selected items (and recursively hide folders’ contents).
- Provides **“Restore Files”** to **unhide** protected items.
- Requires **password authentication** for restore (and at startup).
- Logs activity in an on-screen “Activity Log”.

> Note: “Hiding” here uses Windows file attributes (Hidden/System). It does **not** encrypt data.

## Files
- `projectfyp2.py` — the main application.
- `protected_list.json` — saved list of protected paths (created automatically).

## Requirements
- Windows OS
- Python 3.x

Python packages used (standard library only):
- `tkinter`, `ctypes`, `hashlib`, `json`, etc. (No extra pip dependencies.)

## Passwords
- The application uses a hardcoded password hash.
- Current password in code: **`1234`** (hashed internally).

## How it works (high level)
1. On launch, the app shows a startup password prompt (max 3 attempts).
2. After authentication, the UI loads and the app begins tracking USB drive changes when you press **Start Monitoring**.
3. You can add:
   - **Add File** (select a file)
   - **Add Folder** (select a folder)
4. When you press **Protect Now**, it:
   - Iterates through the configured protected paths
   - Uses Windows attributes to set **Hidden/System**
5. When you press **Restore Files**, it prompts for password again and then unhides items.

## Run the app
From a terminal:
```bat
python projectfyp2.py
```

## Testing
There is a `test_functionsfyp.py` open in your editor, but it appears to reference functions that are not present in `projectfyp2.py` as currently shown (name mismatches like `hide_path_windows`, `load_protected_list`, etc.).

If you want, tests can be updated to call the equivalent functions in `projectfyp2.py`.

## Troubleshooting
- **Hiding may fail** for paths without permission (run as an appropriate user).
- If you select a path that no longer exists, the app will **skip it** and log “Skipped not found”.

## Security warning
This project is a demonstration of Windows attribute-based hiding plus UI/password gating. For real security (confidentiality, tamper resistance), you would need proper encryption, access control, and threat modeling.

