from pylinac import FieldAnalysis, Protocol, Centering, Edge, Normalization, Interpolation

my_file = r"C:\Users\alexandre.serante\Desktop\github\EPID_images\flood_field\AL5_15MV_20x20_5MU.dcm"

#my_img = FieldAnalysis(path=my_file) # no filter apllied to the image
my_img = FieldAnalysis(path=my_file, filter=50) # filter applied


my_img.analyze(protocol=Protocol.VARIAN, interpolation=Interpolation.LINEAR, normalization_method=Normalization.MAX,
               interpolation_resolution_mm=0.5, edge_detection_method=Edge.FWHM, invert=True,
               in_field_ratio=0.8)

print(my_img.results())  # print results as a string
my_img.plot_analyzed_image()  # matplotlib image