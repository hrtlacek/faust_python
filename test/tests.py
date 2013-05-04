import unittest
import cffi
import numpy as np
from tempfile import NamedTemporaryFile
from string import Template
from subprocess import check_call
from FAUSTPy import *

def init_ffi():
    ffi = cffi.FFI()

    faust_dsp = "dattorro_notch_cut_regalia.dsp"

    # just use single precision for tests
    faust_float = "float"

    cdefs = "typedef {0} FAUSTFLOAT;".format(faust_float) + """

    typedef struct {
        void *mInterface;
        void (*declare)(void* interface, const char* key, const char* value);
    } MetaGlue;

    typedef struct {
        // widget layouts
        void (*openVerticalBox)(void*, const char* label);
        void (*openHorizontalBox)(void*, const char* label);
        void (*openTabBox)(void*, const char* label);
        void (*declare)(void*, FAUSTFLOAT*, char*, char*);
        // passive widgets
        void (*addNumDisplay)(void*, const char* label, FAUSTFLOAT* zone, int p);
        void (*addTextDisplay)(void*, const char* label, FAUSTFLOAT* zone, const char* names[], FAUSTFLOAT min, FAUSTFLOAT max);
        void (*addHorizontalBargraph)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT min, FAUSTFLOAT max);
        void (*addVerticalBargraph)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT min, FAUSTFLOAT max);
        // active widgets
        void (*addHorizontalSlider)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT init, FAUSTFLOAT min, FAUSTFLOAT max, FAUSTFLOAT step);
        void (*addVerticalSlider)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT init, FAUSTFLOAT min, FAUSTFLOAT max, FAUSTFLOAT step);
        void (*addButton)(void*, const char* label, FAUSTFLOAT* zone);
        void (*addToggleButton)(void*, const char* label, FAUSTFLOAT* zone);
        void (*addCheckButton)(void*, const char* label, FAUSTFLOAT* zone);
        void (*addNumEntry)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT init, FAUSTFLOAT min, FAUSTFLOAT max, FAUSTFLOAT step);
        void (*closeBox)(void*);
        void* uiInterface;
    } UIGlue;

    typedef struct {...;} mydsp;

    mydsp *newmydsp();
    void deletemydsp(mydsp*);
    void metadatamydsp(MetaGlue* m);
    int getSampleRatemydsp(mydsp* dsp);
    int getNumInputsmydsp(mydsp* dsp);
    int getNumOutputsmydsp(mydsp* dsp);
    int getInputRatemydsp(mydsp* dsp, int channel);
    int getOutputRatemydsp(mydsp* dsp, int channel);
    void classInitmydsp(int samplingFreq);
    void instanceInitmydsp(mydsp* dsp, int samplingFreq);
    void initmydsp(mydsp* dsp, int samplingFreq);
    void buildUserInterfacemydsp(mydsp* dsp, UIGlue* interface);
    void computemydsp(mydsp* dsp, int count, FAUSTFLOAT** inputs, FAUSTFLOAT** outputs);
    """
    ffi.cdef(cdefs)

    with NamedTemporaryFile(suffix=".c") as f:

        faust_args = ["-lang", "c", "-single", "-o", f.name, faust_dsp]

        check_call(["faust"] + faust_args)

        # compile the code
        C = ffi.verify(
            Template("""
            #define FAUSTFLOAT ${FAUSTFLOAT}

            // helper function definitions
            int min(int x, int y) { return x < y ? x : y;};
            int max(int x, int y) { return x > y ? x : y;};

            // the MetaGlue struct that will be wrapped
            typedef struct {
                void *mInterface;
                void (*declare)(void* interface, const char* key, const char* value);
            } MetaGlue;

            // the UIGlue struct that will be wrapped
            typedef struct {
                // widget layouts
                void (*openVerticalBox)(void*, const char* label);
                void (*openHorizontalBox)(void*, const char* label);
                void (*openTabBox)(void*, const char* label);
                void (*declare)(void*, FAUSTFLOAT*, char*, char*);
                // passive widgets
                void (*addNumDisplay)(void*, const char* label, FAUSTFLOAT* zone, int p);
                void (*addTextDisplay)(void*, const char* label, FAUSTFLOAT* zone, const char* names[], FAUSTFLOAT min, FAUSTFLOAT max);
                void (*addHorizontalBargraph)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT min, FAUSTFLOAT max);
                void (*addVerticalBargraph)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT min, FAUSTFLOAT max);
                // active widgets
                void (*addHorizontalSlider)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT init, FAUSTFLOAT min, FAUSTFLOAT max, FAUSTFLOAT step);
                void (*addVerticalSlider)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT init, FAUSTFLOAT min, FAUSTFLOAT max, FAUSTFLOAT step);
                void (*addButton)(void*, const char* label, FAUSTFLOAT* zone);
                void (*addToggleButton)(void*, const char* label, FAUSTFLOAT* zone);
                void (*addCheckButton)(void*, const char* label, FAUSTFLOAT* zone);
                void (*addNumEntry)(void*, const char* label, FAUSTFLOAT* zone, FAUSTFLOAT init, FAUSTFLOAT min, FAUSTFLOAT max, FAUSTFLOAT step);
                void (*closeBox)(void*);
                void* uiInterface;
            } UIGlue;

            #include "${FAUSTC}"
            """).substitute(FAUSTFLOAT=faust_float, FAUSTC=f.name),
            extra_compile_args=["-std=c99"],
        )

        return ffi, C, faust_float

#################################
# test PythonUI
#################################

class test_1_faustui(unittest.TestCase):

    def setUp(self):

        class empty(object):
            pass
        self.bla = empty()

        self.ffi, self.C, self.faust_float = init_ffi()

    def test_init(self):
        "Test initialisation of PythonUI objects."

        PythonUI(self.ffi, self.bla)

    # TODO: split up these tests and complete them
    def test_misc(self):
        "Test miscellanea."

        ui = PythonUI(self.ffi, self.bla).ui
        ui.openVerticalBox(self.ffi.NULL,"bla")

        slider_val = self.ffi.new("FAUSTFLOAT*", 1.0)
        self.assertEqual(slider_val[0], 1.0)

        ui.addHorizontalSlider(self.ffi.NULL, "float", slider_val, 0.0, 0.0, 2.0, 0.1)
        self.assertTrue(hasattr(self.bla.bla, "float"))
        self.assertEqual(self.bla.bla.float.zone, 0.0)

        self.bla.bla.float.zone = 0.5
        self.assertEqual(self.bla.bla.float.zone, slider_val[0])

        button_val = self.ffi.new("FAUSTFLOAT*", 1.0)
        # should do nothing
        ui.addButton(self.ffi.NULL, "float", button_val)


#################################
# test FAUSTDsp
#################################

class test_2_faustdsp(unittest.TestCase):

    def setUp(self):

        self.ffi, self.C, self.faust_float = init_ffi()

    def test_init(self):
        "Test initialisation of FAUSTDsp objects."

        # TODO: how best to keep this test separate, yet in this class, without
        # recompiling the DSP in every test. Maybe I can just set self.dsp if
        # the method order of unittest is equal to the definition order.
        FAUSTDsp(self.C,self.ffi,self.faust_float,48000,PythonUI)

    def test_attributes(self):
        "Verify presence of various attributes."

        dsp = FAUSTDsp(self.C,self.ffi,self.faust_float,48000,PythonUI)
        self.assertTrue(hasattr(dsp, "fs"))
        self.assertTrue(hasattr(dsp, "num_in"))
        self.assertTrue(hasattr(dsp, "num_out"))
        self.assertTrue(hasattr(dsp, "faustfloat"))
        self.assertTrue(hasattr(dsp, "dtype"))

    def test_compute(self):
        "Test the compute() method."

        dsp = FAUSTDsp(self.C,self.ffi,self.faust_float,48000,PythonUI)
        audio = np.zeros((dsp.num_in,48e3), dtype=dsp.dtype)
        audio[:,0] = 1
        out = dsp.compute(audio)

#################################
# test FAUST
#################################

class test_3_faustwrapper(unittest.TestCase):

    def test_init(self):
        """Test initialisation of FAUST objects."""

        FAUST("dattorro_notch_cut_regalia.dsp", 48000)
        FAUST("dattorro_notch_cut_regalia.dsp", 48000, "float")
        FAUST("dattorro_notch_cut_regalia.dsp", 48000, "double")
        FAUST("dattorro_notch_cut_regalia.dsp", 48000, "long double")

    def test_init_wrong_args(self):
        """Test initialisation of FAUST objects with bad arguments."""

        self.assertRaises(ValueError, FAUST, "dattorro_notch_cut_regalia.dsp", 48000, "l double")