import pydicom
import sys
import tkinter as tk
import os
import pandas as pd
from tkinter import *
from tkinter.filedialog import askdirectory, askopenfilename
from datetime import datetime
from PIL import Image, ImageTk
from pylinac import (
    CatPhan503, LeedsTOR, ElektaLasVegas
)
from pydicom.misc import is_dicom


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


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


def analyze_catphan():
    # necessary to use this variable in other functions
    global catphan
    global mainPath
    global filePath

    filePath = openImage()
    mainPath = os.path.dirname(filePath)

    catphan = CatPhan503(mainPath)
    catphan.analyze()

    print(catphan.results(as_list=True))

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
    leeds.analyze(low_contrast_threshold=0.01, high_contrast_threshold=0.5)

    # show message in console
    text_console = "Análise concluída!"
    message_console(text_console)

    # show message in the results frame
    lbl_results.config(text=leeds.results())
    # show images
    leeds.plot_analyzed_image()


def analyze_lasvegas():
    global lasvegas
    global filePath

    filePath = openImage()

    lasvegas = ElektaLasVegas(filePath)
    lasvegas.analyze(angle_override=-90)

    # show message in console
    text_console = "Análise concluída!"
    message_console(text_console)

    # show message in the results frame
    lbl_results.config(text=lasvegas.results())
    # show images
    lasvegas.plot_analyzed_image()


def save_pdf_catphan():
    txt_path = r'R:/ONCORAD/Física Médica/Controles de Qualidade/3 Testes Semestrais/NAO_DELETAR_catphan_results.txt'
    excel_path = r'R:/ONCORAD/Física Médica/Controles de Qualidade/3 Testes Semestrais/NAO_DELETAR_catphan_results.xlsx'

    folder_path = mainPath

    date = datetime.today().strftime("%Y%m%d")
    filename = date + "_Catphan503_" + ".pdf"

    full_path = os.path.join(folder_path, filename)

    catphan.publish_pdf(filename=full_path)

    # show message in console
    text_console = "PDF salvo em: " + full_path
    message_console(text_console)

    '''if is_dicom(filePath):
        ds = pydicom.dcmread(filePath, stop_before_pixels=True)
        if (0x0008, 0x0020) in ds:
            image_date = ds[0x0008, 0x0020].value

    data = catphan.results(as_list=True)
    register_results(data, image_date, txt_path, excel_path)'''


def save_pdf_leedstor():
    txt_path = r'R:/ONCORAD/Física Médica/Controles de Qualidade/3 Testes Semestrais/NAO_DELETAR_leedstor_results.txt'
    excel_path = r'R:/ONCORAD/Física Médica/Controles de Qualidade/3 Testes Semestrais/NAO_DELETAR_leedstor_results.xlsx'

    folder_path = os.path.dirname(filePath)

    date = datetime.today().strftime("%Y%m%d")
    filename = date + "_LeedsTOR_" + ".pdf"

    full_path = os.path.join(folder_path, filename)

    leeds.publish_pdf(filename=full_path)

    # show message in console
    text_console = "PDF salvo em: " + full_path
    message_console(text_console)

    '''if is_dicom(filePath):
        ds = pydicom.dcmread(filePath, stop_before_pixels=True)
        if (0x0008, 0x0020) in ds:
            image_date = ds[0x0008, 0x0020].value

    data = leeds.results(as_list=True)
    register_results(data, image_date, txt_path, excel_path)'''


def save_pdf_lasvegas():
    txt_path = r'R:/ONCORAD/Física Médica/Controles de Qualidade/3 Testes Semestrais/NAO_DELETAR_lasvegas_results.txt'
    excel_path = r'R:/ONCORAD/Física Médica/Controles de Qualidade/3 Testes Semestrais/NAO_DELETAR_lasvegas_results.xlsx'

    folder_path = os.path.dirname(filePath)

    date = datetime.today().strftime("%Y%m%d")
    filename = date + "_LasVegas_" + ".pdf"

    full_path = os.path.join(folder_path, filename)

    lasvegas.publish_pdf(filename=full_path)

    # show message in console
    text_console = "PDF salvo em: " + full_path
    message_console(text_console)

    '''if is_dicom(filePath):
        ds = pydicom.dcmread(filePath, stop_before_pixels=True)
        if (0x0008, 0x0020) in ds:
            image_date = ds[0x0008, 0x0020].value

    data = lasvegas.results(as_list=True)
    register_results(data, image_date, txt_path, excel_path)'''


def register_results(data, image_date, txt_path, excel_path):
    # Build the summary
    summary_data = {}

    for item in data:
        if ":" in item:
            key, value = item.split(":", 1)
            summary_data[key.strip()] = value.strip()

    # Add new information
    summary_data["image_date"] = datetime.strptime(image_date, "%Y%m%d").strftime("%d/%m/%Y")
    summary_data["comment"] = comment_var_leedstor.get()

    # Create the DataFrame
    # Ensure 'image_date' is the first column
    df = pd.DataFrame([summary_data])
    columns_order = ["image_date"] + [col for col in df.columns if col != "image_date"]
    df = df[columns_order]

    # Salvar ou adicionar ao Excel existente
    if os.path.exists(excel_path):
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            sheet = writer.sheets["resultados"]
            startrow = sheet.max_row
            df.to_excel(writer, sheet_name="resultados", index=False, header=True, startrow=startrow)
    else:
        df.to_excel(excel_path, sheet_name="resultados", index=False)

    df.to_csv(txt_path, sep="\t", index=False, mode="a", header=True)

    # show message in console
    text_console = "Resultados salvos!"
    message_console(text_console)


# ########################################################################### #
#                                                                             #
#                                 MAIN PROGRAM                                #
#                                                                             #
# ########################################################################### #

global txt_path

window = tk.Tk()

frm_left = tk.Frame(master=window)
frm_left.grid(row=0, column=0, sticky="n")

# LEFT FRAME
# CATPHAN
frm_catphan = tk.LabelFrame(
    master=frm_left, text="Catphan503", font="VERDANA")
frm_catphan.grid(row=0, column=0, padx=10, pady=5)

image = Image.open(resource_path("catphan.jpg"))
image_catphan_for_tk = ImageTk.PhotoImage(image)
lbl_image = tk.Label(frm_catphan, image=image_catphan_for_tk)
lbl_image.grid(row=0, column=0)

btn_analysis_catphan = tk.Button(
    master=frm_catphan, text="Selecionar imagem", font="VERDANA",
    command=analyze_catphan).grid(row=0, column=1, padx=10, pady=5, columnspan=2)

comment_var_catphan = StringVar()
lbl_comment = tk.Label(master=frm_catphan,
                       text="Comentário: ").grid(row=1, column=0, sticky='e')
entry_comment = tk.Entry(master=frm_catphan,
                         textvariable=comment_var_catphan).grid(row=1, column=1)

btn_save_pdf = tk.Button(
    master=frm_catphan, text="Salvar PDF", font="VERDANA",
    command=save_pdf_catphan).grid(row=1, column=2, padx=10, pady=2)

# LeedsTOR
frm_leedstor = tk.LabelFrame(
    master=frm_left, text="LeedsTOR", font="VERDANA")
frm_leedstor.grid(row=1, column=0, padx=10, pady=5)

image = Image.open(resource_path("leedstor.jpg"))
image_leedstor_for_tk = ImageTk.PhotoImage(image)
lbl_image = tk.Label(frm_leedstor, image=image_leedstor_for_tk)
lbl_image.grid(row=0, column=0)

btn_analysis_leedstor = tk.Button(
    master=frm_leedstor, text="Selecionar imagem", font="VERDANA",
    command=analyze_leedstor).grid(row=0, column=1, padx=10, pady=5, columnspan=2)

comment_var_leedstor = StringVar()
lbl_comment = tk.Label(master=frm_leedstor,
                       text="Comentário: ").grid(row=1, column=0, sticky='e')
entry_comment = tk.Entry(master=frm_leedstor,
                         textvariable=comment_var_leedstor).grid(row=1, column=1)

btn_save_pdf = tk.Button(
    master=frm_leedstor, text="Salvar PDF", font="VERDANA",
    command=save_pdf_leedstor).grid(row=1, column=2, padx=10, pady=2)

# Elekta Las Vegas
frm_lasvegas = tk.LabelFrame(
    master=frm_left, text="Las Vegas", font="VERDANA")
frm_lasvegas.grid(row=2, column=0, padx=10, pady=5)

image = Image.open(resource_path("lasvegas.jpg"))
image_lasvegas_for_tk = ImageTk.PhotoImage(image)
lbl_image = tk.Label(frm_lasvegas, image=image_lasvegas_for_tk)
lbl_image.grid(row=0, column=0)

btn_analysis_lasvegas = tk.Button(
    master=frm_lasvegas, text="Selecionar imagem", font="VERDANA",
    command=analyze_lasvegas).grid(row=0, column=1, padx=10, pady=5, columnspan=2)

comment_var_lasvegas = StringVar()
lbl_comment = tk.Label(master=frm_lasvegas,
                       text="Comentário: ").grid(row=1, column=0, sticky='e')
entry_comment = tk.Entry(master=frm_lasvegas,
                         textvariable=comment_var_lasvegas).grid(row=1, column=1)

btn_save_pdf = tk.Button(
    master=frm_lasvegas, text="Salvar PDF", font="VERDANA",
    command=save_pdf_lasvegas).grid(row=1, column=2, padx=10, pady=2)

# RIGHT FRAME
frm_right = tk.Frame(master=window)
frm_right.grid(row=0, column=1, sticky="n")

# Results frame
frm_results = tk.LabelFrame(
    master=frm_right, width=500, height=450, text="Resultados", font="VERDANA")
frm_results.grid(row=0, column=0, sticky='n')
frm_results.grid_propagate(0)

lbl_results = tk.Label(master=frm_results)
lbl_results.grid(row=0, column=0)

# Console frame
frm_console = tk.LabelFrame(
    master=window, width=500, height=50, text="Console")
frm_console.grid(row=2, column=0, columnspan=3, sticky="nw", padx=5, pady=20)


window.mainloop()
