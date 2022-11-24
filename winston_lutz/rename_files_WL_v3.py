import os
import os.path
import shutil
import tkinter as tk
from tkinter.filedialog import askdirectory
from pylinac import WinstonLutz


def handle_click(event):

    # user select the directory of the images
    main_path = askdirectory(title='Select folder')
    if not main_path:
        print("Nenhuma pasta selecionada!")
        return

    # positions of gantry, col and couch
    gantry = [0, 90, 180, 270, 0, 0, 0, 0]
    colimator = [0, 0, 0, 0, 90, 270, 0, 0]
    couch = [0, 0, 0, 0, 0, 0, 90, 270]

    n = 0
    for folderName, subfolders, filenames in os.walk(main_path):
        for filename in filenames:
            print('FILE INSIDE ' + folderName + ': ' + filename)

            if filename == "DICOMDIR":
                os.remove(folderName + '/' + filename)

            if filename != "DICOMDIR":
                file_path = folderName + '/' + filename

                print('MOVED TO: ' + main_path + "/" + "gantry" +
                      str(gantry[n]) + "coll" + str(colimator[n]) +
                      "couch" + str(couch[n]) + ".dcm" + "\n")
                
                # move the file to the main path
                shutil.move(file_path, main_path + "/" + "gantry" +
                            str(gantry[n]) + "coll" + str(colimator[n]) +
                            "couch" + str(couch[n]) + ".dcm")
                n = n + 1

    '''# print files in main_path
        onlyfiles = [f for f in os.listdir(
        main_path) if os.path.isfile(os.path.join(main_path, f))]
    print(onlyfiles)'''

    # show message concluded
    lbl_concluded = tk.Label(master=frm_select_folder,
                             text="Formatação das imagens concluída")
    lbl_concluded.grid()


# ########################################################## #
#                                                            #
#                         MAIN PROGRAM                       #
#                                                            #
# ########################################################## #


window = tk.Tk()


# Frame to select folder where the dcm images are
frm_select_folder = tk.LabelFrame(
    master=window, text="Select folder", font="VERDANA")
frm_select_folder.grid(row=0, column=0)

lbl_select_folder = tk.Label(
    master=frm_select_folder, text="Clique no botão para selecionar a pasta", font="VERDANA")
lbl_select_folder.grid(row=0, column=0)

button = tk.Button(master=frm_select_folder,
                   text="Selecionar pasta", font="VERDANA")
button.bind("<Button-1>", handle_click)
button.grid(row=1, column=0)

# Frame to choose from which LINAC the WL was run
frm_select_linac = tk.Frame(master=window, borderwidth=1, relief="raised")
frm_select_linac.grid(row=0, column=1)

var_linac = ""
rbtn_linac_4 = tk.Radiobutton(
    master=frm_select_linac, text="AL4", variable=var_linac, value="AL4")
rbtn_linac_5 = tk.Radiobutton(
    master=frm_select_linac, text="AL5", variable=var_linac, value="AL5")
rbtn_linac_6 = tk.Radiobutton(
    master=frm_select_linac, text="AL6", variable=var_linac, value="AL6")
rbtn_linac_4.grid(row=0, column=0)
rbtn_linac_5.grid(row=1, column=0)
rbtn_linac_6.grid(row=2, column=0)

frm_perform_analysis = tk.LabelFrame(
    master=window, text="WL analysis", font="VERDANA")
frm_perform_analysis.grid(row=0, column=2)

btn_perform_analysis = tk.Button(
    master=frm_perform_analysis, text="Fazer análise WL", font="VERDANA")
btn_perform_analysis.grid(row=0, column=0)

window.mainloop()
