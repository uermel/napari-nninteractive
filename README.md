# Napari-nnInteractive

______________________________________________________________________

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/napari-plugin-template#getting-started

and review the napari docs for plugin developers:
https://napari.org/stable/plugins/index.html
-->

## Installation

### Prerequisites
You need a Linux computer with a Nvidia GPU. At least 10-11GB of VRAM.

##### 1. Create a virtual environment:
Conda or pip is fine, we provide an example for conda. Python 3.10 and higher are supported

```
conda create -n nnInteractive python=3.12
conda activate nnInteractive
```

##### 2. Install the correct PyTorch for your system
Go to the [PyTorch homepage](https://pytorch.org/get-started/locally/) and pick the right configuration. 
Note that since recently PyTorch needs to be installed via pip. This is fine to do within your conda environment.

For Ubuntu with a Nvidia GPU, pick 'stable', 'Linux', 'Pip', 'Python', 'CUDA12.6':
```
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

##### 3. Install nnInteractive
This needs to be updated once released
```
git clone git@git.dkfz.de:mic/personal/group8/nninteractive_inference.git
pip install -e nninteractive_inference/
```
(this will be a pypi package so this will be `pip install nninteractive` in the future)

##### 3. Install this repository + dependencies via

```
pip install -e ./
```
(ideally this will also just be a pypi package)

______________________________________________________________________

## Getting Started

Use one of these three options to start napari and activate the plugin.
Afterward, Drag and drop your images into napari.

\***Note if getting asked which plugin to use for opening .nii.gz files use napari-nifti.**

a) Start napari, then Plugins -> nnInteractive.

```
napari
```

b) Run this to start napari with the plugin already started.

```
napari -w napari-nninteractive
```

c) Run this to start napari with the plugin and open an image directly

```
napari demo_data/AbdominalOrganSegmentation_img0004_0000.nii.gz -w napari-nninteractive
```

______________________________________________________________________

## Acknowledgments

<p align="left">
  <img src="imgs/Logos/HI_Logo.png" width="150"> &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="imgs/Logos/DKFZ_Logo.png" width="500">
</p>

This repository is developed and maintained by the Applied Computer Vision Lab (ACVL)
of [Helmholtz Imaging](https://www.helmholtz-imaging.de/).

This [napari] plugin was generated with [copier] using the [napari-plugin-template].

[copier]: https://copier.readthedocs.io/en/stable/
[napari]: https://github.com/napari/napari
[napari-plugin-template]: https://github.com/napari/napari-plugin-template
