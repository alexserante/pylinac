import os
import os.path
import shutil
import re
import tkinter as tk
from tkinter import *
from tkinter.filedialog import askdirectory
from datetime import datetime
from pylinac import CatPhan503


# Function to show messages in the console as labels in the Console Label Frame
def message_console(text_console):
    tk.Label(master=frm_console, text=text_console).grid(sticky="w")
    return


def open_files_path():
	# necessary to use this variable in other functions
	global main_path

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

def analyze_catphan():
	catphan = CatPhan503(main_path)
	catphan.analyze()

	# show message in console
	text_console = "Análise concluída!"
	message_console(text_console)

	# show message with the selected path
	lbl_results.config(text=catphan.results())
	#lbl_shift_bb.config(text="Mover: " + wl.bb_shift_instructions())

	print(catphan.results())
	catphan.plot_analyzed_image()

	#cbct.publish_pdf("catphan_M20", open_file=True)


# ########################################################################### #
#                                                                             #
#                                 MAIN PROGRAM                                #
#                                                                             #
# ########################################################################### #


window = tk.Tk()

frm_left = tk.Frame(master=window)
frm_left.grid(row=0, column=0, sticky="n")

# Folder path frame
frm_select_folder = tk.LabelFrame(
    master=frm_left, text="Diretório", font="VERDANA")
frm_select_folder.grid(row=0, column=0, padx=10, pady=5)

btn_select_folder = tk.Button(master=frm_select_folder,
                              text="Selecionar pasta", font="VERDANA",
                              command=open_files_path).grid(row=0, column=0,
                                                            columnspan=2, padx=10, pady=5)

# Analysis frame
frm_perform_analysis = tk.LabelFrame(
    master=frm_left, text="Análise Catphan", font="VERDANA")
frm_perform_analysis.grid(row=0, column=1, padx=10, pady=5)

btn_perform_analysis = tk.Button(
    master=frm_perform_analysis, text="Fazer análise WL", font="VERDANA",
    command=analyze_catphan).grid(row=0, column=0, padx=10, pady=5)

# RIGHT FRAME
frm_right = tk.Frame(master=window)
frm_right.grid(row=0, column=1, sticky="n")

# Results frame
frm_results = tk.LabelFrame(
    master=frm_right, width=435, height=250, text="Resultados", font="VERDANA")
frm_results.grid(row=0, column=0, sticky='n')
frm_results.grid_propagate(0)

lbl_results = tk.Label(master=frm_results)
lbl_results.grid(row=0, column=0)


# Console frame
frm_console = tk.LabelFrame(
    master=window, width=100, height=50, text="Console")
frm_console.grid(row=2, column=0, columnspan=2, sticky="nw", padx=5, pady=20)


window.mainloop()