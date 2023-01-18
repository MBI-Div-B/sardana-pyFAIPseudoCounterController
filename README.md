# pyFAIPseudoCounterController

A PseudoCounter that uses [pyFAI](https://pyfai.readthedocs.io/) for azimuthal integration/ reordering of 2D scattering images. Depending on the image size, this can be a relatively resource-hungry operation, which is why this PseudoCounter relies on pyFAI using the "CSR" algorithm for the heavy lifting. Refer to the pyFAI documentaion on [performance considerations](https://pyfai.readthedocs.io/en/v2023.1/performance.html).

The PseudoCounter has 4 axes:
* `q`: spectrum of momentum transfer coordinates (unit: 1/nm)
* `chi`: spectrum of azimuthal angle coordinates (unit: degree)
* `I1d`: spectrum of azimuthally integrated intensities as function of `q`
* `I2d`: image of reordered intensities as function of `q` and `chi`

The PseudoCounter axes can directly be plotted, e.g. in taurus, lavue, ...
| dummy detector image I(x, y) | reordered image I(q, chi) | 1D intensity I(q) |
|-|-|-|
|![](doc/lavue_ccd.png) | ![](doc/lavue_ai2d.png) | ![](doc/taurus_ai1d.png) |


## Requirements

* pyFAI, including its optional pyopencl dependency

## Creating the PseudoCounters

Here is an example spock command to create the PseudoCounter with the name "faictrl" using a 2D ExpChannel called "ccd" as image source:

`defctrl FAIPseudoCounterController faictrl image=ccd q=aiQ chi=aiChi I1d=ai1d I2d=ai2d`

## Configuring the azimuthal integration

The PseudoCounter _controller_ has attributes named similarly to the pyFAI AzimuthalIntegrator parameters. These can be set directly:

To set the wavelength used:

`faictrl.wavelength = 1.59e-9`

Alternatively, the energy (in keV) can be set:

`faictrl.energy = 0.779`

Other parameters relate to the sample/detector geometry. The detector class used here is a simple contiguous detector with rectangular pixels. Check the [pyFAI documentation](https://pyfai.readthedocs.io/) for details.

### List of parameters/ controller attributes

| attribute | unit | description |
| - | - | - |
| dist | m | distance sample - detector plane (orthogonal distance, not along the beam)
| npt_q | none | number of points in radial (q) direction
| npt_chi | none | number of points in azimuthal (chi) direction
| wavelength | m | wavelength used - will calculate photon energy accordingly
| energy | keV | photon energy - will calculate wavelength accordingly
| pixel1 | m | pixel size of first detector dimension
| pixel2 | m | pixel size of second detector dimension
| poni1 | m | coordinate of the point of normal incidence along the detector's first dimension (ususally vertical axis)
| poni2 | m | coordinate of the point of normal incidence along the detector's second dimension (ususally horizontal axis)
| rot1 | rad | First rotation from sample ref to detector's ref
| rot2 | rad | Second rotation from sample ref to detector's ref
| rot3 | rad | Third rotation from sample ref to detector's ref

![Sample/ detector geometry illustration from pyfai.readthedocs.io](doc/PONI.png)
(source: pyfai documentation)

## Configuration macro

todo...
