# JSON Toggle

A CLI tool for interactively toggling JSON nodes on and off within a JSON file, storing the original values for easy restoration.

## Features

- **Interactive TUI**: Navigate and select JSON nodes using a Text User Interface (TUI).
- **Toggle Nodes**: Easily remove a JSON node from the main file, storing its original value in a separate toggle file.
- **Revert Toggles**: Restore a previously toggled-out node by reinserting its original value from the toggle file.
- **Persistent Toggles**: Toggled nodes' states are maintained across sessions, allowing you to manage feature flags or configurations effectively.

## Installation

### Prerequisites

- Python 3.8 or higher
- `uv` (optional, for faster dependency management)

### Steps

1. **Clone the repository (if applicable):**
   ```bash
   git clone https://github.com/your-username/jsontoggle.git
   cd jsontoggle
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   Using `uv` (recommended):
   ```bash
   uv sync
   ```
   Or using `pip`:
   ```bash
   pip install -e .
   ```

## Usage

The `jsontoggle` tool provides a TUI for interacting with your JSON files.

### Launching the TUI

You can launch the TUI with an existing JSON file or create a demo file.

#### With an existing JSON file:

```bash
jsontoggle start <path_to_json_file>
```

Example:
```bash
jsontoggle start my_config.json
```

#### With a demo JSON file:

This will create a `demo.json` file in your current directory and launch the TUI with it.

```bash
jsontoggle start --demo
```

### Navigating the TUI

- Use **arrow keys** (Up/Down) to navigate through the JSON tree.
- Press **Space** or **Right Arrow** to expand/collapse nodes.

### Toggling Nodes

- Select a node you wish to toggle.
- Press `t` to **toggle** the selected node.
  - If the node is present, it will be removed from the JSON file, and its original value will be saved in the `toggles/` directory.
  - If the node was previously toggled out (and appears as "(Toggled out)"), pressing `t` will restore it to the JSON file using the saved value from `toggles/`.

### Quitting the TUI

- Press `q` to quit the application.

## Example Workflow

1. **Start with a demo file:**
   ```bash
   jsontoggle start --demo
   ```

2. **Navigate** to `featureFlags.darkMode`.
3. Press `t` to **toggle out** `darkMode`. You'll see it disappear from the main JSON structure, and a message indicating it's been toggled out.
4. The `toggles/` directory will now contain a file like `featureFlags_darkMode.json` with the original value (`false`).
5. **Quit** the application (`q`).
6. **Re-launch** with the `demo.json` file.
   ```bash
   jsontoggle start demo.json
   ```
   You'll notice `featureFlags.darkMode` is still toggled out.
7. **Navigate** to the `featureFlags.darkMode (Toggled out)` node.
8. Press `t` again to **revert** the toggle. The `darkMode` node will reappear in the JSON, and its toggle file will be removed.
9. **Quit** the application.
