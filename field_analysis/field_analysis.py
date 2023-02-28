from pylinac import FieldAnalysis, Protocol, Centering, Edge, Normalization, Interpolation

my_file = r"C:\Users\alexandre.serante\Desktop\WL\AL3_15MV_20x20_5MU.dcm"

#  my_img = FieldAnalysis(path=my_file) # no filter apllied to the image
my_img = FieldAnalysis(path=my_file, filter=30,)


my_img.analyze(protocol=Protocol.VARIAN, in_field_ratio=0.8, interpolation=Interpolation.LINEAR,
               normalization_method=Normalization.MAX, centering=Centering.BEAM_CENTER,
               edge_detection_method=Edge.FWHM, hill_window_ratio=0.05,
               interpolation_resolution_mm=0.5, invert=True)

print(my_img.results())  # print results as a string
my_img.plot_analyzed_image()  # matplotlib image
