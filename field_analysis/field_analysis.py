from pylinac import FieldAnalysis, Protocol, Centering, Edge, Normalization, Interpolation

my_file = r"C:\Users\alexandre.serante\Desktop\github\EPID_images\flood_field\20240223-AL6_6MV_20x20_5MU.dcm"
#  my_img = FieldAnalysis(path=my_file) # no filter apllied to the image
my_img = FieldAnalysis(path=my_file, filter=0)

my_img.analyze(protocol=Protocol.ELEKTA, in_field_ratio=0.8, interpolation=Interpolation.LINEAR,
               normalization_method=Normalization.MAX, centering=Centering.BEAM_CENTER,
               edge_detection_method=Edge.FWHM, invert=True)

# FFF beams 
'''my_img.analyze(protocol=Protocol.ELEKTA, in_field_ratio=0.8, interpolation=Interpolation.LINEAR,
               normalization_method=Normalization.MAX, centering=Centering.BEAM_CENTER,
               edge_detection_method=Edge.INFLECTION_DERIVATIVE, is_FFF=True,
               interpolation_resolution_mm=1, invert=True)
'''
print(my_img.results())  # print results as a string
my_img.plot_analyzed_image()  # matplotlib image
