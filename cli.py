from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Tree
from textual.containers import Container
from textual.widgets.tree import TreeNode
from pathlib import Path
import json
import click
import sys

from jsontoggle.jsontoggle_core import JsonToggleManager, create_demo_file

class JsonTree(Tree):
    def __init__(self, name: str, data: dict | list, path: str = "", **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.data = data
        self.path = path
        self.show_root = False
        self.guide_depth = 3

    def on_mount(self) -> None:
        self.load_json(self.data, self.root)

    def load_json(self, data, node: TreeNode, path: str = "") -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                if isinstance(value, (dict, list)):
                    new_node = node.add(key, expand=False)
                    self.load_json(value, new_node, new_path)
                else:
                    node.add_leaf(f"{key}: {repr(value)}", data={'path': new_path, 'value': value})
        elif isinstance(data, list):
            for i, value in enumerate(data):
                new_path = f"{path}[{i}]"
                if isinstance(value, (dict, list)):
                    new_node = node.add(str(i), expand=False)
                    self.load_json(value, new_node, new_path)
                else:
                    node.add_leaf(f"{i}: {repr(value)}", data={'path': new_path, 'value': value})

class JsonToggleApp(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "toggle_node", "Toggle"),
    ]

    def __init__(self, json_file_path: Path, toggles_dir: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_toggle_manager = JsonToggleManager(json_file_path, toggles_dir)
        self.json_data = self.json_toggle_manager.json_data
        self.json_file_path = json_file_path # Keep for display purposes



    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        if self.json_data is not None:
            yield Container(
                JsonTree(str(self.json_file_path.name), self.json_data, id="json_tree"),
                Static(id="node_value", expand=True)
            )
        else:
            yield Static(f"Could not load JSON from {self.json_file_path}", expand=True)

    def on_mount(self) -> None:
        if self.json_data is not None:
            self.call_after_refresh(lambda: self.query_one("#json_tree").focus())

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if event.node.data and 'path' in event.node.data:
            selected_path = event.node.data['path']
            path_parts = selected_path.split('.')  # Assuming '.' as delimiter
            current_value = self.json_toggle_manager._get_json_node(self.json_data, path_parts)
            self.query_one("#node_value", Static).update(f"Selected Path: {selected_path}\nValue: {repr(current_value)}")
        else:
            self.query_one("#node_value", Static).update("Selected Node")

    def action_toggle_node(self) -> None:
        tree = self.query_one("#json_tree", Tree)
        if tree.cursor_node and tree.cursor_node.data and 'path' in tree.cursor_node.data:
            selected_path = tree.cursor_node.data['path']
            path_parts = selected_path.split('.')
            try:
                message = self.json_toggle_manager.toggle_node(selected_path)
                self.query_one("#node_value", Static).update(message)
                self.json_data = self.json_toggle_manager.json_data # Update local ref
            except ValueError as e:
                self.query_one("#node_value", Static).update(f"Error: {e}")
            
            self.query_one("#json_tree").clear()
            self.query_one("#json_tree").load_json(self.json_data, self.query_one("#json_tree").root)
        else:
            self.query_one("#node_value", Static).update("No togglable node selected.")



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


@click.group()
def cli():
    pass

@cli.command()
@click.argument("json_file", required=False, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--demo", is_flag=True, help="Create and launch with a demo JSON file.")
@click.option("--toggles-dir", type=click.Path(file_okay=False, path_type=Path), default="toggles", help="Directory to store toggled JSON parts.")
def start(json_file: Path | None, demo: bool, toggles_dir: Path):
    "Launch the TUI for toggling parts of JSON files."
    if demo:
        json_file_path = create_demo_file()
    elif json_file:
        json_file_path = json_file
    else:
        click.echo("Usage: python cli.py start <path_to_json_file> or python cli.py start --demo")
        sys.exit(1)

    app = JsonToggleApp(json_file_path, toggles_dir)
    app.run()


if __name__ == "__main__":
    cli()
