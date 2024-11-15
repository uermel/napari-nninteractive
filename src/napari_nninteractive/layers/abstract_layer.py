from abc import ABC, abstractmethod

from napari.layers.base._base_constants import ActionType
from napari.utils.events import Event


class BaseLayerClass(ABC):
    def __init__(self, prompt_index=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_free = True
        self.prompt_index = prompt_index
        self.colors = {
            0: [0.0, 0.694, 0.047, 1],  # [0, 177, 12]
            1: [0.827, 0.027, 0.0, 1],  # [211, 7, 0]
        }
        self.colors_set = {
            0: [0.0, 0.427, 0.027, 1],  # [0, 109, 7]
            1: [0.561, 0.02, 0.0, 1],  # [143, 5, 0]
        }
        self.events.add(finished=Event)

    def set_prompt(self, index):
        self.prompt_index = index
        if not self._is_free:
            self.replace_color(self.colors[self.prompt_index])

    def add(self, data, *arg, **kwargs):
        if self._is_free:
            self._is_free = False
            self._add(data, *arg, **kwargs)
        else:
            self.remove_last()
            self._add(data, *arg, **kwargs)

        self.events.finished(action=ActionType.ADDED, value="ADD")

    def run(self):
        if self._is_free:
            return

        self._is_free = True
        self.replace_color(self.colors_set[self.prompt_index])

    def is_free(self):
        return self._is_free

    @abstractmethod
    def replace_color(self, _color):
        pass

    @abstractmethod
    def remove_last(self):
        pass

    @abstractmethod
    def _add(self, data, *arg, **kwargs):
        pass
