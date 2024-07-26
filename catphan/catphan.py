from pylinac import CatPhan503

my_folder = r"C:\Users\a.serante\Desktop\CQIGRTXV\QA_SEMES\CTM20"

cbct = CatPhan503(my_folder)

cbct.analyze()

print(cbct.results())
cbct.plot_analyzed_image()
cbct.publish_pdf("catphan_M20", open_file=True)