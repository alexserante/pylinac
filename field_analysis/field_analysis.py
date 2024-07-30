from pylinac import FieldAnalysis, Interpolation, Protocol, Centering, Edge, Normalization
'''from pylinac import FieldProfileAnalysis, Centering, Edge, Normalization
from pylinac.metrics.profile import (
    PenumbraRightMetric, 
    PenumbraLeftMetric, 
    SymmetryAreaMetric, 
    FlatnessDifferenceMetric
    )
'''


path = r"G:\ONCORAD\Física Médica\Controles de Qualidade\1 Testes Mensais\FieldAnalysis\6MV_23x23_5MU.dcm"
my_img = FieldAnalysis(path)

my_img.analyze(
    protocol=Protocol.VARIAN,
    in_field_ratio=0.8,
    interpolation=Interpolation.LINEAR,
    interpolation_resolution_mm=0.1,
    normalization_method=Normalization.MAX,
    centering=Centering.BEAM_CENTER,
    edge_detection_method=Edge.INFLECTION_DERIVATIVE,
    invert=True)


# FFF beams 
'''my_img.analyze(
    x_width=0.02,
    y_width=0.02,
    centering=Centering.BEAM_CENTER,
    normalization=Normalization.MAX, 
    edge_type=Edge.INFLECTION_DERIVATIVE,
    ground=True,
    metrics=(
        PenumbraRightMetric(),
        PenumbraLeftMetric(),
        SymmetryAreaMetric(),
        )
)
'''


print(my_img.results())  # print results as a string
my_img.plot_analyzed_image()  # matplotlib image
