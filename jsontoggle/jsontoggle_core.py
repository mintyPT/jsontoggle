from pathlib import Path
import json
import os
import copy

class DictListHelper:
    @staticmethod
    def get(data, path_parts):
        """
        Safely gets a value from a nested dict/list structure.
        Path parts can be list indices or dictionary keys.
        """
        current = data
        for part in path_parts:
            try:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    current = current[int(part)]
                else:
                    return None
            except (KeyError, IndexError, ValueError):
                return None
            if current is None:
                return None
        return current

    @staticmethod
    def set(data, path_parts, value):
        """
        Sets a value in a nested dict/list structure.
        Intermediate dictionaries or lists are created if they don't exist.
        Returns True on success, False on failure.
        """
        current = data
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1: # Last part of the path
                if isinstance(current, dict):
                    current[part] = value
                    return True
                elif isinstance(current, list):
                    try:
                        index = int(part)
                        while len(current) <= index:
                            current.append(None) # Pad list if necessary
                        current[index] = value
                        return True
                    except ValueError:
                        return False # Path part not a valid index for a list
                else:
                    return False # Cannot set on a non-dict/list intermediate
            
            # Not the last part, navigate or create
            if isinstance(current, dict):
                if part not in current or current.get(part) is None:
                    current[part] = {} # Assume dict for next level
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    while len(current) <= index:
                        current.append(None)
                    if current[index] is None:
                        current[index] = {}
                    current = current[index]
                except (ValueError, IndexError):
                    return False # Cannot navigate list with non-integer or out of bounds
            else:
                return False # Cannot navigate non-dict/list intermediate
        return False # Should not reach here if last part handled

    @staticmethod
    def has(data, path_parts):
        """
        Checks if a path exists in the nested dict/list structure.
        """
        current = data
        for i, part in enumerate(path_parts):
            try:
                if isinstance(current, dict):
                    if part not in current:
                        return False
                    current = current[part]
                elif isinstance(current, list):
                    index = int(part)
                    if not (0 <= index < len(current)):
                        return False
                    current = current[index]
                else:
                    return False
            except (KeyError, IndexError, ValueError):
                return False
        return True

    @staticmethod
    def unset(data, path_parts):
        """
        Deletes a node from a nested dict/list structure.
        Returns True on success, False if the path does not exist.
        """
        if not path_parts:
            return False

        current = data
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1: # Last part of the path
                if isinstance(current, dict) and part in current:
                    del current[part]
                    return True
                elif isinstance(current, list):
                    try:
                        index = int(part)
                        if 0 <= index < len(current):
                            del current[index]
                            return True
                    except ValueError:
                        pass # Not a valid index
                return False # Not found or not a dict/list
            
            # Not the last part, navigate
            try:
                if isinstance(current, dict):
                    if part not in current:
                        return False
                    current = current[part]
                elif isinstance(current, list):
                    index = int(part)
                    if not (0 <= index < len(current)):
                        return False
                    current = current[index]
                else:
                    return False
            except (KeyError, IndexError, ValueError):
                return False
        return False



class JsonToggleManager:
    def __init__(self, json_file_path: Path, toggles_dir: Path):
        self.json_file_path = json_file_path
        self.toggles_dir = toggles_dir
        self._ensure_toggles_directory()
        
        # Load the current state from the JSON file (which might have toggles)
        current_data = self._load_json_content(self.json_file_path)
        self.json_data = current_data

        # Reconstruct the original JSON data by reverting any active toggles
        self.original_json_data = self._load_json_with_toggles_reverted(current_data)

    def _ensure_toggles_directory(self):
        os.makedirs(self.toggles_dir, exist_ok=True)

    def _load_json_content(self, file_path: Path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Error: File not found - {file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Error: Invalid JSON in {file_path}")
        except Exception as e:
            raise ValueError(f"Error loading {file_path}: {e}")

    def _load_json_with_toggles_reverted(self, base_data: dict) -> dict:
        reverted_data = copy.deepcopy(base_data)
        for toggle_file in self.toggles_dir.glob("*.json"):
            try:
                # Extract path from filename
                path_parts = toggle_file.stem.replace('__', '.').split('_')

                with open(toggle_file, "r") as f:
                    original_value = json.load(f)
                DictListHelper.set(reverted_data, path_parts, original_value)
            except Exception as e:
                print(f"Warning: Could not revert toggle from {toggle_file.name}: {e}")
        return reverted_data



    def save_current_json(self):
        try:
            with open(self.json_file_path, "w") as f:
                json.dump(self.json_data, f, indent=2)
        except Exception as e:
            raise ValueError(f"Error saving JSON to {self.json_file_path}: {e}")

    def toggle_node(self, selected_path: str):
        path_parts = selected_path.split('.')
        original_value = DictListHelper.get(self.original_json_data, path_parts)

        if original_value is None and not DictListHelper.has(self.original_json_data, path_parts):
            raise ValueError(f"Cannot toggle: {selected_path} does not exist or is invalid.")

        toggle_file_name = f"{selected_path.replace('.', '_').replace('[', '_').replace(']', '')}.json"
        toggle_file_path = self.toggles_dir / toggle_file_name

        if toggle_file_path.exists():
            # Revert: Put the original value back
            with open(toggle_file_path, "r") as f:
                stored_value = json.load(f)
            
            # Update json_data with the stored original value
            if DictListHelper.set(self.json_data, path_parts, stored_value):
                toggle_file_path.unlink()  # Delete the toggle file
                self.save_current_json()
                return f"Reverted: {selected_path}"
            else:
                raise ValueError(f"Error reverting {selected_path}.")
        else:
            # Toggle out: Save original and replace with placeholder
            with open(toggle_file_path, "w") as f:
                json.dump(original_value, f, indent=2)
            
            # Update json_data with the placeholder
            if DictListHelper.unset(self.json_data, path_parts): # Remove the key
                self.save_current_json()
                return f"Toggled out: {selected_path} (stored in {toggle_file_name})"
            else:
                raise ValueError(f"Error toggling out {selected_path}.")

def create_demo_file(file_name="demo.json"):
    demo_content = {
        "featureFlags": {
            "newDashboard": True,
            "darkMode": False,
            "experimentalSearch": {
                "enabled": True,
                "version": 2
            }
        },
        "settings": {
            "theme": "dark",
            "notifications": {
                "email": True,
                "sms": False
            }
        },
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    }
    demo_file_path = Path(file_name)
    with open(demo_file_path, "w") as f:
        json.dump(demo_content, f, indent=2)
    return demo_file_path
