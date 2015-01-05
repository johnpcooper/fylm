from fylm.model.image_slice import ImageSlice
from fylm.model.location import LocationSet
from fylm.model.movie import Movie as MovieModel
from fylm.service.errors import terminal_error
from fylm.service.image_reader import ImageReader
from fylm.service.location import LocationSet as LocationSetService
import logging
from skimage import io
import subprocess
import os

log = logging.getLogger("fylm")
log.setLevel(logging.DEBUG)


class Movie(object):
    def __init__(self, experiment):
        self._location_set = LocationSet(experiment)
        location_service = LocationSetService(experiment)
        location_service.load_existing_models(self._location_set)
        self._image_reader = ImageReader(experiment)
        self._base_dir = experiment.data_dir + "/movie/"
        print(self._base_dir)

    def make_channel_overview(self, timepoint, field_of_view, channel_number):
        """
        Makes a movie of a single catch channel, showing every focus level
        and filter channel available (lined up along the horizontal axis).

        :type field_of_view:    int
        :type channel_number:   int

        """
        self._image_reader.timepoint = timepoint
        self._image_reader.field_of_view = field_of_view
        channels = self._get_channels(self._image_reader)
        z_levels = self._image_reader.nd2.z_level_count
        image_slice = self._get_image_slice(field_of_view, channel_number)
        movie = MovieModel(image_slice.height * 2, image_slice.width)

        images = os.listdir(self._base_dir)
        try:
            for n, image_set in enumerate(self._image_reader):
                filename = "tp%s-fov%s-channel%s-%03d.png" % (timepoint, field_of_view, channel_number, n)
                # if filename not in images:
                if filename not in images:
                    self._update_image_data(image_slice, image_set, channels, z_levels, movie)
                    log.info("Adding movie frame %s" % n)
                    io.imsave(self._base_dir + filename, movie.frame)
                else:
                    log.debug("Skipping %s" % filename)
        except:
            log.exception("Movie maker crashed!")
        else:
            base_filename = self._base_dir + "tp%s-fov%s-channel%s" % (timepoint, field_of_view, channel_number)
            command = ("/usr/bin/mencoder",
                       'mf://%s*.png' % self._base_dir,
                       '-mf',
                       'w=%s:h=%s:fps=24:type=png' % (movie.frame.shape[1], movie.frame.shape[0]),
                       '-ovc', 'copy', '-oac', 'copy', '-o' ' %s.avi' % base_filename)
            print(" ".join(command))
            try:
                failure = subprocess.call(command, shell=True)
                log.info("Done with movie")
                files = os.listdir(self._base_dir)
                if not failure:
                    for f in files:
                        if f.endswith(".png"):
                            log.info("deleting %s" % self._base_dir + f)
                            os.remove(self._base_dir + f)
            except:
                log.exception()
            else:
                log.info("All is over")

    def _get_image_slice(self, field_of_view, channel_number):
        for model in self._location_set.existing:
            if not model.field_of_view == field_of_view:
                continue
            notch, tube = model.get_channel_data(channel_number)
            if notch.x < tube.x:
                x = notch.x
                fliplr = False
            else:
                x = tube.x
                fliplr = True
            y = tube.y
            width = int(abs(notch.x - tube.x))
            height = int(notch.y - tube.y)
            return ImageSlice(x, y, width, height, fliplr=fliplr)
        terminal_error("Channel location has not been provided.")

    @staticmethod
    def _get_channels(image_reader):
        channels = [""]
        for channel in sorted(image_reader.nd2.channels):
            if channel.name not in channels:
                channels.append(channel.name)
        return channels

    @staticmethod
    def _update_image_data(image_slice, image_set, channels, z_levels, movie):
        for channel in channels:
            for z_level in xrange(z_levels):
                image = image_set.get_image(channel, z_level)
                if image is not None:
                    image_slice.set_image(image)
                    movie.update_image(channel, z_level, image_slice.image_data)