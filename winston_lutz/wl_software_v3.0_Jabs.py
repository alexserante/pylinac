import pydicom
import os
import os.path
import shutil
import re
import pandas as pd
import tkinter as tk
from tkinter import *
from tkinter.filedialog import askdirectory
from pylinac import WinstonLutz  # pylinac==3.5.0
from datetime import datetime
from pydicom.misc import is_dicom


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

    gantry = [220, 270, 300, 45, 90, 160, 180, 0,
              0, 0, 0, 0, 0, 0, 0,
              0, 0, 0, 0]
    colimator = [0, 0, 0, 0, 0, 0, 0, 0,
                 45, 90, 120, 180, 300, 270, 220,
                 0, 0, 0, 0]
    couch = [0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0,
             45, 90, 315, 270]

    # count the n of files inside directory and check with the expected n
    num_files = 0
    dicom_infos = []

    for folderName, _, files in os.walk(main_path):
        for filename in files:
            print('FILE INSIDE ' + folderName + ': ' + filename)

            if re.search("^gantry", filename):
                text_console = "Imagens já formatadas!"
                message_console(text_console)
                raise ValueError("Imagens já formatadas!")

            if filename == "DICOMDIR":
                os.remove(main_path + "/" + filename)

            if re.search("^[0-9]+", filename):
                # print('FILE INSIDE ' + folderName + ': ' + filename)
                file_path = os.path.join(folderName, filename)
                try:
                    ds = pydicom.dcmread(file_path, stop_before_pixels=True)
                    if (0x0008, 0x0020) in ds:
                        file_time = ds[0x0008, 0x0030].value
                        file_time_formated = datetime.strptime(file_time.split('.')[0], "%H%M%S")
                        dicom_infos.append((file_path, file_time_formated))
                        num_files = num_files + 1
                    else:
                        raise ValueError(f"A imagem {filename}, não contém a tag (0008, 0020) de data.")
                except Exception as e:
                    print(f"Erro ao ler {file_path}: {e}")

    # check n of files with lenght of array gantry
    if num_files != len(gantry):
        text_console = "Número de imagens incorreto!"
        message_console(text_console)
        raise ValueError("Número de imagens incorreto!")

    dicom_infos.sort(key=lambda x: x[1])

    n = 0
    for i, (old_path, time) in enumerate(dicom_infos, start=1):
        new_name = main_path + "/" + "gantry" + \
            str(gantry[n]) + "coll" + str(colimator[n]) + "couch" + str(couch[n]) + ".dcm"
        shutil.move(old_path, new_name)
        print(f"{os.path.basename(old_path)} -> {new_name}")
        n += 1

    print(f"\nTodos os arquivos foram renomeados e copiados para: {main_path}")

    # delete empty folders
    folders = list(os.walk(main_path, topdown=False))
    for folder in folders:
        if not (folder[1] and folder[2]):
            print("Pasta removida: " + folder[0])
            os.rmdir(folder[0])

    # show message concluded
    text_console = "Formatação das imagens concluída"
    message_console(text_console)


def check_images_date():

    n_files = 0
    acquisition_date = set()

    for root, dirs, files in os.walk(main_path):
        for file in files:
            filePath = os.path.join(root, file)
            if is_dicom(filePath):
                ds = pydicom.dcmread(filePath, stop_before_pixels=True)
                if (0x0008, 0x0020) in ds:
                    acquisition_date.add(ds[0x0008, 0x0020].value)
                    n_files += 1
                else:
                    raise ValueError(f"A imagem {file}, não contém a tag (0008, 0020) de data.")

    # check if the dates of images are the same
    if len(acquisition_date) != 1:
        raise ValueError(f"As imagens possuem datas diferentes: {acquisition_date}. Análise cancelada.")
    else:
        images_date = acquisition_date.pop()
        print(f"{n_files} imagens carregadas. Todas do dia {images_date}.")

    return images_date


def analyze_wl():

    global wl
    global wl_shift
    global images_date

    num_files = 0
    for folderName, subfolders, filenames in os.walk(main_path):
        for filename in filenames:
            if re.search("^gantry", filename):
                num_files = num_files + 1

            if re.search("^[0-9]+", filename):
                text_console = "Formatar imagens!"
                message_console(text_console)
                return

    images_date = check_images_date()

    # use_filenames=True necessary to get angles from the name of the files
    wl = WinstonLutz(main_path, use_filenames=True)
    wl.analyze(bb_size_mm=8)
    print(wl.results())

    # show message with the selected path
    lbl_results.config(text=wl.results())
    lbl_shift_bb.config(text="Mover: " + wl.bb_shift_instructions())

    wl_shift = WinstonLutz(main_path, use_filenames=True)
    wl_shift.analyze(bb_size_mm=8, apply_virtual_shift=True)
    lbl_results_shift.config(text=wl_shift.results())

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
    wl.plot_location()


def save_pdf():
    date = datetime.today().strftime("%Y%m%d")
    path = main_path + "/WL-" + date + ".pdf"

    dem_dict = {'Autor': ''}
    dem_dict['Autor'] = name_var.get()
    wl.publish_pdf(filename=path, metadata=dem_dict)

    # show message in console
    text_console = "PDF salvo em: " + path
    message_console(text_console)

    # Register results in txt and excel file
    save_results()


def save_results():
    data = wl.results_data(as_dict=True)

    # Build the summary
    summary_data = {k: v for k, v in data.items() if k not in ["image_details", "keyed_image_details"]}

    # Separate and add the BB shift vector
    bb_shift = summary_data.pop("bb_shift_vector", None)
    if bb_shift:
        summary_data["bb_shift_x_mm"] = round(bb_shift.get("x", 0), 2)
        summary_data["bb_shift_y_mm"] = round(bb_shift.get("y", 0), 2)
        summary_data["bb_shift_z_mm"] = round(bb_shift.get("z", 0), 2)

    # Add new information
    summary_data["images_date"] = datetime.strptime(images_date, "%Y%m%d").strftime("%d/%m/%Y")

    # Create the DataFrame
    # Ensure 'image_date' is the first column
    df = pd.DataFrame([summary_data])
    columns_order = ["images_date"] + [col for col in df.columns if col != "images_date"]
    df = df[columns_order]

    # Salvar ou adicionar ao Excel existente
    if os.path.exists(excel_path):
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            sheet = writer.sheets["resultados"]
            startrow = sheet.max_row
            df.to_excel(writer, sheet_name="resultados", index=False, header=False, startrow=startrow)
    else:
        df.to_excel(excel_path, sheet_name="resultados", index=False)

    print(f"Resultados salvos/adicionados em: {excel_path}")

    df.to_csv(txt_path, sep="\t", index=False, mode="a", header=False)

    # show message in console
    text_console = "Resultados salvos!"
    message_console(text_console)


# ########################################################################### #
#                                                                             #
#                                 MAIN PROGRAM                                #
#                                                                             #
# ########################################################################### #

global excel_path
excel_path = r'G:/ONCORAD/Física Médica/Controles de Qualidade/1 Testes Mensais/WinstonLutz/NAO_DELETAR_wl_results.xlsx'
global txt_path
txt_path = r'G:/ONCORAD/Física Médica/Controles de Qualidade/1 Testes Mensais/WinstonLutz/NAO_DELETAR_wl_results.txt'


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

btn_format_images = tk.Button(master=frm_select_folder,
                              text="Formatar imagens",
                              font="VERDANA",
                              command=format_images).grid(row=1, column=0,
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
    master=frm_right, width=450, height=260, text="Resultados", font="VERDANA")
frm_results.grid(row=0, column=0, sticky='n')
frm_results.grid_propagate(0)

lbl_results = tk.Label(master=frm_results)
lbl_results.grid(row=0, column=0)

frm_shift_bb = tk.LabelFrame(
    master=frm_right, width=450, height=50, text="Shift", font="VERDANA")
frm_shift_bb.grid(row=1, column=0, sticky='n', pady=10)
frm_shift_bb.grid_propagate(0)

lbl_shift_bb = tk.Label(master=frm_shift_bb, text="", fg="Red", font="VERDANA")
lbl_shift_bb.grid(row=0, column=0)

frm_results_shift = tk.LabelFrame(
    master=frm_right, width=450, height=270, text="Resultados (setup error corrigido)", font="VERDANA")
frm_results_shift.grid(row=2, column=0, sticky='n')
frm_results_shift.grid_propagate(0)

lbl_results_shift = tk.Label(master=frm_results_shift)
lbl_results_shift.grid(row=0, column=0)


frm_save_pdf = tk.LabelFrame(
    master=frm_left, text="Salvar resultados", font="VERDANA")
frm_save_pdf.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="w")

name_var = StringVar()
acelerator_var = StringVar()
lbl_name = tk.Label(master=frm_save_pdf, text="Autor: ").grid(row=0, column=0)
entry_name = tk.Entry(master=frm_save_pdf,
                      textvariable=name_var).grid(row=0, column=1)

btn_save_pdf = tk.Button(
    master=frm_save_pdf, text="Salvar PDF", font="VERDANA",
    command=save_pdf).grid(row=0, column=2, padx=10, pady=2)

# Console frame
frm_console = tk.LabelFrame(
    master=window, width=800, height=50, text="Console")
frm_console.grid(row=2, column=0, columnspan=3, sticky="nw", padx=5, pady=20)


window.mainloop()
