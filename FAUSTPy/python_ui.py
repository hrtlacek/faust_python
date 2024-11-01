# a string consisting of characters that are valid identifiers in both
# Python 2 and Python 3
import string
valid_ident = string.ascii_letters + string.digits + "_"


def str_to_identifier(s):
    """Convert a "bytes" to a valid (in Python 2 and 3) identifier."""

    # convert str/bytes to unicode string
    s = s.decode()

    def filter_chars(s):
        for c in s:
            # periods are used for abbreviations and look ugly when converted
            # to underscore, so filter them out completely
            if c == ".":
                yield ""
            elif c in valid_ident or c == "_":
                yield c
            else:
                yield "_"

    if s[0] in string.digits:
        s = "_"+s

    return ''.join(filter_chars(s))


class Param(object):
    """A UI parameter object.

    This objects represents a FAUST UI input.  It makes sure to enforce the
    constraints specified by the minimum, maximum and step size.

    This object implements the descriptor protocol: reading it works just like
    normal objects, but assignment is redirects to its "zone" attribute.
    """

    def __init__(self, label, zone, init, min, max, step, param_type):
        """Initialise a Param object.

        Parameters:
        -----------

        label : str
            The full label as specified in the FAUST DSP file.
        zone : cffi.CData
            Points to the FAUSTFLOAT object inside the DSP C object.
        init : float
            The initialisation value.
        min : float
            The minimum allowed value.
        max : float
            The maximum allowed value.
        step : float
            The step size of the parameter.
        param_type : str
            The parameter type (e.g., HorizontalSlider)
        """

        # NOTE: _zone is a CData holding a float*
        self.label = label
        self._zone = zone
        self._zone[0] = init
        self.min = min
        self.max = max
        self.step = step
        self.type = param_type

        # extra attributes
        self.default = init
        self.metadata = {}
        self.__doc__ = "min={0}, max={1}, step={2}".format(min, max, step)

    def __zone_getter(self):
        return self._zone[0]

    def __zone_setter(self, x):
        if x >= self.max:
            self._zone[0] = self.max
        elif x <= self.min:
            self._zone[0] = self.min
        else:
            self._zone[0] = self.min + round((x-self.min)/self.step)*self.step

    zone = property(fget=__zone_getter, fset=__zone_setter,
                    doc="Pointer to the value of the parameter.")

    def __set__(self, obj, value):

        self.zone = value


class Box(object):
    def __init__(self, label, layout):
        self.label = label
        self.layout = layout
        self.metadata = {}

    def __setattr__(self, name, value):

        if name in self.__dict__ and hasattr(self.__dict__[name], "__set__"):
            self.__dict__[name].__set__(self, value)
        else:
            object.__setattr__(self, name, value)


# TODO: implement the *Display() and *Bargraph() methods
class PythonUI(object):
    """
    Maps the UI elements of a FAUST DSP to attributes of another object,
    specifically a FAUST wrapper object.

    In FAUST, UI's are specified by the DSP object, which calls methods of a UI
    object to create them.  The PythonUI class implements such a UI object.  It
    creates C callbacks to its methods and stores then in a UI struct, which
    can then be passed to the buildUserInterface() function of a FAUST DSP
    object.

    The DSP object basically calls the methods of the PythonUI class from C via
    the callbacks in the UI struct and thus creates a hierarchical namespace of
    attributes which map back to the DSP's UI elements.

    Notes:
    ------

    Box and Param attributes are prefixed with "b_" and "p_", respectively, in
    order to differentiate them from each other and from regular attributes.

    Boxes and parameters without a label are given a default name of "anon<N>",
    where N is an integer (e.g., "p_anon1" for a label-less parameter).

    See also:
    ---------

    FAUSTPy.Param - wraps the UI input parameters.
    """

    def __init__(self, ffi, obj=None):
        """
        Initialise a PythonUI object.

        Parameters:
        -----------

        ffi : cffi.FFI
            The CFFI instance that holds all the data type declarations.
        obj : object (optional)
            The Python object to which the UI elements are to be added.  If
            None (the default) the PythonUI instance manipulates itself.
        """

        if obj:
            self.__boxes = [obj]
        else:
            self.__boxes = [self]

        self.__num_anon_boxes = [0]
        self.__num_anon_params = [0]
        self.__metadata = [{}]
        self.__group_metadata = {}

        # define C callbacks that know the global PythonUI object
        @ffi.callback("void(void*, FAUSTFLOAT*, char*, char*)")
        def declare(metaInterface, zone, key, value):
            self.declare(zone, ffi.string(key), ffi.string(value))

        @ffi.callback("void(void*, char*)")
        def openVerticalBox(metaInterface, label):
            self.openVerticalBox(ffi.string(label))

        @ffi.callback("void(void*, char*)")
        def openHorizontalBox(metaInterface, label):
            self.openHorizontalBox(ffi.string(label))

        @ffi.callback("void(void*, char*)")
        def openTabBox(metaInterface, label):
            self.openTabBox(ffi.string(label))

        @ffi.callback("void(void*)")
        def closeBox(metaInterface):
            self.closeBox()

        @ffi.callback("void(void*, char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT)")
        def addHorizontalSlider(ignore, c_label, zone, init, min, max, step):
            label = ffi.string(c_label)
            self.addHorizontalSlider(label, zone, init, min, max, step)

        @ffi.callback("void(void*, char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT)")
        def addVerticalSlider(ignore, c_label, zone, init, min, max, step):
            label = ffi.string(c_label)
            self.addVerticalSlider(label, zone, init, min, max, step)

        @ffi.callback("void(void*, char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT)")
        def addNumEntry(ignore, c_label, zone, init, min, max, step):
            label = ffi.string(c_label)
            self.addNumEntry(label, zone, init, min, max, step)

        @ffi.callback("void(void*, char*, FAUSTFLOAT*)")
        def addButton(ignore, c_label, zone):
            self.addButton(ffi.string(c_label), zone)

        @ffi.callback("void(void*, char*, FAUSTFLOAT*)")
        def addToggleButton(ignore, c_label, zone):
            self.addToggleButton(ffi.string(c_label), zone)

        @ffi.callback("void(void*, char*, FAUSTFLOAT*)")
        def addCheckButton(ignore, c_label, zone):
            self.addCheckButton(ffi.string(c_label), zone)

        @ffi.callback("void(void*, char*, FAUSTFLOAT*, int)")
        def addNumDisplay(ignore, c_label, zone, p):
            self.addNumDisplay(ffi.string(c_label), zone, p)

        @ffi.callback("void(void*, char*, FAUSTFLOAT*, char*[], FAUSTFLOAT, FAUSTFLOAT)")
        def addTextDisplay(ignore, c_label, zone, names, min, max):
            self.addTextDisplay(ffi.string(c_label), zone, names, min, max)

        @ffi.callback("void(void*, char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT)")
        def addHorizontalBargraph(ignore, c_label, zone, min, max):
            label = ffi.string(c_label)
            self.addHorizontalBargraph(label, zone, min, max)

        @ffi.callback("void(void*, char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT)")
        def addVerticalBargraph(ignore, c_label, zone, min, max):
            label = ffi.string(c_label)
            self.addVerticalBargraph(label, zone, min, max)

        # create a UI object and store the above callbacks as it's function
        # pointers; also store the above functions in self so that they don't
        # get garbage collected
        ui = ffi.new("UIGlue*")
        ui.declare = self.__declare_c = declare
        ui.openVerticalBox = self.__openVerticalBox_c = openVerticalBox
        ui.openHorizontalBox = self.__openHorizontalBox_c = openHorizontalBox
        ui.openTabBox = self.__openTabBox_c = openTabBox
        ui.closeBox = self.__closeBox_c = closeBox
        ui.addHorizontalSlider = self.__addHorizontalSlider_c = addHorizontalSlider
        ui.addVerticalSlider = self.__addVerticalSlider_c = addVerticalSlider
        ui.addNumEntry = self.__addNumEntry_c = addNumEntry
        ui.addButton = self.__addButton_c = addButton
        ui.addToggleButton = self.__addToggleButton_c = addToggleButton
        ui.addCheckButton = self.__addCheckButton_c = addCheckButton
        ui.addNumDisplay = self.__addNumDisplay_c = addNumDisplay
        ui.addTextDisplay = self.__addTextDisplay_c = addTextDisplay
        ui.addHorizontalBargraph = self.__addHorizontalBargraph_c = addHorizontalBargraph
        ui.addVerticalBargraph = self.__addVerticalBargraph_c = addVerticalBargraph
        ui.uiInterface = ffi.NULL  # we don't use this anyway

        self.__ui = ui
        self.__ffi = ffi

    ui = property(fget=lambda x: x.__ui,
                  doc="The UI struct that calls back to its parent object.")

    def declare(self, zone, key, value):

        if zone == self.__ffi.NULL:
            # set group meta-data
            #
            # the group meta-data is stored temporarily here and is set during
            # the next openBox()
            self.__group_metadata[key] = value
        else:
            # store parameter meta-data
            #
            # since the only identifier we get is the zone (pointer to the
            # control value), we have to store this for now and assign it to
            # the corresponding parameter later in closeBox()
            if zone not in self.__metadata[-1]:
                self.__metadata[-1][zone] = {}
            self.__metadata[-1][zone][key] = value

    ##########################
    # stuff to do with boxes
    ##########################

    def openBox(self, label, layout):
        # If the label is an empty string, don't do anything, just stay in the
        # current Box
        if label:
            # special case the first box, which is always "0x00" (the ASCII
            # Null character), so that it has a consistent name
            if label.decode() == '0x00':
                sane_label = "ui"
            else:
                sane_label = "b_"+str_to_identifier(label)
        else:
            # if the label is empty, create a default label
            self.__num_anon_boxes[-1] += 1
            sane_label = "b_anon" + str(self.__num_anon_boxes[-1])

        # create a new sub-Box and make it a child of the current Box
        box = Box(label, layout)
        setattr(self.__boxes[-1], sane_label, box)
        self.__boxes.append(box)

        # store the group meta-data in the newly opened box and reset
        # self.__group_metadata
        self.__boxes[-1].metadata.update(self.__group_metadata)
        self.__group_metadata = {}

        self.__num_anon_boxes.append(0)
        self.__num_anon_params.append(0)
        self.__metadata.append({})

    def openVerticalBox(self, label):

        self.openBox(label, "vertical")

    def openHorizontalBox(self, label):

        self.openBox(label, "horizontal")

    def openTabBox(self, label):

        self.openBox(label, "tab")

    def closeBox(self):

        cur_metadata = self.__metadata.pop()

        # iterate over the objects in the current box and assign the meta-data
        # to the correct parameters
        for p in self.__boxes[-1].__dict__.values():

            # TODO: add the Display class (or whatever it will be called) to
            # this list once *Display and *Bargraph are implemented
            if type(p) not in (Param,):
                continue

            # iterate over the meta-data that has accumulated in the current
            # box and assign it to its corresponding Param objects
            for zone, mdata in cur_metadata.items():
                if p._zone == zone:
                    p.metadata.update(mdata)

        self.__num_anon_boxes.pop()
        self.__num_anon_params.pop()

        # now pop the box off the stack
        self.__boxes.pop()

    ##########################
    # stuff to do with inputs
    ##########################

    def add_input(self, label, zone, init, min, max, step, param_type):

        if label:
            sane_label = str_to_identifier(label)
        else:
            # if the label is empty, create a default label
            self.__num_anon_params[-1] += 1
            sane_label = "anon" + str(self.__num_anon_params[-1])

        setattr(self.__boxes[-1], "p_"+sane_label,
                Param(label, zone, init, min, max, step, param_type))

    def addHorizontalSlider(self, label, zone, init, min, max, step):

        self.add_input(label, zone, init, min, max, step, "HorizontalSlider")

    def addVerticalSlider(self, label, zone, init, min, max, step):

        self.add_input(label, zone, init, min, max, step, "VerticalSlider")

    def addNumEntry(self, label, zone, init, min, max, step):

        self.add_input(label, zone, init, min, max, step, "NumEntry")

    def addButton(self, label, zone):

        self.add_input(label, zone, 0, 0, 1, 1, "Button")

    def addToggleButton(self, label, zone):

        self.add_input(label, zone, 0, 0, 1, 1, "ToggleButton")

    def addCheckButton(self, label, zone):

        self.add_input(label, zone, 0, 0, 1, 1, "CheckButton")

    def addNumDisplay(self, label, zone, p):
        pass

    def addTextDisplay(self, label, zone, names, min, max):
        pass

    def addHorizontalBargraph(self, label, zone, min, max):
        pass

    def addVerticalBargraph(self, label, zone, min, max):
        pass
