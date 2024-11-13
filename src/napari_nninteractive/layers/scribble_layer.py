from napari.layers import Labels
from napari_nninteractive.layers.abstract_layer import BaseLayerClass
from napari.layers.base._base_constants import ActionType
from napari.utils.events import Event


class ScibbleLayer(BaseLayerClass, Labels):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colormap = {
            None: None,
            1: self.colors[self.prompt_index],
            2: self.colors_set[0],
            3: self.colors_set[1],
        }

        self._is_free = False
        self.mouse_drag_callbacks.append(self.on_draw)
        # self.events.add(finished=Event)

    def replace_color(self, _color):
        self.colormap = {
            None: None,
            1: self.colors[self.prompt_index],
            2: self.colors_set[0],
            3: self.colors_set[1],
        }
        self.refresh()

    def _add(self, data, *arg, **kwargs):
        pass

    def run(self):
        self.data[self.data == 1] = self.prompt_index + 2
        self._is_free = True
        self.refresh()

    def remove_last(self):
        self.undo()

    def _commit_staged_history(self):
        super()._commit_staged_history()
        self._is_free = False
        self.events.finished(action=ActionType.ADDED, value="ADD")

    def on_draw(self, layer, event):
        if not self._is_free:
            self.remove_last()
            self.colormap = {
                None: None,
                1: self.colors[self.prompt_index],
                2: self.colors_set[0],
                3: self.colors_set[1],
            }
            self._is_free = True
            self.refresh()
        self.colormap = {
            None: None,
            1: self.colors[self.prompt_index],
            2: self.colors_set[0],
            3: self.colors_set[1],
        }

    def get_last(self):
        return (self.data == 1).astype(int)
