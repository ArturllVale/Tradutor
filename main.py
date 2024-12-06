#  __                       |
# |  |   _ _ _____ ___ ___  |
# |  |__| | |     | -_|   | |
# |_____|___|_|_|_|___|_|_| |
#         lumen#0110        |
#        2024 - 2025        |
#___________________________|

import os
import asyncio
import logging
from src.gui.main_window import create_gui

# Configurar o logging
logging.basicConfig(level=logging.INFO)

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    root = create_gui()
    root.mainloop()
