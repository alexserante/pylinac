from pylinac import FieldProfileAnalysis, Centering, Edge, Normalization
from pylinac.metrics.profile import (
    PenumbraRightMetric,
    PenumbraLeftMetric,
    SymmetryPointDifferenceMetric,
    FlatnessDifferenceMetric
)


path = r"G:\ONCORAD\Física Médica\Controles de Qualidade\1 Testes Mensais\FieldAnalysis\6MV_5MU_20x20.dcm"
my_img = FieldProfileAnalysis(path)

my_img.analyze(
    normalization=Normalization.MAX,
    centering=Centering.BEAM_CENTER,
    edge_type=Edge.INFLECTION_DERIVATIVE,
    invert=True
)


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
        SymmetryPointDifferenceMetric(),
        FlatnessDifferenceMetric()
    ),
    invert=True
)'''


print(my_img.results())  # print results as a string
my_img.plot_analyzed_images(show_grid=True, mirror="beam")  # matplotlib image
