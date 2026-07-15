#include <Python.h>

typedef struct TSLanguage TSLanguage;

extern TSLanguage *tree_sitter_aware(void);

static PyObject *lang(PyObject *self, PyObject *args) {
    return PyCapsule_New(tree_sitter_aware(), "tree_sitter.Language", NULL);
}
static PyMethodDef methods[] = {{"language", lang, METH_NOARGS, ""}, {NULL}};
static struct PyModuleDef mod = {PyModuleDef_HEAD_INIT, "_binding", NULL, -1, methods};

PyMODINIT_FUNC PyInit__binding(void) { return PyModule_Create(&mod); }
