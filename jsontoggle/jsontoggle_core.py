from pathlib import Path
import json
import os
import copy

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
                path_str = toggle_file.stem.replace('_', '.')
                path_parts = path_str.split('.')

                # Reconstruct list indices if present in filename
                if any(part.isdigit() for part in toggle_file.stem.split('_')):
                    reconstructed_path_parts = []
                    current_segment = ""
                    for part_segment in toggle_file.stem.split('_'):
                        if part_segment.isdigit():
                            if current_segment:
                                reconstructed_path_parts.append(current_segment)
                            reconstructed_path_parts.append(f"[{part_segment}]")
                            current_segment = ""
                        else:
                            if current_segment:
                                current_segment += "." + part_segment
                            else:
                                current_segment = part_segment
                    if current_segment:
                        reconstructed_path_parts.append(current_segment)
                    # Join and split to handle cases like \'users[0].name\'
                    path_parts = "".join(reconstructed_path_parts).replace("].", ".").split('.')

                with open(toggle_file, "r") as f:
                    original_value = json.load(f)
                self._set_json_node(reverted_data, path_parts, original_value)
            except Exception as e:
                print(f"Warning: Could not revert toggle from {toggle_file.name}: {e}")
        return reverted_data


    def _get_json_node(self, data, path_parts):
        current_node = data
        for part in path_parts:
            if isinstance(current_node, dict):
                current_node = current_node.get(part)
            elif isinstance(current_node, list) and part.isdigit():
                try:
                    current_node = current_node[int(part)]
                except IndexError:
                    return None
            else:
                return None
        return current_node

    def _set_json_node(self, data, path_parts, value):
        current_node = data
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1:
                if isinstance(current_node, dict):
                    current_node[part] = value
                elif isinstance(current_node, list) and part.isdigit():
                    try:
                        current_node[int(part)] = value
                    except IndexError:
                        pass
                break
            
            if isinstance(current_node, dict):
                if part not in current_node:
                    return False  # Path not found
                current_node = current_node[part]
            elif isinstance(current_node, list) and part.isdigit():
                idx = int(part)
                if idx >= len(current_node):
                    return False # Path not found
                current_node = current_node[idx]
            else:
                return False # Path not found
        return True

    def save_current_json(self):
        try:
            with open(self.json_file_path, "w") as f:
                json.dump(self.json_data, f, indent=2)
        except Exception as e:
            raise ValueError(f"Error saving JSON to {self.json_file_path}: {e}")

    def toggle_node(self, selected_path: str):
        path_parts = selected_path.split('.')
        original_value = self._get_json_node(self.original_json_data, path_parts)

        if original_value is None:
            raise ValueError(f"Cannot toggle: {selected_path} does not exist or is invalid.")

        toggle_file_name = f"{selected_path.replace('.', '_').replace('[', '_').replace(']', '')}.json"
        toggle_file_path = self.toggles_dir / toggle_file_name

        if toggle_file_path.exists():
            # Revert: Put the original value back
            with open(toggle_file_path, "r") as f:
                stored_value = json.load(f)
            
            # Update json_data with the stored original value
            if self._set_json_node(self.json_data, path_parts, stored_value):
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
            if self._set_json_node(self.json_data, path_parts, "__TOGGLED__"): # Use a placeholder
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
