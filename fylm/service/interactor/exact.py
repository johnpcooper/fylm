from fylm.model.constants import Constants
from fylm.model.image_slice import ImageSlice
from fylm.service.interactor.base import HumanInteractor
import logging
from matplotlib import pyplot as plt

log = logging.getLogger("fylm")


class ExactChannelFinder(HumanInteractor):
    """
    Gets the user to define the exact location of all 28 channels, one-by-one. The user clicks on the notch, then the top right corner of the catch tube (i.e. the
    corner of the catch tube and the central trench). The location of the bottom right corner is inferred from this data.

    """
    def __init__(self, location_model, image):
        super(ExactChannelFinder, self).__init__()
        # some constants
        self._top_left = location_model.top_left
        self._bottom_right = location_model.bottom_right
        self._current_image_slice = None
        self._total_height = self._bottom_right.y - self._top_left.y  # numpy arrays have y increasing as you go downwards
        self._likely_distance = self._total_height / ((Constants.NUM_CATCH_CHANNELS / 2) - 1)  # exclude the first channel because math
        self._expected_channel_width = 230
        self._expected_channel_height = 30
        self._width_margin = 60
        self._height_margin = 30
        self._image = image
        # dynamic variables
        self._location_set_model = location_model
        self._current_channel_number = 1
        self._done = False
        while not self._done:
            self._start()

    def _get_image_slice(self):
        if self._current_channel_number % 2 == 1:
            # left catch channel
            image_slice = ImageSlice(max(0, self._top_left.x - self._width_margin),
                                     max(0, self._top_left.y + self._likely_distance * self._current_channel_number - self._height_margin * 2),
                                     self._expected_channel_width + self._width_margin * 2,
                                     self._expected_channel_height + self._height_margin * 3)
        else:
            # right catch channel
            image_slice = ImageSlice(max(0, self._bottom_right.x - self._expected_channel_width - self._width_margin),
                                     max(0, self._top_left.y + self._likely_distance * self._current_channel_number - self._height_margin * 2),
                                     self._expected_channel_width + self._width_margin * 2,
                                     self._expected_channel_height + self._height_margin * 3)
        image_slice.set_image(self._image)
        return image_slice

    def _on_mouse_click(self, human_input):
        if human_input.left_click and len(self._coordinates) < 2:
            self._add_point(human_input.coordinates.x, human_input.coordinates.y)
        if human_input.right_click:
            self._remove_last_point()

    def _on_key_press(self, human_input):
        if human_input.key == 'q':
            self._done = True
            self._clear()
        if human_input.key == 'enter' and len(self._coordinates) == 2:
            self._handle_results()
        elif human_input.key == 'escape':
            self._clear()
        elif human_input.key == 'left':
            if self._current_channel_number == 1:
                self._current_channel_number = Constants.NUM_CATCH_CHANNELS
            else:
                self._current_channel_number -= 1
        elif human_input.key == 'right':
            if self._current_channel_number == Constants.NUM_CATCH_CHANNELS:
                self._current_channel_number = 1
            else:
                self._current_channel_number += 1

    def _clear(self):
        self._erase_all_points()
        self._close()

    def _handle_results(self):
        notch = self._current_image_slice.get_parent_coordinates(self._coordinates[0])
        tube = self._current_image_slice.get_parent_coordinates(self._coordinates[1])
        self._location_set_model.set_channel_location(self._current_channel_number, notch.x, notch.y, tube.x, tube.y)
        self._clear()

    def _start(self):
        self._current_image_slice = self._get_image_slice()
        self._fig.suptitle("Channel: " + str(self._current_channel_number), fontsize=20)
        self._ax.imshow(self._current_image_slice.image_data, cmap='gray')
        self._ax.autoscale(False)
        self._draw_existing_data()
        plt.show()

    def _draw_existing_data(self):
        pass