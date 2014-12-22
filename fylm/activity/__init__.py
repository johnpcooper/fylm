from fylm.service.rotation import RotationSet as RotationSetService
from fylm.model.rotation import RotationSet
from fylm.service.timestamp import TimestampSet as TimestampSetService
from fylm.model.timestamp import TimestampSet
from fylm.service.registration import RegistrationSet as RegistrationSetService
from fylm.model.registration import RegistrationSet
from fylm.service.location import LocationSet as LocationSetService
from fylm.model.location import LocationSet
from fylm.service.kymograph import KymographSet as KymographSetService
from fylm.model.kymograph import KymographSet
from fylm.service.annotation import AnnotationSet
from fylm.model.annotation import KymographAnnotationSet


class Activity(object):
    def __init__(self, experiment):
        self._experiment = experiment

    def _calculate_and_save_text(self, SetModel, Service):
        set_model = SetModel(self._experiment)
        service = Service(self._experiment)
        service.find_current(set_model)
        service.save_text(set_model)

    def calculate_rotation_offset(self):
        self._calculate_and_save_text(RotationSet, RotationSetService)

    def extract_timestamps(self):
        self._calculate_and_save_text(TimestampSet, TimestampSetService)

    def calculate_registration(self):
        self._calculate_and_save_text(RegistrationSet, RegistrationSetService)

    def input_channel_locations(self):
        self._calculate_and_save_text(LocationSet, LocationSetService)

    def create_kymographs(self):
        """
        We can't use _calulate_and_save() because it would be inefficient to iterate
        over the entire image stack for each channel.

        """
        kymograph_service = KymographSetService(self._experiment)
        kymograph_set = KymographSet(self._experiment)
        kymograph_service.save(kymograph_set)

    def annotate_kymographs(self):
        annotation_service = AnnotationSet(self._experiment)
        annotation_set = KymographAnnotationSet(self._experiment)
        annotation_service.save(annotation_set)

    def fov_movie(self):
        from fylm.service.image_reader import ImageReader
        from skimage import io
        reader = ImageReader(self._experiment)
        reader.field_of_view = 0
        reader.timepoint = 2
        i = 0
        for image_set in reader:
            image = image_set.get_image(channel="", z_level=0)
            name = "/home/jim/Desktop/experiments/141111/%s.png" % i
            print(name)
            io.imsave(name, image)
            i += 1