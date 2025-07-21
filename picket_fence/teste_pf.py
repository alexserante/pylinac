#######################################################
# William A. P. dos Santos                            #
# william.wapsantos@gmail.com                         #
# Interface para análise do picket fence              #
# 14 de julho de 2020                                 #
#######################################################

# gerar executável
# pyinstaller --onefile --paths=C:\\Users\\willi\\AppData\\Local\\Programs\\Python\\Python38-32\\Lib\\site-packages\\skimage\\feature --icon=Imagens/dirac_eqn.ico --additional-hooks-dir=. interface_picket_fence.py


from tkinter import *
from PIL import ImageTk, Image
from tkinter import filedialog, messagebox
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pydicom
import numpy as np
from PIL.TiffTags import TAGS
#import ConvertToDicom
from pylinac import PicketFence
from tkinter import scrolledtext
import subprocess


def teste():
  return


def atualiza_criterios():
  global tolerancia, limite_acao

  try:
    temp1 = float(tolerancia_entry.get())
    temp2 = float(limite_acao_entry.get())
    if temp1 < temp2:
      messagebox.showerror("Valores inválidos",
                           "Valores inválidos.\nLimite de ação deve ser menor que a tolerância.\nNão foi possível atualizar os critérios de análise.")
      toplevel_criterios.destroy()
    elif temp1 < 0 or temp2 < 0:
      messagebox.showerror(
          "Valores inválidos", "Valores inválidos.\nOs valores fornecidos devem ser números reais positivos.\nNão foi possível atualizar os critérios de análise.")
      toplevel_criterios.destroy()
    else:
      tolerancia = temp1
      limite_acao = temp2
      toplevel_criterios.destroy()
  except:
    messagebox.showerror(
        "Valores inválidos", "Valores inválidos.\nOs valores fornecidos devem ser números reais positivos.\nNão foi possível atualizar os critérios de análise.")
    toplevel_criterios.destroy()


def criterios():
  global tolerancia_entry, limite_acao_entry
  global toplevel_criterios

  toplevel_criterios = Toplevel()
  toplevel_criterios.title('Critérios de análise')
  toplevel_criterios.iconbitmap('./Imagens/dirac_eqn.ico')

  tolerancia_label = Label(toplevel_criterios, text="Tolerância (mm):", justify=LEFT)
  limite_acao_label = Label(toplevel_criterios, text="Limite de ação (mm):", justify=LEFT)

  tolerancia_entry = Entry(toplevel_criterios, width=8, borderwidth=5)
  tolerancia_entry.insert(0, tolerancia)
  limite_acao_entry = Entry(toplevel_criterios, width=8, borderwidth=5)
  limite_acao_entry.insert(0, limite_acao)

  btn_atualizar_criterios = Button(toplevel_criterios, text="Atualizar Valores", command=atualiza_criterios)
  btn_fechar_criterios = Button(toplevel_criterios, text="Fechar", command=toplevel_criterios.destroy)

  tolerancia_label.grid(row=0, column=0, padx=5, pady=5)
  tolerancia_entry.grid(row=0, column=1, padx=5, pady=5)
  limite_acao_label.grid(row=1, column=0, padx=5, pady=5)
  limite_acao_entry.grid(row=1, column=1, padx=5, pady=5)
  btn_atualizar_criterios.grid(row=2, column=0, padx=5, pady=5)
  btn_fechar_criterios.grid(row=2, column=1, padx=5, pady=5)


def opcoes_exibicao():
  global toplevel_opcoes_exibicao

  toplevel_opcoes_exibicao = Toplevel()
  # toplevel_opcoes_exibicao.geometry("300x150")
  toplevel_opcoes_exibicao.title('Opções de exibição do resultado')
  toplevel_opcoes_exibicao.iconbitmap('./Imagens/dirac_eqn.ico')

  lista_label_opcoes = ['Guard rails', 'MLC mlc_peaks', 'Overlay', 'Leaf error subplot']
  lista_checkbox_opcoes = []

  for i in range(0, 4):
    checkbox_temp = Checkbutton(toplevel_opcoes_exibicao, text=lista_label_opcoes[i], variable=lista_opcoes_exibicao[i], onvalue=True, offvalue=False)
    lista_checkbox_opcoes.append(checkbox_temp)
    if lista_opcoes_exibicao[i].get():
      lista_checkbox_opcoes[i].select()
    else:
      lista_checkbox_opcoes[i].deselect()

    lista_checkbox_opcoes[i].grid(row=0, column=i, padx=5, pady=5, sticky=W)

  btn_fechar_opcoes = Button(toplevel_opcoes_exibicao, text="Fechar", command=toplevel_opcoes_exibicao.destroy)
  btn_fechar_opcoes.grid(row=1, column=0, padx=5, pady=5, sticky=W + E, columnspan=4)


def on_closing():
  if messagebox.askyesno("Sair", "Deseja fechar o programa?"):
    root.quit()


def atualizar_parametros(lista_entry, dpi):
  global gantry, colimador, sad, sid, x_res, translacao
  global toplevel_importar, x_res_entry

  try:
    gantry = float(lista_entry[0][0].get())
    colimador = float(lista_entry[1][0].get())
    sad = float(lista_entry[2][0].get())
    sid = float(lista_entry[3][0].get())
    x_res = (sid / sad) / (dpi / 25.4)
    x_res_str = f"{x_res:2.3f}"
    x_res_entry.config(state=NORMAL)
    x_res_entry.delete(0, END)
    x_res_entry.insert(0, x_res_str)
    x_res_entry.config(state=DISABLED)
    translacao = [float(lista_entry[5][0].get()), float(lista_entry[6][0].get())]
  except:
    messagebox.showerror("Erro", "Valores inválidos")


def importar_dados(eh_dicom, filename):
  global gantry, colimador, sad, sid, x_res, translacao
  global toplevel_importar, nome_dcm, btn_analisar
  global btn_salvar, btn_imprimir

  if analisou:
    fnc_limpar()

  if eh_dicom:
    nome_dcm = filename
  else:
    caminho, nome = os.path.split(os.path.splitext(filename)[0])
    nome_teste = 'Picket Fence'
    id_teste = 'Picket Fence'
    if os.path.isdir(caminho + '/PF_Dicom'):
      nome_dcm = caminho + '/PF_Dicom/' + nome + '_pfDicom.dcm'
    else:
      try:
        os.mkdir(caminho + '/PF_Dicom')
        nome_dcm = caminho + '/PF_Dicom/' + nome + '_pfDicom.dcm'
      except:
        nome_dcm = caminho + '/' + nome + '_pfDicom.dcm'
    ConvertToDicom.convert(nome_teste, id_teste, filename, nome_dcm, translacao, sad, sid, gantry, colimador)
  messagebox.showinfo("Arquivo importado", "Arquivo importado com sucesso.")
  btn_salvar.config(state=DISABLED)
  btn_imprimir.config(state=DISABLED)
  btn_analisar.config(state=NORMAL)
  menu_arquivo.entryconfig(2, state=NORMAL)
  menu_arquivo.entryconfig(4, state=DISABLED)
  menu_arquivo.entryconfig(5, state=DISABLED)
  toplevel_importar.destroy()


def janela_importar_img(eh_dicom):  # Importa imagem a ser analisada
  global gantry, colimador, sad, sid, x_res, translacao
  global toplevel_importar, x_res_entry

  importou = False
  if eh_dicom:
    tipos = (("Imagens DICOM", "*.dcm"), ("Todos os arquivos", "*.*"))
    #nome_arquivo = "./PF_Dicom/5mm-00Y1x20Y2-1MU_pfDicom.dcm"
  else:
    tipos = (("Imagens TIFF", "*.tif"), ("Todos os arquivos", "*.*"))
    #nome_arquivo = "./G0C0Y1.tif"
  nome_arquivo = filedialog.askopenfilename(initialdir='./',
                                            title="Selecione o arquivo", filetypes=tipos)
  if nome_arquivo != "":
    if eh_dicom:
      try:  # Abrir arquivo dicom
        ds = pydicom.filereader.read_file(nome_arquivo)
        image_array = ds.pixel_array
        try:
          gantry = ds[0x300A, 0x011E].value
        except:
          gantry = 0.0
        try:
          colimador = ds[0x300A, 0x0120].value
        except:
          colimador = 0.0
        try:
          translacao = ds[0x3002, 0x000D].value
        except:
          translacao = [0.0, 0.0]
        try:
          sad = ds[0x3002, 0x0022].value
          sid = ds[0x3002, 0x0026].value
          x_res = ds[0x3002, 0x0011].value[0]
          x_res_str = x_res
          dpmm = (1 / x_res) * sid / sad  # pontos por mm no isocentro
          translacao = [translacao[0] / dpmm, translacao[1] / dpmm]  # deslocamento em mm no painel
        except:
          messagebox.showwarning("Aviso", "Imagem não possui informações importantes para o teste")
        importou = True
      except:
        messagebox.showwarning("Aviso", "Não foi possível abrir o arquivo selecionado")
    else:
      try:  # Abrir arquivo TIFF
        tiff_file = Image.open(nome_arquivo)
        image_array = np.array(tiff_file)
        tiff_meta_dict = {TAGS[key]: tiff_file.tag[key] for key in tiff_file.tag.keys()}
        gantry = 0.0
        colimador = 0.0
        sad = 1000.0
        sid = 1600.0
        try:
          dpi = (tiff_meta_dict['YResolution'][0][0] / tiff_meta_dict['YResolution'][0][1])  # dpi projetada no isocentro para imagens do Iview
          x_res = (sid / sad) / (dpi / 25.4)  # distancia entre detectores no SID (Ex.: 160 cm no Synergy Full com Iview)
          x_res_str = f"{x_res:2.3f}"
        except:
          dpi = 75  # se não encontra resolução, assume uma resolução de 75dpi
          x_res = (sid / sad) / (dpi / 25.4)
          x_res_str = f"{x_res:2.3f}"
        translacao = [0.0, 0.0]
        importou = True
      except:
        messagebox.showwarning("Aviso", "Não foi possível abrir o arquivo selecionado")

    if importou:  # cria a janela de importação com informações pertinentes
      toplevel_importar = Toplevel()
      toplevel_importar.title('Importar imagem')
      #toplevel_importar.iconbitmap('./Imagens/dirac_eqn.ico')

      arquivo_label = Label(toplevel_importar, text="Imagem: " + nome_arquivo, justify=LEFT)
      gantry_label = Label(toplevel_importar, text="Gantry:", justify=LEFT)
      colimador_label = Label(toplevel_importar, text="Colimador:", justify=LEFT)
      sad_label = Label(toplevel_importar, text="SAD (mm):", justify=LEFT)
      sid_label = Label(toplevel_importar, text="SID (mm):", justify=LEFT)
      x_res_label = Label(toplevel_importar, text="Espaçamento entre pixels (mm):", justify=CENTER)
      translacao_x_label = Label(toplevel_importar, text="translacao do painel em x (mm):", justify=LEFT)
      translacao_y_label = Label(toplevel_importar, text="translacao do painel em y (mm):", justify=LEFT)

      gantry_entry = Entry(toplevel_importar, width=8, borderwidth=5)
      colimador_entry = Entry(toplevel_importar, width=8, borderwidth=5)
      sad_entry = Entry(toplevel_importar, width=8, borderwidth=5)
      sid_entry = Entry(toplevel_importar, width=8, borderwidth=5)
      x_res_entry = Entry(toplevel_importar, width=8, borderwidth=5)
      translacao_x_entry = Entry(toplevel_importar, width=8, borderwidth=5)
      translacao_y_entry = Entry(toplevel_importar, width=8, borderwidth=5)

      lista_entry = [[gantry_entry, gantry],
                     [colimador_entry, colimador],
                     [sad_entry, sad],
                     [sid_entry, sid],
                     [x_res_entry, x_res_str],
                     [translacao_x_entry, translacao[0]],
                     [translacao_y_entry, translacao[1]]]

      lin = 0
      for entry_item in lista_entry:
        entry_item[0].grid(row=lin, column=5)
        entry_item[0].insert(0, entry_item[1])
        lin += 1
      x_res_entry.config(state=DISABLED)

      lin = 0
      lista_label = [gantry_label, colimador_label, sad_label, sid_label, x_res_label, translacao_x_label, translacao_y_label]
      for label_item in lista_label:
        label_item.grid(row=lin, column=4)
        lin += 1

      fig = plt.Figure()
      fig.add_subplot(111).imshow(image_array)
      pf_img = FigureCanvasTkAgg(fig, toplevel_importar)
      pf_img.draw()
      pf_img.get_tk_widget().grid(row=1, column=0, rowspan=5, columnspan=3)

      arquivo_label.grid(row=0, column=0, columnspan=3)
      if eh_dicom:
        status_atualizar = DISABLED
      else:
        status_atualizar = NORMAL
      Button(toplevel_importar, text='Atualizar parâmetros', command=lambda: atualizar_parametros(
          lista_entry, dpi), state=status_atualizar).grid(row=7, column=0)
      Button(toplevel_importar, text='Importar', command=lambda: importar_dados(eh_dicom, nome_arquivo)).grid(row=7, column=1)
      Button(toplevel_importar, text='Cancelar', command=toplevel_importar.destroy).grid(row=7, column=2)

  else:
    messagebox.showwarning("Aviso", "Arquivo não selecionado")


def analisar_pf():
  global label_resultado, frame_imagem, frame_texto_analise, analisou
  global btn_salvar, btn_imprimir, pf

  try:
    pf = PicketFence(nome_dcm)
    pf.analyze(mlc_model=mlc_selecionado.get(), tolerance=tolerancia, action_tolerance=limite_acao, orientation=orientacao.get())

    if analisou:
      frame_texto_analise.destroy()
    frame_texto_analise = LabelFrame(root, text="Descrição do resultado", height=60, width=190)
    frame_texto_analise.grid(row=3, column=4, padx=30, pady=20, sticky=W, rowspan=10)

    label_resultado = Label(frame_texto_analise, text=pf.results(), justify=LEFT)
    label_resultado.grid(row=0, column=0)

    if analisou:
      frame_imagem.destroy()
    frame_imagem = LabelFrame(root, text="Resultado da Análise")
    frame_imagem.grid(row=1, column=0, columnspan=4, rowspan=4)

    fig_pf, ax_pf = pf.get_analyzed_image(guard_rails=lista_opcoes_exibicao[0].get(), mlc_peaks=lista_opcoes_exibicao[1].get(),
                                          overlay=lista_opcoes_exibicao[2].get(), leaf_error_subplot=lista_opcoes_exibicao[3].get())
    fig_pf.set_size_inches(0.7 * fig_pf.get_size_inches())
    pf_img = FigureCanvasTkAgg(fig_pf, frame_imagem)
    pf_img.draw()
    pf_img.get_tk_widget().pack()
    pf_img_toolbar = NavigationToolbar2Tk(pf_img, frame_imagem)
    pf_img_toolbar.update()
    analisou = True
    btn_salvar.config(state=NORMAL)
    btn_imprimir.config(state=NORMAL)
    menu_arquivo.entryconfig(2, state=NORMAL)
    menu_arquivo.entryconfig(4, state=NORMAL)
    menu_arquivo.entryconfig(5, state=NORMAL)

  except:
    messagebox.showerror(
        "Erro", "Não foi possível realizar a análise. Verifique os itens abaixo:\n- Imagem carregada.\n- Orientação do MLC.\n- Modelo do MLC.")


def fnc_salvar_relatorio(imprimir):
  global dados_teste, nome_pdf, salvou
  # Atualiza dict dados_teste e notas

  for item in lista_dados:
    dados_teste[item[2]] = item[1].get()
  dados_teste['Modelo do MLC'] = mlc_selecionado.get()
  notas = texto_notas.get("0.0", END)
  notas2 = []
  nova_linha = ''
  max_lin = 10
  for linha in notas:
    if len(notas2) < max_lin:
      if linha == '\n':
        notas2.append(nova_linha)
        nova_linha = ''
      else:
        if (len(nova_linha) > 90) & (linha == ' '):
          notas2.append(nova_linha)
          nova_linha = ''
        else:
          nova_linha += linha
  notas2.append(nova_linha)
  notas = notas2
  tipo_pdf = (("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*"))
  if imprimir & salvou:
    subprocess.Popen(nome_pdf, shell=True)
  else:
    nome_arquivo_pdf = filedialog.asksaveasfile(initialdir='./',
                                                title="Salvar arquivo", filetypes=tipo_pdf)
    nome_arquivo_pdf.close()
    os.remove(nome_arquivo_pdf.name)
    caminho, nome = os.path.split(os.path.splitext(nome_arquivo_pdf.name)[0])
    nome_pdf = caminho + '/' + nome + '.pdf'
    nome_txt = caminho + '/' + nome + '.txt'
    pf.publish_pdf(filename=nome_pdf, notes=notas, open_file=False, metadata=dados_teste, customized=True)
    if imprimir:
      subprocess.Popen(nome_pdf, shell=True)

    pickets = pf.get_test_pickets()
    offsets = 'Dist2CAX'
    for pk in pickets:
      offsets = offsets + '\t' + f'{pk.dist2cax:2.3f}'
    erros = np.zeros([pickets[0].error_array_not_abs.shape[0], len(pickets) + 1])
    text_file = open(nome_txt, "w")
    for lin in range(0, erros.shape[0]):
      texto_lin = ''
      for col in range(0, erros.shape[1]):
        if col == 0:
          if lin == 0:
            texto_header = 'Leaf'
          erros[lin, col] = pickets[col].leafs_idx_in_picket[lin]
          texto_lin = texto_lin + f'{erros[lin,col]:2.0f}'
        else:
          if lin == 0:
            texto_header = texto_header + f'\tPicket {col}'
          erros[lin, col] = pickets[col - 1].error_array_not_abs[lin]
          texto_lin = texto_lin + '\t' + f'{erros[lin,col]:2.3f}'
      if lin == 0:
        text_file.write(offsets + '\n')
        text_file.write(texto_header + '\n')
      text_file.write(texto_lin + '\n')
    text_file.close()
    salvou = True


def fnc_limpar():
  global nome_dcm, btn_analisar, btn_salvar, btn_imprimir
  global analisou, salvou

  if analisou:
    frame_texto_analise.destroy()
    frame_imagem.destroy()
  btn_salvar.config(state=DISABLED)
  btn_imprimir.config(state=DISABLED)
  btn_analisar.config(state=DISABLED)
  menu_arquivo.entryconfig(2, state=DISABLED)
  menu_arquivo.entryconfig(4, state=DISABLED)
  menu_arquivo.entryconfig(5, state=DISABLED)
  nome_dcm = ""
  analisou = False
  salvou = False



####### Inicialização da Janel Principal #######
root = Tk()
root.title('Análise Picket Fence')
#root.iconbitmap('./Imagens/dirac_eqn.ico')
root.state('zoomed')  # inicializa a janela principal maximizada
# root.geometry("1400x720")

tolerancia = 0.5  # tolerancia em mm
limite_acao = 0.3  # limite de ação em mm
nome_dcm = ""
analisou = False
salvou = False

lista_opcoes_exibicao = []  # Boolean: [guard-rails, mlc peaks, overlay, leaf error subplot]

for i in range(0, 4):
  boolean_temp = BooleanVar()
  boolean_temp.set(True)
  lista_opcoes_exibicao.append(boolean_temp)

################################################

########### Criação da Barra de Menu ###########
menubar = Menu(root)

menu_arquivo = Menu(menubar, tearoff=0)
menu_arquivo.add_command(label="Importar imagem TIFF", command=lambda: janela_importar_img(False))
menu_arquivo.add_command(label="Importar imagem DICOM", command=lambda: janela_importar_img(True))
menu_arquivo.add_command(label="Limpar análise", command=fnc_limpar, state=DISABLED)
menu_arquivo.add_separator()
menu_arquivo.add_command(label="Salvar resultados", command=lambda: fnc_salvar_relatorio(False), state=DISABLED)
menu_arquivo.add_command(label="Imprimir relatório", command=lambda: fnc_salvar_relatorio(True), state=DISABLED)
menu_arquivo.add_separator()
menu_arquivo.add_command(label="Sair", command=root.quit)
menubar.add_cascade(label="Arquivo", menu=menu_arquivo)

menu_opcoes = Menu(menubar, tearoff=0)
#menu_opcoes.add_command(label="Editar informações da imagem", command=teste)
menu_opcoes.add_command(label="Critérios de análise", command=criterios)
menu_opcoes.add_command(label="Opções de exibição dos resultados", command=opcoes_exibicao)
menubar.add_cascade(label="Opções", menu=menu_opcoes)

menu_ajuda = Menu(menubar, tearoff=0)
menu_ajuda.add_command(label="Ajuda", command=teste, state=DISABLED)
menu_ajuda.add_separator()
menu_ajuda.add_command(label="Sobre", command=teste, state=DISABLED)
menubar.add_cascade(label="Ajuda", menu=menu_ajuda)

root.config(menu=menubar)
################################################

###### Criação dos widgets da tela inicial######

# Frames
frame_importar = LabelFrame(root, text="Importar Imagem", height=60, width=200)
frame_mlc_model = LabelFrame(root, text="Modelo do MLC", height=60, width=160)
frame_orientacao = LabelFrame(root, text="Orientação MLC", height=60, width=100)
frame_analise = LabelFrame(root, text="Análise", height=60, width=190)
frame_notas = LabelFrame(root, text="Notas", height=150, width=600)
frame_dados = LabelFrame(root, text="Informações do teste", height=205, width=600)
frame_relatorio = LabelFrame(root, text="Relatório", height=60, width=125)

#frame_texto_analise = LabelFrame(root, height=60, width=190)
#frame_imagem = LabelFrame(root)

# ScrolledText
texto_notas = scrolledtext.ScrolledText(frame_notas, height=7, width=70)
texto_notas.grid(row=0, column=0, padx=6)

#Labels and Entry
dados_teste = {'Unidade': '',
               'Acelerador Linear': '',
               'Modelo do MLC': '',
               'Data do teste': '',
               'Realizado por': '',
               'Conferido por': ''}
lista_dados = []
for dado in dados_teste:
  if dado != 'Modelo do MLC':
    lista_dados.append([Label(frame_dados, text=dado + ': '), Entry(frame_dados, width=73, borderwidth=5), dado])


# Drop list
lista_mlc = ['Millennium MLC', 'Millennium HDMLC', 'Agility', 'MLCi2', 'Beam Modulator']
mlc_selecionado = StringVar()
mlc_selecionado.set(lista_mlc[3])
drop_modelo_mlc = OptionMenu(frame_mlc_model, mlc_selecionado, *lista_mlc)  # lista de seleçao do mlc
drop_modelo_mlc.config(width=18)

lista_orientacao = ['up-down', 'left-right']
orientacao = StringVar()
orientacao.set(lista_orientacao[0])
drop_orientacao_mlc = OptionMenu(frame_orientacao, orientacao, *lista_orientacao)  # lista de seleçao do mlc
drop_orientacao_mlc.config(width=8)

# Buttons
btn_import_dcm = Button(frame_importar, text='Arquivo DICOM', command=lambda: janela_importar_img(True))
btn_import_tif = Button(frame_importar, text='Arquivo TIFF', command=lambda: janela_importar_img(False))
btn_criterios = Button(frame_analise, text='Critérios de Análise', command=criterios)
btn_analisar = Button(frame_analise, text='Analisar', command=analisar_pf, state=DISABLED)
btn_salvar = Button(frame_relatorio, text='Salvar', command=lambda: fnc_salvar_relatorio(False), state=DISABLED)
btn_imprimir = Button(frame_relatorio, text='Imprimir', command=lambda: fnc_salvar_relatorio(True), state=DISABLED)

##### Exibição dos widgets da tela inicial ######

# Frames
frame_importar.grid(row=0, column=0, padx=30, pady=20)
frame_importar.grid_propagate(False)
frame_mlc_model.grid(row=0, column=1, padx=30, pady=20)
frame_mlc_model.grid_propagate(False)
frame_orientacao.grid(row=0, column=2, padx=30, pady=20)
frame_orientacao.grid_propagate(False)
frame_analise.grid(row=0, column=3, padx=30, pady=20)
frame_analise.grid_propagate(False)
frame_relatorio.grid(row=0, column=4, padx=30, pady=20, sticky=W)
frame_relatorio.grid_propagate(False)
frame_notas.grid(row=1, column=4, padx=30, pady=20, sticky=W + E)
frame_notas.grid_propagate(False)
frame_dados.grid(row=2, column=4, padx=30, pady=20, sticky=W + E)
frame_dados.grid_propagate(False)


#frame_texto_analise.grid(row=0, column=4)
# frame_imagem.grid(row=1,column=0,columnspan=4)

# ScrolledText
texto_notas.grid(row=0, column=0, padx=6)

#Labels and Entry
lin = 0
for label_dado in lista_dados:
  label_dado[0].grid(row=lin, column=0, padx=5, pady=5, sticky=W)
  label_dado[1].grid(row=lin, column=1, padx=5, pady=5)
  lin += 1

#label_resultado.grid(row=0, column=0)

# Drop list
drop_modelo_mlc.grid(row=0, column=0, padx=2)
drop_orientacao_mlc.grid(row=0, column=0, padx=2)


# Buttons
btn_import_dcm.grid(row=0, column=0, pady=3, padx=5)
btn_import_tif.grid(row=0, column=1, pady=3, padx=5)
btn_criterios.grid(row=0, column=0, pady=3, padx=5)
btn_analisar.grid(row=0, column=1, pady=3, padx=5)
btn_salvar.grid(row=0, column=2, pady=3, padx=5)
btn_imprimir.grid(row=0, column=3, pady=3, padx=5)

################################################


root.protocol("WM_DELETE_WINDOW", on_closing)  # Confirma se o usuário deseja fechar a janela

root.mainloop()
