import os
import os.path
import shutil
import tkinter as tk
from tkinter.filedialog import askdirectory


def move_files_from_subfolders_into_main_path(main_path):

    for folder, subfolders, files in os.walk(main_path, topdown=False):
        # 1. Move files to main folder (out of subfolders:)
        for name in files:
            os.system('move "' + os.path.join(folder, name) + '" "' + main_path +
                      '\\' + os.path.join(name) + '"')  # note \\ at the end

    # 2. Delete empty folders
    folders = list(os.walk(main_path, topdown=False))
    for folder in folders:
        if not folder[2]:
            os.rmdir(folder[0])



# user select the directory of the images
main_path = askdirectory(title='Select folder')
'''if not main_path:
    print("Nenhuma pasta selecionada!")
    return'''

move_files_from_subfolders_into_main_path(main_path)
