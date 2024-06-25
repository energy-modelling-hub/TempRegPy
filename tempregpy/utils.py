import shutil
import os

def copy_file_to_destination(source_filename, destination_directory):
    # Get the current directory
    current_directory = os.getcwd()

    # Construct the full path of the source file (assuming it's in the parent directory)
    source_path = os.path.join(os.path.dirname(current_directory), source_filename)

    # Construct the full path of the destination directory
    destination_path = os.path.join(current_directory, destination_directory)

    try:
        # Create the destination directory if it doesn't exist
        os.makedirs(destination_path, exist_ok=True)

        # Copy the file to the destination directory
        shutil.copy(source_path, destination_path)
        print(f"File '{source_path}' successfully copied to '{destination_path}'")
    except FileNotFoundError:
        print(f"Error: File '{source_path}' not found.")
    except PermissionError:
        print(f"Error: Permission denied when accessing '{destination_path}'")

# Example usage:
# source_filename = "file_to_copy.txt"  # Replace with your source file name
# destination_directory = "destination_folder"  # Replace with your destination directory
#
# copy_file_to_destination(source_filename, destination_directory)