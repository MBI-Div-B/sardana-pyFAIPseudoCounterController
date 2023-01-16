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
    pseudo_counter_roles = ('q', 'I')

    ctrl_attributes = {
        "dist": {
            Type: float,
            Description: (
                "distance sample - detector plane "
                "(orthogonal distance, not along the beam)"),
            DefaultValue: 1},
        "npt": {
            Type: int,
            Description: "number of points in the output pattern",
            DefaultValue: 100},
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
        self._npt = 100

    def GetAxisAttributes(self, axis):
        axis_attrs = PseudoCounterController.GetAxisAttributes(self, axis)
        axis_attrs = dict(axis_attrs)
        axis_attrs['Value'][Type] = (float, )
        axis_attrs['Value'][MaxDimSize] = (4096, )
        return axis_attrs

    def GetAxisPar(self, axis, par):
        if par == "shape":
            return (self._npt, )

    def GetCtrlPar(self, par):
        if par in _EXP_KEYS:
            return self.ai.__getattribute__(par)
        elif par in _DETECTOR_KEYS:
            return self.detector.__getattribute__(par)
        elif par == "npt":
            return self._npt

    def SetCtrlPar(self, par, value):
        if par == "npt":
            if value > 4096 or value < 1:
                raise ValueError("npt out of range [1, 4096]")
            self._npt = value
        elif par in _DETECTOR_KEYS:
            self.detector.__setattr__(par, value)
        elif par in _EXP_KEYS:
            self.ai.__setattr__(par, value)

    def Calc(self, axis, image):
        # FIXME: avoid calculating twice!
        image = image[0]
        q, I = self.ai.integrate1d(image, npt=self._npt)
        if axis == 1:
            return q
        else:
            return I

