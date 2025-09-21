import pytest
import json
from pathlib import Path
from jsontoggle.jsontoggle_core import JsonToggleManager
import pydash as _

@pytest.fixture
def demo_json_path(tmp_path: Path) -> Path:
    # Create a temporary demo.json for testing
    file_path = tmp_path / "demo.json"
    content = {
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
    with open(file_path, "w") as f:
        json.dump(content, f, indent=2)
    return file_path

@pytest.fixture
def toggles_dir(tmp_path: Path) -> Path:
    # Create a temporary toggles directory
    dir_path = tmp_path / "toggles"
    dir_path.mkdir()
    return dir_path

def test_json_toggle_manager_init(demo_json_path: Path, toggles_dir: Path):
    manager = JsonToggleManager(demo_json_path, toggles_dir)
    assert manager.json_file_path == demo_json_path
    assert manager.toggles_dir == toggles_dir
    assert isinstance(manager.original_json_data, dict)
    assert manager.json_data == manager.original_json_data
    assert toggles_dir.is_dir()

def test_load_json_file_not_found(tmp_path: Path, toggles_dir: Path):
    non_existent_path = tmp_path / "non_existent.json"
    with pytest.raises(ValueError, match="File not found"):
        JsonToggleManager(non_existent_path, toggles_dir)

def test_load_invalid_json_file(tmp_path: Path, toggles_dir: Path):
    invalid_json_path = tmp_path / "invalid.json"
    invalid_json_path.write_text("{\"key\": \"value") # Malformed JSON
    with pytest.raises(ValueError, match="Invalid JSON"):
        JsonToggleManager(invalid_json_path, toggles_dir)

def test_get_json_node(demo_json_path: Path, toggles_dir: Path):
    manager = JsonToggleManager(demo_json_path, toggles_dir)
    assert _.get(manager.json_data, ["featureFlags", "newDashboard"]) is True
    assert _.get(manager.json_data, ["settings", "theme"]) == "dark"
    assert _.get(manager.json_data, ["users", 0, "name"]) == "Alice"
    assert _.get(manager.json_data, ["nonExistent"]) is None
    assert _.get(manager.json_data, ["users", 10]) is None # Index out of bounds

def test_set_json_node(demo_json_path: Path, toggles_dir: Path):
    manager = JsonToggleManager(demo_json_path, toggles_dir)
    
    # Test setting a dict value
    _.set_(manager.json_data, ["featureFlags", "darkMode"], True)
    assert _.get(manager.json_data, ["featureFlags", "darkMode"]) is True

    # Test setting a list value
    _.set_(manager.json_data, ["users", 0, "name"], "Alicia")
    assert _.get(manager.json_data, ["users", 0, "name"]) == "Alicia"

    # Test setting a non-existent path (should return False)
    _.set_(manager.json_data, ["newRootKey", "subKey"], "value")
    assert _.get(manager.json_data, ["newRootKey", "subKey"]) == "value"

def test_toggle_node_out(demo_json_path: Path, toggles_dir: Path):
    manager = JsonToggleManager(demo_json_path, toggles_dir)
    path_to_toggle = "featureFlags.newDashboard"
    toggle_file_name = "featureFlags_newDashboard.json"
    toggle_file_path = toggles_dir / toggle_file_name

    # Toggle out
    manager.toggle_node(path_to_toggle)
    assert _.get(manager.json_data, path_to_toggle.split('.')) is None
    assert toggle_file_path.exists()
    with open(toggle_file_path, "r") as f:
        stored_value = json.load(f)
    assert stored_value is True
    
    # Verify original file on disk is updated
    with open(demo_json_path, "r") as f:
        on_disk_data = json.load(f)
    assert "newDashboard" not in on_disk_data["featureFlags"]

def test_toggle_node_in(demo_json_path: Path, toggles_dir: Path):
    manager = JsonToggleManager(demo_json_path, toggles_dir)
    path_to_toggle = "featureFlags.newDashboard"
    toggle_file_name = "featureFlags_newDashboard.json"
    toggle_file_path = toggles_dir / toggle_file_name
    
    # First, toggle out the node
    manager.toggle_node(path_to_toggle)
    
    # Then, toggle it back in
    manager.toggle_node(path_to_toggle)
    assert _.get(manager.json_data, path_to_toggle.split('.')) is True
    assert not toggle_file_path.exists()

    # Verify original file on disk is updated
    with open(demo_json_path, "r") as f:
        on_disk_data = json.load(f)
    assert on_disk_data["featureFlags"]["newDashboard"] is True

def test_toggle_non_existent_node(demo_json_path: Path, toggles_dir: Path):
    manager = JsonToggleManager(demo_json_path, toggles_dir)
    with pytest.raises(ValueError, match="Cannot toggle: nonExistent.path does not exist or is invalid."):
        manager.toggle_node("nonExistent.path")

def test_load_current_json_with_toggled_value(demo_json_path: Path, toggles_dir: Path):
    # Simulate a scenario where demo.json already has a toggled value
    manager1 = JsonToggleManager(demo_json_path, toggles_dir)
    path_to_toggle = "featureFlags.newDashboard"
    manager1.toggle_node(path_to_toggle)
    
    # Now, initialize a new manager and ensure it loads the toggled state
    manager2 = JsonToggleManager(demo_json_path, toggles_dir)
    assert "newDashboard" not in manager2.json_data["featureFlags"]
    assert manager2.original_json_data["featureFlags"]["newDashboard"] is True

def test_save_current_json(demo_json_path: Path, toggles_dir: Path):
    manager = JsonToggleManager(demo_json_path, toggles_dir)
    manager.json_data["featureFlags"]["darkMode"] = True
    manager.save_current_json()
    
    with open(demo_json_path, "r") as f:
        updated_data = json.load(f)
    assert updated_data["featureFlags"]["darkMode"] is True
