# Napari-nnInteractive

______________________________________________________________________

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/napari-plugin-template#getting-started

and review the napari docs for plugin developers:
https://napari.org/stable/plugins/index.html
-->

## Installation

##### 1. Use this python version:

```
conda create -n nnInteractive python=3.12
conda activate nnInteractive
```

##### 2. Install nnUNet (+Set the Paths) (branch project/nnInteractive)

```
pip install git+https://github.com/MIC-DKFZ/batchgeneratorsv2.git
git clone git@git.dkfz.de:mic/internal/nnu-net.git
cd nnu-net
git checkout project/nnInteractive
pip install -e ./
```

##### 3. Install some more stuff require for nnInteractive

```
pip install git+https://github.com/FabianIsensee/BatchViewer.git
pip install git+https://github.com/dalcalab/voxynth.git
```

##### 4. Install this repository + dependencies via

```
pip install -e ./
```

##### 5. Place nnInteractive Checkpoints ("Dataset224_nnInteractive") in your nnUNet_results folder

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
