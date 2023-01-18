from sardana.macroserver.macro import macro, Type, Optional, Table
from tango import DeviceProxy

_CTRL_ATTRS = [
    "wavelength", "energy", "dist", "poni1", "poni2", "rot1", "rot2", "rot3",
    "pixel1", "pixel2",
]

@macro([
    ["ctrl", Type.Controller, None, "Name of FAI PseudoCounter controller"],
])
def FAIconfig(self, ctrl):
    """View FAI configuration."""
    if not ctrl.parent == "FAIPseudoCounterController":
        self.warning("This is not a pyFAIPseudoCounterController!")
        return

    dev = DeviceProxy(ctrl.full_name)

    pars = {k: dev[k].value for k in _CTRL_ATTRS}
    table = Table(
        [list(pars.values())],
        row_head_str=list(pars.keys()),
        row_head_fmt="%*s",
        col_sep="  =  "
    )

    self.output("FAI configuration:")
    for line in table.genOutput():
        self.output(line)

