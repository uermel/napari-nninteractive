from pathlib import Path


def determine_layer_index(name, layer_names, splitter) -> str:
    """
    Determines the index assigned to the next layer.
    """
    layer_names = [l_name for l_name in layer_names if name in l_name and name != l_name]
    if layer_names != []:
        return max([int(layer_name.split(splitter)[-1]) for layer_name in layer_names]) + 1
    else:
        return 0
    # print(f"{name} - object {max(layer_index)}")
    # return f"{name} - object {max(layer_index)}"
    # else:
    #
    #
    # pass
    # if Path(join(folder, name + dtype)).exists():
    #     index = len(glob.glob(join(folder, name + "*" + dtype)))
    #     return join(folder, f"{name}_{index}{dtype}")
    # else:
    #     return join(folder, name + dtype)
