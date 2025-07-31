
import pydicom
import os
import shutil
import re
import pandas as pd
import tkinter as tk
from tkinter.filedialog import askopenfilename
from pylinac import (
    FieldProfileAnalysis, Interpolation,
    Centering, Edge, Normalization
)
from pylinac.metrics.profile import (
    PenumbraLeftMetric,
    PenumbraRightMetric,
    SymmetryAreaMetric,
    FlatnessDifferenceMetric,
)
from datetime import datetime
from pydicom.misc import is_dicom


# Function to show messages in the console as labels in the Console Label Frame
def message_console(text_console):
    tk.Label(master=frm_console, text=text_console).grid(sticky="w")
    return


def open_files_path():
    # necessary to use this variable in other functions
    global file_path

    file_path = ""

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
        analyze_field()


def analyze_field():
    global fa

    fa = FieldProfileAnalysis(file_path)
    fa.analyze(
        x_width=0.02,
        y_width=0.02,
        normalization=Normalization.BEAM_CENTER,
        centering=Centering.BEAM_CENTER,
        edge_type=Edge.INFLECTION_DERIVATIVE,
        invert=True,
        ground=True,
        metrics=(
            PenumbraLeftMetric(),
            PenumbraRightMetric(),
            SymmetryAreaMetric(),
            FlatnessDifferenceMetric(),
        ),
    )
    print(fa.results())
    fa.plot_analyzed_images(show_grid=True)

    # show message in console
    text_console = "Análise concluída!"
    message_console(text_console)


def show_histogram():
    fa.plot_histogram()


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
