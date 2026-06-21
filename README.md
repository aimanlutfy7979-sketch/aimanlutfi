# Smart File Protector (Windows)

A Windows-only **Tkinter desktop** app that helps you “protect” selected files/folders by **hiding** them using Windows file attributes (Hidden + System). It also includes:
- **USB removable-drive monitoring** (detect insert/remove events)
- **Password authentication** (startup + restore action)
- A **configurable list** of protected paths saved locally
- A live **activity log** in the UI

> **Important:** This does **not** encrypt your data. “Protecting” = changing Windows attributes so items become hidden.

---

## What the app does
### 1) Startup authentication
When you run the program, it immediately asks for the application password.
- After **3 failed attempts**, it blocks access.
- If authentication succeeds, the main UI opens.

### 2) USB monitoring (optional)
In the UI you can press **▶ Start Monitoring**.
- The app checks removable drives every ~1.5 seconds.
- It compares the current set of drives with the last known set to detect:
  - **Inserted** drives
  - **Removed** drives
- The UI updates a “USB Status” card and logs events.

### 3) Manage protected items
You maintain a list of items to protect:
- **Add File** → choose a file
- **Add Folder** → choose a folder
- **Remove Selected** → remove selected rows from the list

Each protected item is stored as an **absolute path**.

### 4) Protect Now
When you press **🛡 Protect Now** the app:
- Iterates over every configured protected path
- If it’s a file → calls Windows API to set Hidden/System attributes
- If it’s a folder → recursively walks the directory and hides:
  - the folder itself
  - all subfolders
  - all files
- It logs how many items were updated and skips paths that no longer exist.

### 5) Restore Files
When you press **🔓 Restore Files** the app:
- Prompts for password again
- If password is valid, it performs the reverse operation:
  - folders are recursively unhiden
  - files are unhidden
- It then updates the UI back to an “IDLE” protection state.

---

## Files used by the project
### `projectfyp2.py`
Main application code.
Key features implemented here:
- Windows API integration (via `ctypes`) to set/unset Hidden/System attributes
- Tkinter UI (cards, buttons, tree table, and log)
- USB detection loop in a background thread
- Password hashing + verification
- Local persistence of protected paths

### `protected_list.json`
A JSON file created/updated by the app to store the protected path list.
- Location: in the **same working directory** where the app runs
- Format: a JSON list of strings (paths)

> If you run the script from a different folder, the JSON file will also be created in that folder.

---

## Passwords (as in the current code)
The password in `projectfyp2.py` is hardcoded as a SHA-256 hash.
- Current plain-text password embedded in code: **`1234`**

The app never stores the plain-text password; it stores/verifies against the hash.

---

## Requirements / dependencies
- **Windows 10/11**
- **Python 3.x**
- Uses **standard library** only:
  - `tkinter` for UI
  - `ctypes` for Windows attribute changes
  - `hashlib`, `json`, `threading`, `os`, etc.

No pip install is required.

---

## How to run
From the folder where `projectfyp2.py` is located:
```bat
python projectfyp2.py
```

The UI will open after startup authentication.

---

## How to use (step-by-step)
1. Run the script
2. Enter the startup password
3. (Optional) Click **▶ Start Monitoring**
4. Click **📄 Add File** or **📁 Add Folder** to choose items
5. Click **🛡 Protect Now** to hide them
6. To undo, click **🔓 Restore Files** and enter the password

---

## Notes about behavior & limitations
- **Permission issues:** If Windows denies attribute changes for some paths, the app will log failures.
- **Nonexistent paths:** If a protected path no longer exists, it will be skipped.
- **“Hidden” is not security:** Hidden files can still be recovered by anyone with enough access/tools.
- **Hardcoded password:** For a real project, you would typically externalize credentials and add better security.

---

## Testing note (`test_functionsfyp.py`)
Your repository also contains `test_functionsfyp.py`, but from what is currently visible:
- It references functions like `hide_path_windows`, `load_protected_list`, `save_protected_list`.
- These names don’t directly match the functions implemented in `projectfyp2.py` (for example `set_hidden`, `hide_recursively`, `load_protected_items`, `save_protected_items`).

So the tests may currently fail until the test file is updated to call the correct functions.

---

## How to update tests (high level)
If you want to align tests with the app code, you would typically:
- Map test helper names → the actual functions in `projectfyp2.py`
- Ensure the test expects the correct JSON format (`protected_list.json`) and keys

---

## Quick project description (for your report)
**Smart File Protector** is a user-facing Windows application that monitors USB drive insertion/removal and provides a password-protected workflow to hide/unhide user-selected files and folders by manipulating Windows file attributes. It keeps a persistent list of protected items in JSON and provides real-time logging through a custom Tkinter GUI.

