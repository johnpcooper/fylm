from fylm.service.rotation import RotationCorrector
from fylm.model.rotation import RotationSet
from fylm.service.timestamp import TimestampExtractor
from fylm.model.timestamp import TimestampSet


class Activity(object):
    def __init__(self, experiment):
        self._experiment = experiment

    def calculate_rotation_offset(self):
        rotation_set = RotationSet(self._experiment)
        corrector = RotationCorrector(self._experiment)
        corrector.find_current(rotation_set)
        corrector.save(rotation_set)

    def extract_timestamps(self):
        timestamp_set = TimestampSet(self._experiment)
        extractor = TimestampExtractor(self._experiment)
        extractor.find_current(timestamp_set)
        extractor.save(timestamp_set)