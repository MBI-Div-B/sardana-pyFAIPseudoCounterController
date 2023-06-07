from sardana.pool.controller import (
    PseudoCounterController,
    Type,
    Description,
    DefaultValue,
    MaxDimSize,
)
from pyFAI.detectors import Detector
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
import numpy as np
import tango
from tango import AttributeProxy, EventType
import json

_DETECTOR_KEYS = [
    "pixel1",
    "pixel2",
]
_EXP_KEYS = [
    "wavelength",
    "energy",
    "dist",
    "poni1",
    "poni2",
    "rot1",
    "rot2",
    "rot3",
]
_MISC_KEYS = [
    "lavue_tango_attribute_path",
    "lavue_outer_ROI_name",
    "direct_beam_ROI_name",
    "mask",
    "npt_q",
    "npt_chi",
    "event_id",
]


class FAIPseudoCounterController(PseudoCounterController):

    counter_roles = ("image",)
    pseudo_counter_roles = ("q", "chi", "I1d", "I2d")

    ctrl_attributes = {
        "dist": {
            Type: float,
            Description: (
                "distance sample - detector plane "
                "(orthogonal distance, not along the beam)"
            ),
            DefaultValue: 1,
        },
        "npt_q": {
            Type: int,
            Description: "number of points in radial (q) direction",
            DefaultValue: 100,
        },
        "npt_chi": {
            Type: int,
            Description: "number of points in azimuthal (chi) direction",
            DefaultValue: 36,
        },
        "wavelength": {
            Type: float,
            Description: "Wavelength used (m)",
            DefaultValue: 1e-9,
        },
        "energy": {
            Type: float,
            Description: "Photon energy (keV)",
            DefaultValue: 1.240,
        },
        "pixel1": {
            Type: float,
            Description: "Pixel size of first detector dimension (m)",
            DefaultValue: 1e-5,
        },
        "pixel2": {
            Type: float,
            Description: "Pixel size of second detector dimension (m)",
            DefaultValue: 1e-5,
        },
        "poni1": {
            Type: float,
            Description: (
                "Coordinate of the point of normal incidence along "
                "the detector's first dimension (m)"
            ),
            DefaultValue: 0,
        },
        "poni2": {
            Type: float,
            Description: (
                "Coordinate of the point of normal incidence along "
                "the detector's second dimension (m)"
            ),
            DefaultValue: 0,
        },
        "rot1": {
            Type: float,
            Description: ("First rotation from sample ref to detector's ref (rad)"),
            DefaultValue: 0,
        },
        "rot2": {
            Type: float,
            Description: ("Second rotation from sample ref to detector's ref (rad)"),
            DefaultValue: 0,
        },
        "rot3": {
            Type: float,
            Description: ("Third rotation from sample ref to detector's ref (rad)"),
            DefaultValue: 0,
        },
        "lavue_tango_attribute_path": {
            Type: str,
            Description: ("Full path to laVue TangoDS attribute"),
            DefaultValue: "rsxs/lavuecontroller/henry/DetectorROIs",
        },
        "event_id": {
            Type: int,
            Description: ("Event subscribtion id"),
            DefaultValue: -1,
        },
        "lavue_outer_ROI_name": {
            Type: str,
            Description: ("Name of bigger ROI"),
            DefaultValue: "pyfai_ROI_mask",
        },
        "direct_beam_ROI_name": {
            Type: str,
            Description: ("Name of direct beam ROI"),
            DefaultValue: "pyfai_direct_beam_mask",
        },
        "mask": {
            Type: ((int, int),),
            Description: (
                "Pixel mask bitmap. Must match the image dimensions. "
                "Zero denotes unmasked (valid) pixels, all other are masked"
            ),
            DefaultValue: np.zeros([1, 1]),
        },
    }

    def __init__(self, inst, props, *args, **kwargs):
        self.detector = Detector()
        self.ai = AzimuthalIntegrator(detector=self.detector)
        self._npt_q = 100
        self._npt_chi = 36
        self._I2d = np.zeros([self._npt_chi, self._npt_q])
        self._q = np.arange(self._npt_q)
        self._chi = np.arange(self._npt_chi)
        self._image = np.array([])
        self._mask = np.zeros([1, 1])
        self._lavue_tango_attribute_path = ""
        self._event_id = -1
        self._lavue_outer_ROI_name = ""
        self._direct_beam_ROI_name = ""
        super(FAIPseudoCounterController, self).__init__(inst, props, *args, **kwargs)
        self.create_attribute_proxy()

    def GetAxisAttributes(self, axis):
        axis_attrs = PseudoCounterController.GetAxisAttributes(self, axis)
        axis_attrs = dict(axis_attrs)
        if axis == 4:
            axis_attrs["Value"][Type] = ((float, float),)
            axis_attrs["Value"][MaxDimSize] = (360, 4096)
        else:
            axis_attrs["Value"][Type] = (float,)
            axis_attrs["Value"][MaxDimSize] = (4096,)
        return axis_attrs

    def GetAxisPar(self, axis, par):
        if par == "shape":
            if axis == 1:
                return (self._npt_q,)
            elif axis == 2:
                return (self._npt_chi,)
            elif axis == 3:
                return (self._npt_q,)
            elif axis == 4:
                return (self._npt_chi, self._npt_q)

    def GetCtrlPar(self, par):
        if par in _EXP_KEYS:
            return getattr(self.ai, par)
        elif par in _DETECTOR_KEYS:
            return getattr(self.detector, par)
        elif par in _MISC_KEYS:
            return getattr(self, f"_{par}")

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
        elif par == "lavue_tango_attribute_path":
            self._lavue_tango_attribute_path = value
            try:
                self.lavue_attr.unsubscribe_event(self._event_id)
            except:
                pass
            self.create_attribute_proxy()
        elif par == "event_id":
            self._event_id = value
        elif par == "lavue_outer_ROI_name":
            self._lavue_outer_ROI_name = value
        elif par == "direct_beam_ROI_name":
            self._direct_beam_ROI_name = value
        elif par == "mask":
            self._mask = np.array(value)
        elif par in _DETECTOR_KEYS:
            setattr(self.detector, par, value)
        elif par in _EXP_KEYS:
            setattr(self.ai, par, value)

    def Calc(self, axis, image):
        image = image[0]
        # calculate az2d if image has changed
        if not np.array_equal(self._image, image):
            # check mask shape matches, use no mask otherwise
            mask = self._mask if image.shape == self._mask.shape else None
            regrouped = self.ai.integrate2d(
                image,
                self._npt_q,
                self._npt_chi,
                method="csr",
                mask=mask,
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

    def update_mask(self, e=None):
        self._mask = np.zeros([400, 400], dtype=int)
        if self._image is not None:
            self._mask = np.zeros_like(self._image, dtype=int)
        if self.lavue_attr is not None:
            try:
                self._log.debug(".")
                print("enter try")
                ROIs = json.loads(self.lavue_attr.read().value)
            except:
                print("except")
            direct_beam_ROI, selected_ROI = (
                ROIs.get(self._direct_beam_ROI_name),
                ROIs.get(self._lavue_outer_ROI_name),
            )
            if selected_ROI is not None:
                x1, y1, x2, y2 = list(map(lambda x: max(x, 0), selected_ROI[0]))
                print(x1, x2, y1, y2)
                temp = np.ones_like(self._mask, dtype=int)
                temp[y1:y2, x1:x2] = 0
                self._mask = temp

            if direct_beam_ROI is not None:
                x1, y1, x2, y2 = list(map(lambda x: max(x, 0), direct_beam_ROI[0]))
                print(x1, x2, y1, y2)
                self._mask[y1:y2, x1:x2] = 1

    def create_attribute_proxy(self):
        try:
            self.lavue_attr = AttributeProxy(self._lavue_tango_attribute_path)
            self.lavue_attr.poll(1000)
            self._event_id = self.lavue_attr.subscribe_event(
                EventType.CHANGE_EVENT, self.update_mask
            )
        except:
            self.lavue_attr = None
