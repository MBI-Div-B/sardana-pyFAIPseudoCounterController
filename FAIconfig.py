from sardana.macroserver.macro import macro, Type, Optional


@macro([["pcname", Type.Controller, "Name of FAI PseudoCounter controller"]])
def FAIconfig(self, pcname):
    """View and edit FAI configuration."""
    pass