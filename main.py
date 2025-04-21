import os
from gui.main_window import MainWindow
from gui.style import setup_style
from utils.config import get_project_directory


def main():
    root = setup_style()
    app = MainWindow(root)
    directory = get_project_directory()
    app.initialize(directory)
    root.mainloop()


if __name__ == "__main__":
    main()
