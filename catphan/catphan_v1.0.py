import tkinter as tk
import os
from tkinter import *
from tkinter.filedialog import askdirectory, askopenfilename
from datetime import datetime
from pylinac import (
    CatPhan503, LeedsTOR, ElektaLasVegas
)


# Function to show messages in the console as labels in the Console Label Frame
def message_console(text_console):
    tk.Label(master=frm_console, text=text_console).grid(sticky="w")
    return


def openImage():
    # user select the file
    file_path = askopenfilename(title='Select dcm file')
    if not file_path:
        text_console = "Nenhum arquivo selecionado!"
        message_console(text_console)
        return
    else:
        # print("Caminho selecionado: " + file_path)
        text_console = "Arquivo selecionado: " + file_path
        message_console(text_console)
        return file_path


def openPath():
    # user select the directory of the images
    main_path = askdirectory(title='Select folder')
    if not main_path:
        # print("Nenhuma pasta selecionada!")
        text_console = "Nenhuma pasta selecionada!"
        message_console(text_console)
        return
    else:
        # print("Caminho selecionado: " + main_path)
        text_console = "Caminho selecionado: " + main_path
        message_console(text_console)
        return main_path


def analyze_catphan():
    # necessary to use this variable in other functions
    global catphan
    global mainPath

    mainPath = openPath()

    catphan = CatPhan503(mainPath)
    catphan.analyze()

    print(catphan.results())

    # show message in console
    text_console = "Análise concluída!"
    message_console(text_console)

    # show message in the results frame
    lbl_results.config(text=catphan.results())
    # show images
    catphan.plot_analyzed_image()


def analyze_leedstor():
    global leeds
    global filePath

    filePath = openImage()

    leeds = LeedsTOR(filePath)
    leeds.analyze()

    # show message in console
    text_console = "Análise concluída!"
    message_console(text_console)

    # show message in the results frame
    lbl_results.config(text=leeds.results())
    # show images
    leeds.plot_analyzed_image()

    print(leeds.results())


def save_pdf_catphan():
    folder_path = mainPath

    date = datetime.today().strftime("%Y%m%d")
    filename = date + "_catphan_" + ".pdf"

    full_path = os.path.join(folder_path, filename)

    catphan.publish_pdf(filename=full_path)

    # show message in console
    text_console = "PDF salvo em: " + full_path
    message_console(text_console)


def save_pdf_leedstor():
    folder_path = os.path.dirname(filePath)

    date = datetime.today().strftime("%Y%m%d")
    filename = date + "_leedsTOR_" + ".pdf"

    full_path = os.path.join(folder_path, filename)

    leeds.publish_pdf(filename=full_path)

    # show message in console
    text_console = "PDF salvo em: " + full_path
    message_console(text_console)


# ########################################################################### #
#                                                                             #
#                                 MAIN PROGRAM                                #
#                                                                             #
# ########################################################################### #


window = tk.Tk()

frm_left = tk.Frame(master=window)
frm_left.grid(row=0, column=0, sticky="n")

# LEFT FRAME
# CATPHAN
frm_catphan = tk.LabelFrame(
    master=frm_left, text="Catphan503", font="VERDANA")
frm_catphan.grid(row=0, column=0, padx=10, pady=5)

btn_analysis_catphan = tk.Button(
    master=frm_catphan, text="Selecionar diretório", font="VERDANA",
    command=analyze_catphan).grid(row=0, column=0, padx=10, pady=5)

btn_save_pdf = tk.Button(
    master=frm_catphan, text="Salvar PDF", font="VERDANA",
    command=save_pdf_catphan).grid(row=0, column=1, padx=10, pady=2)

# LeedsTOR
frm_leedstor = tk.LabelFrame(
    master=frm_left, text="LeedsTOR", font="VERDANA")
frm_leedstor.grid(row=1, column=0, padx=10, pady=5)

btn_analysis_leedstor = tk.Button(
    master=frm_leedstor, text="Selecionar imagem", font="VERDANA",
    command=analyze_leedstor).grid(row=0, column=0, padx=10, pady=5)

btn_save_pdf = tk.Button(
    master=frm_leedstor, text="Salvar PDF", font="VERDANA",
    command=save_pdf_leedstor).grid(row=0, column=1, padx=10, pady=2)

# RIGHT FRAME
frm_right = tk.Frame(master=window)
frm_right.grid(row=0, column=1, sticky="n")

# Results frame
frm_results = tk.LabelFrame(
    master=frm_right, width=380, height=410, text="Resultados", font="VERDANA")
frm_results.grid(row=0, column=0, sticky='n')
frm_results.grid_propagate(0)

lbl_results = tk.Label(master=frm_results)
lbl_results.grid(row=0, column=0)

# Console frame
frm_console = tk.LabelFrame(
    master=window, width=500, height=50, text="Console")
frm_console.grid(row=2, column=0, columnspan=3, sticky="nw", padx=5, pady=20)


window.mainloop()
