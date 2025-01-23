import tkinter as tk
from gui.gui import AppGUI
from helpers.processing import ProcessLogic

def main():
    """Main entry point of the application."""
    root = tk.Tk()
    root.title("Document Dependency Mapper")
    process_logic = ProcessLogic()
    app = AppGUI(root, process_logic)
    root.mainloop()

if __name__ == "__main__":
    main()