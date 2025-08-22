import pydicom
import os
import shutil
import re
import pandas as pd
import tkinter as tk
from tkinter.filedialog import askopenfilename
from pylinac.picketfence import PicketFence, MLC  # pylinac==3.5.0
from datetime import datetime
from pydicom.misc import is_dicom


# Function to show messages in the console as labels in the Console Label Frame
def message_console(text_console):
    tk.Label(master=frm_console, text=text_console).grid(sticky="w")
    return


def open_files_path():
    # necessary to use this variable in other functions
    global file_path

    # usuário seleciona o arquivo
    file_path = askopenfilename(title='Selecione o arquivo de imagem')
    if not file_path:
        text_console = "Nenhum arquivo selecionado!"
        message_console(text_console)
        return
    else:
        # mostra o caminho do arquivo selecionado
        text_console = "Arquivo selecionado: " + file_path
        message_console(text_console)
        analyze_pf()


def analyze_pf():
    global pf

    pf = PicketFence(file_path, mlc=MLC.AGILITY,
                     crop_mm=5)
    pf.analyze(tolerance=0.5, action_tolerance=0.25,
               sag_adjustment=5)
    print(pf.results())
    print(pf.results_data(as_dict=True)['picket_widths'])
    pf.plot_analyzed_image(show_text=True)

    # show message in console
    text_console = "Análise concluída!"
    message_console(text_console)


def show_histogram():
    pf.plot_histogram()


# ########################################################################### #
#                                                                             #
#                                 MAIN PROGRAM                                #
#                                                                             #
# ########################################################################### #


window = tk.Tk()

frm_left = tk.Frame(master=window)
frm_left.grid(row=0, column=0, sticky="n")

# Frame to select folder where the dcm images are
frm_select_folder = tk.LabelFrame(
    master=frm_left, text="Diretório", font="VERDANA")
frm_select_folder.grid(row=0, column=0, padx=10, pady=5)

btn_select_folder = tk.Button(master=frm_select_folder,
                              text="Selecionar arquivo", font="VERDANA",
                              command=open_files_path).grid(row=0, column=0,
                                                            columnspan=2, padx=10, pady=5)

btn_plot_hist = tk.Button(master=frm_select_folder,
                          text="Mostrar histograma", font="VERDANA",
                          command=show_histogram).grid(row=1, column=0,
                                                       columnspan=2, padx=10, pady=5)


# Console frame
frm_console = tk.LabelFrame(
    master=window, width=800, height=50, text="Console")
frm_console.grid(row=2, column=0, columnspan=3, sticky="nw", padx=5, pady=20)


window.mainloop()
