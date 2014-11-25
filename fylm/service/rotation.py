from skimage import transform
from fylm.service.utilities import ImageUtilities, FileInteractor
from skimage.morphology import skeletonize
from fylm.model.constants import Constants
import nd2reader
import numpy as np
import math
import logging


log = logging.getLogger("fylm")


class RotationCorrector(object):
    """
    Determines the rotational skew of an image.

    """
    def __init__(self, experiment):
        self._experiment = experiment

    def save(self, rotation_set):
        """
        Creates rotation offset files for every field of view and image stack available.

        :type rotation_set:   fylm.model.RotationSet()

        """
        did_work = False
        for rotation_model in rotation_set.remaining:
            did_work = True
            writer = FileInteractor(rotation_model)
            log.debug("Creating rotation file %s" % rotation_model.filename)
            # This is a pretty naive loop - the same file will get opened 8-12 times
            # There are obvious ways to optimize this but that can be done later if it matters
            # It probably doesn't matter though and I like simple things
            nd2_filename = self._experiment.get_nd2_from_timepoint(rotation_model.timepoint)
            nd2 = nd2reader.Nd2(nd2_filename)
            # gets the first in-focus image from the first timpoint in the stack
            # TODO: Update nd2reader to figure out which one is in focus or to be able to set it
            image = nd2.get_image(0, rotation_model.field_of_view, "", 1)
            offset = self._determine_rotation_offset(image.data)
            rotation_model.offset = offset
            writer.write_text()
        if not did_work:
            log.debug("All rotation corrections have been calculated.")

    @staticmethod
    def _determine_rotation_offset(image):
        """
        Finds rotational skew so that the sides of the central trench are (nearly) perfectly vertical.

        """
        segmentation = ImageUtilities.create_vertical_segments(image)
        # Draw a line that follows the center of the segments at each point, which should be roughly vertical
        # We should expect this to give us four approximately-vertical lines, possibly with many gaps in each line
        skeletons = skeletonize(segmentation)
        # Use the Hough transform to get the closest lines that approximate those four lines
        hough = transform.hough_line(skeletons, np.arange(-Constants.FIFTEEN_DEGREES_IN_RADIANS,
                                                          Constants.FIFTEEN_DEGREES_IN_RADIANS,
                                                          0.0001))
        # Create a list of the angles (in radians) of all of the lines the Hough transform produced, with 0.0 being
        # completely vertical
        # These angles correspond to the angles of the four sides of the channels, which we need to correct for
        angles = [angle for _, angle, dist in zip(*transform.hough_line_peaks(*hough))]
        if not angles:
            log.warn("Image skew could not be calculated. The image is probably invalid.")
            return 0.0
        else:
            # Get the average angle and convert it to degrees
            offset = sum(angles) / len(angles) * 180.0 / math.pi
            if offset > Constants.ACCEPTABLE_SKEW_THRESHOLD:
                log.warn("Image is heavily skewed. Check that the images are valid.")
            return offset