import os
import subprocess
import sys
sys.path.append('..')
from projectfyp import hide_path_windows, load_protected_list, save_protected_list

# Test hide_path_windows function
def test_hide_function():
    test_file = "test_file.txt"
    if not os.path.exists(test_file):
        with open(test_file, "w") as f:
            f.write("test content")

    print("Before hiding:")
    result = subprocess.run(f'attrib "{test_file}"', shell=True, capture_output=True, text=True)
    print(result.stdout)

    success = hide_path_windows(test_file)
    print(f"Hide function returned: {success}")

    print("After hiding:")
    result = subprocess.run(f'attrib "{test_file}"', shell=True, capture_output=True, text=True)
    print(result.stdout)

    # Check if hidden
    if os.path.exists(test_file):
        print("File still exists (good for hidden)")
    else:
        print("File not found")

# Test load/save protected list
def test_config():
    paths = ["C:\\test\\path1", "C:\\test\\path2"]
    save_protected_list(paths)
    loaded = load_protected_list()
    print(f"Saved: {paths}")
    print(f"Loaded: {loaded['paths']}")
    assert loaded['paths'] == paths, "Config save/load failed"
    print("Config test passed")

# Test edge cases
def test_edge_cases():
    # Test hiding non-existent file
    success = hide_path_windows("non_existent_file.txt")
    print(f"Hide non-existent file: {success} (expected False)")

    # Test hiding invalid path
    success = hide_path_windows("")
    print(f"Hide empty path: {success} (expected False)")

    # Test config with empty list
    save_protected_list([])
    loaded = load_protected_list()
    assert loaded['paths'] == [], "Empty config failed"
    print("Empty config test passed")

    # Test config with invalid JSON (simulate by corrupting file)
    try:
        with open("protected_list.json", "w") as f:
            f.write("invalid json")
        loaded = load_protected_list()
        assert loaded['paths'] == [], "Invalid JSON handling failed"
        print("Invalid JSON test passed")
    except Exception as e:
        print(f"Invalid JSON test error: {e}")

if __name__ == "__main__":
    test_hide_function()
    test_config()
    test_edge_cases()
