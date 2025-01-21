import tkinter as tk
from gui.gui import AppGUI
from helpers.processing import ProcessLogic

if __name__ == "__main__":
    root = tk.Tk()
    process_logic = ProcessLogic()
    app = AppGUI(root, process_logic)
    root.mainloop()
