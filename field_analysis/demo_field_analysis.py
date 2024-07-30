from pylinac import FieldProfileAnalysis, Centering, Normalization, Edge
from pylinac.metrics.profile import (
    PenumbraLeftMetric,
    PenumbraRightMetric,
    SymmetryAreaMetric,
    FlatnessDifferenceMetric,
)

path = r"G:\ONCORAD\Física Médica\Controles de Qualidade\1 Testes Mensais\FieldAnalysis\6MV_23x23_5MU.dcm"
field_analyzer = FieldProfileAnalysis(path)
field_analyzer.analyze(
    centering=Centering.BEAM_CENTER,
    x_width=0.02,
    y_width=0.02,
    normalization=Normalization.BEAM_CENTER,
    edge_type=Edge.INFLECTION_DERIVATIVE,
    ground=True,
    metrics=(
        PenumbraLeftMetric(),
        PenumbraRightMetric(),
        SymmetryAreaMetric(),
        FlatnessDifferenceMetric(),
    ),
)
field_analyzer.plot_analyzed_images(show_grid=True, mirror="beam")