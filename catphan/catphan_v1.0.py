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
	global catphan

	if not var_ct_type.get():
		# show message in console
		text_console = "Selecionar tipo de imagem: CT ou CBCT"
		message_console(text_console)
	else:
		catphan = CatPhan503(main_path)
		catphan.analyze()

		# show message in console
		text_console = "Análise concluída!"
		message_console(text_console)

		# show message in the results frame
		lbl_results.config(text=catphan.results())

		print(catphan.results())

def show_images():
	catphan.plot_analyzed_image()

def save_pdf():
	date = datetime.today().strftime("%Y%m%d")
	path = date + "_catphan_" + var_ct_type.get() + var_preset_type.get() + ".pdf"

	catphan.publish_pdf(filename=path)

	# show message in console
	text_console = "PDF salvo em: " + path
	message_console(text_console)



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
frm_perform_analysis.grid(row=1, column=0, padx=10, pady=5)

var_ct_type = StringVar()
rbtn_wl_type_1 = tk.Radiobutton(
    master=frm_perform_analysis, text="CT",
    variable=var_ct_type, value="CT").grid(row=0, column=0)
rbtn_wl_type_2 = tk.Radiobutton(
    master=frm_perform_analysis, text="CBCT",
    variable=var_ct_type, value="CBCT").grid(row=0, column=1)

btn_perform_analysis = tk.Button(
    master=frm_perform_analysis, text="Fazer análise", font="VERDANA",
    command=analyze_catphan).grid(row=1, column=0, padx=10, pady=5)

btn_show_images = tk.Button(
    master=frm_perform_analysis, text="Plotar imagens", font="VERDANA",
    command=show_images).grid(row=2, column=0, padx=10, pady=5)

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


# Save pdf frame
frm_save_pdf = tk.LabelFrame(
    master=frm_left, text="Salvar resultados", font="VERDANA")
frm_save_pdf.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="w")

var_preset_type = StringVar()
lbl_name = tk.Label(master=frm_save_pdf, text="Preset: ").grid(row=0, column=0)
entry_name = tk.Entry(master=frm_save_pdf,
                      textvariable=var_preset_type).grid(row=0, column=1)

btn_save_pdf = tk.Button(
    master=frm_save_pdf, text="Salvar PDF", font="VERDANA",
    command=save_pdf).grid(row=0, column=2, padx=10, pady=2)


# Console frame
frm_console = tk.LabelFrame(
    master=window, width=500, height=50, text="Console")
frm_console.grid(row=2, column=0, columnspan=3, sticky="nw", padx=5, pady=20)


window.mainloop()