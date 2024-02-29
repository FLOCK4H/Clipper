import os
import winshell

def create_shortcut_to_startup(program_path, shortcut_name):
    # Get the startup folder path for the current user
    startup_folder = winshell.startup()

    # Path where the shortcut will be created
    shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")

    # Create a shortcut in the startup folder
    with winshell.shortcut(shortcut_path) as shortcut:
        shortcut.path = program_path
        shortcut.description = "Shortcut to my program"
        # You can also set the icon for the shortcut if you want
        # shortcut.icon_location = (program_path, 0)

# Usage
create_shortcut_to_startup("Clipper.exe", "Clipboard Tool")