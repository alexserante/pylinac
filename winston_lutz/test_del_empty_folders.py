import os
import os.path
import shutil
import re
import tkinter as tk
from tkinter.filedialog import askdirectory


def test_function(main_path):
    gantry = [0, 90, 180, 270, 0, 0, 0, 0]
    lenght = len(gantry)
    n = 0
    for folderName, subfolders, filenames in os.walk(main_path):
        for filename in filenames:
            if re.search("^gantry", filename):
                print("Imagens já formatadas!")
                return
            if re.search("^[0-9]+", filename):
                print('FILE INSIDE ' + folderName + ': ' + filename)
                n = n + 1
    print(n)
    print(lenght)



# user select the directory of the images
main_path = askdirectory(title='Select folder')
'''if not main_path:
    print("Nenhuma pasta selecionada!")
    return'''

test_function(main_path)
