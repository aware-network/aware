/* CPython 3.12 private complete preparation scan. No cache or object ownership
 * replaces the Python guard's retained rows or integer identity expectations. */
#define PY_SSIZE_T_CLEAN
#define Py_BUILD_CORE
#include <Python.h>
#include <stdint.h>
#include <internal/pycore_dict.h>
#undef Py_BUILD_CORE

#if PY_MAJOR_VERSION != 3 || PY_MINOR_VERSION != 12
#error "preparation scan requires the admitted CPython 3.12 ABI"
#endif

/* A successful invocation observes every row freshly while holding the GIL.
 * All mismatch paths return false; Python raises its retained native refusal.
 * Exceptions from the original native attribute fallback remain exceptions. */
typedef enum {
    FIELD_STATE, FIELD_STATE_CODE, FIELD_REFUSE, FIELD_REFUSE_CODE, FIELD_PRIMITIVE_NAMESPACE, FIELD_PRIMITIVE_KEYS, FIELD_PRIMITIVE_ITEMS, FIELD_STRING_KIND_ID, FIELD_NATIVE_ID, FIELD_GET, FIELD_CLASS_GET, FIELD_GET_DICT, FIELD_DICT_KEYS, FIELD_DICT_ITEMS, FIELD_NATIVE_TUPLE, FIELD_NATIVE_ANY, FIELD_MODULE_ROWS, FIELD_REGEX_CACHE_ROWS, FIELD_CLASS_ROWS, FIELD_RECEIVER_ROWS, FIELD_FUNCTION_ROWS, FIELD_RECEIVER_FUNCTION_ROWS, FIELD_DATA_ROWS, FIELD_RECEIVER_DATA_ROWS, FIELD_RECEIVER_OWNER, FIELD_HOST, FIELD_HOST_BINDINGS, FIELD_NAMESPACE, FIELD_EXECUTION_NAMESPACE, FIELD_OPERATION, FIELD_PROTECTED, FIELD_CHECK_CODE, FIELD_CHECK, FIELD_BINDING_FAILURE, FIELD_COUNT
} Field;
static const char *field_names[FIELD_COUNT] = {
    "state", "state_code", "refuse", "refuse_code", "primitive_namespace", "primitive_keys", "primitive_items", "string_kind_id", "native_id", "get", "class_get", "get_dict", "dict_keys", "dict_items", "native_tuple", "native_any", "module_rows", "regex_cache_rows", "class_rows", "receiver_rows", "function_rows", "receiver_function_rows", "data_rows", "receiver_data_rows", "receiver_owner", "host", "host_bindings", "namespace", "execution_namespace", "operation", "protected", "check_code", "check", "binding_failure"
};
typedef struct CodeLayout {
    PyObject *code_ref, *names;
    Py_ssize_t indices[FIELD_COUNT];
    struct CodeLayout *next;
} CodeLayout;

/* Topology is a second closed checker shape in this SAME qualified backend.
 * Only original code identity and immutable field positions are cached. */
enum {
    T_MODULE_PLANS, T_CLASS_PLANS, T_CLASS_IDENTITY, T_LOWER_PLANS,
    T_SYS_GET, T_REGISTRY_GET, T_REGISTRY_ROWS, T_SINGLETON_ROWS,
    T_BUILTIN_NAMESPACE, T_BUILTIN_KEYS, T_BUILTIN_PLAN,
    T_CONTAINER_PLANS, T_CELL_PLAN, T_SPECIAL_CELLS, T_OWN_GUARD_CELL,
    T_FUNCTION_PLAN, T_GUARD, T_GUARD_CODE, T_COUNT
};
static const char *topology_names[T_COUNT] = {
    "module_plans", "class_plans", "class_identity", "lower_plans",
    "sys_get", "registry_get", "registry_rows", "singleton_rows",
    "builtin_namespace", "builtin_keys", "builtin_plan",
    "container_plans", "cell_plan", "special_cells", "own_guard_cell",
    "function_plan", "guard", "guard_code"
};
typedef struct TopologyLayout {
    PyObject *code_ref, *names;
    Py_ssize_t indices[T_COUNT];
    Py_ssize_t anchor;
    struct TopologyLayout *next;
} TopologyLayout;

enum {
    O_NAMESPACE, O_OWNER_KEYS, O_OWNER_PLAN, O_BUILTIN_NAMESPACE,
    O_BUILTIN_KEYS, O_BUILTIN_PLAN, O_GUARD_VALUES, O_EXPECTED_GUARD,
    O_NAMESPACE_PLANS, O_CLASS_PLANS, O_CLASS_KINDS, O_MEMBER_PLANS,
    O_CONTAINER_PLANS, O_DESCRIPTORS, O_DESCRIPTOR_KINDS, O_FUNCTIONS, O_CELL_PLAN,
    O_SPECIAL_CELLS, O_RETAINED_GUARD_CELL, O_ATTEMPT_GUARD_CELL,
    O_CHECK, O_COUNT
};
static const char *owner_names[O_COUNT] = {
    "namespace", "owner_keys", "owner_plan", "builtin_namespace",
    "builtin_keys", "builtin_plan", "guard_values", "expected_guard",
    "namespace_plans", "class_plans", "class_kinds", "member_plans",
    "container_plans", "descriptors", "descriptor_kinds", "functions", "cell_plan",
    "special_cells", "retained_guard_cell", "attempt_guard_cell", "check"
};
typedef struct OwnerLayout {
    PyObject *code_ref;
    Py_ssize_t indices[O_COUNT], anchor;
    struct OwnerLayout *next;
} OwnerLayout;

typedef struct {
    PyObject *scan_builtin;
    PyObject *fingerprint_builtin;
    CodeLayout *layouts;
    PyObject *topology_builtin;
    TopologyLayout *topology_layouts;
    PyObject *owner_builtin;
    PyObject *codec_key_builtin;
    OwnerLayout *owner_layouts;
    PyObject *metadata_names[4];
    PyObject *class_names[7];
    PyObject *class_descriptors[7];
    PyObject *native_id;
    PyObject *native_length;
    PyObject *native_any;
    PyObject *native_accessors[5];
} ModuleState;

typedef struct {
    const char *field;
    Py_ssize_t group, row, position;
    uintptr_t address;
} ReadEvent;

typedef struct {
    PyObject *check;
    CodeLayout *layout;
    PyObject *closure;
    unsigned long long *counts;
    ReadEvent *events;
    Py_ssize_t event_count, event_capacity;
    int tracing;
    ModuleState *module;
    PyObject **metadata_names;
    PyObject *mapping, *zipping, *kind_of, *size_of;
    PyObject *snapshots[8];
    PyObject *host_context;
    Py_ssize_t group_index;
    Py_ssize_t row_index;
} Scan;
enum { MODULE_ROWS, CLASS_ROWS, FUNCTION_ROWS, FUNCTION_KIND, FIXED_FIELDS,
       METADATA_FIELDS, CELL_KIND, CELL_FIELDS, DATA_ROWS, DATA_KIND, DATA_LENGTH,
       DATA_IDENTITIES, FALLBACK_STATES, FOUNDATION_KEYS, FOUNDATION_ITEMS,
       FOUNDATION_CODE_READS, FALLBACK_IDENTITIES, COUNT_SIZE };
static const char *count_names[COUNT_SIZE] = {
    "module_rows", "class_rows", "function_rows", "function_kind_reads",
    "function_fixed_reads", "function_metadata_reads", "cell_kind_reads",
    "cell_contents_reads", "data_rows", "data_kind_reads", "data_length_reads",
    "data_identity_reads", "fallback_states", "foundation_key_reads",
    "foundation_item_reads", "foundation_code_reads", "fallback_identity_reads"
};
#define COUNT(s, n) do { if ((s)->counts != NULL) ++(s)->counts[n]; } while (0)

/* Diagnostic events use raw native storage during the scan. Python objects
 * are produced only afterward, so instrumentation cannot run GC callbacks while
 * borrowed container elements or function fields are being observed. */
static int record_read(Scan *s, const char *field, Py_ssize_t position, PyObject *value) {
    if (!s->tracing) return 0;
    if (s->event_count == s->event_capacity) {
        Py_ssize_t next = s->event_capacity == 0 ? 16384 : s->event_capacity * 2;
        if (next < s->event_capacity || (size_t)next > SIZE_MAX / sizeof(ReadEvent)) {
            PyErr_NoMemory(); return -1;
        }
        ReadEvent *events = PyMem_Realloc(s->events, (size_t)next * sizeof(ReadEvent));
        if (events == NULL) { PyErr_NoMemory(); return -1; }
        s->events = events; s->event_capacity = next;
    }
    ReadEvent *event = &s->events[s->event_count++];
    event->field = field; event->group = s->group_index; event->row = s->row_index;
    event->position = position; event->address = (uintptr_t)value;
    return 0;
}
#define READ(s, name, position, value) do { \
    if (record_read((s), (name), (position), (value)) < 0) return -1; \
} while (0)
static PyObject *serialize_events(Scan *s) {
    PyObject *events = PyList_New(s->event_count);
    if (events == NULL) return NULL;
    for (Py_ssize_t i = 0; i < s->event_count; ++i) {
        ReadEvent *event = &s->events[i];
        PyObject *identity = PyLong_FromVoidPtr((void *)event->address);
        if (identity == NULL) { Py_DECREF(events); return NULL; }
        PyObject *entry = Py_BuildValue("(snnnO)", event->field, event->group, event->row, event->position, identity);
        Py_DECREF(identity);
        if (entry == NULL) { Py_DECREF(events); return NULL; }
        PyList_SET_ITEM(events, i, entry);
    }
    return events;
}

static int tuple_size(PyObject *o, Py_ssize_t n) {
    return PyTuple_CheckExact(o) && PyTuple_GET_SIZE(o) == n;
}
static PyObject *none_if_null(PyObject *o) { return o == NULL ? Py_None : o; }
/* Fresh cell access is deliberately delayed until its original scan phase. */
static PyObject *load(Scan *s, Field field) {
    Py_ssize_t index = s->layout->indices[field];
    PyObject *cell = PyTuple_GET_ITEM(s->closure, index);
    if (!Py_IS_TYPE(cell, &PyCell_Type)) return NULL;
    PyObject *value = PyCell_GET(cell);
    return value == NULL ? NULL : Py_NewRef(value);
}
/* Native weak references retain exact immutable code identity without an
 * untracked CodeObject -> constants -> Cmodule ownership cycle.
 * Only immutable closure-name positions are retained. Actual cell contents are
 * freshly read at each original phase; no rows, operands or results are cached. */
static CodeLayout *prepare_layout(PyObject *code) {
    CodeLayout *layout = PyMem_Calloc(1, sizeof(CodeLayout));
    if (layout == NULL) { PyErr_NoMemory(); return NULL; }
    layout->code_ref = PyWeakref_NewRef(code, NULL);
    if (layout->code_ref == NULL) goto error;
    layout->names = PyCode_GetFreevars((PyCodeObject *)code);
    if (layout->names == NULL) goto error;
    for (int field = 0; field < FIELD_COUNT; ++field) {
        layout->indices[field] = -1;
        for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(layout->names); ++i) {
            PyObject *name = PyTuple_GET_ITEM(layout->names, i);
            if (!PyUnicode_CheckExact(name)) goto incomplete;
            if (PyUnicode_CompareWithASCIIString(name, field_names[field]) == 0) {
                if (layout->indices[field] >= 0) goto incomplete;
                layout->indices[field] = i;
            }
        }
        if (layout->indices[field] < 0) goto incomplete;
    }
    return layout;
incomplete:
    PyErr_SetString(PyExc_RuntimeError, "native binding requires the complete authored closure layout");
error:
    Py_XDECREF(layout->code_ref); Py_XDECREF(layout->names); PyMem_Free(layout); return NULL;
}
static void release_layout(CodeLayout *layout) {
    Py_XDECREF(layout->code_ref); Py_XDECREF(layout->names); PyMem_Free(layout);
}
/* Exact CPython 3.12 integer digits retain Python id() equality semantics.
 * Negative and out-of-pointer-range integers never match an object address. */
static int id_matches(PyObject *object, PyObject *expected) {
    if (!PyLong_CheckExact(expected)) return 0;
    PyLongObject *number = (PyLongObject *)expected;
    uintptr_t tag = number->long_value.lv_tag;
    if ((tag & _PyLong_SIGN_MASK) == 2) return 0;
    uintptr_t count = tag >> _PyLong_NON_SIZE_BITS;
    uintptr_t address = (uintptr_t)object;
    if (count == 2 && PyLong_SHIFT == 30) {
        return number->long_value.ob_digit[0] == (address & PyLong_MASK) &&
            number->long_value.ob_digit[1] == (address >> PyLong_SHIFT);
    }
    if (count > (sizeof(uintptr_t) * 8 + PyLong_SHIFT - 1) / PyLong_SHIFT) return 0;
    uintptr_t value = 0;
    for (uintptr_t i = count; i > 0; --i) {
        if (value > (UINTPTR_MAX >> PyLong_SHIFT)) return 0;
        value = (value << PyLong_SHIFT) | number->long_value.ob_digit[i - 1];
    }
    return address == value;
}
static int exact_string_keys(PyObject *dict) {
    Py_ssize_t pos = 0; PyObject *key, *value;
    if (!PyDict_CheckExact(dict)) return 0;
    /* Fresh representation proof, not a cached verdict: CPython 3.12 only
     * stores exact str keys in a unicode-key table. General tables (including
     * str subclasses, or formerly non-string keys) retain the original walk. */
    if (DK_IS_UNICODE(((PyDictObject *)dict)->ma_keys)) return 1;
    while (PyDict_Next(dict, &pos, &key, &value))
        if (!PyUnicode_CheckExact(key)) return 0;
    return 1;
}
/* One callback/allocation-free walk of a combined unicode table. The pinned
 * CPython header defines insertion order and holes. Both keys and values are
 * freshly compared; no version tag, retained address or successful admission
 * is reused. Split/general dictionaries keep the original iterator fallback.
 * -2 means the representation is not this fast path, never an acceptance. */
static int combined_namespace(PyObject *dict, PyObject *keys, PyObject *values,
                              int string_keys) {
    if (!PyDict_CheckExact(dict) || !PyTuple_CheckExact(keys) || !PyTuple_CheckExact(values)) return 0;
    Py_ssize_t count = PyDict_GET_SIZE(dict);
    if (count != PyTuple_GET_SIZE(keys) || count != PyTuple_GET_SIZE(values)) return 0;
    PyDictObject *mapping = (PyDictObject *)dict;
    if (mapping->ma_values != NULL || !DK_IS_UNICODE(mapping->ma_keys)) return -2;
    PyDictUnicodeEntry *entries = DK_UNICODE_ENTRIES(mapping->ma_keys);
    Py_ssize_t position = 0;
    for (Py_ssize_t i = 0; i < mapping->ma_keys->dk_nentries; ++i) {
        PyObject *value = entries[i].me_value;
        if (value == NULL) continue;
        if (position >= count) return 0;
        PyObject *key = entries[i].me_key;
        PyObject *expected = PyTuple_GET_ITEM(keys, position);
        if (string_keys) {
            if (!PyUnicode_CheckExact(key) || !PyUnicode_CheckExact(expected)) return 0;
            if (key != expected && PyUnicode_Compare(key, expected) != 0) return 0;
        } else if (key != expected) return 0;
        if (value != PyTuple_GET_ITEM(values, position++)) return 0;
    }
    return position == count;
}
static int ordered_keys(PyObject *dict, PyObject *names) {
    if (!PyDict_CheckExact(dict) || !PyTuple_CheckExact(names)) return 0;
    if (PyDict_GET_SIZE(dict) != PyTuple_GET_SIZE(names)) return 0;
    Py_ssize_t pos = 0, i = 0; PyObject *key, *value;
    while (PyDict_Next(dict, &pos, &key, &value)) {
        PyObject *expected = PyTuple_GET_ITEM(names, i++);
        if (!PyUnicode_CheckExact(key) || !PyUnicode_CheckExact(expected)) return 0;
        if (key != expected && PyUnicode_Compare(key, expected) != 0) return 0;
    }
    return 1;
}
static int dict_items_match(PyObject *dict, PyObject *items) {
    if (!PyDict_CheckExact(dict) || !PyTuple_CheckExact(items)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(items); ++i) {
        PyObject *pair = PyTuple_GET_ITEM(items, i);
        if (!tuple_size(pair, 2)) return 0;
        PyObject *name = PyTuple_GET_ITEM(pair, 0);
        if (!PyUnicode_CheckExact(name)) return 0;
        PyObject *actual = PyDict_GetItemWithError(dict, name);
        if (actual == NULL && PyErr_Occurred()) return -1;
        if (none_if_null(actual) != PyTuple_GET_ITEM(pair, 1)) return 0;
    }
    return 1;
}
/* Original foundation phase: local kind admission, state/refuse code fields,
 * complete current-key kind/order inspection, then every primitive value. */
static int scan_foundation(Scan *s) {
    if (s->kind_of != (PyObject *)&PyType_Type) return 0;
    const Field names[] = {FIELD_STATE, FIELD_STATE_CODE, FIELD_REFUSE, FIELD_REFUSE_CODE,
        FIELD_PRIMITIVE_NAMESPACE, FIELD_PRIMITIVE_KEYS, FIELD_PRIMITIVE_ITEMS, FIELD_STRING_KIND_ID,
        FIELD_NATIVE_ID, FIELD_GET, FIELD_CLASS_GET, FIELD_GET_DICT, FIELD_DICT_KEYS, FIELD_DICT_ITEMS,
        FIELD_NATIVE_TUPLE, FIELD_NATIVE_ANY};
    PyObject *values[16] = {NULL};
    int result = 0;
    for (int i = 0; i < 2; ++i) { values[i] = load(s, names[i]); if (values[i] == NULL) goto done; }
    if (!PyFunction_Check(values[0])) goto done;
    COUNT(s, FOUNDATION_CODE_READS);
    PyObject *state_code = PyFunction_GET_CODE(values[0]);
    if (record_read(s, "foundation.state.code", 0, state_code) < 0) { result = -1; goto done; }
    if (state_code != values[1]) goto done;
    for (int i = 2; i < 4; ++i) { values[i] = load(s, names[i]); if (values[i] == NULL) goto done; }
    if (!PyFunction_Check(values[2])) goto done;
    COUNT(s, FOUNDATION_CODE_READS);
    PyObject *refuse_code = PyFunction_GET_CODE(values[2]);
    if (record_read(s, "foundation.refuse.code", 1, refuse_code) < 0) { result = -1; goto done; }
    if (refuse_code != values[3]) goto done;
    for (int i = 4; i < 8; ++i) { values[i] = load(s, names[i]); if (values[i] == NULL) goto done; }
    PyObject *bank = values[4], *keys = values[5], *items = values[6];
    if (!PyDict_CheckExact(bank) || !PyTuple_CheckExact(keys) || !PyTuple_CheckExact(items)) goto done;
    Py_ssize_t pos = 0, index = 0; PyObject *key, *value;
    while (PyDict_Next(bank, &pos, &key, NULL)) {
        COUNT(s, FOUNDATION_KEYS);
        if (record_read(s, "foundation.key.kind", index++, (PyObject *)Py_TYPE(key)) < 0) { result = -1; goto done; }
        if (!PyUnicode_CheckExact(key) || !id_matches((PyObject *)Py_TYPE(key), values[7])) goto done;
    }
    if (!ordered_keys(bank, keys)) goto done;
    PyObject *mapping = NULL, *identity = NULL, *zipping = NULL;
    PyObject *type = NULL, *length = NULL, *value_error = NULL, *runtime_error = NULL;
    PyObject *dictionary = NULL, *frozen = NULL, *any = NULL;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(items); ++i) {
        PyObject *pair = PyTuple_GET_ITEM(items, i);
        if (!tuple_size(pair, 2)) goto done;
        PyObject *name = PyTuple_GET_ITEM(pair, 0), *expected = PyTuple_GET_ITEM(pair, 1);
        if (!PyUnicode_CheckExact(name)) goto done;
        value = PyDict_GetItemWithError(bank, name);
        if (value == NULL && PyErr_Occurred()) { result = -1; goto done; }
        value = none_if_null(value);
        COUNT(s, FOUNDATION_ITEMS);
        if (record_read(s, "foundation.item", i, value) < 0) { result = -1; goto done; }
        if (value != expected) goto done;
        if (PyUnicode_CompareWithASCIIString(name, "map") == 0) mapping = expected;
        else if (PyUnicode_CompareWithASCIIString(name, "id") == 0) identity = expected;
        else if (PyUnicode_CompareWithASCIIString(name, "zip") == 0) zipping = expected;
        else if (PyUnicode_CompareWithASCIIString(name, "type") == 0) type = expected;
        else if (PyUnicode_CompareWithASCIIString(name, "len") == 0) length = expected;
        else if (PyUnicode_CompareWithASCIIString(name, "ValueError") == 0) value_error = expected;
        else if (PyUnicode_CompareWithASCIIString(name, "RuntimeError") == 0) runtime_error = expected;
        else if (PyUnicode_CompareWithASCIIString(name, "dict") == 0) dictionary = expected;
        else if (PyUnicode_CompareWithASCIIString(name, "frozenset") == 0) frozen = expected;
        else if (PyUnicode_CompareWithASCIIString(name, "any") == 0) any = expected;
    }
    for (int i = 8; i < 16; ++i) { values[i] = load(s, names[i]); if (values[i] == NULL) goto done; }
    if (mapping != (PyObject *)&PyMap_Type || identity != s->module->native_id ||
        zipping != (PyObject *)&PyZip_Type || value_error != PyExc_ValueError ||
        runtime_error != PyExc_RuntimeError || dictionary != (PyObject *)&PyDict_Type ||
        frozen != (PyObject *)&PyFrozenSet_Type || type != (PyObject *)&PyType_Type ||
        length != s->module->native_length || s->mapping != mapping || s->zipping != zipping ||
        s->kind_of != type || s->size_of != length || values[8] != identity) goto done;
    /* Immutable originals are used by native scans and subsequent Python host
     * postlude. A changed captured accessor is rejected before it can dispatch. */
    if (values[9] != s->module->native_accessors[0] ||
        values[10] != s->module->native_accessors[1] ||
        values[11] != s->module->native_accessors[2] ||
        values[12] != s->module->native_accessors[3] ||
        values[13] != s->module->native_accessors[4] ||
        values[14] != (PyObject *)&PyTuple_Type || values[15] != s->module->native_any ||
        any != s->module->native_any) goto done;
    /* These actual pre-call locals, rather than subsequently reread cells, are
     * the only dispatch primitives permitted in the Python host postlude. */
    if (s->snapshots[0] != s->module->native_accessors[0] ||
        s->snapshots[1] != s->module->native_accessors[2] ||
        s->snapshots[2] != s->module->native_accessors[1] ||
        s->snapshots[3] != s->module->native_id ||
        s->snapshots[4] != (PyObject *)&PyTuple_Type ||
        s->snapshots[5] != s->module->native_any ||
        s->snapshots[6] != s->module->native_accessors[3] ||
        s->snapshots[7] != s->module->native_accessors[4]) goto done;
    result = 1;
done:
    for (int i = 0; i < 16; ++i) Py_XDECREF(values[i]);
    return result;
}
static int scan_modules(Scan *s) {
    PyObject *rows = load(s, FIELD_MODULE_ROWS);
    if (rows == NULL) return 0;
    int result = 0;
    if (!PyTuple_CheckExact(rows)) goto done;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 4)) goto done;
        COUNT(s, MODULE_ROWS);
        PyObject *module = PyTuple_GET_ITEM(row, 0);
        if (!PyModule_CheckExact(module)) goto done;
        PyObject *dict = PyModule_GetDict(module);
        if (!exact_string_keys(dict) || !ordered_keys(dict, PyTuple_GET_ITEM(row, 1))) goto done;
        int ok = dict_items_match(dict, PyTuple_GET_ITEM(row, 2));
        if (ok <= 0) { result = ok; goto done; }
        PyObject *absent = PyTuple_GET_ITEM(row, 3);
        if (!PyTuple_CheckExact(absent)) goto done;
        for (Py_ssize_t j = 0; j < PyTuple_GET_SIZE(absent); ++j) {
            PyObject *name = PyTuple_GET_ITEM(absent, j);
            if (!PyUnicode_CheckExact(name)) goto done;
            int found = PyDict_Contains(dict, name);
            if (found < 0) { result = -1; goto done; }
            if (found) goto done;
        }
    }
    result = 1;
done: Py_DECREF(rows); return result;
}
static int scan_regex(Scan *s) {
    PyObject *rows = load(s, FIELD_REGEX_CACHE_ROWS);
    if (rows == NULL) return 0;
    int result = 0;
    if (!PyTuple_CheckExact(rows)) goto done;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 3)) goto done;
        PyObject *module = PyTuple_GET_ITEM(row, 0), *name = PyTuple_GET_ITEM(row, 1);
        if (!PyModule_CheckExact(module) || !PyUnicode_CheckExact(name)) goto done;
        PyObject *cache = PyDict_GetItemWithError(PyModule_GetDict(module), name);
        if (cache == NULL && PyErr_Occurred()) { result = -1; goto done; }
        if (cache == NULL || !PyDict_CheckExact(cache)) goto done;
        int ok = id_matches(cache, PyTuple_GET_ITEM(row, 2));
        if (ok <= 0) { result = ok; goto done; }
    }
    result = 1;
done: Py_DECREF(rows); return result;
}
/* Admit the actual metaclass descriptor before reading the corresponding
 * native field. A custom descriptor is never invoked as a scan side effect. */
static int class_descriptor_admitted(Scan *s, PyObject *cls, int field) {
    PyTypeObject *meta = Py_TYPE(cls);
    if (meta == &PyType_Type) return 1; /* immutable original descriptors */
    PyObject *mro = meta->tp_mro;
    if (!PyTuple_CheckExact(mro)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(mro); ++i) {
        PyObject *base = PyTuple_GET_ITEM(mro, i);
        if (!PyType_Check(base)) return 0;
        PyObject *dict = PyType_GetDict((PyTypeObject *)base);
        if (dict == NULL) return PyErr_Occurred() ? -1 : 0;
        if (!exact_string_keys(dict)) { Py_DECREF(dict); return 0; }
        PyObject *descriptor = PyDict_GetItemWithError(dict, s->module->class_names[field]);
        int found = descriptor != NULL;
        int admitted = descriptor == s->module->class_descriptors[field];
        Py_DECREF(dict);
        if (!found && PyErr_Occurred()) return -1;
        if (found) return admitted;
    }
    return 0;
}
static int scan_class_row(Scan *s, PyObject *row) {
    if (!tuple_size(row, 7)) return 0;
    COUNT(s, CLASS_ROWS);
    PyObject *cls = PyTuple_GET_ITEM(row, 0);
    if ((PyObject *)Py_TYPE(cls) != PyTuple_GET_ITEM(row, 1) || !PyType_Check(cls)) return 0;
    PyTypeObject *type = (PyTypeObject *)cls;
    int ok = class_descriptor_admitted(s, cls, 0);
    if (ok <= 0) return ok;
    READ(s, "class.bases", 0, type->tp_bases);
    if (type->tp_bases != PyTuple_GET_ITEM(row, 2)) return 0;
    ok = class_descriptor_admitted(s, cls, 1);
    if (ok <= 0) return ok;
    READ(s, "class.mro", 1, type->tp_mro);
    if (type->tp_mro != PyTuple_GET_ITEM(row, 3)) return 0;
    PyObject *metadata = PyTuple_GET_ITEM(row, 4);
    if (!PyTuple_CheckExact(metadata)) return 0;
    for (Py_ssize_t j = 0; j < PyTuple_GET_SIZE(metadata); ++j) {
        PyObject *pair = PyTuple_GET_ITEM(metadata, j);
        if (!tuple_size(pair, 2)) return 0;
        PyObject *name = PyTuple_GET_ITEM(pair, 0);
        if (!PyUnicode_CheckExact(name)) return 0;
        int field = -1;
        for (int k = 2; k < 5; ++k)
            if (name == s->module->class_names[k] || PyUnicode_Compare(name, s->module->class_names[k]) == 0) { field = k; break; }
        /* The qualified metadata profile uses these three native type fields.
         * Nonstandard class metadata cannot invoke a descriptor speculatively. */
        if (field < 0) return 0;
        ok = class_descriptor_admitted(s, cls, field);
        if (ok <= 0) return ok;
        PyObject *actual = NULL;
        int owned = 0;
        if (type->tp_flags & Py_TPFLAGS_HEAPTYPE) {
            PyHeapTypeObject *heap = (PyHeapTypeObject *)cls;
            if (field == 2) actual = heap->ht_name;
            else if (field == 3) actual = heap->ht_qualname;
            else {
                PyObject *dict = PyType_GetDict(type);
                if (dict == NULL) return PyErr_Occurred() ? -1 : 0;
                if (!exact_string_keys(dict)) { Py_DECREF(dict); return 0; }
                PyObject *item = PyDict_GetItemWithError(dict, s->module->class_names[4]);
                if (item != NULL) { actual = Py_NewRef(item); owned = 1; }
                Py_DECREF(dict);
                if (actual == NULL) return PyErr_Occurred() ? -1 : 0;
            }
        } else {
            /* Static native types synthesize their native name/module strings.
             * Descriptor admission makes this original native accessor safe. */
            actual = PyType_Type.tp_getattro(cls, name);
            if (actual == NULL) return -1;
            owned = 1;
        }
        if (record_read(s, "class.metadata", j, actual) < 0) {
            if (owned) Py_DECREF(actual);
            return -1;
        }
        ok = actual == PyTuple_GET_ITEM(pair, 1);
        if (owned) Py_DECREF(actual);
        if (!ok) return 0;
    }
    ok = class_descriptor_admitted(s, cls, 5);
    if (ok <= 0) return ok;
    PyObject *dict = PyType_GetDict(type);
    if (dict == NULL) return PyErr_Occurred() ? -1 : 0;
    if (record_read(s, "class.dict", 5, dict) < 0) { Py_DECREF(dict); return -1; }
    if (!ordered_keys(dict, PyTuple_GET_ITEM(row, 6))) { Py_DECREF(dict); return 0; }
    ok = dict_items_match(dict, PyTuple_GET_ITEM(row, 5));
    Py_DECREF(dict);
    return ok;
}
static int scan_classes(Scan *s) {
    PyObject *rows = load(s, FIELD_CLASS_ROWS), *receivers = load(s, FIELD_RECEIVER_ROWS);
    PyObject **receiver_classes = NULL;
    int result = 0;
    if (rows == NULL || receivers == NULL) goto done;
    if (!PyTuple_CheckExact(rows) || !PyTuple_CheckExact(receivers)) goto done;
    Py_ssize_t n = PyTuple_GET_SIZE(receivers);
    if ((size_t)n > SIZE_MAX / sizeof(PyObject *)) { PyErr_NoMemory(); result = -1; goto done; }
    if (n > 0) {
        receiver_classes = PyMem_Malloc((size_t)n * sizeof(PyObject *));
        if (receiver_classes == NULL) { PyErr_NoMemory(); result = -1; goto done; }
    }
    /* Resolve every receiver's class row before the first ordinary class row,
     * as the original flattened native class-group expression does. */
    for (Py_ssize_t i = 0; i < n; ++i) {
        PyObject *row = PyTuple_GET_ITEM(receivers, i);
        if (!tuple_size(row, 3)) goto done;
        receiver_classes[i] = PyTuple_GET_ITEM(row, 2);
    }
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        s->group_index = 0; s->row_index = i;
        int ok = scan_class_row(s, PyTuple_GET_ITEM(rows, i));
        if (ok <= 0) { result = ok; goto done; }
    }
    for (Py_ssize_t i = 0; i < n; ++i) {
        s->group_index = 1; s->row_index = i;
        int ok = scan_class_row(s, receiver_classes[i]);
        if (ok <= 0) { result = ok; goto done; }
    }
    result = 1;
done: PyMem_Free(receiver_classes); Py_XDECREF(rows); Py_XDECREF(receivers); return result;
}

/* Rare fallback fingerprints eagerly collect raw addresses, then compare.
 * Native memory allocation cannot run Python GC/finalizer callbacks. All ids
 * are observed even when the first eventual comparison is a refusal. */
static int state_matches(Scan *s, PyObject *value, PyObject *expected, int data_phase) {
    COUNT(s, FALLBACK_STATES);
    PyObject *kind = (PyObject *)Py_TYPE(value);
    if (PyDict_CheckExact(value) && PyDict_GET_SIZE(value) > PY_SSIZE_T_MAX / 2) { PyErr_NoMemory(); return -1; }
    Py_ssize_t count = PyDict_CheckExact(value) ? PyDict_GET_SIZE(value) * 2 :
        PyTuple_CheckExact(value) ? PyTuple_GET_SIZE(value) :
        PyList_CheckExact(value) ? PyList_GET_SIZE(value) :
        (PySet_CheckExact(value) || PyFrozenSet_CheckExact(value)) ? PySet_GET_SIZE(value) : 1;
    if (count < 0 || (size_t)count > SIZE_MAX / sizeof(uintptr_t)) { PyErr_NoMemory(); return -1; }
    uintptr_t *addresses = count == 0 ? NULL : PyMem_Malloc((size_t)count * sizeof(uintptr_t));
    if (count != 0 && addresses == NULL) { PyErr_NoMemory(); return -1; }
    int result = 0;
    if (PyDict_CheckExact(value)) {
        Py_ssize_t key_pos = 0, value_pos = 0, i = 0; PyObject *key, *item;
        while (PyDict_Next(value, &key_pos, &key, NULL)) {
            COUNT(s, FALLBACK_IDENTITIES); if (data_phase) COUNT(s, DATA_IDENTITIES);
            addresses[i++] = (uintptr_t)key;
            if (record_read(s, data_phase ? "data.key" : "attributes.key", i / 2, key) < 0) { result = -1; goto done; }
            if (!PyDict_Next(value, &value_pos, NULL, &item)) goto done;
            COUNT(s, FALLBACK_IDENTITIES); if (data_phase) COUNT(s, DATA_IDENTITIES);
            addresses[i++] = (uintptr_t)item;
            if (record_read(s, data_phase ? "data.value" : "attributes.value", (i - 1) / 2, item) < 0) { result = -1; goto done; }
        }
        if (i != count) goto done;
    } else if (PyTuple_CheckExact(value) || PyList_CheckExact(value) || PySet_CheckExact(value) || PyFrozenSet_CheckExact(value)) {
        Py_ssize_t pos = 0; PyObject *item; Py_hash_t hash;
        for (Py_ssize_t i = 0; i < count; ++i) {
            if (PyTuple_CheckExact(value)) item = PyTuple_GET_ITEM(value, i);
            else if (PyList_CheckExact(value)) item = PyList_GET_ITEM(value, i);
            else if (!_PySet_NextEntry(value, &pos, &item, &hash)) goto done;
            COUNT(s, FALLBACK_IDENTITIES); if (data_phase) COUNT(s, DATA_IDENTITIES);
            addresses[i] = (uintptr_t)item;
            if (record_read(s, data_phase ? "data.item" : "attributes.item", i, item) < 0) { result = -1; goto done; }
        }
    } else {
        COUNT(s, FALLBACK_IDENTITIES); if (data_phase) COUNT(s, DATA_IDENTITIES);
        addresses[0] = (uintptr_t)value;
        if (record_read(s, data_phase ? "data.scalar" : "attributes.scalar", 0, value) < 0) { result = -1; goto done; }
    }
    /* Every actual identity has now been read, before expected shape, kind,
     * cardinality, or identity comparisons can short-circuit the refusal. */
    if (!tuple_size(expected, 2) || !id_matches(kind, PyTuple_GET_ITEM(expected, 0))) goto done;
    PyObject *ids = PyTuple_GET_ITEM(expected, 1);
    if (PyDict_CheckExact(value)) {
        if (!PyTuple_CheckExact(ids) || PyTuple_GET_SIZE(ids) != count / 2) goto done;
        for (Py_ssize_t i = 0; i < count / 2; ++i) {
            PyObject *pair = PyTuple_GET_ITEM(ids, i);
            if (!tuple_size(pair, 2) || !id_matches((PyObject *)addresses[2*i], PyTuple_GET_ITEM(pair, 0)) ||
                !id_matches((PyObject *)addresses[2*i+1], PyTuple_GET_ITEM(pair, 1))) goto done;
        }
    } else if (PyTuple_CheckExact(value) || PyList_CheckExact(value) || PySet_CheckExact(value) || PyFrozenSet_CheckExact(value)) {
        if (!PyTuple_CheckExact(ids) || PyTuple_GET_SIZE(ids) != count) goto done;
        for (Py_ssize_t i = 0; i < count; ++i)
            if (!id_matches((PyObject *)addresses[i], PyTuple_GET_ITEM(ids, i))) goto done;
    } else if (!id_matches((PyObject *)addresses[0], ids)) goto done;
    result = 1;
done: PyMem_Free(addresses); return result;
}
static int scan_function_row(Scan *s, PyObject *row) {
    if (!tuple_size(row, 7)) return 0;
    COUNT(s, FUNCTION_ROWS); COUNT(s, FUNCTION_KIND);
    PyObject *target = PyTuple_GET_ITEM(row, 0);
    if (!PyFunction_Check(target)) return 0;
    PyFunctionObject *function = (PyFunctionObject *)target;
    COUNT(s, FIXED_FIELDS);
    PyObject *actual_code = function->func_code;
    READ(s, "function.code", 0, actual_code);
    if (actual_code != PyTuple_GET_ITEM(row, 1)) return 0;
    COUNT(s, FIXED_FIELDS);
    PyObject *actual_defaults = none_if_null(function->func_defaults);
    READ(s, "function.defaults", 1, actual_defaults);
    if (actual_defaults != PyTuple_GET_ITEM(row, 2)) return 0;
    COUNT(s, FIXED_FIELDS);
    PyObject *actual_kwdefaults = none_if_null(function->func_kwdefaults);
    READ(s, "function.kwdefaults", 2, actual_kwdefaults);
    if (actual_kwdefaults != PyTuple_GET_ITEM(row, 3)) return 0;
    COUNT(s, FIXED_FIELDS);
    PyObject *attributes = PyTuple_GET_ITEM(row, 4);
    if (!tuple_size(attributes, 2)) return 0;
    PyObject *current = function->func_dict;
    if (current == NULL) {
        /* The native __dict__ descriptor creates a missing empty dictionary. */
        current = PyObject_GetAttrString(target, "__dict__");
        if (current == NULL) return -1;
    } else Py_INCREF(current);
    if (record_read(s, "function.dict", 3, current) < 0) { Py_DECREF(current); return -1; }
    int ok = 1;
    if (!PyDict_CheckExact(current) || current != PyTuple_GET_ITEM(attributes, 0))
        ok = state_matches(s, current, PyTuple_GET_ITEM(attributes, 1), 0);
    Py_DECREF(current);
    if (ok <= 0) return ok;
    PyObject *metadata = PyTuple_GET_ITEM(row, 5);
    if (!PyTuple_CheckExact(metadata)) return 0;
    for (Py_ssize_t j = 0; j < PyTuple_GET_SIZE(metadata); ++j) {
        PyObject *pair = PyTuple_GET_ITEM(metadata, j);
        if (!tuple_size(pair, 2)) return 0;
        PyObject *name = PyTuple_GET_ITEM(pair, 0);
        if (!PyUnicode_CheckExact(name)) return 0;
        COUNT(s, METADATA_FIELDS);
        /* Original immutable field names select direct native function slots.
         * Nonstandard metadata and lazily absent annotations use the exact
         * function type's original immutable native attribute accessor. */
        PyObject *actual = NULL;
        int owned = 0;
        if (name == s->metadata_names[0])
            actual = function->func_name;
        else if (name == s->metadata_names[1])
            actual = function->func_qualname;
        else if (name == s->metadata_names[2])
            actual = none_if_null(function->func_module);
        else if (name == s->metadata_names[3] &&
                 function->func_annotations != NULL && PyDict_CheckExact(function->func_annotations))
            actual = function->func_annotations;
        else {
            if (function->func_dict != NULL && !exact_string_keys(function->func_dict)) return 0;
            actual = PyObject_GetAttr(target, name);
            if (actual == NULL) return -1;
            owned = 1;
        }
        if (record_read(s, "function.metadata", j, actual) < 0) {
            if (owned) Py_DECREF(actual);
            return -1;
        }
        ok = actual == PyTuple_GET_ITEM(pair, 1);
        if (owned) Py_DECREF(actual);
        if (!ok) return 0;
    }
    PyObject *cells = PyTuple_GET_ITEM(row, 6);
    if (!PyTuple_CheckExact(cells)) return 0;
    for (Py_ssize_t j = 0; j < PyTuple_GET_SIZE(cells); ++j) {
        PyObject *pair = PyTuple_GET_ITEM(cells, j);
        if (!tuple_size(pair, 2)) return 0;
        PyObject *cell = PyTuple_GET_ITEM(pair, 0);
        COUNT(s, CELL_KIND);
        if (!Py_IS_TYPE(cell, &PyCell_Type)) return 0;
        COUNT(s, CELL_FIELDS);
        PyObject *actual = PyCell_GET(cell);
        if (actual == NULL) { PyErr_SetString(PyExc_ValueError, "Cell is empty"); return -1; }
        READ(s, "cell.contents", j, actual);
        if (actual != PyTuple_GET_ITEM(pair, 1)) return 0;
    }
    return 1;
}
static int scan_functions(Scan *s) {
    PyObject *groups[2] = {load(s, FIELD_FUNCTION_ROWS), load(s, FIELD_RECEIVER_FUNCTION_ROWS)};
    int result = 0;
    if (groups[0] == NULL || groups[1] == NULL) goto done;
    for (int g = 0; g < 2; ++g) {
        if (!PyTuple_CheckExact(groups[g])) goto done;
        for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(groups[g]); ++i) {
            s->group_index = g; s->row_index = i;
            int ok = scan_function_row(s, PyTuple_GET_ITEM(groups[g], i));
            if (ok <= 0) { result = ok; goto done; }
        }
    }
    result = 1;
done: Py_XDECREF(groups[0]); Py_XDECREF(groups[1]); return result;
}
static int scan_data_row(Scan *s, PyObject *row) {
    if (!tuple_size(row, 2)) return 0;
    COUNT(s, DATA_ROWS);
    PyObject *value = PyTuple_GET_ITEM(row, 0), *expected = PyTuple_GET_ITEM(row, 1);
    if (!tuple_size(expected, 2)) return 0;
    PyObject *kind_id = PyTuple_GET_ITEM(expected, 0), *ids = PyTuple_GET_ITEM(expected, 1);
    int dictionary_expected = id_matches((PyObject *)&PyDict_Type, kind_id);
    if (dictionary_expected < 0) return -1;
    COUNT(s, DATA_KIND);
    if (dictionary_expected) {
        if (!PyDict_CheckExact(value)) return 0;
        COUNT(s, DATA_LENGTH); COUNT(s, DATA_LENGTH);
        if (!PyTuple_CheckExact(ids) || PyDict_GET_SIZE(value) != PyTuple_GET_SIZE(ids)) return 0;
        Py_ssize_t key_pos = 0, value_pos = 0, i = 0; PyObject *key, *item;
        while (PyDict_Next(value, &key_pos, &key, NULL)) {
            PyObject *pair = PyTuple_GET_ITEM(ids, i++);
            if (!tuple_size(pair, 2)) return 0;
            /* Observe key then value, before checking either expected identity. */
            COUNT(s, DATA_IDENTITIES); uintptr_t key_id = (uintptr_t)key;
            READ(s, "data.key", i - 1, key);
            if (!PyDict_Next(value, &value_pos, NULL, &item)) return 0;
            COUNT(s, DATA_IDENTITIES); uintptr_t item_id = (uintptr_t)item;
            READ(s, "data.value", i - 1, item);
            int key_ok = id_matches((PyObject *)key_id, PyTuple_GET_ITEM(pair, 0));
            if (key_ok <= 0) return key_ok;
            int item_ok = id_matches((PyObject *)item_id, PyTuple_GET_ITEM(pair, 1));
            if (item_ok <= 0) return item_ok;
        }
        return 1;
    }
    if (PyTuple_CheckExact(value) || PyList_CheckExact(value) || PySet_CheckExact(value) || PyFrozenSet_CheckExact(value)) {
        int ok = id_matches((PyObject *)Py_TYPE(value), kind_id);
        if (ok <= 0) return ok;
        if (!PyTuple_CheckExact(ids)) return 0;
        COUNT(s, DATA_LENGTH); COUNT(s, DATA_LENGTH);
        Py_ssize_t count = PyTuple_CheckExact(value) ? PyTuple_GET_SIZE(value) :
            PyList_CheckExact(value) ? PyList_GET_SIZE(value) : PySet_GET_SIZE(value);
        if (count != PyTuple_GET_SIZE(ids)) return 0;
        Py_ssize_t pos = 0; PyObject *item; Py_hash_t hash;
        for (Py_ssize_t i = 0; i < count; ++i) {
            if (PyTuple_CheckExact(value)) item = PyTuple_GET_ITEM(value, i);
            else if (PyList_CheckExact(value)) item = PyList_GET_ITEM(value, i);
            else if (!_PySet_NextEntry(value, &pos, &item, &hash)) return 0;
            COUNT(s, DATA_IDENTITIES);
            READ(s, "data.item", i, item);
            ok = id_matches(item, PyTuple_GET_ITEM(ids, i));
            if (ok <= 0) return ok;
        }
        return 1;
    }
    return state_matches(s, value, expected, 1);
}
static int scan_data(Scan *s) {
    PyObject *groups[2] = {load(s, FIELD_DATA_ROWS), load(s, FIELD_RECEIVER_DATA_ROWS)};
    int result = 0;
    if (groups[0] == NULL || groups[1] == NULL) goto done;
    for (int g = 0; g < 2; ++g) {
        if (!PyTuple_CheckExact(groups[g])) goto done;
        for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(groups[g]); ++i) {
            s->group_index = g; s->row_index = i;
            int ok = scan_data_row(s, PyTuple_GET_ITEM(groups[g], i));
            if (ok <= 0) { result = ok; goto done; }
        }
    }
    result = 1;
done: Py_XDECREF(groups[0]); Py_XDECREF(groups[1]); return result;
}
/* The host continuation uses only this invocation's immutable local bank.
 * Match original native types without consulting mutable Python namespaces.
 * Receiver ownership is freshly read after all scan-time lazy allocations,
 * and again after diagnostic report allocations before accepted publication. */
static int final_acceptance(Scan *s, PyObject *check, PyObject *code) {
    if (!PyFunction_Check(check) || PyFunction_GET_CODE(check) != code) return 0;
    if (s->host_context != NULL) {
        PyObject *bank = s->host_context;
        if (!tuple_size(bank, 26)) return 0;
        PyTypeObject *types[12] = {&PyType_Type, &PyUnicode_Type, &PyDict_Type,
            &PyList_Type, &PyTuple_Type, &PySet_Type, &PyFrozenSet_Type,
            &PyFunction_Type, &PyModule_Type, &PyClassMethod_Type,
            &PyStaticMethod_Type, &PyProperty_Type};
        for (int i = 0; i < 12; ++i)
            if (PyTuple_GET_ITEM(bank, i) != (PyObject *)types[i]) return 0;
        PyObject *modules = PyTuple_GET_ITEM(bank, 12);
        if (!PyDict_CheckExact(modules) || modules != PyImport_GetModuleDict()) return 0;
        PyObject *closure = PyFunction_GET_CLOSURE(check);
        if (closure == NULL || !tuple_size(closure, PyTuple_GET_SIZE(s->layout->names))) return 0;
        const Field fields[13] = {FIELD_HOST, FIELD_HOST_BINDINGS, FIELD_NAMESPACE,
            FIELD_EXECUTION_NAMESPACE, FIELD_RECEIVER_ROWS, FIELD_RECEIVER_FUNCTION_ROWS,
            FIELD_RECEIVER_DATA_ROWS, FIELD_OPERATION, FIELD_PROTECTED,
            FIELD_RECEIVER_OWNER, FIELD_CHECK_CODE, FIELD_CHECK, FIELD_BINDING_FAILURE};
        for (int i = 0; i < 13; ++i) {
            PyObject *cell = PyTuple_GET_ITEM(closure, s->layout->indices[fields[i]]);
            if (!Py_IS_TYPE(cell, &PyCell_Type) ||
                    PyCell_GET(cell) != PyTuple_GET_ITEM(bank, 13+i)) return 0;
        }
        if (PyTuple_GET_ITEM(bank, 13) != Py_True) return 0;
        PyObject *bindings = PyTuple_GET_ITEM(bank, 14);
        if (!PyTuple_CheckExact(bindings)) return 0;
        for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(bindings); ++i) {
            PyObject *row = PyTuple_GET_ITEM(bindings, i);
            if (!tuple_size(row, 3) || !PyUnicode_CheckExact(PyTuple_GET_ITEM(row, 0)) ||
                    !PyBool_Check(PyTuple_GET_ITEM(row, 1))) return 0;
        }
        if (!exact_string_keys(PyTuple_GET_ITEM(bank, 15)) ||
                !exact_string_keys(PyTuple_GET_ITEM(bank, 16))) return 0;
        PyObject *receiver_rows = PyTuple_GET_ITEM(bank, 17);
        if (!PyTuple_CheckExact(receiver_rows) ||
                !PyTuple_CheckExact(PyTuple_GET_ITEM(bank, 18)) ||
                !PyTuple_CheckExact(PyTuple_GET_ITEM(bank, 19))) return 0;
        for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(receiver_rows); ++i) {
            PyObject *entry = PyTuple_GET_ITEM(receiver_rows, i);
            if (!tuple_size(entry, 3) || !exact_string_keys(PyTuple_GET_ITEM(entry, 0)) ||
                    !PyUnicode_CheckExact(PyTuple_GET_ITEM(entry, 1))) return 0;
            PyObject *row = PyTuple_GET_ITEM(entry, 2);
            if (!tuple_size(row, 7) || !Py_IS_TYPE(PyTuple_GET_ITEM(row, 0), &PyType_Type) ||
                    PyTuple_GET_ITEM(row, 1) != (PyObject *)&PyType_Type) return 0;
        }
        if (!PyFunction_Check(PyTuple_GET_ITEM(bank, 20)) ||
                !PyFunction_Check(PyTuple_GET_ITEM(bank, 21)) ||
                PyTuple_GET_ITEM(bank, 23) != code ||
                PyTuple_GET_ITEM(bank, 24) != check) return 0;
        PyObject *owner = PyTuple_GET_ITEM(bank, 22);
        if (owner != Py_None) {
            if (!Py_IS_TYPE(owner, &PyType_Type)) return 0;
            PyObject *rows_cell = PyTuple_GET_ITEM(closure, s->layout->indices[FIELD_RECEIVER_ROWS]);
            if (!Py_IS_TYPE(rows_cell, &PyCell_Type)) return 0;
            PyObject *rows = PyCell_GET(rows_cell);
            if (rows == NULL || !PyTuple_CheckExact(rows)) return 0;
            int registered = 0;
            for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
                PyObject *entry = PyTuple_GET_ITEM(rows, i);
                if (!tuple_size(entry, 3)) return 0;
                PyObject *row = PyTuple_GET_ITEM(entry, 2);
                if (!tuple_size(row, 7)) return 0;
                if (PyTuple_GET_ITEM(row, 0) == owner &&
                        PyTuple_GET_ITEM(row, 1) == (PyObject *)&PyType_Type) registered = 1;
            }
            if (!registered) return 0;
        }
    }
    return PyFunction_GET_CODE(check) == code;
}
static int run_scan(Scan *s, PyObject *check, PyObject *code) {
    if (!PyFunction_Check(check) || !PyCode_Check(code) || PyFunction_GET_CODE(check) != code) return 0;
    s->check = check;
    s->layout = s->module->layouts;
    while (s->layout != NULL && PyWeakref_GET_OBJECT(s->layout->code_ref) != code) s->layout = s->layout->next;
    if (s->layout == NULL) return 0;
    s->closure = PyFunction_GET_CLOSURE(check);
    if (s->closure == NULL || !PyTuple_CheckExact(s->closure) ||
            PyTuple_GET_SIZE(s->closure) != PyTuple_GET_SIZE(s->layout->names)) return 0;
    Py_INCREF(s->closure);
    int result = final_acceptance(s, check, code);
    if (result > 0) result = scan_foundation(s);
    if (result > 0) result = scan_modules(s);
    if (result > 0) result = scan_regex(s);
    if (result > 0) result = scan_classes(s);
    if (result > 0) result = scan_functions(s);
    if (result > 0) result = scan_data(s);
    if (result > 0) result = final_acceptance(s, check, code);
    Py_CLEAR(s->closure);
    if (result == 0 && PyErr_Occurred()) return -1;
    return result;
}
static PyObject *scan(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 14 && nargs != 15) { PyErr_SetString(PyExc_TypeError, "scan requires fourteen inputs and optional host context"); return NULL; }
    ModuleState *state = (ModuleState *)PyModule_GetState(self);
    Scan context = {.module = state, .metadata_names = state->metadata_names,
        .mapping = args[2], .zipping = args[3], .kind_of = args[4], .size_of = args[5]};
    for (int i = 0; i < 8; ++i) context.snapshots[i] = args[6+i];
    if (nargs == 15) context.host_context = args[14];
    int result = run_scan(&context, args[0], args[1]);
    if (result < 0) return NULL;
    return PyBool_FromLong(result);
}
static PyObject *observe(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs < 14 || nargs > 16) { PyErr_SetString(PyExc_TypeError, "observe requires fourteen inputs, optional host context and optional exact bool"); return NULL; }
    PyObject *host_context = NULL, *trace_option = Py_False;
    if (nargs == 15) {
        if (PyBool_Check(args[14])) trace_option = args[14];
        else host_context = args[14];
    } else if (nargs == 16) {
        host_context = args[14]; trace_option = args[15];
        if (!PyBool_Check(trace_option)) { PyErr_SetString(PyExc_TypeError, "trace option must be exact bool"); return NULL; }
    }
    unsigned long long counts[COUNT_SIZE] = {0};
    ModuleState *state = (ModuleState *)PyModule_GetState(self);
    Scan context = {.counts = counts, .module = state, .metadata_names = state->metadata_names,
        .mapping = args[2], .zipping = args[3], .kind_of = args[4], .size_of = args[5],
        .tracing = trace_option == Py_True, .host_context = host_context};
    for (int i = 0; i < 8; ++i) context.snapshots[i] = args[6+i];
    int result = run_scan(&context, args[0], args[1]);
    if (result < 0) { PyMem_Free(context.events); return NULL; }
    PyObject *report = PyDict_New();
    if (report == NULL) { PyMem_Free(context.events); return NULL; }
    if (context.tracing) {
        PyObject *trace = serialize_events(&context);
        if (trace == NULL) goto error;
        int ok = PyDict_SetItemString(report, "trace", trace);
        Py_DECREF(trace);
        if (ok < 0) goto error;
    }
    PyMem_Free(context.events); context.events = NULL;
    for (int i = 0; i < COUNT_SIZE; ++i) {
        PyObject *value = PyLong_FromUnsignedLongLong(counts[i]);
        if (value == NULL) goto error;
        int ok = PyDict_SetItemString(report, count_names[i], value);
        Py_DECREF(value);
        if (ok < 0) goto error;
    }
    if (result > 0) result = final_acceptance(&context, args[0], args[1]);
    if (PyDict_SetItemString(report, "accepted", result ? Py_True : Py_False) < 0) goto error;
    return report;
error: PyMem_Free(context.events); Py_DECREF(report); return NULL;
}
/* Install-time binding replaces only one explicitly authored sentinel constant.
 * It neither parses nor compiles a new body. The unchanged bytecode and closure
 * layout subsequently load the original native builtin from admitted immutable
 * code, instead of selecting it through mutable globals or captured cells. */
static PyObject *replace_constants(PyObject *code, PyObject *constants) {
    if (!PyCode_Check(code) || !PyTuple_CheckExact(constants)) {
        PyErr_SetString(PyExc_TypeError, "native binding requires exact code and constants");
        return NULL;
    }
    PyObject *replace = PyObject_GetAttrString(code, "replace");
    if (replace == NULL) return NULL;
    PyObject *args = PyTuple_New(0), *kwargs = PyDict_New();
    if (args == NULL || kwargs == NULL || PyDict_SetItemString(kwargs, "co_consts", constants) < 0) {
        Py_XDECREF(args); Py_XDECREF(kwargs); Py_DECREF(replace); return NULL;
    }
    PyObject *result = PyObject_Call(replace, args, kwargs);
    Py_DECREF(args); Py_DECREF(kwargs); Py_DECREF(replace);
    return result;
}
static PyObject *bind_installer(PyObject *self, PyObject *installer) {
    if (!PyFunction_Check(installer)) {
        PyErr_SetString(PyExc_TypeError, "native binding requires an exact installer function"); return NULL;
    }
    ModuleState *state = (ModuleState *)PyModule_GetState(self);
    PyObject *outer = Py_NewRef(PyFunction_GET_CODE(installer));
    PyObject *new_check = NULL, *new_outer = NULL, *constants = NULL;
    CodeLayout *layout = NULL;
    if (!PyCode_Check(outer)) goto ambiguous;
    PyObject *outer_constants = ((PyCodeObject *)outer)->co_consts;
    Py_ssize_t check_index = -1;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(outer_constants); ++i) {
        PyObject *item = PyTuple_GET_ITEM(outer_constants, i);
        if (PyCode_Check(item) && PyUnicode_CompareWithASCIIString(((PyCodeObject *)item)->co_name, "check") == 0) {
            if (check_index >= 0) goto ambiguous;
            check_index = i;
        }
    }
    if (check_index < 0) goto ambiguous;
    PyObject *check = PyTuple_GET_ITEM(outer_constants, check_index);
    PyObject *check_constants = ((PyCodeObject *)check)->co_consts;
    Py_ssize_t scan_index = -1, state_index = -1;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(check_constants); ++i) {
        PyObject *item = PyTuple_GET_ITEM(check_constants, i);
        if (!PyUnicode_CheckExact(item)) continue;
        if (PyUnicode_CompareWithASCIIString(item, "__aware_native_preparation_scan_anchor_v1__") == 0) {
            if (scan_index >= 0) goto ambiguous;
            scan_index = i;
        } else if (PyUnicode_CompareWithASCIIString(item, "__aware_native_preparation_state_anchor_v1__") == 0) {
            if (state_index >= 0) goto ambiguous;
            state_index = i;
        }
    }
    if (scan_index < 0 || state_index < 0) goto ambiguous;
    constants = PyTuple_New(PyTuple_GET_SIZE(check_constants));
    if (constants == NULL) goto error;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(check_constants); ++i) {
        PyObject *item = i == scan_index ? state->scan_builtin :
            i == state_index ? state->fingerprint_builtin : PyTuple_GET_ITEM(check_constants, i);
        PyTuple_SET_ITEM(constants, i, Py_NewRef(item));
    }
    new_check = replace_constants(check, constants); Py_CLEAR(constants);
    if (new_check == NULL) goto error;
    layout = prepare_layout(new_check);
    if (layout == NULL) goto error;
    constants = PyTuple_New(PyTuple_GET_SIZE(outer_constants));
    if (constants == NULL) goto error;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(outer_constants); ++i)
        PyTuple_SET_ITEM(constants, i, Py_NewRef(i == check_index ? new_check : PyTuple_GET_ITEM(outer_constants, i)));
    new_outer = replace_constants(outer, constants); Py_CLEAR(constants);
    if (new_outer == NULL) goto error;
    if (PyFunction_GET_CODE(installer) != outer) goto ambiguous;
    if (PyObject_SetAttrString(installer, "__code__", new_outer) < 0) goto error;
    /* Append a new exact weak CodeObject layout without replacing older records.
     * Installer mutation happens only after both anchors and layout exist. */
    layout->next = state->layouts; state->layouts = layout; layout = NULL;
    Py_DECREF(new_check); Py_DECREF(new_outer); Py_DECREF(outer); Py_RETURN_NONE;
ambiguous:
    PyErr_SetString(PyExc_RuntimeError, "native binding requires one authored scan and state sentinel");
error:
    Py_XDECREF(constants); Py_XDECREF(new_check); Py_XDECREF(new_outer); Py_DECREF(outer);
    if (layout != NULL) release_layout(layout);
    return NULL;
}

static void release_topology_layout(TopologyLayout *layout) {
    Py_XDECREF(layout->code_ref); Py_XDECREF(layout->names); PyMem_Free(layout);
}
static void prune_topology_layouts(ModuleState *state) {
    TopologyLayout **slot = &state->topology_layouts;
    while (*slot != NULL) {
        TopologyLayout *item = *slot;
        if (PyWeakref_GET_OBJECT(item->code_ref) == Py_None) {
            *slot = item->next; release_topology_layout(item);
        } else slot = &item->next;
    }
}
static TopologyLayout *prepare_topology_layout(PyObject *code, Py_ssize_t anchor) {
    TopologyLayout *layout = PyMem_Calloc(1, sizeof(TopologyLayout));
    if (layout == NULL) { PyErr_NoMemory(); return NULL; }
    layout->anchor = anchor;
    layout->code_ref = PyWeakref_NewRef(code, NULL);
    if (layout->code_ref == NULL) goto error;
    layout->names = PyCode_GetFreevars((PyCodeObject *)code);
    if (layout->names == NULL) goto error;
    for (int field = 0; field < T_COUNT; ++field) {
        layout->indices[field] = -1;
        for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(layout->names); ++i) {
            PyObject *name = PyTuple_GET_ITEM(layout->names, i);
            if (!PyUnicode_CheckExact(name)) goto incomplete;
            if (PyUnicode_CompareWithASCIIString(name, topology_names[field]) == 0) {
                if (layout->indices[field] >= 0) goto incomplete;
                layout->indices[field] = i;
            }
        }
        if (layout->indices[field] < 0) goto incomplete;
    }
    return layout;
incomplete: PyErr_SetString(PyExc_RuntimeError, "topology checker has an unsupported closure layout");
error: release_topology_layout(layout); return NULL;
}
static Py_ssize_t one_nested_code(PyObject *code, const char *name) {
    PyObject *constants = ((PyCodeObject *)code)->co_consts;
    Py_ssize_t found = -1;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(constants); ++i) {
        PyObject *item = PyTuple_GET_ITEM(constants, i);
        if (PyCode_Check(item) && PyUnicode_CompareWithASCIIString(((PyCodeObject *)item)->co_name, name) == 0) {
            if (found >= 0) return -1;
            found = i;
        }
    }
    return found;
}
static PyObject *replace_one_constant(PyObject *code, Py_ssize_t index, PyObject *replacement) {
    PyObject *old = ((PyCodeObject *)code)->co_consts;
    PyObject *constants = PyTuple_New(PyTuple_GET_SIZE(old));
    if (constants == NULL) return NULL;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(old); ++i)
        PyTuple_SET_ITEM(constants, i, Py_NewRef(i == index ? replacement : PyTuple_GET_ITEM(old, i)));
    PyObject *result = replace_constants(code, constants); Py_DECREF(constants);
    return result;
}
static PyObject *bind_topology_installer(PyObject *self, PyObject *installer) {
    if (!PyFunction_Check(installer)) { PyErr_SetString(PyExc_TypeError, "topology binding requires an original installer function"); return NULL; }
    ModuleState *state = PyModule_GetState(self);
    PyObject *outer = Py_NewRef(PyFunction_GET_CODE(installer));
    PyObject *new_check = NULL, *new_seal = NULL, *new_outer = NULL;
    TopologyLayout *layout = NULL;
    Py_ssize_t seal_index = one_nested_code(outer, "seal");
    if (seal_index < 0) goto ambiguous;
    PyObject *seal = PyTuple_GET_ITEM(((PyCodeObject *)outer)->co_consts, seal_index);
    Py_ssize_t check_index = one_nested_code(seal, "check");
    if (check_index < 0) goto ambiguous;
    PyObject *check = PyTuple_GET_ITEM(((PyCodeObject *)seal)->co_consts, check_index);
    PyObject *constants = ((PyCodeObject *)check)->co_consts;
    Py_ssize_t anchor = -1;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(constants); ++i) {
        PyObject *item = PyTuple_GET_ITEM(constants, i);
        if (PyUnicode_CheckExact(item) && PyUnicode_CompareWithASCIIString(item, "__aware_native_topology_scan_anchor_v1__") == 0) {
            if (anchor >= 0) goto ambiguous;
            anchor = i;
        }
    }
    if (anchor < 0) goto ambiguous;
    new_check = replace_one_constant(check, anchor, state->topology_builtin);
    if (new_check == NULL) goto error;
    layout = prepare_topology_layout(new_check, anchor);
    if (layout == NULL) goto error;
    new_seal = replace_one_constant(seal, check_index, new_check);
    if (new_seal == NULL) goto error;
    new_outer = replace_one_constant(outer, seal_index, new_seal);
    if (new_outer == NULL) goto error;
    if (PyFunction_GET_CODE(installer) != outer) goto ambiguous;
    if (PyObject_SetAttrString(installer, "__code__", new_outer) < 0) goto error;
    prune_topology_layouts(state);
    layout->next = state->topology_layouts; state->topology_layouts = layout; layout = NULL;
    Py_DECREF(new_check); Py_DECREF(new_seal); Py_DECREF(new_outer); Py_DECREF(outer);
    Py_RETURN_NONE;
ambiguous: PyErr_SetString(PyExc_RuntimeError, "topology binding requires one seal, checker and authored sentinel");
error:
    Py_XDECREF(new_check); Py_XDECREF(new_seal); Py_XDECREF(new_outer); Py_DECREF(outer);
    if (layout != NULL) release_topology_layout(layout);
    return NULL;
}

typedef struct {
    Scan observations;
    TopologyLayout *layout;
    PyObject *closure;
    PyObject *held[T_COUNT];
} TopologyScan;
static PyObject *topology_load(TopologyScan *s, int field) {
    if (s->held[field] != NULL) return s->held[field];
    PyObject *cell = PyTuple_GET_ITEM(s->closure, s->layout->indices[field]);
    if (!Py_IS_TYPE(cell, &PyCell_Type)) return NULL;
    PyObject *value = PyCell_GET(cell);
    if (value == NULL) return NULL;
    s->held[field] = Py_NewRef(value);
    return value;
}
/* These walks allocate no GC-tracked objects and never invoke operands.
 * Observations are accumulated in raw memory and serialized only afterward. */
static int topology_namespace(Scan *s, PyObject *dict, PyObject *keys, PyObject *values, int string_keys) {
    if (!s->tracing) {
        int direct = combined_namespace(dict, keys, values, string_keys);
        if (direct != -2) return direct;
    }
    if (!PyDict_CheckExact(dict) || !PyTuple_CheckExact(keys) || !PyTuple_CheckExact(values)) return 0;
    Py_ssize_t n = PyDict_GET_SIZE(dict), pos = 0, i = 0;
    if (n != PyTuple_GET_SIZE(keys) || n != PyTuple_GET_SIZE(values)) return 0;
    int matches = 1; PyObject *key, *value;
    while (PyDict_Next(dict, &pos, &key, NULL)) {
        READ(s, "topology.key.kind", i, (PyObject *)Py_TYPE(key));
        READ(s, "topology.key", i, key);
        PyObject *expected = PyTuple_GET_ITEM(keys, i++);
        if (string_keys) {
            if (!PyUnicode_CheckExact(key) || !PyUnicode_CheckExact(expected)) matches = 0;
            else if (key != expected && PyUnicode_Compare(key, expected) != 0) matches = 0;
        } else if (key != expected) matches = 0;
    }
    if (!matches) return 0;
    pos = 0; i = 0;
    while (PyDict_Next(dict, &pos, NULL, &value)) {
        READ(s, "topology.value", i, value);
        if (value != PyTuple_GET_ITEM(values, i++)) matches = 0;
    }
    return matches;
}
static int topology_key_kinds(Scan *s, PyObject *dict) {
    if (!s->tracing) return exact_string_keys(dict);
    if (!PyDict_CheckExact(dict)) return 0;
    Py_ssize_t pos = 0, i = 0; PyObject *key;
    int matches = 1;
    while (PyDict_Next(dict, &pos, &key, NULL)) {
        READ(s, "topology.key.kind", i++, (PyObject *)Py_TYPE(key));
        if (!PyUnicode_CheckExact(key)) matches = 0;
    }
    return matches;
}
static PyObject *topology_get_receiver(ModuleState *state, PyObject *getter) {
    if (!PyCFunction_Check(getter) || !Py_IS_TYPE(state->native_accessors[2], &PyMethodDescr_Type)) return NULL;
    if (PyCFunction_GET_FUNCTION(getter) != ((PyMethodDescrObject *)state->native_accessors[2])->d_method->ml_meth) return NULL;
    PyObject *receiver = PyCFunction_GET_SELF(getter);
    return receiver != NULL && PyDict_CheckExact(receiver) ? receiver : NULL;
}
static int topology_class_labels(Scan *s, PyObject *cls, PyObject *labels) {
    if (!PyType_Check(cls) || !PyTuple_CheckExact(labels)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(labels); ++i) {
        PyObject *pair = PyTuple_GET_ITEM(labels, i);
        if (!tuple_size(pair, 2) || !PyUnicode_CheckExact(PyTuple_GET_ITEM(pair, 0))) return 0;
        int field = -1;
        for (int j = 2; j <= 4; ++j)
            if (PyTuple_GET_ITEM(pair, 0) == s->module->class_names[j] || PyUnicode_Compare(PyTuple_GET_ITEM(pair, 0), s->module->class_names[j]) == 0) { field = j; break; }
        if (field < 0) return 0;
        int ok = class_descriptor_admitted(s, cls, field);
        /* Enum metaclasses carry an ordinary __module__ string. It is a
         * NON-data attribute: the class's own module field wins. Never invoke
         * a foreign data descriptor to discover whether it would agree. */
        if (ok == 0 && field == 4 && PyTuple_CheckExact(Py_TYPE(cls)->tp_mro)) {
            PyObject *mro = Py_TYPE(cls)->tp_mro;
            for (Py_ssize_t j = 0; j < PyTuple_GET_SIZE(mro); ++j) {
                PyObject *base = PyTuple_GET_ITEM(mro, j);
                if (!PyType_Check(base)) break;
                PyObject *dict = PyType_GetDict((PyTypeObject *)base);
                if (dict == NULL) return -1;
                if (!exact_string_keys(dict)) { Py_DECREF(dict); break; }
                PyObject *descriptor = PyDict_GetItemWithError(dict, s->module->class_names[field]);
                if (descriptor != NULL) {
                    ok = !PyDescr_IsData(descriptor);
                    Py_DECREF(dict); break;
                }
                Py_DECREF(dict);
            }
        }
        if (ok <= 0) return ok;
        PyObject *actual = NULL; int owned = 0;
        if (((PyTypeObject *)cls)->tp_flags & Py_TPFLAGS_HEAPTYPE) {
            if (field == 2) actual = ((PyHeapTypeObject *)cls)->ht_name;
            else if (field == 3) actual = ((PyHeapTypeObject *)cls)->ht_qualname;
            else {
                PyObject *dict = PyType_GetDict((PyTypeObject *)cls);
                if (dict == NULL) return -1;
                if (!exact_string_keys(dict)) { Py_DECREF(dict); return 0; }
                actual = PyDict_GetItemWithError(dict, s->module->class_names[field]);
                Py_XINCREF(actual); owned = actual != NULL; Py_DECREF(dict);
                if (actual == NULL) return PyErr_Occurred() ? -1 : 0;
            }
        } else {
            actual = PyType_Type.tp_getattro(cls, s->module->class_names[field]);
            if (actual == NULL) return -1;
            owned = 1;
        }
        int traced = record_read(s, "topology.class.label", i, actual);
        ok = actual == PyTuple_GET_ITEM(pair, 1);
        if (owned) Py_DECREF(actual);
        if (traced < 0) return -1;
        if (!ok) return 0;
    }
    return 1;
}
static int topology_body(TopologyScan *context, PyObject *check, PyObject *code) {
    Scan *s = &context->observations;
    PyObject *get_sys = topology_load(context, T_SYS_GET), *get_registry = topology_load(context, T_REGISTRY_GET);
    if (get_sys == NULL || get_registry == NULL) return 0;
    PyObject *sysdict = topology_get_receiver(s->module, get_sys);
    PyObject *registry = topology_get_receiver(s->module, get_registry);
    if (sysdict == NULL) return 0;
    s->group_index = 0;
    int ok = topology_key_kinds(s, sysdict);
    if (ok <= 0) return ok;
    if (registry == NULL || PyDict_GetItemString(sysdict, "modules") != registry) return 0;
    s->group_index = 1; ok = topology_key_kinds(s, registry);
    if (ok <= 0) return ok;
    PyObject *rows = topology_load(context, T_REGISTRY_ROWS);
    if (rows == NULL || !PyTuple_CheckExact(rows)) return 0;
    ok = dict_items_match(registry, rows); if (ok <= 0) return ok;
    rows = topology_load(context, T_SINGLETON_ROWS);
    if (rows == NULL || !PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 2)) return 0;
        READ(s, "topology.singleton.kind", i, (PyObject *)Py_TYPE(PyTuple_GET_ITEM(row, 0)));
        if ((PyObject *)Py_TYPE(PyTuple_GET_ITEM(row, 0)) != PyTuple_GET_ITEM(row, 1)) return 0;
    }
    PyObject *builtin = topology_load(context, T_BUILTIN_NAMESPACE), *keys = topology_load(context, T_BUILTIN_KEYS);
    PyObject *plan = topology_load(context, T_BUILTIN_PLAN);
    if (builtin == NULL || keys == NULL || plan == NULL || !tuple_size(plan, 2)) return 0;
    s->group_index = 2;
    ok = topology_namespace(s, builtin, keys, PyTuple_GET_ITEM(plan, 1), 1); if (ok <= 0) return ok;
    rows = topology_load(context, T_MODULE_PLANS);
    if (rows == NULL || !PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 4)) return 0;
        PyObject *mod = PyTuple_GET_ITEM(row, 0);
        if (!PyModule_CheckExact(mod)) return 0;
        s->group_index = 3; s->row_index = i; COUNT(s, MODULE_ROWS);
        ok = topology_namespace(s, PyModule_GetDict(mod), PyTuple_GET_ITEM(row, 1), PyTuple_GET_ITEM(row, 3), 1);
        if (ok <= 0) return ok;
    }
    rows = topology_load(context, T_CLASS_PLANS);
    if (rows == NULL || !PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 5)) return 0;
        PyObject *cls = PyTuple_GET_ITEM(row, 0);
        if (!PyType_Check(cls) || (PyObject *)Py_TYPE(cls) != PyTuple_GET_ITEM(row, 1)) return 0;
        s->group_index = 4; s->row_index = i; COUNT(s, CLASS_ROWS);
        PyObject *dict = PyType_GetDict((PyTypeObject *)cls);
        if (dict == NULL) return -1;
        ok = topology_namespace(s, dict, PyTuple_GET_ITEM(row, 2), PyTuple_GET_ITEM(row, 4), 1);
        Py_DECREF(dict); if (ok <= 0) return ok;
    }
    rows = topology_load(context, T_CLASS_IDENTITY);
    if (rows == NULL || !PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 4)) return 0;
        PyObject *cls = PyTuple_GET_ITEM(row, 0);
        if (!PyType_Check(cls)) return 0;
        s->group_index = 5; s->row_index = i;
        ok = class_descriptor_admitted(s, cls, 0); if (ok <= 0) return ok;
        READ(s, "topology.class.bases", 0, ((PyTypeObject *)cls)->tp_bases);
        if (((PyTypeObject *)cls)->tp_bases != PyTuple_GET_ITEM(row, 1)) return 0;
        ok = class_descriptor_admitted(s, cls, 1); if (ok <= 0) return ok;
        READ(s, "topology.class.mro", 1, ((PyTypeObject *)cls)->tp_mro);
        if (((PyTypeObject *)cls)->tp_mro != PyTuple_GET_ITEM(row, 2)) return 0;
        ok = topology_class_labels(s, cls, PyTuple_GET_ITEM(row, 3)); if (ok <= 0) return ok;
    }
    rows = topology_load(context, T_CONTAINER_PLANS);
    if (rows == NULL || !PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 4)) return 0;
        PyObject *value = PyTuple_GET_ITEM(row, 0), *expected = PyTuple_GET_ITEM(row, 3);
        s->group_index = 6; s->row_index = i; COUNT(s, DATA_ROWS);
        if (PyDict_CheckExact(value)) {
            ok = topology_namespace(s, value, PyTuple_GET_ITEM(row, 2), expected, 0); if (ok <= 0) return ok;
        } else if (PyList_CheckExact(value)) {
            if (!PyTuple_CheckExact(expected) || PyList_GET_SIZE(value) != PyTuple_GET_SIZE(expected)) return 0;
            int same = 1;
            for (Py_ssize_t j = 0; j < PyList_GET_SIZE(value); ++j) {
                READ(s, "topology.list.item", j, PyList_GET_ITEM(value, j));
                if (PyList_GET_ITEM(value, j) != PyTuple_GET_ITEM(expected, j)) same = 0;
            }
            if (!same) return 0;
        } else if (!PyTuple_CheckExact(value)) return 0;
    }
    plan = topology_load(context, T_CELL_PLAN);
    if (plan == NULL || !tuple_size(plan, 3)) return 0;
    rows = PyTuple_GET_ITEM(plan, 0);
    if (!PyTuple_CheckExact(rows)) return 0;
    s->group_index = 7;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 2)) return 0;
        PyObject *cell = PyTuple_GET_ITEM(row, 0);
        if (!Py_IS_TYPE(cell, &PyCell_Type)) return 0;
        READ(s, "topology.cell", i, PyCell_GET(cell)); COUNT(s, CELL_FIELDS);
        if (PyCell_GET(cell) != PyTuple_GET_ITEM(row, 1)) return 0;
    }
    rows = topology_load(context, T_SPECIAL_CELLS);
    PyObject *own = topology_load(context, T_OWN_GUARD_CELL);
    if (rows == NULL || own == NULL || !PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *cell = PyTuple_GET_ITEM(rows, i);
        if (!Py_IS_TYPE(cell, &PyCell_Type)) return 0;
        if (PyCell_GET(cell) != (cell == own ? check : code)) return 0;
    }
    plan = topology_load(context, T_FUNCTION_PLAN);
    if (plan == NULL || !tuple_size(plan, 4)) return 0;
    rows = PyTuple_GET_ITEM(plan, 0);
    if (!PyTuple_CheckExact(rows)) return 0;
    s->group_index = 8;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 4)) return 0;
        PyObject *target = PyTuple_GET_ITEM(row, 0);
        if (!PyFunction_Check(target)) return 0;
        COUNT(s, FUNCTION_ROWS); s->row_index = i;
        PyObject *actual[3] = {PyFunction_GET_CODE(target), none_if_null(PyFunction_GET_DEFAULTS(target)), none_if_null(PyFunction_GET_KW_DEFAULTS(target))};
        for (int j = 0; j < 3; ++j) { READ(s, "topology.function", j, actual[j]); if (actual[j] != PyTuple_GET_ITEM(row, j+1)) return 0; }
    }
    rows = topology_load(context, T_LOWER_PLANS);
    if (rows == NULL || !PyTuple_CheckExact(rows)) return 0;
    s->group_index = 9;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 3)) return 0;
        PyObject *dict = PyTuple_GET_ITEM(row, 0), *expected = PyTuple_GET_ITEM(row, 2);
        if (!PyDict_CheckExact(dict) || !PyTuple_CheckExact(expected) || PyDict_GET_SIZE(dict) != PyTuple_GET_SIZE(expected)) return 0;
        Py_ssize_t pos = 0, j = 0; PyObject *value; int same = 1;
        s->row_index = i;
        while (PyDict_Next(dict, &pos, NULL, &value)) { READ(s, "topology.lower.value", j, value); if (value != PyTuple_GET_ITEM(expected, j++)) same = 0; }
        if (!same) return 0;
    }
    return topology_load(context, T_GUARD) == check && topology_load(context, T_GUARD_CODE) == code
        && PyFunction_GET_CODE(check) == code;
}
static int run_topology_scan(TopologyScan *s, PyObject *check, PyObject *code) {
    if (!PyFunction_Check(check) || !PyCode_Check(code) || PyFunction_GET_CODE(check) != code) return 0;
    ModuleState *state = s->observations.module;
    prune_topology_layouts(state);
    s->layout = state->topology_layouts;
    while (s->layout != NULL && PyWeakref_GET_OBJECT(s->layout->code_ref) != code) s->layout = s->layout->next;
    if (s->layout == NULL || PyTuple_GET_ITEM(((PyCodeObject *)code)->co_consts, s->layout->anchor) != state->topology_builtin) return 0;
    s->closure = PyFunction_GET_CLOSURE(check);
    if (s->closure == NULL || !PyTuple_CheckExact(s->closure) || PyTuple_GET_SIZE(s->closure) != PyTuple_GET_SIZE(s->layout->names)) return 0;
    Py_INCREF(s->closure);
    int result = topology_load(s, T_GUARD) == check && topology_load(s, T_GUARD_CODE) == code
        ? topology_body(s, check, code) : 0;
    for (int i = 0; i < T_COUNT; ++i) Py_CLEAR(s->held[i]);
    Py_CLEAR(s->closure);
    return result == 0 && PyErr_Occurred() ? -1 : result;
}
static PyObject *scan_topology(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 2) { PyErr_SetString(PyExc_TypeError, "topology scan requires original checker and code"); return NULL; }
    TopologyScan context = {.observations = {.module = PyModule_GetState(self)}};
    int result = run_topology_scan(&context, args[0], args[1]);
    if (result < 0) return NULL;
    return PyBool_FromLong(result);
}
/* Original owner-value scan. No observed value or successful admission is
 * cached. Only weak original-code identity and immutable closure positions
 * survive a call; all dictionaries, fields and cells are read afresh. */
static void prune_owner_layouts(ModuleState *state) {
    OwnerLayout **slot = &state->owner_layouts;
    while (*slot != NULL) {
        OwnerLayout *item = *slot;
        if (PyWeakref_GET_OBJECT(item->code_ref) == Py_None) {
            *slot = item->next; Py_DECREF(item->code_ref); PyMem_Free(item);
        } else slot = &item->next;
    }
}
static PyObject *bind_owner_installer(PyObject *self, PyObject *installer) {
    if (!PyFunction_Check(installer)) { PyErr_SetString(PyExc_TypeError, "owner binding requires original installer"); return NULL; }
    ModuleState *state = PyModule_GetState(self);
    PyObject *outer = Py_NewRef(PyFunction_GET_CODE(installer));
    PyObject *new_check = NULL, *new_outer = NULL, *names = NULL;
    OwnerLayout *layout = NULL;
    Py_ssize_t index = one_nested_code(outer, "check"), anchor = -1;
    if (index < 0) goto ambiguous;
    PyObject *check = PyTuple_GET_ITEM(((PyCodeObject *)outer)->co_consts, index);
    PyObject *constants = ((PyCodeObject *)check)->co_consts;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(constants); ++i) {
        PyObject *value = PyTuple_GET_ITEM(constants, i);
        if (PyUnicode_CheckExact(value) && PyUnicode_CompareWithASCIIString(value, "__aware_native_owner_scan_anchor_v1__") == 0) {
            if (anchor >= 0) goto ambiguous;
            anchor = i;
        }
    }
    if (anchor < 0) goto ambiguous;
    new_check = replace_one_constant(check, anchor, state->owner_builtin);
    if (new_check == NULL) goto error;
    names = PyCode_GetFreevars((PyCodeObject *)new_check);
    if (names == NULL) goto error;
    layout = PyMem_Calloc(1, sizeof(OwnerLayout));
    if (layout == NULL) { PyErr_NoMemory(); goto error; }
    layout->anchor = anchor;
    for (int field = 0; field < O_COUNT; ++field) {
        layout->indices[field] = -1;
        for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(names); ++i) {
            if (!PyUnicode_CheckExact(PyTuple_GET_ITEM(names, i))) goto ambiguous;
            if (PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(names, i), owner_names[field]) == 0) {
                if (layout->indices[field] >= 0) goto ambiguous;
                layout->indices[field] = i;
            }
        }
        if (layout->indices[field] < 0) goto ambiguous;
    }
    layout->code_ref = PyWeakref_NewRef(new_check, NULL);
    if (layout->code_ref == NULL) goto error;
    new_outer = replace_one_constant(outer, index, new_check);
    if (new_outer == NULL) goto error;
    if (PyFunction_GET_CODE(installer) != outer) goto ambiguous;
    if (PyObject_SetAttrString(installer, "__code__", new_outer) < 0) goto error;
    prune_owner_layouts(state);
    layout->next = state->owner_layouts; state->owner_layouts = layout; layout = NULL;
    Py_DECREF(names); Py_DECREF(new_check); Py_DECREF(new_outer); Py_DECREF(outer);
    Py_RETURN_NONE;
ambiguous: PyErr_SetString(PyExc_RuntimeError, "owner binding requires one original checker, sentinel and complete closure");
error:
    Py_XDECREF(names); Py_XDECREF(new_check); Py_XDECREF(new_outer); Py_DECREF(outer);
    if (layout != NULL) { Py_XDECREF(layout->code_ref); PyMem_Free(layout); }
    return NULL;
}
static int owner_keys_match(PyObject *dict, PyObject *keys) {
    if (!PyDict_CheckExact(dict) || !PyTuple_CheckExact(keys) || PyDict_GET_SIZE(dict) != PyTuple_GET_SIZE(keys)) return 0;
    Py_ssize_t pos = 0, i = 0; PyObject *key;
    while (PyDict_Next(dict, &pos, &key, NULL)) {
        PyObject *expected = PyTuple_GET_ITEM(keys, i++);
        if (!PyUnicode_CheckExact(key) || !PyUnicode_CheckExact(expected)) return 0;
        if (key != expected && PyUnicode_Compare(key, expected) != 0) return 0;
    }
    return 1;
}
static int owner_values_match(PyObject *dict, PyObject *values) {
    if (!PyDict_CheckExact(dict) || !PyTuple_CheckExact(values) || PyDict_GET_SIZE(dict) != PyTuple_GET_SIZE(values)) return 0;
    Py_ssize_t pos = 0, i = 0; PyObject *value;
    while (PyDict_Next(dict, &pos, NULL, &value))
        if (value != PyTuple_GET_ITEM(values, i++)) return 0;
    return 1;
}
static int owner_namespace_match(PyObject *dict, PyObject *keys, PyObject *values) {
    int direct = combined_namespace(dict, keys, values, 1);
    return direct == -2 ? owner_keys_match(dict, keys) && owner_values_match(dict, values) : direct;
}
static int owner_body(PyObject **b, PyObject *check) {
    PyObject *namespace = b[O_NAMESPACE], *keys = b[O_OWNER_KEYS], *plan = b[O_OWNER_PLAN];
    if (b[O_CHECK] != check || !owner_keys_match(namespace, keys) || !tuple_size(plan, 3)) return 0;
    PyObject *indices = PyTuple_GET_ITEM(plan, 1), *expected = PyTuple_GET_ITEM(plan, 2);
    if (!PyTuple_CheckExact(indices) || !PyTuple_CheckExact(expected) || PyTuple_GET_SIZE(indices) != PyTuple_GET_SIZE(expected)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(indices); ++i) {
        PyObject *index = PyTuple_GET_ITEM(indices, i);
        if (!PyLong_CheckExact(index)) return 0;
        Py_ssize_t j = PyLong_AsSsize_t(index);
        if (j < 0 || j >= PyTuple_GET_SIZE(keys)) return 0;
        if (PyDict_GetItemWithError(namespace, PyTuple_GET_ITEM(keys, j)) != PyTuple_GET_ITEM(expected, i)) return 0;
    }
    if (!tuple_size(b[O_BUILTIN_PLAN], 2) || !owner_namespace_match(b[O_BUILTIN_NAMESPACE], b[O_BUILTIN_KEYS], PyTuple_GET_ITEM(b[O_BUILTIN_PLAN], 1))) return 0;
    if (!PyDict_CheckExact(b[O_GUARD_VALUES]) || !PyUnicode_CheckExact(b[O_EXPECTED_GUARD])
        || !exact_string_keys(b[O_GUARD_VALUES])
        || PyDict_GetItemWithError(b[O_GUARD_VALUES], b[O_EXPECTED_GUARD]) != check) return 0;
    PyObject *rows = b[O_NAMESPACE_PLANS];
    if (!PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 4) || !PyModule_CheckExact(PyTuple_GET_ITEM(row, 0))) return 0;
        PyObject *dict = PyModule_GetDict(PyTuple_GET_ITEM(row, 0));
        if (!owner_namespace_match(dict, PyTuple_GET_ITEM(row, 1), PyTuple_GET_ITEM(row, 3))) return 0;
    }
    rows = b[O_CLASS_PLANS]; PyObject *kinds = b[O_CLASS_KINDS];
    if (!PyTuple_CheckExact(rows) || !PyTuple_CheckExact(kinds) || PyTuple_GET_SIZE(rows) != PyTuple_GET_SIZE(kinds)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i), *kind = PyTuple_GET_ITEM(kinds, i);
        if (!tuple_size(row, 4) || !tuple_size(kind, 2) || PyTuple_GET_ITEM(row, 0) != PyTuple_GET_ITEM(kind, 0)) return 0;
        PyObject *cls = PyTuple_GET_ITEM(row, 0);
        if (!PyType_Check(cls) || (PyObject *)Py_TYPE(cls) != PyTuple_GET_ITEM(kind, 1)) return 0;
        PyObject *dict = PyType_GetDict((PyTypeObject *)cls);
        if (dict == NULL) return -1;
        int ok = owner_namespace_match(dict, PyTuple_GET_ITEM(row, 1), PyTuple_GET_ITEM(row, 3));
        Py_DECREF(dict); if (!ok) return 0;
    }
    rows = b[O_MEMBER_PLANS];
    if (!PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 4) || !owner_namespace_match(PyTuple_GET_ITEM(row, 0), PyTuple_GET_ITEM(row, 1), PyTuple_GET_ITEM(row, 3))) return 0;
    }
    rows = b[O_CONTAINER_PLANS];
    if (!PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 4)) return 0;
        PyObject *target = PyTuple_GET_ITEM(row, 0), *values = PyTuple_GET_ITEM(row, 3);
        if (PyDict_CheckExact(target)) {
            PyObject *wanted = PyTuple_GET_ITEM(row, 2);
            if (!PyTuple_CheckExact(wanted) || !PyTuple_CheckExact(values) || PyDict_GET_SIZE(target) != PyTuple_GET_SIZE(wanted) || PyDict_GET_SIZE(target) != PyTuple_GET_SIZE(values)) return 0;
            Py_ssize_t pos = 0, j = 0; PyObject *key, *value;
            while (PyDict_Next(target, &pos, &key, &value)) {
                if (key != PyTuple_GET_ITEM(wanted, j) || value != PyTuple_GET_ITEM(values, j)) return 0;
                ++j;
            }
        } else {
            if (!PyList_CheckExact(target) || !PyTuple_CheckExact(values) || PyList_GET_SIZE(target) != PyTuple_GET_SIZE(values)) return 0;
            for (Py_ssize_t j = 0; j < PyList_GET_SIZE(target); ++j)
                if (PyList_GET_ITEM(target, j) != PyTuple_GET_ITEM(values, j)) return 0;
        }
    }
    rows = b[O_DESCRIPTORS];
    PyObject *descriptor_kinds = b[O_DESCRIPTOR_KINDS];
    if (!PyTuple_CheckExact(rows) || !PyTuple_CheckExact(descriptor_kinds) || PyTuple_GET_SIZE(rows) != PyTuple_GET_SIZE(descriptor_kinds)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 2) || !PyTuple_CheckExact(PyTuple_GET_ITEM(row, 1))) return 0;
        /* Only the two exact descriptor classes captured by the authored
         * installer may reach native GenericGetAttr. Refuse class swapping
         * BEFORE a foreign data descriptor could receive control. */
        PyObject *target = PyTuple_GET_ITEM(row, 0), *classes = b[O_CLASS_PLANS];
        PyObject *kind = PyTuple_GET_ITEM(descriptor_kinds, i);
        if (!tuple_size(kind, 2) || PyTuple_GET_ITEM(kind, 0) != target || (PyObject *)Py_TYPE(target) != PyTuple_GET_ITEM(kind, 1)) return 0;
        if (!PyTuple_CheckExact(classes) || PyTuple_GET_SIZE(classes) < 7) return 0;
        PyObject *enum_property = PyTuple_GET_ITEM(classes, 6);
        if (!tuple_size(enum_property, 4)) return 0;
        if (!Py_IS_TYPE(target, &PyProperty_Type) && (PyObject *)Py_TYPE(target) != PyTuple_GET_ITEM(enum_property, 0)) return 0;
        PyObject *accessors = PyTuple_GET_ITEM(row, 1);
        for (Py_ssize_t j = 0; j < PyTuple_GET_SIZE(accessors); ++j) {
            PyObject *pair = PyTuple_GET_ITEM(accessors, j);
            if (!tuple_size(pair, 2) || !PyUnicode_CheckExact(PyTuple_GET_ITEM(pair, 0))) return 0;
            PyObject *actual = PyObject_GenericGetAttr(PyTuple_GET_ITEM(row, 0), PyTuple_GET_ITEM(pair, 0));
            if (actual == NULL) return -1;
            int same = actual == PyTuple_GET_ITEM(pair, 1); Py_DECREF(actual); if (!same) return 0;
        }
    }
    rows = b[O_FUNCTIONS];
    if (!PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 5)) return 0;
        PyObject *target = PyTuple_GET_ITEM(row, 0);
        if (!PyFunction_Check(target) || PyFunction_GET_CODE(target) != PyTuple_GET_ITEM(row, 1)
            || none_if_null(PyFunction_GET_DEFAULTS(target)) != PyTuple_GET_ITEM(row, 2)
            || none_if_null(PyFunction_GET_KW_DEFAULTS(target)) != PyTuple_GET_ITEM(row, 3)) return 0;
    }
    plan = b[O_CELL_PLAN];
    if (!tuple_size(plan, 3) || !PyTuple_CheckExact(PyTuple_GET_ITEM(plan, 0))) return 0;
    rows = PyTuple_GET_ITEM(plan, 0);
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *row = PyTuple_GET_ITEM(rows, i);
        if (!tuple_size(row, 2) || !Py_IS_TYPE(PyTuple_GET_ITEM(row, 0), &PyCell_Type)
            || PyCell_GET(PyTuple_GET_ITEM(row, 0)) != PyTuple_GET_ITEM(row, 1)) return 0;
    }
    rows = b[O_SPECIAL_CELLS];
    if (!PyTuple_CheckExact(rows)) return 0;
    for (Py_ssize_t i = 0; i < PyTuple_GET_SIZE(rows); ++i) {
        PyObject *cell = PyTuple_GET_ITEM(rows, i);
        PyObject *wanted = cell == b[O_RETAINED_GUARD_CELL] ? check : PyDict_GetItemString(namespace, "_attempt_guard");
        if (!Py_IS_TYPE(cell, &PyCell_Type) || (cell != b[O_RETAINED_GUARD_CELL] && cell != b[O_ATTEMPT_GUARD_CELL]) || PyCell_GET(cell) != wanted) return 0;
    }
    return 1;
}
static PyObject *scan_owner(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 2) { PyErr_SetString(PyExc_TypeError, "owner scan requires original checker and code"); return NULL; }
    ModuleState *state = PyModule_GetState(self);
    PyObject *check = args[0], *code = args[1];
    if (!PyFunction_Check(check) || !PyCode_Check(code) || PyFunction_GET_CODE(check) != code) Py_RETURN_FALSE;
    prune_owner_layouts(state);
    OwnerLayout *layout = state->owner_layouts;
    while (layout != NULL && PyWeakref_GET_OBJECT(layout->code_ref) != code) layout = layout->next;
    if (layout == NULL || PyTuple_GET_ITEM(((PyCodeObject *)code)->co_consts, layout->anchor) != state->owner_builtin) Py_RETURN_FALSE;
    PyObject *closure = PyFunction_GET_CLOSURE(check);
    if (closure == NULL || !PyTuple_CheckExact(closure)) Py_RETURN_FALSE;
    PyObject *bank[O_COUNT] = {NULL};
    int result = 0;
    for (int i = 0; i < O_COUNT; ++i) {
        if (layout->indices[i] >= PyTuple_GET_SIZE(closure)) goto done;
        PyObject *cell = PyTuple_GET_ITEM(closure, layout->indices[i]);
        if (!Py_IS_TYPE(cell, &PyCell_Type) || PyCell_GET(cell) == NULL) goto done;
        bank[i] = Py_NewRef(PyCell_GET(cell));
    }
    result = owner_body(bank, check);
    if (result > 0) {
        if (PyFunction_GET_CODE(check) != code) result = 0;
        for (int i = 0; i < O_COUNT; ++i)
            if (PyCell_GET(PyTuple_GET_ITEM(closure, layout->indices[i])) != bank[i]) result = 0;
    }
done:
    for (int i = 0; i < O_COUNT; ++i) Py_XDECREF(bank[i]);
    if (PyErr_Occurred()) return NULL;
    return PyBool_FromLong(result > 0);
}
static PyObject *observe_topology(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 2 && nargs != 3) { PyErr_SetString(PyExc_TypeError, "topology observation requires original checker, code and optional exact GC-stress bool"); return NULL; }
    if (nargs == 3 && !PyBool_Check(args[2])) { PyErr_SetString(PyExc_TypeError, "GC-stress option must be exact bool"); return NULL; }
    TopologyScan context = {.observations = {.module = PyModule_GetState(self), .tracing = 1}};
    int result = run_topology_scan(&context, args[0], args[1]);
    if (result < 0) { PyMem_Free(context.observations.events); return NULL; }
    PyObject *report = PyDict_New();
    if (report == NULL) { PyMem_Free(context.observations.events); return NULL; }
    PyObject *events = serialize_events(&context.observations);
    PyMem_Free(context.observations.events);
    if (events == NULL || PyDict_SetItemString(report, "trace", events) < 0 || PyDict_SetItemString(report, "accepted", Py_False) < 0) {
        Py_XDECREF(events); Py_DECREF(report); return NULL;
    }
    Py_DECREF(events);
    /* Diagnostic-only explicit collection makes this allocation boundary
     * reproducible with automatic GC disabled. It never authorizes a scan. */
    if (nargs == 3 && args[2] == Py_True) {
        int enabled = PyGC_IsEnabled();
        if (!enabled) PyGC_Enable();
        Py_ssize_t collected = PyGC_Collect();
        if (!enabled) PyGC_Disable();
        if (collected < 0) { Py_DECREF(report); return NULL; }
    }
    /* Trace serialization can run GC. Recheck ALL fresh state afterward. */
    TopologyScan terminal = {.observations = {.module = PyModule_GetState(self)}};
    int fresh = run_topology_scan(&terminal, args[0], args[1]);
    if (fresh < 0 || PyDict_SetItemString(report, "accepted", result > 0 && fresh > 0 ? Py_True : Py_False) < 0) { Py_DECREF(report); return NULL; }
    return report;
}
/* Preserve the original state(value) shape. Capture all actual addresses in
 * raw storage before creating Python tuples/integers; no borrowed element is
 * used after the first GC-capable Python allocation. Subclasses are scalar. */
static PyObject *fingerprint_state(PyObject *value) {
    uintptr_t kind_address = (uintptr_t)Py_TYPE(value);
    int dictionary = PyDict_CheckExact(value);
    int sequence = PyTuple_CheckExact(value) || PyList_CheckExact(value) ||
        PySet_CheckExact(value) || PyFrozenSet_CheckExact(value);
    Py_ssize_t count;
    if (dictionary) {
        if (PyDict_GET_SIZE(value) > PY_SSIZE_T_MAX / 2) { PyErr_NoMemory(); return NULL; }
        count = PyDict_GET_SIZE(value) * 2;
    } else if (PyTuple_CheckExact(value)) count = PyTuple_GET_SIZE(value);
    else if (PyList_CheckExact(value)) count = PyList_GET_SIZE(value);
    else if (PySet_CheckExact(value) || PyFrozenSet_CheckExact(value)) count = PySet_GET_SIZE(value);
    else count = 1;
    if (count < 0 || (size_t)count > SIZE_MAX / sizeof(uintptr_t)) { PyErr_NoMemory(); return NULL; }
    uintptr_t *addresses = count == 0 ? NULL : PyMem_Malloc((size_t)count * sizeof(uintptr_t));
    if (count != 0 && addresses == NULL) { PyErr_NoMemory(); return NULL; }
    if (dictionary) {
        Py_ssize_t key_pos = 0, value_pos = 0, i = 0; PyObject *key, *item;
        while (PyDict_Next(value, &key_pos, &key, NULL)) {
            addresses[i++] = (uintptr_t)key;
            if (!PyDict_Next(value, &value_pos, NULL, &item)) goto inconsistent;
            addresses[i++] = (uintptr_t)item;
        }
        if (i != count) goto inconsistent;
    } else if (sequence) {
        Py_ssize_t pos = 0; PyObject *item; Py_hash_t hash;
        for (Py_ssize_t i = 0; i < count; ++i) {
            if (PyTuple_CheckExact(value)) item = PyTuple_GET_ITEM(value, i);
            else if (PyList_CheckExact(value)) item = PyList_GET_ITEM(value, i);
            else if (!_PySet_NextEntry(value, &pos, &item, &hash)) goto inconsistent;
            addresses[i] = (uintptr_t)item;
        }
    } else addresses[0] = (uintptr_t)value;
    PyObject *identities = NULL, *kind = NULL, *result = NULL;
    if (dictionary) {
        identities = PyTuple_New(count / 2);
        if (identities == NULL) goto error;
        for (Py_ssize_t i = 0; i < count / 2; ++i) {
            PyObject *pair = PyTuple_New(2);
            if (pair == NULL) goto error;
            PyTuple_SET_ITEM(identities, i, pair);
            PyObject *key = PyLong_FromVoidPtr((void *)addresses[2*i]);
            if (key == NULL) goto error;
            PyTuple_SET_ITEM(pair, 0, key);
            PyObject *item = PyLong_FromVoidPtr((void *)addresses[2*i+1]);
            if (item == NULL) goto error;
            PyTuple_SET_ITEM(pair, 1, item);
        }
    } else if (sequence) {
        identities = PyTuple_New(count);
        if (identities == NULL) goto error;
        for (Py_ssize_t i = 0; i < count; ++i) {
            PyObject *item = PyLong_FromVoidPtr((void *)addresses[i]);
            if (item == NULL) goto error;
            PyTuple_SET_ITEM(identities, i, item);
        }
    } else {
        identities = PyLong_FromVoidPtr((void *)addresses[0]);
        if (identities == NULL) goto error;
    }
    kind = PyLong_FromVoidPtr((void *)kind_address);
    if (kind == NULL) goto error;
    result = PyTuple_Pack(2, kind, identities);
error:
    PyMem_Free(addresses); Py_XDECREF(kind); Py_XDECREF(identities); return result;
inconsistent:
    PyMem_Free(addresses);
    PyErr_SetString(PyExc_RuntimeError, "native fingerprint cardinality changed without native dispatch"); return NULL;
}

/* The host receiver path reads the native instance dictionary directly.
 * Exact owner/metaclass admission precedes raw dict access and never resolves
 * a receiver's mutable __dict__ descriptor or __getattribute__ method. */
static PyObject *fingerprint(PyObject *self, PyObject *args) {
    (void)self;
    Py_ssize_t count = PyTuple_GET_SIZE(args);
    if (count == 1) return fingerprint_state(PyTuple_GET_ITEM(args, 0));
    if (count == 2) {
        PyObject *receiver = PyTuple_GET_ITEM(args, 0), *owner = PyTuple_GET_ITEM(args, 1);
        if (!Py_IS_TYPE(owner, &PyType_Type) || Py_TYPE(receiver) != (PyTypeObject *)owner)
            Py_RETURN_NONE;
        PyObject *dictionary = PyObject_GenericGetDict(receiver, NULL);
        if (dictionary == NULL) {
            if (PyErr_ExceptionMatches(PyExc_AttributeError)) {
                PyErr_Clear(); Py_RETURN_NONE;
            }
            return NULL;
        }
        /* Dictionary creation can allocate. Fresh exact-owner admission after
         * that boundary retains the Python caller's native binding refusal. */
        if (!Py_IS_TYPE(owner, &PyType_Type) || Py_TYPE(receiver) != (PyTypeObject *)owner ||
                !PyDict_CheckExact(dictionary)) {
            Py_DECREF(dictionary); Py_RETURN_NONE;
        }
        return dictionary;
    }
    PyErr_SetString(PyExc_TypeError, "fingerprint requires one value or receiver and retained owner");
    return NULL;
}
/* Recursive codec fingerprints preserve the Python oracle's complete shape.
 * The read pass allocates only raw memory and integer-only memo entries: no
 * Python container/tuple construction or caller dispatch occurs while source
 * pointers are borrowed. Only exact primitive leaves are retained strongly.
 * All Python-result allocations happen after the read pass. A GC callback at
 * that later boundary cannot invalidate a borrowed container or peer pointer.
 * This memo is private to ONE call; it is never an admission cache. */
typedef struct {
    uintptr_t kind, identity;
    PyObject *scalar, *result;
    Py_ssize_t *children, count;
    int container, dictionary, active;
} CodecNode;
typedef struct {
    CodecNode *nodes;
    Py_ssize_t count, capacity;
    int depth;
    PyObject *memo;
} CodecGraph;

static Py_ssize_t codec_read(CodecGraph *graph, PyObject *value) {
    if (graph->depth >= Py_GetRecursionLimit()) {
        PyErr_SetString(PyExc_RecursionError, "codec capture recursion limit exceeded"); return -1;
    }
    if (Py_EnterRecursiveCall(" while capturing codec state")) return -1;
    graph->depth++;
    Py_ssize_t index = -1;
    PyObject *key = NULL;
    int container = PyTuple_CheckExact(value) || PyList_CheckExact(value) || PyDict_CheckExact(value);
    if (container) {
        key = PyLong_FromVoidPtr(value);
        if (key == NULL) goto done;
        PyObject *old = PyDict_GetItemWithError(graph->memo, key);
        if (old != NULL) {
            Py_ssize_t prior = PyLong_AsSsize_t(old);
            if (!graph->nodes[prior].active) { index = prior; goto done; }
            container = 0; /* A cycle contributes identity, as in the oracle. */
        } else if (PyErr_Occurred()) goto done;
    }
    if (graph->count == graph->capacity) {
        Py_ssize_t capacity = graph->capacity == 0 ? 64 : graph->capacity * 2;
        if (capacity < graph->capacity || (size_t)capacity > SIZE_MAX / sizeof(CodecNode)) {
            PyErr_NoMemory(); goto done;
        }
        CodecNode *nodes = PyMem_Realloc(graph->nodes, (size_t)capacity * sizeof(CodecNode));
        if (nodes == NULL) { PyErr_NoMemory(); goto done; }
        graph->nodes = nodes; graph->capacity = capacity;
    }
    index = graph->count++;
    graph->nodes[index] = (CodecNode){.kind = (uintptr_t)Py_TYPE(value), .identity = (uintptr_t)value,
        .container = container, .dictionary = PyDict_CheckExact(value), .active = container};
    if (!container) {
        if (PyUnicode_CheckExact(value) || PyBytes_CheckExact(value) || PyLong_CheckExact(value)
            || PyBool_Check(value) || value == Py_None) graph->nodes[index].scalar = Py_NewRef(value);
        goto done;
    }
    PyObject *coordinate = PyLong_FromSsize_t(index);
    if (coordinate == NULL) goto failed;
    int inserted = PyDict_SetItem(graph->memo, key, coordinate); Py_DECREF(coordinate);
    if (inserted < 0) goto failed;
    Py_ssize_t count = PyDict_CheckExact(value) ? PyDict_GET_SIZE(value)
        : PyTuple_CheckExact(value) ? PyTuple_GET_SIZE(value) : PyList_GET_SIZE(value);
    if (PyDict_CheckExact(value)) {
        if (count > PY_SSIZE_T_MAX / 2) { PyErr_NoMemory(); goto failed; }
        count *= 2;
    }
    if ((size_t)count > SIZE_MAX / sizeof(Py_ssize_t)) { PyErr_NoMemory(); goto failed; }
    Py_ssize_t *children = count == 0 ? NULL : PyMem_Malloc((size_t)count * sizeof(Py_ssize_t));
    if (count != 0 && children == NULL) { PyErr_NoMemory(); goto failed; }
    graph->nodes[index].children = children; graph->nodes[index].count = count;
    if (PyDict_CheckExact(value)) {
        Py_ssize_t position = 0, offset = 0; PyObject *name, *item;
        while (PyDict_Next(value, &position, &name, &item)) {
            children[offset++] = codec_read(graph, name);
            if (children[offset-1] < 0) goto failed;
            children[offset++] = codec_read(graph, item);
            if (children[offset-1] < 0) goto failed;
        }
    } else {
        for (Py_ssize_t offset = 0; offset < count; ++offset) {
            PyObject *item = PyTuple_CheckExact(value) ? PyTuple_GET_ITEM(value, offset) : PyList_GET_ITEM(value, offset);
            children[offset] = codec_read(graph, item);
            if (children[offset] < 0) goto failed;
        }
    }
    graph->nodes[index].active = 0;
    goto done;
failed:
    index = -1;
done:
    Py_XDECREF(key); graph->depth--; Py_LeaveRecursiveCall(); return index;
}

static PyObject *codec_materialize(CodecGraph *graph, Py_ssize_t index) {
    CodecNode *node = &graph->nodes[index];
    if (node->result != NULL) return Py_NewRef(node->result);
    if (Py_EnterRecursiveCall(" while constructing codec state")) return NULL;
    PyObject *body = NULL, *kind = NULL, *result = NULL;
    if (!node->container) body = node->scalar != NULL ? Py_NewRef(node->scalar)
        : PyLong_FromVoidPtr((void *)node->identity);
    else {
        Py_ssize_t length = node->dictionary ? node->count / 2 : node->count;
        body = PyTuple_New(length);
        if (body == NULL) goto done;
        for (Py_ssize_t offset = 0; offset < length; ++offset) {
            PyObject *item = codec_materialize(graph, node->children[node->dictionary ? offset*2 : offset]);
            if (item == NULL) goto done;
            if (node->dictionary) {
                PyObject *value = codec_materialize(graph, node->children[offset*2+1]);
                PyObject *pair = value == NULL ? NULL : PyTuple_Pack(2, item, value);
                Py_DECREF(item); Py_XDECREF(value); item = pair;
                if (item == NULL) goto done;
            }
            PyTuple_SET_ITEM(body, offset, item);
        }
    }
    if (body == NULL) goto done;
    kind = PyLong_FromVoidPtr((void *)node->kind);
    if (kind == NULL) goto done;
    result = PyTuple_Pack(2, kind, body);
    if (result != NULL) node->result = Py_NewRef(result);
done:
    Py_XDECREF(body); Py_XDECREF(kind); Py_LeaveRecursiveCall(); return result;
}

static PyObject *codec_state_key(PyObject *self, PyObject *value) {
    (void)self;
    CodecGraph graph = {.memo = PyDict_New()};
    if (graph.memo == NULL) return NULL;
    Py_ssize_t root = codec_read(&graph, value);
    PyObject *result = root < 0 ? NULL : codec_materialize(&graph, root);
    for (Py_ssize_t index = 0; index < graph.count; ++index) {
        Py_XDECREF(graph.nodes[index].scalar); Py_XDECREF(graph.nodes[index].result);
        PyMem_Free(graph.nodes[index].children);
    }
    PyMem_Free(graph.nodes); Py_DECREF(graph.memo); return result;
}

static PyObject *bind_codec_state_key(PyObject *self, PyObject *operation) {
    if (!PyFunction_Check(operation)) {
        PyErr_SetString(PyExc_TypeError, "codec binding requires an exact function"); return NULL;
    }
    ModuleState *state = PyModule_GetState(self);
    PyObject *code = Py_NewRef(PyFunction_GET_CODE(operation));
    PyObject *old = ((PyCodeObject *)code)->co_consts;
    PyObject *constants = PyTuple_New(PyTuple_GET_SIZE(old));
    if (constants == NULL) { Py_DECREF(code); return NULL; }
    int found = 0;
    for (Py_ssize_t index = 0; index < PyTuple_GET_SIZE(old); ++index) {
        PyObject *item = PyTuple_GET_ITEM(old, index);
        if (PyUnicode_CheckExact(item) && PyUnicode_CompareWithASCIIString(item, "__aware_native_codec_key_v1__") == 0) {
            found++; item = state->codec_key_builtin;
        }
        PyTuple_SET_ITEM(constants, index, Py_NewRef(item));
    }
    PyObject *replacement = found == 1 ? replace_constants(code, constants) : NULL;
    Py_DECREF(constants);
    if (found != 1) PyErr_SetString(PyExc_RuntimeError, "codec key anchor missing or already bound");
    if (replacement == NULL) { Py_DECREF(code); return NULL; }
    int changed = PyFunction_GET_CODE(operation) != code;
    int outcome = changed ? -1 : PyObject_SetAttrString(operation, "__code__", replacement);
    Py_DECREF(code); Py_DECREF(replacement);
    if (changed) PyErr_SetString(PyExc_RuntimeError, "codec key changed during binding");
    if (outcome < 0) return NULL;
    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
    {"codec_state_key", codec_state_key, METH_O, "Fresh callback-free recursive codec fingerprint; one-call memo only."},
    {"bind_codec_state_key", bind_codec_state_key, METH_O, "Bind original codec fingerprint to its compiled symbol before capture."},
    {"scan", (PyCFunction)(void(*)(void))scan, METH_FASTCALL, "Fresh complete guarded rows; no validation cache."},
    {"observe", (PyCFunction)(void(*)(void))observe, METH_FASTCALL, "Same scan with separate observation counters."},
    {"fingerprint", (PyCFunction)fingerprint, METH_VARARGS, "Native eager identity fingerprint for retained host enrollment."},
    {"bind_installer", bind_installer, METH_O, "Bind both authored code constants before installation."},
    {"scan_topology", (PyCFunction)(void(*)(void))scan_topology, METH_FASTCALL, "Fresh original topology checker; no caller rows."},
    {"scan_owner", (PyCFunction)(void(*)(void))scan_owner, METH_FASTCALL, "Fresh original owner checker; no caller rows."},
    {"bind_owner_installer", bind_owner_installer, METH_O, "Bind original owner checker before first capture."},
    {"observe_topology", (PyCFunction)(void(*)(void))observe_topology, METH_FASTCALL, "Same topology scan with raw observation trace."},
    {"bind_topology_installer", bind_topology_installer, METH_O, "Bind the one authored topology sentinel before installation."},
    {NULL, NULL, 0, NULL}
};
static int traverse(PyObject *module, visitproc visit, void *arg) {
    ModuleState *state = (ModuleState *)PyModule_GetState(module);
    Py_VISIT(state->scan_builtin); Py_VISIT(state->fingerprint_builtin);
    Py_VISIT(state->topology_builtin);
    Py_VISIT(state->owner_builtin);
    Py_VISIT(state->codec_key_builtin);
    for (OwnerLayout *layout = state->owner_layouts; layout != NULL; layout = layout->next) Py_VISIT(layout->code_ref);
    for (TopologyLayout *layout = state->topology_layouts; layout != NULL; layout = layout->next) {
        Py_VISIT(layout->code_ref); Py_VISIT(layout->names);
    }
    for (CodeLayout *layout = state->layouts; layout != NULL; layout = layout->next) {
        Py_VISIT(layout->code_ref); Py_VISIT(layout->names);
    }
    for (int i = 0; i < 4; ++i) Py_VISIT(state->metadata_names[i]);
    for (int i = 0; i < 7; ++i) { Py_VISIT(state->class_names[i]); Py_VISIT(state->class_descriptors[i]); }
    Py_VISIT(state->native_id); Py_VISIT(state->native_length); Py_VISIT(state->native_any);
    for (int i = 0; i < 5; ++i) Py_VISIT(state->native_accessors[i]);
    return 0;
}
static int clear(PyObject *module) {
    ModuleState *state = (ModuleState *)PyModule_GetState(module);
    Py_CLEAR(state->scan_builtin); Py_CLEAR(state->fingerprint_builtin);
    Py_CLEAR(state->topology_builtin);
    Py_CLEAR(state->owner_builtin);
    Py_CLEAR(state->codec_key_builtin);
    OwnerLayout *owner = state->owner_layouts; state->owner_layouts = NULL;
    while (owner != NULL) { OwnerLayout *next = owner->next; Py_DECREF(owner->code_ref); PyMem_Free(owner); owner = next; }
    TopologyLayout *topology = state->topology_layouts; state->topology_layouts = NULL;
    while (topology != NULL) { TopologyLayout *next = topology->next; release_topology_layout(topology); topology = next; }
    CodeLayout *layout = state->layouts; state->layouts = NULL;
    while (layout != NULL) { CodeLayout *next = layout->next; release_layout(layout); layout = next; }
    for (int i = 0; i < 4; ++i) Py_CLEAR(state->metadata_names[i]);
    for (int i = 0; i < 7; ++i) { Py_CLEAR(state->class_names[i]); Py_CLEAR(state->class_descriptors[i]); }
    Py_CLEAR(state->native_id); Py_CLEAR(state->native_length); Py_CLEAR(state->native_any);
    for (int i = 0; i < 5; ++i) Py_CLEAR(state->native_accessors[i]);
    return 0;
}
static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "_preparation_scan", NULL, sizeof(ModuleState), methods,
    NULL, traverse, clear, NULL
};
PyMODINIT_FUNC PyInit__preparation_scan(void) {
    PyObject *result = PyModule_Create(&module);
    if (result == NULL) return NULL;
    ModuleState *state = (ModuleState *)PyModule_GetState(result);
    PyObject *native = PyDict_GetItemString(PyModule_GetDict(result), "scan");
    if (native == NULL) { Py_DECREF(result); return NULL; }
    state->scan_builtin = Py_NewRef(native);
    native = PyDict_GetItemString(PyModule_GetDict(result), "fingerprint");
    if (native == NULL) { Py_DECREF(result); return NULL; }
    state->fingerprint_builtin = Py_NewRef(native);
    native = PyDict_GetItemString(PyModule_GetDict(result), "scan_topology");
    if (native == NULL) { Py_DECREF(result); return NULL; }
    state->topology_builtin = Py_NewRef(native);
    native = PyDict_GetItemString(PyModule_GetDict(result), "scan_owner");
    if (native == NULL) { Py_DECREF(result); return NULL; }
    state->owner_builtin = Py_NewRef(native);
    native = PyDict_GetItemString(PyModule_GetDict(result), "codec_state_key");
    if (native == NULL) { Py_DECREF(result); return NULL; }
    state->codec_key_builtin = Py_NewRef(native);
    const char *names[4] = {"__name__", "__qualname__", "__module__", "__annotations__"};
    for (int i = 0; i < 4; ++i) {
        state->metadata_names[i] = PyUnicode_InternFromString(names[i]);
        if (state->metadata_names[i] == NULL) { Py_DECREF(result); return NULL; }
    }
    const char *class_names[7] = {"__bases__", "__mro__", "__name__", "__qualname__", "__module__", "__dict__", "__doc__"};
    for (int i = 0; i < 7; ++i) {
        state->class_names[i] = PyUnicode_InternFromString(class_names[i]);
        if (state->class_names[i] == NULL) { Py_DECREF(result); return NULL; }
        PyObject *dict = PyType_GetDict(&PyType_Type);
        if (dict == NULL) { Py_DECREF(result); return NULL; }
        PyObject *descriptor = PyDict_GetItemWithError(dict, state->class_names[i]);
        if (descriptor != NULL) state->class_descriptors[i] = Py_NewRef(descriptor);
        Py_DECREF(dict);
        if (descriptor == NULL) { PyErr_SetString(PyExc_RuntimeError, "native class descriptor bootstrap is incomplete"); Py_DECREF(result); return NULL; }
    }
    PyObject *builtins = PyEval_GetBuiltins();
    PyObject *native_id = PyDict_GetItemString(builtins, "id"), *native_length = PyDict_GetItemString(builtins, "len");
    PyObject *native_any = PyDict_GetItemString(builtins, "any");
    if (native_id == NULL || native_length == NULL || native_any == NULL ||
        !PyCFunction_Check(native_id) || !PyCFunction_Check(native_length) || !PyCFunction_Check(native_any)) {
        PyErr_SetString(PyExc_RuntimeError, "native primitive bootstrap requires original builtin functions");
        Py_DECREF(result); return NULL;
    }
    state->native_id = Py_NewRef(native_id); state->native_length = Py_NewRef(native_length);
    state->native_any = Py_NewRef(native_any);
    PyTypeObject *accessor_types[5] = {&PyBaseObject_Type, &PyType_Type, &PyDict_Type, &PyDict_Type, &PyDict_Type};
    const char *accessor_names[5] = {"__getattribute__", "__getattribute__", "get", "keys", "items"};
    for (int i = 0; i < 5; ++i) {
        PyObject *dict = PyType_GetDict(accessor_types[i]);
        if (dict == NULL) { Py_DECREF(result); return NULL; }
        PyObject *accessor = PyDict_GetItemString(dict, accessor_names[i]);
        if (accessor != NULL) state->native_accessors[i] = Py_NewRef(accessor);
        Py_DECREF(dict);
        if (accessor == NULL) { PyErr_SetString(PyExc_RuntimeError, "native accessor bootstrap is incomplete"); Py_DECREF(result); return NULL; }
    }
    return result;
}
