from abc import abstractproperty, abstractmethod
import logging
import numpy as np
import re

log = logging.getLogger(__name__)


class BaseResult(object):
    """
    Models a file we use to store intermediate and final analyses.

    """
    def __init__(self):
        self.base_path = None
        self.time_period = None
        self.field_of_view = None

    @property
    def path(self):
        return "%s/%s" % (self.base_path, self.filename)

    @property
    def filename(self):
        # This is just the default filename and it won't always be valid.
        return "tp%s-fov%s.txt" % (self.time_period, self.field_of_view)

    @abstractmethod
    def load(self, *args):
        """
        Populates some or all of the model's attributes from a text stream.

        :param data:    a stream of text representing the data in a model
        :type data:     str

        """
        raise NotImplemented

    @abstractproperty
    def data(self):
        """
        Yields or returns the data that was written to disk, with the types converted appropriately from strings.
        Data is returned in the order it was obtained in the experiment.

        """
        raise NotImplemented


class BaseTextFile(BaseResult):
    """
    Models a text file that stores results.

    """
    kind = "text"

    @abstractproperty
    def lines(self):
        """
        Yields lines of text that should be written to the file.

        """
        raise NotImplemented

    @abstractmethod
    def load(self, *args):
        raise NotImplemented

    @abstractproperty
    def data(self):
        raise NotImplemented


class BaseImage(BaseResult):
    kind = "image"

    def __init__(self):
        super(BaseImage, self).__init__()
        self._image_data = None

    def load(self, image):
        """
        :param image:   a 2D numpy array representing an image
        :type image:    np.ndarray

        """
        assert isinstance(image, np.ndarray)
        self._image_data = image

    @abstractproperty
    def data(self):
        raise NotImplemented


class BaseMovie(BaseResult):
    kind = "movie"

    def __init__(self):
        super(BaseMovie, self).__init__()
        self._movie_data = None


class BaseSet(object):
    def __init__(self, experiment, top_level_dir):
        self.base_path = experiment.data_dir + "/" + top_level_dir
        self._current_filenames = []
        self._existing = []
        # The default regex assumes the only distinguishing features are time_periods and fields of view.
        self._regex = re.compile(r"""tp\d+-fov\d+.txt""")
        # We use 0-based indexing for fields of view
        self._fields_of_view = [fov for fov in range(experiment.field_of_view_count)]
        # Time periods are 1-based since they come from the ND2 filenames
        self._time_periods = [time_period for time_period in experiment.time_periods]
        # The BaseFile model that this set contains
        self._model = None

    @property
    def _expected(self):
        """
        Yields instantiated children of BaseFile that represent the work we expect to have done.

        """
        assert self._model is not None
        for field_of_view in self._fields_of_view:
            for time_period in self._time_periods:
                model = self._model()
                model.time_period = time_period
                model.field_of_view = field_of_view
                model.base_path = self.base_path
                yield model

    @property
    def remaining(self):
        """
        Yields a child of BaseFile that represents work needing to be done.

        """
        for model in self._expected:
            if model.filename not in self._current_filenames:
                yield model

    @property
    def existing(self):
        """
        Yields a child of BaseFile that represents work already done.

        """
        if not self._existing:
            for model in self._expected:
                if model.filename in self._current_filenames:
                    self._existing.append(model)
        return self._existing

    def _get_current(self, field_of_view):
        """
        Yields models in order of acquisition for a given field of view.

        """
        for model in sorted(self.existing, key=lambda x: x.time_period):
            if model.field_of_view == field_of_view:
                yield model

    def get_data(self, field_of_view, time_period):
        """
        Yields model data in order of acquisition across all time_periods.

        """
        for model in self._get_current(field_of_view):
            for data in model.data:
                if model.time_period == time_period:
                    yield data

    def add_existing_data_file(self, filename):
        """
        Informs the model of a unit of work that has already been done.

        :param filename:    path to a file that contains completed work
        :type filename:     str

        """
        if self._regex.match(filename):
            self._current_filenames.append(filename)