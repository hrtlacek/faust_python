#define FAUSTFLOAT float

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
