from collections import defaultdict
import numpy as np
from skimage import draw
from skimage.color import gray2rgb


class Movie(object):
    """
    has a "frame" property which dynamically builds the image
    for each frame, the service updates the pictures as they're available
    so if a fluorescence image isn't there, we use the already-existing image by default and thus can use any frequency of FL images
    slots are labelled by channel and zoom level, they need a deterministic order
    write orange triangles, deal with overflow

    """
    # We create a single triangle once to save time
    triangle_width = 11  # must be odd
    triangle_height = 12
    triangle_x_coords = np.array([0, triangle_width, (triangle_width - 1) / 2])
    triangle_y_coords = np.array([0, 0, triangle_height])
    rr, cc = draw.polygon(triangle_y_coords, triangle_x_coords)
    triangle = np.zeros((triangle_height, triangle_width, 3), dtype=np.uint16)
    triangle[rr, cc] = 45536, 23000, 0

    def __init__(self, height, width):
        self._slot_height = height
        self._slot_width = width
        self._slots = defaultdict(dict)
        self._channel_order = {0: ""}
        self._frame_height = None

    @property
    def frame(self):
        """
        Combines the image data from each of the slots in a deterministic order, adds arrows if needed, and returns the image

        :return:    np.ndarray()

        """
        for slot in self.slots:
            pass

    @property
    def frame_height(self):
        slot_count = 0
        if self._frame_height is None:
            for channel in self._slots.values():
                slot_count += len(channel)
            self._frame_height = slot_count * self._slot_height
        return self._frame_height

    @property
    def frame_width(self):
        return self._slot_width

    @property
    def slots(self):
        """
        Yields slots in a deterministic order.

        :return:    np.ndarray()

        """
        for index, channel in sorted(self._channel_order.items()):
            for slot_index, slot in sorted(self._slots[channel].items()):
                yield slot

    def add_slot(self, channel_name, z_level):
        """
        Allocates space for a slot in the movie frame.

        :type channel_name:     str
        :type z_level:          int

        """
        # Images are placed from top to bottom in order of channel, in the order that the channels are added
        # Here we add the channel to the list of channels to yield if we don't have it yet.
        # The brightfield channel always comes first, however. It's called "" (empty string)
        if channel_name not in self._channel_order.keys():
            index = max(self._channel_order.keys()) + 1
            self._channel_order[index] = channel_name
        # Now allocate some space for the image. We start with zeros (i.e. a black image) in case this particular channel
        # doesn't have image data for the first frame. This occurs for fluorescent channels sometimes since we only take
        # those images every four minutes instead of every two, in order to minimize the amount of blue light that the cells
        # are exposed to (there's evidence that it's phototoxic).
        self._slots[channel_name][z_level] = np.zeros((self._slot_height, self._slot_width, 3))

    def update_image(self, channel_name, z_level, image_data):
        self._slots[channel_name][z_level] = gray2rgb(image_data[:, :])

    def _get_triangle(self, pointing, trim=0):
        assert pointing in ("up", "down")
        if pointing == "down":
            triangle = Movie.triangle
        if pointing == "up":
            triangle = np.flipud(Movie.triangle)
        x_start, x_stop = self._get_triangle_boundaries(trim)
        return np.copy(triangle[:, x_start:x_stop, :])

    @staticmethod
    def _get_triangle_boundaries(trim):
        """
        Finds the boundaries needed if the triangle goes partially out of the frame. The point will always be within the limits
        of the frame as its location is determined by the kymograph annotation, which guarantees bounds won't be violated.

        :param trim:    the number of pixels to trim from the edge. Positive numbers trim the left, negative trim the right
        :type trim:     int
        :return:        (int, int)

        """
        x_start = 0 if trim < 0 else trim
        x_stop = Movie.triangle_width if trim >= 0 else Movie.triangle_width + trim
        return x_start, x_stop