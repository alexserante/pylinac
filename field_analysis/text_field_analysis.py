from pylinac import FieldAnalysis, Protocol, Centering, Edge, Normalization, Interpolation

my_file = r"C:\Users\alexandre.serante\Desktop\github\EPID_images\flood_field\AL5_6MV_20x20_10MU.dcm"

#  my_img = FieldAnalysis(path=my_file) # no filter apllied to the image
my_img = FieldAnalysis(path=my_file, filter=10,)


my_img.analyze(protocol=Protocol.VARIAN, in_field_ratio=0.8,
               edge_detection_method=Edge.INFLECTION_HILL, hill_window_ratio=0.1,)

print(my_img.results())  # print results as a string
my_img.plot_analyzed_image()  # matplotlib image