from napari.layers import Labels


class ScibbleLayer(Labels):
    def __init__(self, data=None, prompt_index=0, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.prompt_index = prompt_index
        self.data_current = None
        # Connect the custom event handler for new scribbles

        self.events.data.connect(self.reset_to_single_scribble)

    def run(self):
        pass

    def set_prompt(self, index):
        self.prompt_index = index

    def reset_to_single_scribble(self, *args, **kwargs):
        # Create a copy of the data to detect changes
        print("Hallo")
        print(self.data.shape)

    # def set_prompt(self):
    #     coord = self.data_current
    #     self.remove()
    #     self.add()

    # def add(self, coord):
    #     if self.data_current is None:
    #         self.data_current = coord.copy()
    #         self.add()
    #     else:
    #         self.data_current = coord.copy()
    #         self.remove()
    #         self.add()
    #
    # def run(self):
    #     self.save_current()
    #     self.remove()
    #     self.add()
    #     return

    #
    # # def paint(self, *args, **kwargs):
    # #     print("YY")
    #
    # def _draw(self, new_label, last_cursor_coord, coordinates):
    #     print(new_label)
    #     print(last_cursor_coord)
    #     print(coordinates)
    #
    #     print("data.shape")
    #     super()._draw(new_label, last_cursor_coord, coordinates)
    #
