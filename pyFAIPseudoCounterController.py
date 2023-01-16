from sardana.pool.controller import (
    PseudoCounterController, Type, Description, DefaultValue, MaxDimSize,
)
from pyFAI.detectors import Detector
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
import numpy as np


_DETECTOR_KEYS = ["pixel1", "pixel2",]
_EXP_KEYS = [
    "wavelength", "energy", "dist", "poni1", "poni2",
    "rot1", "rot2", "rot3",
    ]


class FAI1DPseudoCounterController(PseudoCounterController):

    counter_roles = ("image", )
    pseudo_counter_roles = ('q', 'chi', 'I1d', 'I2d')

    ctrl_attributes = {
        "dist": {
            Type: float,
            Description: (
                "distance sample - detector plane "
                "(orthogonal distance, not along the beam)"),
            DefaultValue: 1},
        "npt_q": {
            Type: int,
            Description: "number of points in radial (q) direction",
            DefaultValue: 100},
        "npt_chi": {
            Type: int,
            Description: "number of points in azimuthal (chi) direction",
            DefaultValue: 36},
        "wavelength": {
            Type: float,
            Description: "Wavelength used (m)",
            DefaultValue: 1e-9},
        "energy": {
            Type: float,
            Description: "Photon energy (keV)",
            DefaultValue: 1.240},
        "pixel1": {
            Type: float,
            Description: "Pixel size of first detector dimension (m)",
            DefaultValue: 0},
        "pixel2": {
            Type: float,
            Description: "Pixel size of second detector dimension (m)",
            DefaultValue: 0},
        "poni1": {
            Type: float,
            Description: (
                "Coordinate of the point of normal incidence along "
                "the detector's first dimension (m)"),
            DefaultValue: 0},
        "poni2": {
            Type: float,
            Description: (
                "Coordinate of the point of normal incidence along "
                "the detector's second dimension (m)"),
            DefaultValue: 0},
        "rot1": {
            Type: float,
            Description: (
                "First rotation from sample ref to detector's ref (rad)"),
            DefaultValue: 0},
        "rot2": {
            Type: float,
            Description: (
                "Second rotation from sample ref to detector's ref (rad)"),
            DefaultValue: 0},
        "rot3": {
            Type: float,
            Description: (
                "Third rotation from sample ref to detector's ref (rad)"),
            DefaultValue: 0},
    }

    def __init__(self, inst, props, *args, **kwargs):
        super(FAI1DPseudoCounterController, self).__init__(
            inst, props, *args, **kwargs
        )
        self.detector = Detector()
        self.ai = AzimuthalIntegrator(detector=self.detector)
        self._npt_q = 100
        self._npt_chi = 36
        self._I2d = np.zeros([self._npt_chi, self._npt_q])
        self._q = np.arange(self._npt_q)
        self._chi = np.arange(self._npt_chi)
        self._image = None

    def GetAxisAttributes(self, axis):
        axis_attrs = PseudoCounterController.GetAxisAttributes(self, axis)
        axis_attrs = dict(axis_attrs)
        if axis == 4:
            axis_attrs['Value'][Type] = ((float, float), )
            axis_attrs['Value'][MaxDimSize] = (4096, 4096)
        else:
            axis_attrs['Value'][Type] = (float, )
            axis_attrs['Value'][MaxDimSize] = (4096, )
        return axis_attrs

    def GetAxisPar(self, axis, par):
        if par == "shape":
            if axis == 1:
                return (self._npt_q, )
            elif axis == 2:
                return (self._npt_chi, )
            elif axis == 3:
                return (self._npt_q, )
            elif axis == 4:
                return (self._npt_chi, self._npt_q)

    def GetCtrlPar(self, par):
        if par in _EXP_KEYS:
            return self.ai.__getattribute__(par)
        elif par in _DETECTOR_KEYS:
            return self.detector.__getattribute__(par)
        elif par == "npt_q":
            return self._npt_q
        elif par == "npt_chi":
            return self._npt_chi

    def SetCtrlPar(self, par, value):
        if par == "npt_q":
            if value > 4096 or value < 1:
                raise ValueError("npt_q out of range [1, 4096]")
            else:
                self._npt_q = value
        elif par == "npt_chi":
            if value > 360 or value < 1:
                raise ValueError("npt_chi out of range [1, 360]")
            else:
                self._npt_chi = value
        elif par in _DETECTOR_KEYS:
            self.detector.__setattr__(par, value)
        elif par in _EXP_KEYS:
            self.ai.__setattr__(par, value)

    def Calc(self, axis, image):
        image = image[0]
        # calculate az2d if image has changed
        if not np.array_equal(self._image, image):
            regrouped = self.ai.integrate2d(
                image, self._npt_q, self._npt_chi, method="csr"
                )
            self._I2d, self._q, self._chi = regrouped
            self._image = image.copy()

        # return requested pseudocounter
        if axis == 1:
            return self._q
        elif axis == 2:
            return self._chi
        elif axis == 3:
            return self._I2d.sum(axis=0)
        elif axis == 4:
            return self._I2d

