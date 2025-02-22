import tkinter as tk
from gui.gui import AppGUI
from helpers.processing import ProcessLogic


def main():
    """
    Main entry point of the application.

    - Initializes the Tkinter root window.
    - Sets the application title.
    - Creates an instance of ProcessLogic (handles text similarity logic).
    - Initializes the graphical user interface (GUI).
    - Starts the Tkinter event loop to keep the application running.
    """
    root = tk.Tk()
    root.title("Document Dependency Mapper")  # Sets the window title

    process_logic = ProcessLogic()  # Initializes the processing logic
    app = AppGUI(root, process_logic)  # Passes the logic to the GUI

    root.mainloop()  # Starts the Tkinter main event loop


# Run the application if the script is executed directly
if __name__ == "__main__":
    main()
