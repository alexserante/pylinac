import os
import os.path
import shutil
import re
import tkinter as tk
from tkinter import *
from tkinter.filedialog import askdirectory
from pylinac import WinstonLutz  # pylinac==3.5.0
from datetime import datetime


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


def format_images():

    # positions of gantry, col and couch
    if not str(var_wl_type.get()):
        text_console = "Selecione o tipo de WL: Completo ou Básico"
        message_console(text_console)
        return
    else:
        if str(var_wl_type.get()) == "Completo":
            gantry = [0, 30, 45, 90, 150, 180, 320, 270, 220,
                      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            colimator = [0, 0, 0, 0, 0, 0, 0, 0, 0, 30, 45,
                         90, 150, 180, 320, 270, 220, 0, 0, 0, 0, 0, 0]
            couch = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 30, 45, 90, 330, 315, 270]
        if str(var_wl_type.get()) == "Básico":
            gantry = [0, 90, 180, 270, 0, 0, 0, 0]
            colimator = [0, 0, 0, 0, 90, 270, 0, 0]
            couch = [0, 0, 0, 0, 0, 0, 90, 270]

    # count the n of files inside directory and check with the expected n
    num_files = 0
    for folderName, subfolders, filenames in os.walk(main_path):
        for filename in filenames:
            if re.search("^gantry", filename):
                # print("Imagens já formatadas!")
                text_console = "Imagens já formatadas!"
                message_console(text_console)
                return
            if re.search("^[0-9]+", filename):
                # print('FILE INSIDE ' + folderName + ': ' + filename)
                num_files = num_files + 1
    print(num_files)

    if num_files != len(gantry):
        text_console = "Número de imagens incorreto!"
        message_console(text_console)
        # print("Número de imagens incorreto!")
        return

    # move the files to the main path
    n = 0
    for folderName, subfolders, filenames in os.walk(main_path):
        for filename in filenames:
            print('FILE INSIDE ' + folderName + ': ' + filename)

            if filename == "DICOMDIR":
                os.remove(main_path + "/" + filename)

            if filename != "DICOMDIR":
                file_path = folderName + '/' + filename

                print('MOVED TO: ' + main_path + "/" + "gantry" +
                      str(gantry[n]) + "coll" + str(colimator[n]) +
                      "couch" + str(couch[n]) + ".dcm" + "\n")

                shutil.move(file_path, main_path + "/" + "gantry" +
                            str(gantry[n]) + "coll" + str(colimator[n]) +
                            "couch" + str(couch[n]) + ".dcm")
                n = n + 1

    # delete empty folders
    folders = list(os.walk(main_path, topdown=False))
    for folder in folders:
        if not (folder[1] and folder[2]):
            print("Pasta removida: " + folder[0])
            os.rmdir(folder[0])

    # show message concluded
    text_console = "Formatação das imagens concluída"
    message_console(text_console)


def analyze_wl():

    global wl

    # use_filenames=True necessary to get angles from the name of the files
    wl = WinstonLutz(main_path, use_filenames=True)
    wl.analyze(bb_size_mm=8)
    print(wl.results())
    # show message with the selected path
    lbl_results.config(text=wl.results())
    lbl_shift_bb.config(text="Mover: " + wl.bb_shift_instructions())

    # show message in console
    text_console = "Análise concluída!"
    message_console(text_console)


def show_images_gantry():
    wl.plot_images(axis="Gantry")


def show_images_col():
    wl.plot_images(axis="Collimator")


def show_images_couch():
    wl.plot_images(axis="Couch")


def show_plots():
    wl.plot_summary()


def save_pdf():
    date = datetime.today().strftime("%Y%m%d")
    path = main_path + "/WL-" + date + ".pdf"

    dem_dict = {'Autor': '', 'Acelerador': ''}
    dem_dict['Autor'] = name_var.get()
    dem_dict['Acelerador'] = acelerator_var.get()
    wl.publish_pdf(filename=path, metadata=dem_dict)

    # show message in console
    text_console = "PDF salvo em: " + path
    message_console(text_console)


def save_results():
    shift_vector = [round(wl.bb_shift_vector.x, 3), round(
        wl.bb_shift_vector.y, 3), round(wl.bb_shift_vector.z, 3)]

    with open("L:/Radioterapia/Fisicos/Controle_Qualidade/WL/AL06_WL.txt", "a") as f:
        f.write(datetime.today().strftime("%Y%m%d") + " ")
        for a in shift_vector:
            f.write(str(a) + " ")
        f.write("\n")

    # show message in console
    text_console = "Resultados salvos!"
    message_console(text_console)


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
                              text="Selecionar pasta", font="VERDANA",
                              command=open_files_path).grid(row=0, column=0,
                                                            columnspan=2, padx=10, pady=5)

lbl_wl_type = tk.Label(master=frm_select_folder,
                       text="Tipo WL:").grid(row=1, column=0, sticky="w")

var_wl_type = StringVar()
rbtn_wl_type_1 = tk.Radiobutton(
    master=frm_select_folder, text="Completo \n(23 imagens)",
    variable=var_wl_type, value="Completo").grid(row=3, column=0)
rbtn_wl_type_2 = tk.Radiobutton(
    master=frm_select_folder, text="Básico \n(8 imagens)",
    variable=var_wl_type, value="Básico").grid(row=3, column=1)

btn_format_images = tk.Button(master=frm_select_folder,
                              text="Formatar imagens",
                              font="VERDANA",
                              command=format_images).grid(row=5, column=0,
                                                          columnspan=2, padx=10, pady=5)


frm_perform_analysis = tk.LabelFrame(
    master=frm_left, text="Análise WL", font="VERDANA")
frm_perform_analysis.grid(row=0, column=1, padx=10, pady=5)

btn_perform_analysis = tk.Button(
    master=frm_perform_analysis, text="Fazer análise WL", font="VERDANA",
    command=analyze_wl).grid(row=0, column=0, padx=10, pady=5)

btn_plot_summary = tk.Button(
    master=frm_perform_analysis, text="Plotar gráficos", font="VERDANA",
    command=show_plots).grid(row=2, column=0, padx=10, pady=5)


frm_images = tk.LabelFrame(master=frm_left, text="Imagens", font="VERDANA")
frm_images.grid(row=1, column=0, columnspan=2, padx=20, pady=5)

btn_gantry_images = tk.Button(
    master=frm_images, text="Gantry", font="VERDANA",
    command=show_images_gantry).grid(row=0, column=0, padx=10, pady=5)
btn_collimator_images = tk.Button(
    master=frm_images, text="Colimador", font="VERDANA",
    command=show_images_col).grid(row=0, column=1, padx=10, pady=5)
btn_couch_images = tk.Button(
    master=frm_images, text="Mesa", font="VERDANA",
    command=show_images_couch).grid(row=0, column=2, padx=10, pady=5)


frm_right = tk.Frame(master=window)
frm_right.grid(row=0, column=1, sticky="n")

frm_results = tk.LabelFrame(
    master=frm_right, width=435, height=250, text="Resultados", font="VERDANA")
frm_results.grid(row=0, column=3, sticky='n')
frm_results.grid_propagate(0)

lbl_results = tk.Label(master=frm_results)
lbl_results.grid(row=0, column=0)

frm_shift_bb = tk.LabelFrame(
    master=frm_right, width=435, height=50, text="Shift", font="VERDANA")
frm_shift_bb.grid(row=1, column=3, sticky='n', pady=10)
frm_shift_bb.grid_propagate(0)

lbl_shift_bb = tk.Label(master=frm_shift_bb, text="", fg="Red", font="VERDANA")
lbl_shift_bb.grid(row=0, column=0)


frm_save_pdf = tk.LabelFrame(
    master=frm_left, text="Salvar resultados", font="VERDANA")
frm_save_pdf.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="w")

name_var = StringVar()
acelerator_var = StringVar()
lbl_name = tk.Label(master=frm_save_pdf, text="Autor: ").grid(row=0, column=0)
entry_name = tk.Entry(master=frm_save_pdf,
                      textvariable=name_var).grid(row=0, column=1)
lbl_acelerador = tk.Label(
    master=frm_save_pdf, text="Acelerador: ").grid(row=1, column=0, rowspan=2, sticky="nw")
entry_acelerator = tk.Entry(
    master=frm_save_pdf, textvariable=acelerator_var, width=3).grid(row=1, column=1, rowspan=2, sticky="nw")

btn_save_pdf = tk.Button(
    master=frm_save_pdf, text="Salvar PDF", font="VERDANA",
    command=save_pdf).grid(row=0, column=2, padx=10, pady=2)

btn_save_results = tk.Button(
    master=frm_save_pdf, text="Registrar resultado", font="VERDANA",
    command=save_results).grid(row=1, column=2, padx=10, pady=5)


# Console frame
frm_console = tk.LabelFrame(
    master=window, width=800, height=50, text="Console")
frm_console.grid(row=2, column=0, columnspan=3, sticky="nw", padx=5, pady=20)


window.mainloop()
