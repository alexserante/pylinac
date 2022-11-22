from pylinac import WinstonLutz

my_directory = 'L:/Radioterapia/Fisicos/Controle_Qualidade/WL/WL-AL06/IMAGENS/20221110'

wl = WinstonLutz(my_directory, use_filenames=True)

wl.analyze(bb_size_mm=8)


pdf_name = my_directory[62:80]
wl.publish_pdf(pdf_name + '.pdf')

# plot all the images
wl.plot_images()