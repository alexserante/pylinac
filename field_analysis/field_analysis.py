from pylinac import FieldAnalysis, Protocol, Centering, Edge, Normalization, Interpolation

my_file = r"C:/Users/alexandre.serante/Desktop/flood_field/AL6_6MV_21x16.dcm"
my_img = FieldAnalysis(path=my_file)


my_img.analyze(protocol=Protocol.ELEKTA, centering=Centering.MANUAL, vert_position=0.5, horiz_position=0.5, 
               interpolation=Interpolation.LINEAR, normalization_method=Normalization.MAX,
               interpolation_resolution_mm=0.1, edge_detection_method=Edge.FWHM, invert=True)

print(my_img.results())  # print results as a string
my_img.plot_analyzed_image()  # matplotlib image