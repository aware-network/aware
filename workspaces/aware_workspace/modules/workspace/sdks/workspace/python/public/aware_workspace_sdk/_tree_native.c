#define PY_SSIZE_T_CLEAN
#define Py_BUILD_CORE
#include <Python.h>
#include "internal/pycore_interp.h"
#include "internal/pycore_dict.h"
#include <string.h>
#include <descrobject.h>
#include <structmember.h>
#ifdef WORKSPACE_FORMATTER_COSTS
#include <time.h>
typedef struct {
    uint64_t started,child;
    int category;
}
cost_Frame;
static _Thread_local cost_Frame cost_stack[64];
static _Thread_local int cost_depth;
static uint64_t cost_calls[6],cost_total[6],cost_exclusive[6],cost_errors,cost_overflow,cost_active;
static uint64_t cost_clock(void){
    struct timespec value;
    if(clock_gettime(CLOCK_THREAD_CPUTIME_ID,&value)){
        cost_errors++;
        return 0;
    }
    return(uint64_t)value.tv_sec*1000000000ULL+(uint64_t)value.tv_nsec;
}
static int cost_begin(int category){
    if(cost_depth>=64){
        cost_overflow++;
        return -1;
    }
    int slot=cost_depth++;
    cost_active++;
    cost_stack[slot].child=0;
    cost_stack[slot].category=category;
    cost_stack[slot].started=cost_clock();
    return slot;
}
static PyObject *cost_finish(int slot,PyObject *result){
    if(slot<0)return result;
    if(cost_depth!=slot+1){
        cost_errors++;
        return result;
    }
    uint64_t ended=cost_clock(),started=cost_stack[slot].started,elapsed=ended>=started?ended-started:0;
    int category=cost_stack[slot].category;
    cost_calls[category]++;
    cost_total[category]+=elapsed;
    cost_exclusive[category]+=elapsed>=cost_stack[slot].child?elapsed-cost_stack[slot].child:0;
    cost_active--;
    cost_depth--;
    if(cost_depth)cost_stack[cost_depth-1].child+=elapsed;
    return result;
}
static PyObject *cost_read(PyObject *self,PyObject *unused){
    (void)self;
    (void)unused;
    const char *names[]={
        "tree_fields_and_nested_semantics","tree_identity_verification","receipt_metadata_prelude","receipt_field_traversal","index_canonical_formatting","tree_canonical_formatting"
    };
    PyObject *out=PyDict_New();
    if(!out)return NULL;
    for(int i=0;i<6;i++){
        PyObject *row=Py_BuildValue("{s:K,s:K,s:K}","calls",(unsigned long long)cost_calls[i],"inclusive_thread_cpu_ns",(unsigned long long)cost_total[i],"exclusive_marked_thread_cpu_ns",(unsigned long long)cost_exclusive[i]);
        if(!row||PyDict_SetItemString(out,names[i],row)<0){
            Py_XDECREF(row);
            Py_DECREF(out);
            return NULL;
        }
        Py_DECREF(row);
    }
    PyObject *errors=Py_BuildValue("{s:K,s:K}","clock_errors",(unsigned long long)cost_errors,"nesting_overflow",(unsigned long long)cost_overflow);
    if(!errors||PyDict_SetItemString(out,"diagnostics",errors)<0){
        Py_XDECREF(errors);
        Py_DECREF(out);
        return NULL;
    }
    Py_DECREF(errors);
    return out;
}
static PyObject *cost_reset(PyObject *self,PyObject *unused){
    (void)self;
    (void)unused;
    if(cost_active){
        PyErr_SetString(PyExc_RuntimeError,"Cannot reset active descriptive counters");
        return NULL;
    }
    memset(cost_calls,0,sizeof(cost_calls));
    memset(cost_total,0,sizeof(cost_total));
    memset(cost_exclusive,0,sizeof(cost_exclusive));
    cost_errors=cost_overflow=0;
    Py_RETURN_NONE;
}
#define COST_BEGIN(category) int _cost_slot=cost_begin(category)
#define COST_RETURN(value) return cost_finish(_cost_slot,(value))
#else
#define COST_BEGIN(category) ((void)0)
#define COST_RETURN(value) return (value)
#endif
/* Interpreter-owned immutable identifiers only; every lookup stays fresh. */
static _Py_Identifier PyId_INFINITY={
    "INFINITY",-1
};
static _Py_Identifier PyId_JSONEncoder={
    "JSONEncoder",-1
};
static _Py_Identifier PyId_MAX_TREE_RECEIPTS={
    "MAX_TREE_RECEIPTS",-1
};
static _Py_Identifier PyId__RECEIPT_FIELDS_BY_ID={
    "_RECEIPT_FIELDS_BY_ID",-1
};
static _Py_Identifier PyId__RECEIPT_ORIGINAL_ENTRIES={
    "_RECEIPT_ORIGINAL_ENTRIES",-1
};
static _Py_Identifier PyId__RECEIPT_ORIGINAL_REGISTRY={
    "_RECEIPT_ORIGINAL_REGISTRY",-1
};
static _Py_Identifier PyId__TREE_NATIVE_CONVERT={
    "_TREE_NATIVE_CONVERT",-1
};
static _Py_Identifier PyId__TREE_NATIVE_VERIFY={
    "_TREE_NATIVE_VERIFY",-1
};
static _Py_Identifier PyId___call__={
    "__call__",-1
};
static _Py_Identifier PyId___dataclass_fields__={
    "__dataclass_fields__",-1
};
static _Py_Identifier PyId___new__={
    "__new__",-1
};
static _Py_Identifier PyId__type_hints={
    "_type_hints",-1
};
static _Py_Identifier PyId_c_make_encoder={
    "c_make_encoder",-1
};
static _Py_Identifier PyId_convert_receipt={
    "convert_receipt",-1
};
static _Py_Identifier PyId_convert_root={
    "convert_root",-1
};
static _Py_Identifier PyId_dumps={
    "dumps",-1
};
static _Py_Identifier PyId_encode_basestring={
    "encode_basestring",-1
};
static _Py_Identifier PyId_encode_basestring_ascii={
    "encode_basestring_ascii",-1
};
static _Py_Identifier PyId_isinstance={
    "isinstance",-1
};
static _Py_Identifier PyId_make_encoder={
    "make_encoder",-1
};
static _Py_Identifier PyId_receipt_prelude={
    "receipt_prelude",-1
};
static _Py_Identifier PyId_values={
    "values",-1
};
static _Py_Identifier PyId_verify={
    "verify",-1
};
static PyObject *literal_lookup(PyObject *mapping,_Py_Identifier *identifier){
    /* General-key dictionaries retain the literal original allocation/callback
     * path. The live CPython Unicode-only table flag is a structural fact,
     * never a remembered namespace or authority verdict. */
    if(!PyDict_CheckExact(mapping)||!DK_IS_UNICODE(((PyDictObject*)mapping)->ma_keys))
    return PyDict_GetItemString(mapping,identifier->string);
    PyObject *name=_PyUnicode_FromId(identifier);
    if(!name){
        PyErr_Clear();
        return NULL;
    }
    return PyDict_GetItem(mapping,name);
}
/* Optional CPython-patch-qualified descriptive metadata conversion.
 * Every value field is read afresh. No owner handle or authorization is held.
 * Immutable declaration/configuration references are sealed before first use. */
static int fail(PyObject *config,const char *reason) {
    PyErr_SetString(PyTuple_GET_ITEM(config,6),reason);
    return -1;
}
static void replace_error(PyObject *config, const char *reason) {
    /* Match a Python except/raise: preserve the handled exception as context. */
    PyObject *previous=PyErr_GetRaisedException();
    fail(config,reason);
    PyObject *current=PyErr_GetRaisedException();
    if(current && previous)PyException_SetContext(current,previous);
    else Py_XDECREF(previous);
    if(current)PyErr_SetRaisedException(current);
}
static int keys_exact(PyObject *dict,PyTypeObject *type){
    if(!PyDict_CheckExact(dict))return 0;
    Py_ssize_t pos=0;
    PyObject *k,*v;
    while(PyDict_Next(dict,&pos,&k,&v))if(Py_TYPE(k)!=type)return 0;
    return 1;
}
static int auth(PyObject *config) {
    PyObject *native_module=PyCFunction_GET_SELF(PyTuple_GET_ITEM(config,4));
    if(!PyModule_CheckExact(native_module) ||
    !keys_exact(PyModule_GetDict(native_module),&PyUnicode_Type))
    return fail(config,"native metadata module origin changed");
    PyObject *native_namespace=PyModule_GetDict(native_module);
    if(literal_lookup(native_namespace,&PyId_convert_root)!=PyTuple_GET_ITEM(config,4) ||
    literal_lookup(native_namespace,&PyId_verify)!=PyTuple_GET_ITEM(config,5))
    return fail(config,"native metadata export changed");
    PyObject *m=PyTuple_GET_ITEM(config,0);
    if(!PyModule_CheckExact(m)||!PyModule_CheckExact(PyTuple_GET_ITEM(config,15)))return fail(config,"native whole module origin substituted");
    PyObject *ns=PyModule_GetDict(m);
    if(!keys_exact(ns,&PyUnicode_Type)||!keys_exact(PyModule_GetDict(PyTuple_GET_ITEM(config,15)),&PyUnicode_Type))return fail(config,"native metadata key substituted");
    if(literal_lookup(ns,&PyId_values)!=PyTuple_GET_ITEM(config,15))return fail(config,"native whole values origin substituted");
    PyObject *regs=PyTuple_GET_ITEM(config,3);
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(regs);i++){
        PyObject *pin=PyTuple_GET_ITEM(regs,i);
        if(PyDict_GetItemWithError(ns,PyTuple_GET_ITEM(pin,0))!=PyTuple_GET_ITEM(pin,1))return fail(config,"native whole origin substituted");
        if(!keys_exact(PyTuple_GET_ITEM(pin,1),i==5?&PyUnicode_Type:&PyLong_Type))return fail(config,"native registry key substituted");
    }
    if(literal_lookup(ns,&PyId__TREE_NATIVE_CONVERT)!=PyTuple_GET_ITEM(config,4)||
    literal_lookup(ns,&PyId__TREE_NATIVE_VERIFY)!=PyTuple_GET_ITEM(config,5))return fail(config,"native whole origin substituted");
    PyObject *pins=PyTuple_GET_ITEM(config,2);
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(pins);i++){
        PyObject *p=PyTuple_GET_ITEM(pins,i),*fn=PyTuple_GET_ITEM(p,1);
        if(!PyFunction_Check(fn)||PyDict_GetItemWithError(ns,PyTuple_GET_ITEM(p,0))!=fn||
        PyFunction_GET_CODE(fn)!=PyTuple_GET_ITEM(p,2))return fail(config,"native whole origin substituted");
        PyObject *defaults=PyFunction_GET_DEFAULTS(fn),*kw=PyFunction_GET_KW_DEFAULTS(fn);
        if(defaults==NULL)defaults=Py_None;
        if(kw==NULL)kw=Py_None;
        if(defaults!=PyTuple_GET_ITEM(p,3)||kw!=PyTuple_GET_ITEM(p,4))return fail(config,"native whole defaults substituted");
        if(kw!=Py_None){
            PyObject *items=PyTuple_GET_ITEM(p,5);
            if(!PyDict_CheckExact(kw)||PyDict_GET_SIZE(kw)!=PyTuple_GET_SIZE(items))return fail(config,"native whole defaults substituted");
            Py_ssize_t pos=0,n=0;
            PyObject *key,*value;
            while(PyDict_Next(kw,&pos,&key,&value)){
                PyObject *pair=PyTuple_GET_ITEM(items,n++);
                if(key!=PyTuple_GET_ITEM(pair,0)||value!=PyTuple_GET_ITEM(pair,1)){
                    if(!(i==1&&PyTuple_GET_SIZE(items)==1&&key==PyTuple_GET_ITEM(pair,0)&&PyLong_CheckExact(value)))return fail(config,"native whole defaults substituted");
                }
            }
        }
    }
    if(PyErr_Occurred())return -1;
    return 0;
}
static PyObject *record_for(PyObject *config,PyObject *hint) {
    PyObject *records=PyTuple_GET_ITEM(config,1);
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(records);i++){
        PyObject *r=PyTuple_GET_ITEM(records,i);
        if(PyTuple_GET_ITEM(r,0)==hint)return r;
    }
    return NULL;
}
typedef struct {
    int clean;
    uint64_t records;
    Py_ssize_t gc_epoch[3];
    /* Immutable sealed declarations only, borrowed for this C invocation.
     * Live registry authentication still follows every successful lookup. */
    PyObject *shape_rows[64];
}
Proof;
static PyObject *shape_for(PyObject *config,PyObject *hint,Proof *proof) {
    uintptr_t address=(uintptr_t)hint;
    Py_ssize_t slot=(Py_ssize_t)(((address>>4)^(address>>13))&63);
    PyObject *selected=proof->shape_rows[slot];
    if(!selected||PyTuple_GET_ITEM(selected,0)!=hint){
        selected=NULL;
        PyObject *shapes=PyTuple_GET_ITEM(config,8);
        for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(shapes);i++){
            PyObject *row=PyTuple_GET_ITEM(shapes,i);
            if(PyTuple_GET_ITEM(row,0)==hint){selected=row;break;}
        }
        proof->shape_rows[slot]=selected;
    }
    if(selected){
        PyObject *registry=PyTuple_GET_ITEM(PyTuple_GET_ITEM(PyTuple_GET_ITEM(config,3),4),1);
        if(PyDict_GetItemWithError(registry,PyTuple_GET_ITEM(selected,3))!=PyTuple_GET_ITEM(selected,4)){
            fail(config,"native whole hint shape substituted");
            return NULL;
        }
    }
    return selected;
}
static int ensure(PyObject *config,Proof *proof){
    struct _gc_runtime_state*g=&PyThreadState_Get()->interp->gc;
    if(!proof->clean||proof->gc_epoch[0]!=g->generation_stats[0].collections||proof->gc_epoch[1]!=g->generation_stats[1].collections||proof->gc_epoch[2]!=g->generation_stats[2].collections){
        if(auth(config)<0)return -1;
        proof->clean=1;
        proof->records=0;
        for(int k=0;k<3;k++)proof->gc_epoch[k]=g->generation_stats[k].collections;
    }
    return 0;
}
static PyObject *field(PyObject *record,PyObject *payload,Py_ssize_t index){
    PyObject *row=PyTuple_GET_ITEM(PyTuple_GET_ITEM(record,1),index);
    return PyDict_GetItemWithError(payload,PyTuple_GET_ITEM(row,0));
}
static int payload_shape(PyObject *record,PyObject *payload){
    PyObject *defs=PyTuple_GET_ITEM(record,1);
    if(!keys_exact(payload,&PyUnicode_Type)||PyDict_GET_SIZE(payload)!=PyTuple_GET_SIZE(defs))return 0;
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(defs);i++){
        PyObject *name=PyTuple_GET_ITEM(PyTuple_GET_ITEM(defs,i),0);
        if(PyDict_GetItemWithError(payload,name)==NULL)return PyErr_Occurred()?-1:0;
    }
    return 1;
}
static int ascii_path(PyObject *value){
    if(!PyUnicode_CheckExact(value)||!PyUnicode_IS_ASCII(value))return 0;
    Py_ssize_t n=PyUnicode_GET_LENGTH(value),start=0;
    if(n<1||n>1024)return 0;
    const Py_UCS1 *p=PyUnicode_1BYTE_DATA(value);
    for(Py_ssize_t i=0;i<=n;i++){
        if(i<n&&(p[i]<0x20||p[i]>0x7e||p[i]=='\\'))return 0;
        if(i==n||p[i]=='/'){
            Py_ssize_t size=i-start;
            if(size<1||size>255||(size==1&&p[start]=='.')||(size==2&&p[start]=='.'&&p[start+1]=='.'))return 0;
            start=i+1;
        }
    }
    return 1;
}
static int digest(PyObject *value){
    if(!PyUnicode_CheckExact(value)||!PyUnicode_IS_ASCII(value)||PyUnicode_GET_LENGTH(value)!=71)return 0;
    const Py_UCS1 *p=PyUnicode_1BYTE_DATA(value);
    if(memcmp(p,"sha256:",7)!=0)return 0;
    for(int i=7;i<71;i++)if(!((p[i]>='0'&&p[i]<='9')||(p[i]>='a'&&p[i]<='f')))return 0;
    return 1;
}
static int is_text(PyObject *value,const char *text){
    return PyUnicode_CheckExact(value)&&PyUnicode_IS_ASCII(value)&&PyUnicode_CompareWithASCIIString(value,text)==0;
}
static int allowed_mode(PyObject *value,int scratch_create){
    if(!PyLong_CheckExact(value))return 0;
    long n=PyLong_AsLong(value);
    if(n==-1&&PyErr_Occurred()){
        PyErr_Clear();
        return 0;
    }
    return n==420||n==493||(scratch_create&&n==384);
}
/* Pure ASCII grammar acceleration only: no context, field/payload cache,
 * source, owner or authority. Unknown/invalid data takes the original path. */
static PyObject *ascii_path_positive(PyObject *self,PyObject *const *args,Py_ssize_t nargs){
    (void)self;
    if(nargs!=2){PyErr_SetString(PyExc_TypeError,"ascii_path_positive requires two arguments");return NULL;}
    PyObject *value=args[0],*maximum=args[1];
    if(!PyUnicode_CheckExact(value)||!PyUnicode_IS_ASCII(value)||!PyLong_CheckExact(maximum))Py_RETURN_FALSE;
    Py_ssize_t bound=PyLong_AsSsize_t(maximum);
    if(bound==-1&&PyErr_Occurred()){PyErr_Clear();Py_RETURN_FALSE;}
    if(PyUnicode_GET_LENGTH(value)>bound)Py_RETURN_FALSE;
    return PyBool_FromLong(ascii_path(value));
}
/* Positive-only complete leaf semantics. Invalid/uncertain data takes the exact
   original validator on this already freshly converted payload, in original order. */
static int positive_semantics(PyObject *c,PyObject *record,PyObject *out){
    /* The original validator selects branches through both module namespaces.
     * Initial declaration-time versions are never refreshed after any edit.
     * A changed namespace uses that original validator, including its original
     * error and callback behavior; three leaf aliases alone are insufficient. */
    PyObject *codec_dict=PyModule_GetDict(PyTuple_GET_ITEM(c,0));
    PyObject *values_dict=PyModule_GetDict(PyTuple_GET_ITEM(c,15));
    if(((PyDictObject*)codec_dict)->ma_version_tag!=PyLong_AsUnsignedLongLong(PyTuple_GET_ITEM(c,26))||
       ((PyDictObject*)values_dict)->ma_version_tag!=PyLong_AsUnsignedLongLong(PyTuple_GET_ITEM(c,27)))return 0;
    PyObject *cls=PyTuple_GET_ITEM(record,0),*classes=PyTuple_GET_ITEM(c,16);
    int kind=-1;
    for(int i=0;i<3;i++)if(cls==PyTuple_GET_ITEM(classes,i))kind=i;
    if(kind<0)return 0;
    int payload_ok=payload_shape(record,out);
    if(payload_ok<=0)return payload_ok;
    PyObject *vns=PyModule_GetDict(PyTuple_GET_ITEM(c,15)),*ns=PyModule_GetDict(PyTuple_GET_ITEM(c,0));
    PyObject *names=PyTuple_GET_ITEM(c,17);
    for(int i=0;i<3;i++)if(PyDict_GetItemWithError(vns,PyTuple_GET_ITEM(names,i))!=PyTuple_GET_ITEM(classes,i))return 0;
    if(PyDict_GetItemWithError(ns,PyTuple_GET_ITEM(c,22))!=PyTuple_GET_ITEM(c,18))return 0;
    PyObject *pathpin=PyTuple_GET_ITEM(PyTuple_GET_ITEM(c,2),1),*kw=PyFunction_GET_KW_DEFAULTS(PyTuple_GET_ITEM(pathpin,1));
    if(kw==NULL||PyDict_GetItemWithError(kw,PyTuple_GET_ITEM(c,24))!=PyTuple_GET_ITEM(c,19))return 0;
    PyObject *masks=PyTuple_GET_ITEM(PyTuple_GET_ITEM(record,3),1);
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(masks);i++){
        PyObject *m=PyTuple_GET_ITEM(masks,i),*item=PyDict_GetItemWithError(out,PyTuple_GET_ITEM(m,0));
        if(item==NULL)return -1;
        if(item==Py_None)continue;
        long mask=PyLong_AsLong(PyTuple_GET_ITEM(m,1));
        if(mask==-1&&PyErr_Occurred())return -1;
        if((mask&1)&&!digest(item))return 0;
        if((mask&2)&&!ascii_path(item))return 0;
        if((mask&4)&&(!PyList_CheckExact(item)||PyList_GET_SIZE(item)!=2))return 0;
        if((mask&8)&&(!PyUnicode_CheckExact(item)||PyUnicode_GET_LENGTH(item)==0))return 0;
    }
    if(kind==0){
        /* EntryPin */
        PyObject *exists=field(record,out,0);
        if(exists==Py_False){
            for(int i=1;i<9;i++)if(field(record,out,i)!=Py_None)return 0;
            return 1;
        }
        for(int i=1;i<8;i++)if(field(record,out,i)==Py_None)return 0;
        long mode=PyLong_AsLong(field(record,out,6)),links=PyLong_AsLong(field(record,out,7));
        if(PyErr_Occurred()){
            PyErr_Clear();
            return 0;
        }
        return mode>=0&&mode<=4095&&links>=1;
    }
    if(kind==2){
        /* ScratchEffect */
        PyObject *mode=field(record,out,4);
        return mode==Py_None||allowed_mode(mode,is_text(field(record,out,3),"create"));
    }
    /* FileTransition */
    PyObject *entry_record=record_for(c,PyTuple_GET_ITEM(classes,0));
    PyObject *before=field(record,out,4),*body=field(record,out,5),*requested=field(record,out,9);
    payload_ok=payload_shape(entry_record,before);
    if(payload_ok<=0)return payload_ok;
    PyObject *before_exists=field(entry_record,before,0),*before_links=field(entry_record,before,7),*before_size=field(entry_record,before,3),*before_digest=field(entry_record,before,8);
    if(Py_TYPE(before_exists)!=&PyBool_Type||(before_links!=Py_None&&!PyLong_CheckExact(before_links))||
    (before_size!=Py_None&&!PyLong_CheckExact(before_size))||(before_digest!=Py_None&&!PyUnicode_CheckExact(before_digest)))return 0;
    int deleted=is_text(field(record,out,1),"DELETE"),created=is_text(field(record,out,1),"CREATE");
    if(deleted){
        if(field(record,out,2)!=Py_None||requested!=Py_None)return 0;
    }
    else if(field(record,out,2)==Py_None||!allowed_mode(requested,0))return 0;
    PyObject *exists=field(entry_record,before,0);
    if((exists==Py_True)==created)return 0;
    if(exists==Py_True){
        PyObject *links=field(entry_record,before,7);
        int equal=PyObject_RichCompareBool(links,PyTuple_GET_ITEM(c,21),Py_EQ);
        if(equal<0)return -1;
        if(!equal||field(entry_record,before,8)==Py_None||body==Py_None)return 0;
    }
    else if(body!=Py_None)return 0;
    int indexes[4]={
        3,6,7,8
    };
    for(int i=0;i<4;i++)if((field(record,out,indexes[i])==Py_None)!=deleted)return 0;
    PyObject *cap=PyDict_GetItemWithError(vns,PyTuple_GET_ITEM(c,23));
    if(cap!=PyTuple_GET_ITEM(c,20))return 0;
    PyObject *sizes[2]={
        field(record,out,8),field(entry_record,before,3)
    };
    for(int i=0;i<2;i++){
        PyObject *size=sizes[i]==Py_None?PyTuple_GET_ITEM(c,9):sizes[i];
        int exceeds=PyObject_RichCompareBool(size,cap,Py_GT);
        if(exceeds<0)return -1;
        if(exceeds)return 0;
    }
    return 1;
}
static PyObject *convert(PyObject *,PyObject *,PyObject *,long,PyObject *,Proof *);
static PyObject *primitive(PyObject *c,PyObject *hint,PyObject *value,PyObject *name) {
    if(Py_TYPE(value)!=(PyTypeObject *)hint){
        fail(c,"tree primitive type differs");
        return NULL;
    }
    if(hint==(PyObject *)&PyUnicode_Type){
        Py_ssize_t bytes;
        const char *data=PyUnicode_AsUTF8AndSize(value,&bytes);
        if(data==NULL){
            if(PyErr_ExceptionMatches(PyExc_UnicodeError)){
                replace_error(c,"tree text must be UTF-8");
            }
            return NULL;
        }
        if(bytes>16384){
            fail(c,"tree text exceeds bound");
            return NULL;
        }
    }
    else if(hint==(PyObject *)&PyLong_Type){
        int signed_timestamp=PyUnicode_CheckExact(name)&&
        (PyUnicode_CompareWithASCIIString(name,"mtime_ns")==0||PyUnicode_CompareWithASCIIString(name,"ctime_ns")==0);
        PyObject *floor=PyTuple_GET_ITEM(c,signed_timestamp?10:9),*ceiling=PyTuple_GET_ITEM(c,11);
        int a=PyObject_RichCompareBool(value,floor,Py_GE),b=PyObject_RichCompareBool(value,ceiling,Py_LE);
        if(a<0||b<0)return NULL;
        if(!a||!b){
            fail(c,"tree integer exceeds bound");
            return NULL;
        }
    }
    return Py_NewRef(value);
}
static int record_ready(PyObject*c,PyObject*record,PyObject*hint,Proof*proof,uint64_t bit){
    if(ensure(c,proof)<0)return -1;
    if(bit&&(proof->records&bit))return 0;
    if(!keys_exact(((PyTypeObject*)hint)->tp_dict,&PyUnicode_Type))return fail(c,"native descriptive schema key changed");
    PyObject *defs=PyTuple_GET_ITEM(record,1),*schema=PyTuple_GET_ITEM(record,2),*key=PyTuple_GET_ITEM(record,4);
    PyObject *ns=((PyTypeObject *)hint)->tp_dict;
    PyObject *regs=PyTuple_GET_ITEM(c,3);
    /* Registry order: definitions,native,originals,fieldchecks,hintshapes. */
    for(int k=0;k<4;k++){
        PyObject *registry=PyTuple_GET_ITEM(PyTuple_GET_ITEM(regs,k),1);
        PyObject *expected=PyTuple_GET_ITEM(record,k==0?5:k==3?3:2);
        if(PyDict_GetItemWithError(registry,key)!=expected){
            fail(c,"exact descriptive tree value required");
            return -1;
        }
    }
    if(!PyTuple_CheckExact(schema)||PyTuple_GET_SIZE(schema)!=3){
        fail(c,"exact descriptive tree value required");
        return -1;
    }
    PyObject *pair=PyTuple_GET_ITEM(schema,2),*fn=PyTuple_GET_ITEM(pair,0);
    if(!PyFunction_Check(fn)||PyFunction_GET_CODE(fn)!=PyTuple_GET_ITEM(pair,1)||PyFunction_GET_DEFAULTS(fn)!=NULL||PyFunction_GET_KW_DEFAULTS(fn)!=NULL){
        fail(c,"native tree schema code or defaults changed");
        return -1;
    }
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(defs);i++){
        PyObject *f=PyTuple_GET_ITEM(defs,i),*descriptor=PyTuple_GET_ITEM(f,1);
        if(Py_TYPE(descriptor)!=&PyMemberDescr_Type||PyDescr_TYPE(descriptor)!=(PyTypeObject *)hint||
        PyDict_GetItemWithError(ns,PyTuple_GET_ITEM(f,0))!=descriptor){
            fail(c,"tree slot descriptor changed");
            return -1;
        }
    }
    if(bit)proof->records|=bit;
    return 0;
}
static PyObject *convert(PyObject *c,PyObject *hint,PyObject *value,long depth,PyObject *name,Proof *proof) {
    if(depth>24){
        fail(c,"tree metadata nesting exceeds bound");
        return NULL;
    }
    if(hint==(PyObject *)&PyUnicode_Type||hint==(PyObject *)&PyLong_Type||hint==(PyObject *)&PyBool_Type)return primitive(c,hint,value,name);
    PyObject *record=record_for(c,hint);
    if(record!=NULL){
        /* An ordinal in the immutable sealed declaration is computed once in
         * this frame. All original record_ready authentication checkpoints and
         * their GC-epoch invalidation still execute; only the repeated linear
         * search for this same membership bit is removed. No value is cached. */
        PyObject *records=PyTuple_GET_ITEM(c,1);
        Py_ssize_t ordinal=0;
        while(ordinal<PyTuple_GET_SIZE(records)&&PyTuple_GET_ITEM(records,ordinal)!=record)ordinal++;
        uint64_t record_bit=ordinal<64?((uint64_t)1<<ordinal):0;
        if(record_ready(c,record,hint,proof,record_bit)<0)return NULL;
        PyObject *defs=PyTuple_GET_ITEM(record,1);
        if(Py_TYPE(value)!=(PyTypeObject *)hint){
            fail(c,"exact descriptive tree value required");
            return NULL;
        }
        PyObject *out=PyDict_New();
        if(out==NULL)return NULL;
        if(record_ready(c,record,hint,proof,record_bit)<0){
            Py_DECREF(out);
            return NULL;
        }
        if(Py_TYPE(value)!=(PyTypeObject *)hint){
            Py_DECREF(out);
            fail(c,"exact descriptive tree value required");
            return NULL;
        }
        for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(defs);i++){
            PyObject *f=PyTuple_GET_ITEM(defs,i),*fieldname=PyTuple_GET_ITEM(f,0),*descriptor=PyTuple_GET_ITEM(f,1);
            if(record_ready(c,record,hint,proof,record_bit)<0){
                Py_DECREF(out);
                return NULL;
            }
            PyObject *raw=Py_TYPE(descriptor)->tp_descr_get(descriptor,value,hint);
            if(raw==NULL){
                Py_DECREF(out);
                if(PyErr_ExceptionMatches(PyExc_AttributeError)){
                    replace_error(c,"tree fields missing");
                }
                return NULL;
            }
            PyObject *child=convert(c,PyTuple_GET_ITEM(f,2),raw,depth+1,fieldname,proof);
            Py_DECREF(raw);
            if(child==NULL){
                Py_DECREF(out);
                /* The literal parent catches AttributeError from its complete
                   generated field conversion, including nested validation. */
                if(PyErr_ExceptionMatches(PyExc_AttributeError)){
                    replace_error(c,"tree fields missing");
                }
                return NULL;
            }
            int okay=PyDict_SetItem(out,fieldname,child);
            Py_DECREF(child);
            if(okay<0){
                Py_DECREF(out);
                return NULL;
            }
        }
        if(record_ready(c,record,hint,proof,record_bit)<0){
            Py_DECREF(out);
            return NULL;
        }
        /* The unchanged Python caller performs the root semantic check once,
         * immediately after this generated field traversal returns. */
        int root = hint == PyTuple_GET_ITEM(c, 25);
        int native_positive = root ? 1 : positive_semantics(c,record,out);
        if(native_positive<0){
            Py_DECREF(out);
            return NULL;
        }
        if(!native_positive){
            PyObject *validator=PyTuple_GET_ITEM(PyTuple_GET_ITEM(PyTuple_GET_ITEM(c,2),0),1);
            PyObject *args[2]={
                hint,out
            };
            proof->clean=0;
            PyObject *result=PyObject_Vectorcall(validator,args,2,NULL);
            if(result==NULL){
                Py_DECREF(out);
                return NULL;
            }
            Py_DECREF(result);
            if(record_ready(c,record,hint,proof,record_bit)<0){
                Py_DECREF(out);
                return NULL;
            }
        }
        return out;
    }
    if(ensure(c,proof)<0)return NULL;
    PyObject *shape=shape_for(c,hint,proof);
    if(shape==NULL){
        if(!PyErr_Occurred())fail(c,"unsupported tree metadata type");
        return NULL;
    }
    PyObject *origin=PyTuple_GET_ITEM(shape,1),*args=PyTuple_GET_ITEM(shape,2);
    PyObject *pins=PyTuple_GET_ITEM(c,12);
    if(origin==PyTuple_GET_ITEM(pins,0)){
        int nullable=0;
        PyObject *selected=NULL;
        for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(args);i++){
            PyObject *a=PyTuple_GET_ITEM(args,i);
            if(a==(PyObject *)Py_TYPE(Py_None))nullable=1;
            else if(selected==NULL)selected=a;
        }
        if(value==Py_None&&nullable)return Py_NewRef(Py_None);
        if(selected==NULL){
            fail(c,"unsupported tree metadata type");
            return NULL;
        }
        return convert(c,selected,value,depth+1,name,proof);
    }
    if(origin==PyTuple_GET_ITEM(pins,1)){
        if(PyUnicode_CheckExact(value)||PyLong_CheckExact(value)){
            for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(args);i++){
                PyObject *a=PyTuple_GET_ITEM(args,i);
                if(Py_TYPE(a)!=Py_TYPE(value))continue;
                int same=PyObject_RichCompareBool(value,a,Py_EQ);
                if(same<0)return NULL;
                if(same)return Py_NewRef(value);
            }
        }
        fail(c,"unknown tree enum");
        return NULL;
    }
    if(origin==(PyObject *)&PyTuple_Type){
        if(!PyTuple_CheckExact(value)){
            fail(c,"tree ordered collection type differs");
            return NULL;
        }
        PyObject *values_module=PyTuple_GET_ITEM(c,15),*ns=PyModule_GetDict(PyTuple_GET_ITEM(c,0));
        if(literal_lookup(ns,&PyId_values)!=values_module){
            fail(c,"native whole values origin substituted");
            return NULL;
        }
        PyObject *default_cap=literal_lookup(PyModule_GetDict(values_module),&PyId_MAX_TREE_RECEIPTS);
        if(default_cap==NULL){
            if(!PyErr_Occurred())fail(c,"native whole collection bound missing");
            return NULL;
        }
        PyObject *limits=PyTuple_GET_ITEM(c,7),*cap=PyDict_GetItemWithError(limits,name);
        if(cap==NULL){
            if(PyErr_Occurred())return NULL;
            cap=default_cap;
        }
        if(!PyLong_CheckExact(cap)){
            fail(c,"native whole collection bound substituted");
            return NULL;
        }
        Py_ssize_t n=PyTuple_GET_SIZE(value);
        int exceeds=0;
        PyObject *size=PyLong_FromSsize_t(n);
        if(size==NULL)return NULL;
        exceeds=PyObject_RichCompareBool(size,cap,Py_GT);
        Py_DECREF(size);
        if(exceeds<0)return NULL;
        if(exceeds){
            fail(c,"tree ordered collection exceeds bound");
            return NULL;
        }
        PyObject *out=PyList_New(n);
        if(out==NULL)return NULL;
        for(Py_ssize_t i=0;i<n;i++){
            PyObject *child=convert(c,PyTuple_GET_ITEM(args,0),PyTuple_GET_ITEM(value,i),depth+1,PyTuple_GET_ITEM(c,14),proof);
            if(child==NULL){
                Py_DECREF(out);
                return NULL;
            }
            PyList_SET_ITEM(out,i,child);
        }
        return out;
    }
    fail(c,"unsupported tree metadata type");
    return NULL;
}
/* A sealed, GC-tracked nominal context keeps unchecked tuple access behind
 * bounded behavior-free declaration validation. No operation or value is held. */
typedef struct {
    PyObject_HEAD int phase;
    PyObject *config;
    PyObject *weakrefs;
}
NativeConfig;
static int traverse_context(NativeConfig *self, visitproc visit, void *arg) {
    Py_VISIT(self->config);
    return 0;
}
static int clear_context(NativeConfig *self) {
    self->phase=3;
    Py_CLEAR(self->config);
    return 0;
}
static void destroy_context(NativeConfig *self) {
    PyObject_GC_UnTrack(self);
    if(self->weakrefs)PyObject_ClearWeakRefs((PyObject*)self);
    clear_context(self);
    PyObject_GC_Del(self);
}
static PyObject *no_construct(PyTypeObject *type, PyObject *args, PyObject *kw) {
    (void)type;
    (void)args;
    (void)kw;
    PyErr_SetString(PyExc_TypeError,"use the original metadata context factory");
    return NULL;
}
static PyTypeObject ContextType={
    PyVarObject_HEAD_INIT(NULL,0)
    .tp_name="aware_workspace_sdk._tree_native._Context",
    .tp_basicsize=sizeof(NativeConfig),
    .tp_flags=Py_TPFLAGS_DEFAULT|Py_TPFLAGS_HAVE_GC,
    .tp_dealloc=(destructor)destroy_context,
    .tp_traverse=(traverseproc)traverse_context,
    .tp_clear=(inquiry)clear_context,
    .tp_new=no_construct,
    .tp_weaklistoffset=offsetof(NativeConfig,weakrefs),
};
static PyObject *convert_root(PyObject *, PyObject *);
static PyObject *ascii_paths_last(PyObject *,PyObject *const *,Py_ssize_t);
static PyObject *verify(PyObject *, PyObject *);
static int tuple_size(PyObject *v, Py_ssize_t n) {
    return PyTuple_CheckExact(v) && PyTuple_GET_SIZE(v) == n;
}
static int bounded_tuple(PyObject *v, Py_ssize_t n) {
    return PyTuple_CheckExact(v) && PyTuple_GET_SIZE(v) <= n;
}
static int declarations(PyObject *c) {
    if (!tuple_size(c, 26) || !PyModule_CheckExact(PyTuple_GET_ITEM(c, 0)) ||
    !PyModule_CheckExact(PyTuple_GET_ITEM(c, 15))) return 0;
    PyObject *records=PyTuple_GET_ITEM(c,1), *functions=PyTuple_GET_ITEM(c,2);
    PyObject *regs=PyTuple_GET_ITEM(c,3), *shapes=PyTuple_GET_ITEM(c,8);
    if (!bounded_tuple(records,64) || !bounded_tuple(functions,32) ||
    !tuple_size(regs,6) || !bounded_tuple(shapes,512)) return 0;
    PyObject *ns=PyModule_GetDict(PyTuple_GET_ITEM(c,0));
    for (Py_ssize_t j=0;j<6;j++) {
        PyObject *r=PyTuple_GET_ITEM(regs,j);
        if (!tuple_size(r,2) || !PyUnicode_CheckExact(PyTuple_GET_ITEM(r,0)) ||
        !keys_exact(PyTuple_GET_ITEM(r,1),j==5?&PyUnicode_Type:&PyLong_Type)) return 0;
    }
    for (Py_ssize_t j=0;j<PyTuple_GET_SIZE(functions);j++) {
        PyObject *r=PyTuple_GET_ITEM(functions,j);
        if (!tuple_size(r,6) || !PyUnicode_CheckExact(PyTuple_GET_ITEM(r,0))) return 0;
        PyObject *f=PyTuple_GET_ITEM(r,1), *code=PyTuple_GET_ITEM(r,2);
        PyObject *defaults=PyTuple_GET_ITEM(r,3), *kw=PyTuple_GET_ITEM(r,4);
        PyObject *items=PyTuple_GET_ITEM(r,5);
        if (Py_TYPE(f)!=&PyFunction_Type || !PyCode_Check(code) ||
        (j!=6 && PyFunction_GET_GLOBALS(f)!=ns) || PyFunction_GET_CODE(f)!=code ||
        (defaults!=Py_None && !PyTuple_CheckExact(defaults))) return 0;
        if (kw==Py_None) {
            if(items!=Py_None) return 0;
        }
        else {
            if (!PyDict_CheckExact(kw) || !tuple_size(items,PyDict_GET_SIZE(kw))) return 0;
            for (Py_ssize_t k=0;k<PyTuple_GET_SIZE(items);k++) {
                PyObject *pair=PyTuple_GET_ITEM(items,k);
                if (!tuple_size(pair,2) || !PyUnicode_CheckExact(PyTuple_GET_ITEM(pair,0))) return 0;
            }
        }
    }
    if (PyTuple_GET_SIZE(functions)<7) return 0;
    /* An optional code-constant dispatch must be this exact original image's
     * intrinsic. Unbound/older-source slots retain the portable validator. */
    PyObject *path_fn=PyTuple_GET_ITEM(PyTuple_GET_ITEM(functions,1),1);
    PyObject *constants=((PyCodeObject*)PyFunction_GET_CODE(path_fn))->co_consts;
    for(Py_ssize_t n=0;n<PyTuple_GET_SIZE(constants);n++){
        PyObject *slot=PyTuple_GET_ITEM(constants,n);
        if(!tuple_size(slot,2)||!PyUnicode_CheckExact(PyTuple_GET_ITEM(slot,0))||
        PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(slot,0),"__workspace_ascii_path_slot_v2__"))continue;
        PyObject *method=PyTuple_GET_ITEM(slot,1);
        if(method==Py_None)continue;
        if(!PyCFunction_Check(method)||PyCFunction_GET_FUNCTION(method)!=_PyCFunction_CAST(ascii_path_positive)||
        PyCFunction_GET_SELF(method)!=PyCFunction_GET_SELF(PyTuple_GET_ITEM(c,4))||
        PyCFunction_GET_FLAGS(method)!=METH_FASTCALL)return 0;
    }

    PyObject *sequence=PyTuple_GET_ITEM(PyTuple_GET_ITEM(functions,3),1);
    PyObject *sequence_constants=((PyCodeObject*)PyFunction_GET_CODE(sequence))->co_consts;
    int batch_slots=0;
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(sequence_constants);i++){
        PyObject *slot=PyTuple_GET_ITEM(sequence_constants,i);
        if(!tuple_size(slot,3)||!PyUnicode_CheckExact(PyTuple_GET_ITEM(slot,0))||
        PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(slot,0),"__workspace_ascii_paths_slot_v1__"))continue;
        if(++batch_slots>1)return 0;
        PyObject *method=PyTuple_GET_ITEM(slot,1),*reference=PyTuple_GET_ITEM(slot,2);
        if(method==Py_None){if(reference!=Py_None)return 0;continue;}
        if(!PyCFunction_Check(method)||PyCFunction_GET_FUNCTION(method)!=_PyCFunction_CAST(ascii_paths_last)||
        PyCFunction_GET_FLAGS(method)!=METH_FASTCALL||
        PyCFunction_GET_SELF(method)!=PyCFunction_GET_SELF(PyTuple_GET_ITEM(c,4))||
        !PyWeakref_CheckRefExact(reference))return 0;
    }
    for (Py_ssize_t j=0;j<PyTuple_GET_SIZE(records);j++) {
        PyObject *r=PyTuple_GET_ITEM(records,j);
        if (!tuple_size(r,6)) return 0;
        PyObject *cls=PyTuple_GET_ITEM(r,0), *defs=PyTuple_GET_ITEM(r,1);
        PyObject *schema=PyTuple_GET_ITEM(r,2), *checks=PyTuple_GET_ITEM(r,3);
        PyObject *key=PyTuple_GET_ITEM(r,4), *definition=PyTuple_GET_ITEM(r,5);
        if (Py_TYPE(cls)!=&PyType_Type || !bounded_tuple(defs,128) ||
        !tuple_size(schema,3) || PyTuple_GET_ITEM(schema,0)!=cls ||
        PyTuple_GET_ITEM(schema,1)!=defs || !tuple_size(PyTuple_GET_ITEM(schema,2),2) ||
        !tuple_size(checks,2) || PyTuple_GET_ITEM(checks,0)!=cls ||
        !bounded_tuple(PyTuple_GET_ITEM(checks,1),128) ||
        !PyLong_CheckExact(key) || !tuple_size(definition,2) ||
        PyTuple_GET_ITEM(definition,0)!=cls || PyTuple_GET_ITEM(definition,1)!=defs) return 0;
        if (PyLong_AsVoidPtr(key)!=cls) return 0;
        for (Py_ssize_t k=0;k<PyTuple_GET_SIZE(defs);k++) {
            PyObject *f=PyTuple_GET_ITEM(defs,k);
            if (!tuple_size(f,3) || !PyUnicode_CheckExact(PyTuple_GET_ITEM(f,0)) ||
            Py_TYPE(PyTuple_GET_ITEM(f,1))!=&PyMemberDescr_Type ||
            PyDescr_TYPE(PyTuple_GET_ITEM(f,1))!=(PyTypeObject*)cls) return 0;
        }
        PyObject *masks=PyTuple_GET_ITEM(checks,1);
        for (Py_ssize_t k=0;k<PyTuple_GET_SIZE(masks);k++) {
            PyObject *m=PyTuple_GET_ITEM(masks,k);
            if (!tuple_size(m,2) || !PyUnicode_CheckExact(PyTuple_GET_ITEM(m,0)) ||
            !PyLong_CheckExact(PyTuple_GET_ITEM(m,1))) return 0;
            long n=PyLong_AsLong(PyTuple_GET_ITEM(m,1));
            if(n<0||n>15||PyErr_Occurred())return 0;
        }
    }
    for (Py_ssize_t j=0;j<PyTuple_GET_SIZE(shapes);j++) {
        PyObject *r=PyTuple_GET_ITEM(shapes,j);
        if (!tuple_size(r,5) || !bounded_tuple(PyTuple_GET_ITEM(r,2),128) ||
        !PyLong_CheckExact(PyTuple_GET_ITEM(r,3)) ||
        !tuple_size(PyTuple_GET_ITEM(r,4),3)) return 0;
    }
    if (!PyCFunction_Check(PyTuple_GET_ITEM(c,4)) ||
    PyCFunction_GET_FUNCTION(PyTuple_GET_ITEM(c,4))!=(PyCFunction)convert_root ||
    !PyCFunction_Check(PyTuple_GET_ITEM(c,5)) ||
    PyCFunction_GET_FUNCTION(PyTuple_GET_ITEM(c,5))!=(PyCFunction)verify ||
    !PyModule_CheckExact(PyCFunction_GET_SELF(PyTuple_GET_ITEM(c,4))) ||
    PyCFunction_GET_SELF(PyTuple_GET_ITEM(c,4))!=PyCFunction_GET_SELF(PyTuple_GET_ITEM(c,5)) ||
    Py_TYPE(PyTuple_GET_ITEM(c,6))!=&PyType_Type ||
    !PyType_IsSubtype((PyTypeObject*)PyTuple_GET_ITEM(c,6),(PyTypeObject*)PyExc_ValueError) ||
    !keys_exact(PyTuple_GET_ITEM(c,7),&PyUnicode_Type) ||
    !tuple_size(PyTuple_GET_ITEM(c,12),2) ||
    !PyUnicode_CheckExact(PyTuple_GET_ITEM(c,14)) ||
    !tuple_size(PyTuple_GET_ITEM(c,16),3) ||
    !tuple_size(PyTuple_GET_ITEM(c,17),3)) return 0;
    const int integers[]={
        9,10,11,13,19,20,21
    };
    for (unsigned j=0;j<sizeof(integers)/sizeof(integers[0]);j++)
    if(!PyLong_CheckExact(PyTuple_GET_ITEM(c,integers[j])))return 0;
    for(int j=22;j<25;j++)if(!PyUnicode_CheckExact(PyTuple_GET_ITEM(c,j)))return 0;
    const char *entry_fields[]={
        "exists","device","inode","size_bytes","mtime_ns","ctime_ns","mode","link_count","content_digest"
    };
    const char *file_fields[]={
        "path","kind","source_output_path","source_path","before","before_body_ref","successor_body_ref","successor_digest","successor_size_bytes","requested_mode"
    };
    const char *scratch_fields[]={
        "path","role","ordinal","kind","requested_mode"
    };
    const char **orders[]={
        entry_fields,file_fields,scratch_fields
    };
    const Py_ssize_t counts[]={
        9,10,5
    };
    for (int j=0;j<3;j++) {
        PyObject *r=record_for(c,PyTuple_GET_ITEM(PyTuple_GET_ITEM(c,16),j));
        if (!r || !PyUnicode_CheckExact(PyTuple_GET_ITEM(PyTuple_GET_ITEM(c,17),j))) return 0;
        PyObject *defs=PyTuple_GET_ITEM(r,1);
        if(PyTuple_GET_SIZE(defs)!=counts[j])return 0;
        for(Py_ssize_t k=0;k<counts[j];k++)
        if(PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(PyTuple_GET_ITEM(defs,k),0),orders[j][k])!=0)return 0;
    }
    return record_for(c,PyTuple_GET_ITEM(c,25))!=NULL;
}
static NativeConfig *context(PyObject *v, int sealed) {
    if(Py_TYPE(v)!=&ContextType) {
        PyErr_SetString(PyExc_TypeError,"original native metadata context required");
        return NULL;
    }
    NativeConfig *s=(NativeConfig*)v;
    if(sealed && s->phase!=2) {
        PyErr_SetString(PyExc_RuntimeError,"native metadata context is not sealed");
        return NULL;
    }
    return s;
}
static PyObject *new_context(PyObject *self, PyObject *unused) {
    (void)self;
    (void)unused;
    NativeConfig *s=PyObject_GC_New(NativeConfig,&ContextType);
    if(!s)return NULL;
    s->phase=0;
    s->config=NULL;
    s->weakrefs=NULL;
    PyObject_GC_Track(s);
    return (PyObject*)s;
}
static PyObject *seal(PyObject *self, PyObject *args) {
    (void)self;
    PyObject *v,*c;
    if(!PyArg_ParseTuple(args,"OO:seal",&v,&c))return NULL;
    NativeConfig *s=context(v,0);
    if(!s)return NULL;
    if(s->phase){
        PyErr_SetString(PyExc_RuntimeError,"native metadata context already spent");
        return NULL;
    }
    s->phase=1;
    if(!declarations(c)){
        s->phase=3;
        if(!PyErr_Occurred())PyErr_SetString(PyExc_TypeError,"complete original native metadata declaration required");
        return NULL;
    }
    PyObject *sequence=PyTuple_GET_ITEM(PyTuple_GET_ITEM(PyTuple_GET_ITEM(c,2),3),1);
    PyObject *sequence_constants=((PyCodeObject*)PyFunction_GET_CODE(sequence))->co_consts;
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(sequence_constants);i++){
        PyObject *slot=PyTuple_GET_ITEM(sequence_constants,i);
        if(tuple_size(slot,3)&&PyUnicode_CheckExact(PyTuple_GET_ITEM(slot,0))&&
        !PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(slot,0),"__workspace_ascii_paths_slot_v1__")&&
        PyTuple_GET_ITEM(slot,1)!=Py_None&&PyWeakref_GET_OBJECT(PyTuple_GET_ITEM(slot,2))!=v){
            s->phase=3;
            PyErr_SetString(PyExc_TypeError,"original batch path context required");
            return NULL;
        }
    }
    if(auth(c)<0){
        s->phase=3;
        return NULL;
    }
    /* Keep the incoming declaration unchanged for older callers. Only this
     * private tree context extends it with immutable namespace witnesses. */
    uint64_t codec_version=((PyDictObject*)PyModule_GetDict(PyTuple_GET_ITEM(c,0)))->ma_version_tag;
    uint64_t values_version=((PyDictObject*)PyModule_GetDict(PyTuple_GET_ITEM(c,15)))->ma_version_tag;
    PyObject *sealed=PyTuple_New(28);
    if(sealed==NULL){s->phase=3;return NULL;}
    for(Py_ssize_t i=0;i<26;i++)PyTuple_SET_ITEM(sealed,i,Py_NewRef(PyTuple_GET_ITEM(c,i)));
    PyObject *codec_stamp=PyLong_FromUnsignedLongLong(codec_version);
    PyObject *values_stamp=PyLong_FromUnsignedLongLong(values_version);
    if(codec_stamp==NULL||values_stamp==NULL){
        Py_XDECREF(codec_stamp);Py_XDECREF(values_stamp);Py_DECREF(sealed);s->phase=3;return NULL;
    }
    PyTuple_SET_ITEM(sealed,26,codec_stamp);PyTuple_SET_ITEM(sealed,27,values_stamp);
    if(auth(sealed)<0){Py_DECREF(sealed);s->phase=3;return NULL;}
    s->config=sealed;
    s->phase=2;
    Py_RETURN_NONE;
}
static PyObject *convert_root(PyObject *self, PyObject *args) {
    COST_BEGIN(0);
    (void)self;
    PyObject *v,*hint,*value,*name;
    long depth;
    if(!PyArg_ParseTuple(args,"OOOOl:convert_root",&v,&hint,&value,&name,&depth))COST_RETURN(NULL);
    NativeConfig *s=context(v,1);
    if(!s)COST_RETURN(NULL);
    if(hint!=PyTuple_GET_ITEM(s->config,25)||!PyUnicode_CheckExact(name))COST_RETURN(Py_NewRef(Py_NotImplemented));
    Proof proof={
        0
    };
    if(ensure(s->config,&proof)<0)COST_RETURN(NULL);
    PyObject *out=convert(s->config,hint,value,depth,name,&proof);
    if(out && auth(s->config)<0){
        Py_DECREF(out);
        COST_RETURN(NULL);
    }
    COST_RETURN(out);
}
static PyObject *verify(PyObject *self, PyObject *v) {
    COST_BEGIN(1);
    (void)self;
    NativeConfig *s=context(v,1);
    if(!s)COST_RETURN(NULL);
    if(auth(s->config)<0)COST_RETURN(NULL);
    COST_RETURN(Py_NewRef(Py_None));
}
/* Positive-only batching of the original ASCII leaf grammar. This is a
 * descriptive check, not source/currentness/owner authority. Unknown inputs or
 * observers keep the literal original ordered Python loop. Every supplied path
 * is freshly read; no input, payload or validation result is retained. */
static PyObject *ascii_paths_last(PyObject *self,PyObject *const *args,Py_ssize_t nargs){
    if(nargs!=4){PyErr_SetString(PyExc_TypeError,"four batch path arguments required");return NULL;}
    if(Py_TYPE(args[0])!=&ContextType||((NativeConfig*)args[0])->phase!=2)Py_RETURN_NONE;
    NativeConfig *context=(NativeConfig*)args[0];
    if(!PyModule_CheckExact(self)){PyErr_SetString(PyExc_TypeError,"original batch path module required");return NULL;}
    PyObject *exports=PyModule_GetDict(self);
    if(!keys_exact(exports,&PyUnicode_Type)){PyErr_SetString(PyExc_TypeError,"original batch path exports required");return NULL;}
    PyObject *method=PyDict_GetItemString(exports,"ascii_paths_last");
    if(!method&&PyErr_Occurred())return NULL;
    PyObject *abi=PyDict_GetItemString(exports,"ASCII_PATH_BATCH_ABI");
    if(!abi&&PyErr_Occurred())return NULL;
    if(!method||!PyCFunction_Check(method)||PyCFunction_GET_FUNCTION(method)!=_PyCFunction_CAST(ascii_paths_last)||
    PyCFunction_GET_FLAGS(method)!=METH_FASTCALL||PyCFunction_GET_SELF(method)!=self||
    !abi||!PyLong_CheckExact(abi)||!_PyLong_IsCompact((PyLongObject*)abi)||_PyLong_CompactValue((PyLongObject*)abi)!=1){
        if(!PyErr_Occurred())PyErr_SetString(PyExc_TypeError,"original batch path export required");
        return NULL;
    }
    if(PyCFunction_GET_SELF(PyTuple_GET_ITEM(context->config,4))!=self){PyErr_SetString(PyExc_TypeError,"original batch path receiver required");return NULL;}
    if(auth(context->config)<0)return NULL;
    PyObject *config=context->config;
    PyObject *codec=PyModule_GetDict(PyTuple_GET_ITEM(config,0));
    PyObject *values=PyModule_GetDict(PyTuple_GET_ITEM(config,15));
    uint64_t codec_clock=PyLong_AsUnsignedLongLong(PyTuple_GET_ITEM(config,26));
    if(PyErr_Occurred())return NULL;
    uint64_t values_clock=PyLong_AsUnsignedLongLong(PyTuple_GET_ITEM(config,27));
    if(PyErr_Occurred())return NULL;
    if(((PyDictObject*)codec)->ma_version_tag!=codec_clock||
    ((PyDictObject*)values)->ma_version_tag!=values_clock)Py_RETURN_NONE;
    PyObject *path_function=PyTuple_GET_ITEM(PyTuple_GET_ITEM(PyTuple_GET_ITEM(config,2),1),1);
    PyObject *global_type=PyDict_GetItemString(codec,"type");
    if(!global_type&&PyErr_Occurred())return NULL;
    PyObject *global_str=PyDict_GetItemString(codec,"str");
    if(!global_str&&PyErr_Occurred())return NULL;
    if((global_type&&global_type!=(PyObject*)&PyType_Type)||
    (global_str&&global_str!=(PyObject*)&PyUnicode_Type))Py_RETURN_NONE;
    int original_intrinsic=0;
    PyObject *path_constants=((PyCodeObject*)PyFunction_GET_CODE(path_function))->co_consts;
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(path_constants);i++){
        PyObject *slot=PyTuple_GET_ITEM(path_constants,i);
        if(!tuple_size(slot,2)||!PyUnicode_CheckExact(PyTuple_GET_ITEM(slot,0))||
        PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(slot,0),"__workspace_ascii_path_slot_v2__"))continue;
        PyObject *method=PyTuple_GET_ITEM(slot,1);
        if(PyCFunction_Check(method)&&PyCFunction_GET_FUNCTION(method)==_PyCFunction_CAST(ascii_path_positive)&&
        PyCFunction_GET_FLAGS(method)==METH_FASTCALL&&PyCFunction_GET_SELF(method)==self)original_intrinsic++;
    }
    if(original_intrinsic!=1)Py_RETURN_NONE;
    PyObject *builtins=((PyFunctionObject*)path_function)->func_builtins;
    if(!keys_exact(builtins,&PyUnicode_Type))Py_RETURN_NONE;
    PyObject *builtin_type=PyDict_GetItemString(builtins,"type");
    if(!builtin_type&&PyErr_Occurred())return NULL;
    PyObject *builtin_str=PyDict_GetItemString(builtins,"str");
    if(!builtin_str&&PyErr_Occurred())return NULL;
    if(builtin_type!=(PyObject*)&PyType_Type||builtin_str!=(PyObject*)&PyUnicode_Type)Py_RETURN_NONE;
    PyThreadState *thread=PyThreadState_Get();
    if(thread->c_profilefunc||thread->c_tracefunc||
    _PyInterpreterState_GetEvalFrameFunc(thread->interp)!=_PyEval_EvalFrameDefault)Py_RETURN_NONE;
    for(int i=0;i<PY_MONITORING_TOOL_IDS;i++){
        if(thread->interp->monitoring_tool_names[i])Py_RETURN_NONE;
        for(int e=0;e<_PY_MONITORING_EVENTS;e++)if(thread->interp->monitoring_callables[i][e]&&thread->interp->monitoring_callables[i][e]!=Py_None)Py_RETURN_NONE;
    }
    if(thread->interp->gc.callbacks&&PyList_GET_SIZE(thread->interp->gc.callbacks))Py_RETURN_NONE;
    if(!PyList_CheckExact(args[1])||!keys_exact(args[2],&PyUnicode_Type)||
    !keys_exact(args[3],&PyUnicode_Type))Py_RETURN_NONE;
    PyObject *effects=PyDict_GetItemString(args[2],"effect_paths");
    if(!effects&&PyErr_Occurred())return NULL;
    PyObject *guards=PyDict_GetItemString(args[2],"read_guard_paths");
    if(!guards&&PyErr_Occurred())return NULL;
    PyObject *maximum_object=PyDict_GetItemString(args[3],"maximum_path_utf8_bytes");
    if(!maximum_object&&PyErr_Occurred())return NULL;
    PyObject *metadata=PyDict_GetItemString(args[3],"maximum_metadata_bytes");
    if(!metadata&&PyErr_Occurred())return NULL;
    if(!effects||!guards||!PyList_CheckExact(effects)||!PyList_CheckExact(guards)||
    !maximum_object||!metadata||!PyLong_CheckExact(maximum_object)||!PyLong_CheckExact(metadata))Py_RETURN_NONE;
    PyObject *lists[3]={args[1],effects,guards};
    Py_ssize_t total=0;
    for(int j=0;j<3;j++){
        Py_ssize_t length=PyList_GET_SIZE(lists[j]);
        if(length>16384-total)Py_RETURN_NONE;
        total+=length;
    }
    if(!total)Py_RETURN_NONE;
    int overflow=0;long maximum=PyLong_AsLongAndOverflow(maximum_object,&overflow);
    if(PyErr_Occurred())return NULL;
    if(overflow||maximum<0||maximum>1024)Py_RETURN_NONE;
    PyObject *last=NULL;
    for(int j=0;j<3;j++)for(Py_ssize_t i=0;i<PyList_GET_SIZE(lists[j]);i++){
        PyObject *path=PyList_GET_ITEM(lists[j],i);
        if(!ascii_path(path)||PyUnicode_GET_LENGTH(path)>maximum)Py_RETURN_NONE;
        last=path;
    }
    return Py_NewRef(last);
}
/* The separate receipt context holds declarations only, never receipt values.
 * The Python caller retains lazy hints and complete entry authentication. */
static PyTypeObject ReceiptContextType={
    PyVarObject_HEAD_INIT(NULL,0)
    .tp_name="aware_workspace_sdk._tree_native._ReceiptContext",
    .tp_basicsize=sizeof(NativeConfig),
    .tp_flags=Py_TPFLAGS_DEFAULT|Py_TPFLAGS_HAVE_GC,
    .tp_dealloc=(destructor)destroy_context,
    .tp_traverse=(traverseproc)traverse_context,
    .tp_clear=(inquiry)clear_context,
    .tp_new=no_construct,
    .tp_weaklistoffset=offsetof(NativeConfig,weakrefs),
};
static PyObject *convert_receipt(PyObject *,PyObject *);
static int receipt_clock_matches(PyObject *dict,PyObject *pin){
    return PyDict_CheckExact(dict)&&PyLong_CheckExact(pin)&&
    ((PyDictObject*)dict)->ma_version_tag==PyLong_AsUnsignedLongLong(pin);
}
static PyObject *receipt_prelude(PyObject *,PyObject *);
static int receipt_auth(PyObject *config){
    PyObject *fn=PyTuple_GET_ITEM(config,4),*module=PyCFunction_GET_SELF(fn);
    int sealed=tuple_size(config,9);
    PyObject *clocks=sealed?PyTuple_GET_ITEM(config,5):NULL;
    if(!PyModule_CheckExact(module)||
    (!(sealed&&receipt_clock_matches(PyModule_GetDict(module),PyTuple_GET_ITEM(clocks,1)))&&
    (!keys_exact(PyModule_GetDict(module),&PyUnicode_Type)||
    literal_lookup(PyModule_GetDict(module),&PyId_convert_receipt)!=fn||
    literal_lookup(PyModule_GetDict(module),&PyId_receipt_prelude)!=PyTuple_GET_ITEM(config,sealed?7:6)))){
        PyErr_SetString(PyExc_TypeError,"original native receipt export required");
        return -1;
    }
    PyObject *ns=PyModule_GetDict(PyTuple_GET_ITEM(config,0)),*functions=PyTuple_GET_ITEM(config,2);
    int unchanged=sealed&&receipt_clock_matches(ns,PyTuple_GET_ITEM(clocks,0));
    if(!unchanged&&!keys_exact(ns,&PyUnicode_Type)){
        PyErr_SetString(PyExc_TypeError,"original receipt namespace required");
        return -1;
    }
    for(Py_ssize_t i=0;i<(sealed?2:PyTuple_GET_SIZE(functions));i++){
        PyObject *pin=PyTuple_GET_ITEM(functions,i),*function=PyTuple_GET_ITEM(pin,1);
        if((!unchanged&&PyDict_GetItemWithError(ns,PyTuple_GET_ITEM(pin,0))!=function)||
        PyFunction_GET_CODE(function)!=PyTuple_GET_ITEM(pin,2)||
        PyFunction_GET_DEFAULTS(function)!=NULL||PyFunction_GET_KW_DEFAULTS(function)!=NULL){
            PyErr_SetString(PyExc_TypeError,"original native receipt delegate required");
            return -1;
        }
    }
    return 0;
}
static NativeConfig *receipt_context(PyObject *object,int sealed){
    if(Py_TYPE(object)!=&ReceiptContextType){
        PyErr_SetString(PyExc_TypeError,"original native receipt context required");
        return NULL;
    }
    NativeConfig *s=(NativeConfig*)object;
    if(sealed&&s->phase!=2){
        PyErr_SetString(PyExc_RuntimeError,"native receipt context is not sealed");
        return NULL;
    }
    return s;
}
static PyObject *new_receipt_context(PyObject *self,PyObject *unused){
    (void)self;
    (void)unused;
    NativeConfig *s=PyObject_GC_New(NativeConfig,&ReceiptContextType);
    if(!s)return NULL;
    s->phase=0;
    s->config=NULL;
    s->weakrefs=NULL;
    PyObject_GC_Track(s);
    return (PyObject*)s;
}
static int receipt_declarations(PyObject *c){
    if(!tuple_size(c,7)||!PyModule_CheckExact(PyTuple_GET_ITEM(c,0))||
    !bounded_tuple(PyTuple_GET_ITEM(c,1),64)||
    !((tuple_size(PyTuple_GET_ITEM(c,2),2)&&tuple_size(PyTuple_GET_ITEM(c,3),13))||
    (tuple_size(PyTuple_GET_ITEM(c,2),3)&&tuple_size(PyTuple_GET_ITEM(c,3),14))))return 0;
    PyObject *native=PyTuple_GET_ITEM(c,4);
    if(!PyCFunction_Check(native)||PyCFunction_GET_FUNCTION(native)!=(PyCFunction)convert_receipt)return 0;
    PyObject *prelude=PyTuple_GET_ITEM(c,6),*regs=PyTuple_GET_ITEM(c,5);
    if(!PyCFunction_Check(prelude)||PyCFunction_GET_FUNCTION(prelude)!=(PyCFunction)receipt_prelude||
    PyCFunction_GET_SELF(prelude)!=PyCFunction_GET_SELF(native)||!tuple_size(regs,3))return 0;
    for(int i=0;i<3;i++)if(!keys_exact(PyTuple_GET_ITEM(regs,i),&PyLong_Type))return 0;
    PyObject *initial_ns=PyModule_GetDict(PyTuple_GET_ITEM(c,0));
    if(literal_lookup(initial_ns,&PyId__RECEIPT_FIELDS_BY_ID)!=PyTuple_GET_ITEM(regs,0)||
    literal_lookup(initial_ns,&PyId__RECEIPT_ORIGINAL_REGISTRY)!=PyTuple_GET_ITEM(regs,1)||
    literal_lookup(initial_ns,&PyId__RECEIPT_ORIGINAL_ENTRIES)!=PyTuple_GET_ITEM(regs,2))return 0;
    PyObject *functions=PyTuple_GET_ITEM(c,2),*ns=PyModule_GetDict(PyTuple_GET_ITEM(c,0));
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(functions);i++){
        PyObject *p=PyTuple_GET_ITEM(functions,i);
        if(!tuple_size(p,3)||!PyUnicode_CheckExact(PyTuple_GET_ITEM(p,0))||
        Py_TYPE(PyTuple_GET_ITEM(p,1))!=&PyFunction_Type||!PyCode_Check(PyTuple_GET_ITEM(p,2))||
        PyFunction_GET_GLOBALS(PyTuple_GET_ITEM(p,1))!=ns)return 0;
    }
    PyObject *fixed=PyTuple_GET_ITEM(c,3);
    if(PyTuple_GET_SIZE(fixed)==14){
        PyObject *extra=PyTuple_GET_ITEM(fixed,13);
        if(!tuple_size(extra,5)||Py_TYPE(PyTuple_GET_ITEM(extra,1))!=&PyType_Type||
        Py_TYPE(PyTuple_GET_ITEM(extra,0))!=(PyTypeObject*)PyTuple_GET_ITEM(extra,1)||
        Py_TYPE(PyTuple_GET_ITEM(extra,2))!=&PyFunction_Type||!PyCode_Check(PyTuple_GET_ITEM(extra,3))||
        PyFunction_GET_CODE(PyTuple_GET_ITEM(extra,2))!=PyTuple_GET_ITEM(extra,3)||
        PyFunction_GET_GLOBALS(PyTuple_GET_ITEM(extra,2))!=ns)return 0;
    }
    for(Py_ssize_t i=0;i<3;i++)if(Py_TYPE(PyTuple_GET_ITEM(fixed,i))!=&PyType_Type)return 0;
    for(Py_ssize_t i=3;i<9;i++)if(!PyUnicode_CheckExact(PyTuple_GET_ITEM(fixed,i)))return 0;
    if(Py_TYPE(PyTuple_GET_ITEM(fixed,9))!=&PyType_Type||
    Py_TYPE(PyTuple_GET_ITEM(fixed,11))!=&PyMemberDescr_Type||
    Py_TYPE(PyTuple_GET_ITEM(fixed,12))!=&PyMemberDescr_Type)return 0;
    PyObject *records=PyTuple_GET_ITEM(c,1);
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(records);i++){
        PyObject *r=PyTuple_GET_ITEM(records,i);
        if(!tuple_size(r,5)||!bounded_tuple(PyTuple_GET_ITEM(r,0),128)||
        !tuple_size(PyTuple_GET_ITEM(r,1),PyTuple_GET_SIZE(PyTuple_GET_ITEM(r,0))))return 0;
        PyObject *cls=PyTuple_GET_ITEM(r,2),*entry=PyTuple_GET_ITEM(r,3),*key=PyTuple_GET_ITEM(r,4);
        if(Py_TYPE(cls)!=&PyType_Type||!tuple_size(entry,5)||PyTuple_GET_ITEM(entry,0)!=cls||
        PyTuple_GET_ITEM(entry,1)!=PyTuple_GET_ITEM(r,0)||!PyLong_CheckExact(key)||PyLong_AsVoidPtr(key)!=cls||
        !PyDict_CheckExact(PyTuple_GET_ITEM(entry,3))||!tuple_size(PyTuple_GET_ITEM(entry,4),PyDict_GET_SIZE(PyTuple_GET_ITEM(entry,3)))||
        literal_lookup(((PyTypeObject*)cls)->tp_dict,&PyId___dataclass_fields__)!=PyTuple_GET_ITEM(entry,3))return 0;
        PyObject *pair=PyTuple_GET_ITEM(entry,2);
        if(!tuple_size(pair,2)||Py_TYPE(PyTuple_GET_ITEM(pair,0))!=&PyFunction_Type||!PyCode_Check(PyTuple_GET_ITEM(pair,1)))return 0;
        Py_ssize_t pos=0,order=0;
        PyObject *name,*field;
        while(PyDict_Next(PyTuple_GET_ITEM(entry,3),&pos,&name,&field)){
            PyObject *id=PyTuple_GET_ITEM(PyTuple_GET_ITEM(entry,4),order++);
            if(!PyUnicode_CheckExact(name)||!PyLong_CheckExact(id)||PyLong_AsVoidPtr(id)!=field)return 0;
        }
        PyObject *defs=PyTuple_GET_ITEM(r,0),*specs=PyTuple_GET_ITEM(r,1);
        for(Py_ssize_t j=0;j<PyTuple_GET_SIZE(defs);j++){
            if(!tuple_size(PyTuple_GET_ITEM(defs,j),5))return 0;
            PyObject *spec=PyTuple_GET_ITEM(specs,j);
            if(!tuple_size(spec,4)||!PyLong_CheckExact(PyTuple_GET_ITEM(spec,0))||
            !bounded_tuple(PyTuple_GET_ITEM(spec,2),2)||!bounded_tuple(PyTuple_GET_ITEM(spec,3),2))return 0;
            long kind=PyLong_AsLong(PyTuple_GET_ITEM(spec,0));
            if(kind<0||kind>6||PyErr_Occurred())return 0;
            if((kind==2||kind==3)&&(!tuple_size(PyTuple_GET_ITEM(spec,2),2)||
            Py_TYPE(PyTuple_GET_ITEM(spec,1))!=&PyType_Type))return 0;
            if(kind==4&&!tuple_size(PyTuple_GET_ITEM(spec,3),2))return 0;
        }
    }
    return 1;
}
static PyObject *seal_receipts(PyObject *self,PyObject *args){
    (void)self;
    PyObject *object,*c;
    if(!PyArg_ParseTuple(args,"OO:seal_receipts",&object,&c))return NULL;
    NativeConfig *s=receipt_context(object,0);
    if(!s)return NULL;
    if(s->phase){
        PyErr_SetString(PyExc_RuntimeError,"native receipt context already spent");
        return NULL;
    }
    s->phase=1;
    if(!receipt_declarations(c)){
        s->phase=3;
        if(!PyErr_Occurred())PyErr_SetString(PyExc_TypeError,"complete original receipt declaration required");
        return NULL;
    }
    if(receipt_auth(c)<0){
        s->phase=3;
        return NULL;
    }
    PyObject *fixed=PyTuple_GET_ITEM(c,3),*next_fixed=PyTuple_New(PyTuple_GET_SIZE(fixed)),*config=PyTuple_New(9);
    if(!next_fixed||!config){
        Py_XDECREF(next_fixed);
        Py_XDECREF(config);
        s->phase=3;
        return NULL;
    }
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(fixed);i++)PyTuple_SET_ITEM(next_fixed,i,Py_NewRef(PyTuple_GET_ITEM(fixed,i)));
    if(PyTuple_GET_SIZE(fixed)==14){
        PyObject *extra=PyTuple_GET_ITEM(fixed,13),*copy=PyTuple_New(5);
        if(!copy){
            Py_DECREF(next_fixed);
            Py_DECREF(config);
            s->phase=3;
            return NULL;
        }
        for(int part=0;part<5;part++)PyTuple_SET_ITEM(copy,part,Py_NewRef(PyTuple_GET_ITEM(extra,part)));
        PyObject *type=PyTuple_GET_ITEM(extra,1),*version=PyLong_FromUnsignedLongLong(((PyDictObject*)((PyTypeObject*)type)->tp_dict)->ma_version_tag);
        if(!version){
            Py_DECREF(copy);
            Py_DECREF(next_fixed);
            Py_DECREF(config);
            s->phase=3;
            return NULL;
        }
        Py_DECREF(PyTuple_GET_ITEM(copy,4));
        PyTuple_SET_ITEM(copy,4,version);
        Py_DECREF(PyTuple_GET_ITEM(next_fixed,13));
        PyTuple_SET_ITEM(next_fixed,13,copy);
    }
    Py_DECREF(PyTuple_GET_ITEM(next_fixed,10));
    PyObject *clock=PyLong_FromUnsignedLongLong(((PyDictObject*)((PyTypeObject*)PyTuple_GET_ITEM(fixed,9))->tp_dict)->ma_version_tag);
    PyTuple_SET_ITEM(next_fixed,10,clock);
    PyObject *ns=PyModule_GetDict(PyTuple_GET_ITEM(c,0));
    PyObject *native_ns=PyModule_GetDict(PyCFunction_GET_SELF(PyTuple_GET_ITEM(c,4)));
    PyObject *regs=PyTuple_GET_ITEM(c,5),*records=PyTuple_GET_ITEM(c,1);
    PyObject *clocks=Py_BuildValue("(KKKK)",(unsigned long long)((PyDictObject*)ns)->ma_version_tag,
    (unsigned long long)((PyDictObject*)native_ns)->ma_version_tag,
    (unsigned long long)((PyDictObject*)PyTuple_GET_ITEM(regs,0))->ma_version_tag,
    (unsigned long long)((PyDictObject*)PyTuple_GET_ITEM(regs,2))->ma_version_tag);
    PyObject *versions=PyTuple_New(PyTuple_GET_SIZE(records));
    if(versions)for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(records);i++){
        PyObject *r=PyTuple_GET_ITEM(records,i),*cls=PyTuple_GET_ITEM(r,2),*entry=PyTuple_GET_ITEM(r,3);
        PyObject *row=Py_BuildValue("(KK)",(unsigned long long)((PyDictObject*)((PyTypeObject*)cls)->tp_dict)->ma_version_tag,
        (unsigned long long)((PyDictObject*)PyTuple_GET_ITEM(entry,3))->ma_version_tag);
        PyTuple_SET_ITEM(versions,i,row);
        if(!row){
            Py_CLEAR(versions);
            break;
        }
    }
    for(Py_ssize_t i=0;i<5;i++)PyTuple_SET_ITEM(config,i,Py_NewRef(PyTuple_GET_ITEM(c,i)));
    Py_DECREF(PyTuple_GET_ITEM(config,3));
    PyTuple_SET_ITEM(config,3,next_fixed);
    PyTuple_SET_ITEM(config,5,clocks);
    PyTuple_SET_ITEM(config,6,Py_NewRef(regs));
    PyTuple_SET_ITEM(config,7,Py_NewRef(PyTuple_GET_ITEM(c,6)));
    PyTuple_SET_ITEM(config,8,versions);
    if(!clock||!clocks||!versions){
        Py_DECREF(config);
        s->phase=3;
        return NULL;
    }
    /* Allocation may run GC callbacks after the first proof. Recheck the
     * complete original unsealed declaration and namespace bindings after all
     * allocation, immediately before publication. Never refresh clocks after
     * this proof: stale clocks conservatively force later live checks. */
    if(receipt_auth(c)<0||
    literal_lookup(ns,&PyId__RECEIPT_FIELDS_BY_ID)!=PyTuple_GET_ITEM(regs,0)||
    literal_lookup(ns,&PyId__RECEIPT_ORIGINAL_REGISTRY)!=PyTuple_GET_ITEM(regs,1)||
    literal_lookup(ns,&PyId__RECEIPT_ORIGINAL_ENTRIES)!=PyTuple_GET_ITEM(regs,2)){
        s->phase=3;
        Py_DECREF(config);
        if(!PyErr_Occurred())PyErr_SetString(PyExc_TypeError,"Original receipt compiler registry required");
        return NULL;
    }
    s->config=config;
    s->phase=2;
    Py_RETURN_NONE;
}
static int receipt_registries(PyObject *config,PyObject *registry,PyObject *original,PyObject *entries){
    PyObject *regs=PyTuple_GET_ITEM(config,6),*ns=PyModule_GetDict(PyTuple_GET_ITEM(config,0));
    PyObject *clocks=PyTuple_GET_ITEM(config,5);
    return registry==original&&registry==PyTuple_GET_ITEM(regs,0)&&original==PyTuple_GET_ITEM(regs,1)&&
    entries==PyTuple_GET_ITEM(regs,2)&&
    (receipt_clock_matches(ns,PyTuple_GET_ITEM(clocks,0))||
    (literal_lookup(ns,&PyId__RECEIPT_FIELDS_BY_ID)==registry&&
    literal_lookup(ns,&PyId__RECEIPT_ORIGINAL_REGISTRY)==original&&
    literal_lookup(ns,&PyId__RECEIPT_ORIGINAL_ENTRIES)==entries))&&
    receipt_clock_matches(registry,PyTuple_GET_ITEM(clocks,2))&&receipt_clock_matches(entries,PyTuple_GET_ITEM(clocks,3));
}
static Py_ssize_t receipt_record_index(PyObject *config,PyObject *cls){
    PyObject *records=PyTuple_GET_ITEM(config,1);
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(records);i++)if(PyTuple_GET_ITEM(PyTuple_GET_ITEM(records,i),2)==cls)return i;
    return -1;
}
static int receipt_metadata(PyObject *config,Py_ssize_t index){
    PyObject *r=PyTuple_GET_ITEM(PyTuple_GET_ITEM(config,1),index),*entry=PyTuple_GET_ITEM(r,3);
    PyObject *versions=PyTuple_GET_ITEM(PyTuple_GET_ITEM(config,8),index);
    return receipt_clock_matches(((PyTypeObject*)PyTuple_GET_ITEM(r,2))->tp_dict,PyTuple_GET_ITEM(versions,0))&&
    receipt_clock_matches(PyTuple_GET_ITEM(entry,3),PyTuple_GET_ITEM(versions,1));
}
static PyObject *receipt_prelude(PyObject *self,PyObject *args){
    COST_BEGIN(2);
    (void)self;
    PyObject *object,*cls,*registry,*original,*entries;
    if(!PyArg_ParseTuple(args,"OOOOO:receipt_prelude",&object,&cls,&registry,&original,&entries))COST_RETURN(NULL);
    NativeConfig *s=receipt_context(object,1);
    if(!s)COST_RETURN(NULL);
    if(receipt_auth(s->config)<0)COST_RETURN(NULL);
    Py_ssize_t index=receipt_record_index(s->config,cls);
    if(index<0||!receipt_registries(s->config,registry,original,entries)||!receipt_metadata(s->config,index))COST_RETURN(Py_NewRef(Py_NotImplemented));
    PyObject *r=PyTuple_GET_ITEM(PyTuple_GET_ITEM(s->config,1),index),*entry=PyTuple_GET_ITEM(r,3),*key=PyTuple_GET_ITEM(r,4);
    if(PyDict_GetItemWithError(registry,key)!=entry||PyDict_GetItemWithError(entries,key)!=entry)COST_RETURN(Py_NewRef(Py_NotImplemented));
    COST_RETURN(PyTuple_Pack(2,registry,entry));
}
typedef struct {
    PyTypeObject *type;
    uint64_t clock;
    Py_ssize_t offsets[2];
}
ReceiptFieldGeometry;
typedef struct {
    uint64_t native_clock,namespace_clock;
    int initialized;
} ReceiptAuthProof;
typedef struct {
    PyObject *config,*specs,*fixed;
    int depth;
    ReceiptFieldGeometry fields;
    ReceiptAuthProof *auth_proof;
}
ReceiptConversion;
/* A dictionary version proves only the original declaration association
 * established by the complete verifier in this same uninterrupted root call.
 * Every checkpoint freshly reads both versions and every original function
 * code/default. Drift re-enters the literal full verifier before renewing this
 * stack proof. It contains no field, payload, owner, validation or authority
 * result and is never retained by the context or beyond the root invocation. */
static int receipt_conversion_auth(ReceiptConversion *c){
    PyObject *config=c->config;
    ReceiptAuthProof *proof=c->auth_proof;
    PyObject *native=PyCFunction_GET_SELF(PyTuple_GET_ITEM(config,4));
    if(!PyModule_CheckExact(native))return receipt_auth(config);
    PyObject *native_ns=PyModule_GetDict(native);
    PyObject *ns=PyModule_GetDict(PyTuple_GET_ITEM(config,0));
    uint64_t native_clock=((PyDictObject*)native_ns)->ma_version_tag;
    uint64_t namespace_clock=((PyDictObject*)ns)->ma_version_tag;
    if(!proof||!proof->initialized||proof->native_clock!=native_clock||proof->namespace_clock!=namespace_clock){
        if(receipt_auth(config)<0)return -1;
        if(proof){
            proof->native_clock=((PyDictObject*)native_ns)->ma_version_tag;
            proof->namespace_clock=((PyDictObject*)ns)->ma_version_tag;
            proof->initialized=1;
        }
        return 0;
    }
    PyObject *functions=PyTuple_GET_ITEM(config,2);
    for(Py_ssize_t i=0;i<2;i++){
        PyObject *pin=PyTuple_GET_ITEM(functions,i),*function=PyTuple_GET_ITEM(pin,1);
        if(PyFunction_GET_CODE(function)!=PyTuple_GET_ITEM(pin,2)||
        PyFunction_GET_DEFAULTS(function)!=NULL||PyFunction_GET_KW_DEFAULTS(function)!=NULL){
            PyErr_SetString(PyExc_TypeError,"original native receipt delegate required");
            return -1;
        }
    }
    return 0;
}
/* Only immutable own MemberDescriptor layout is compiled. Namespace version,
 * getattribute, slot bounds and each current flag/name remain freshly checked
 * at every read. This stack schema never owns a value, payload or authority. */
static int receipt_field_geometry(PyObject *fixed,ReceiptFieldGeometry *out){
    out->type=(PyTypeObject*)PyTuple_GET_ITEM(fixed,9);
    out->clock=PyLong_AsUnsignedLongLong(PyTuple_GET_ITEM(fixed,10));
    if(PyErr_Occurred())return -1;
    for(int name=0;name<2;name++){
        out->offsets[name]=-1;
        PyObject *descriptor=PyTuple_GET_ITEM(fixed,name?11:12);
        if(Py_TYPE(descriptor)==&PyMemberDescr_Type&&PyDescr_TYPE(descriptor)==out->type){
            PyMemberDef *member=((PyMemberDescrObject*)descriptor)->d_member;
            if(member->type==T_OBJECT_EX&&member->offset>=(Py_ssize_t)sizeof(PyObject))out->offsets[name]=member->offset;
        }
    }
    return 0;
}
static PyObject *receipt_direct_record(ReceiptConversion *,PyObject *,PyObject *);
static PyObject *receipt_direct_sequence(ReceiptConversion *,PyObject *,PyObject *);
static PyObject *receipt_call(ReceiptConversion *c,int index,PyObject *value,PyObject *hint){
    if(index==0){
        PyObject *direct=receipt_direct_record(c,value,hint);
        if(!direct||direct!=Py_NotImplemented)return direct;
        Py_DECREF(direct);
        direct=receipt_direct_sequence(c,value,hint);
        if(!direct||direct!=Py_NotImplemented)return direct;
        Py_DECREF(direct);
    }
    if(receipt_conversion_auth(c)<0)return NULL;
    PyObject *function=PyTuple_GET_ITEM(PyTuple_GET_ITEM(PyTuple_GET_ITEM(c->config,2),index),1);
    PyObject *args[2]={
        value,hint
    },*out=PyObject_Vectorcall(function,args,index==0?2:1,NULL);
    if(!out)return NULL;
    if(receipt_conversion_auth(c)<0){
        Py_DECREF(out);
        return NULL;
    }
    return out;
}
static int receipt_equivalent(ReceiptConversion *c,PyObject *hint,PyObject *decl,PyObject *spec){
    if(hint==decl)return 1;
    long kind=PyLong_AsLong(PyTuple_GET_ITEM(spec,0));
    if((kind==2||kind==3)&&Py_TYPE(hint)==(PyTypeObject*)PyTuple_GET_ITEM(c->fixed,1)){
        PyObject *args=PyObject_GetAttr(hint,PyTuple_GET_ITEM(c->fixed,7));
        if(!args)return -1;
        PyObject *old=PyTuple_GET_ITEM(spec,2);
        int same=tuple_size(args,2)&&((PyTuple_GET_ITEM(args,0)==PyTuple_GET_ITEM(old,0)&&PyTuple_GET_ITEM(args,1)==PyTuple_GET_ITEM(old,1))||
        (PyTuple_GET_ITEM(args,0)==PyTuple_GET_ITEM(old,1)&&PyTuple_GET_ITEM(args,1)==PyTuple_GET_ITEM(old,0)));
        Py_DECREF(args);
        return same;
    }
    if(kind==4&&Py_TYPE(hint)==(PyTypeObject*)PyTuple_GET_ITEM(c->fixed,2)){
        PyObject *origin=PyObject_GetAttr(hint,PyTuple_GET_ITEM(c->fixed,8));
        if(!origin)return -1;
        int same=origin==(PyObject*)&PyTuple_Type;
        Py_DECREF(origin);
        if(!same)return 0;
        PyObject *args=PyObject_GetAttr(hint,PyTuple_GET_ITEM(c->fixed,7));
        if(!args)return -1;
        same=tuple_size(args,2)&&PyTuple_GET_ITEM(args,1)==Py_Ellipsis&&
        PyTuple_GET_ITEM(args,0)==PyTuple_GET_ITEM(PyTuple_GET_ITEM(spec,3),0);
        Py_DECREF(args);
        return same;
    }
    return 0;
}
static PyObject *receipt_iter(PyObject *member){
    PyObject *iterator=PyObject_GetIter(member);
    if(!iterator)return NULL;
    PyObject *out=PyList_New(0);
    if(!out){
        Py_DECREF(iterator);
        return NULL;
    }
    PyObject *item;
    while((item=PyIter_Next(iterator))){
        int ok=PyList_Append(out,item);
        Py_DECREF(item);
        if(ok<0){
            Py_DECREF(out);
            Py_DECREF(iterator);
            return NULL;
        }
    }
    Py_DECREF(iterator);
    if(PyErr_Occurred()){
        Py_DECREF(out);
        return NULL;
    }
    return out;
}
static PyObject *receipt_field_attr(ReceiptConversion *c,PyObject *field,int name){
    ReceiptFieldGeometry *schema=&c->fields;
    Py_ssize_t offset=schema->offsets[name];
    if(offset>=(Py_ssize_t)sizeof(PyObject)&&Py_TYPE(field)==schema->type&&
    schema->type->tp_getattro==PyObject_GenericGetAttr&&
    PyDict_CheckExact(schema->type->tp_dict)&&
    ((PyDictObject*)schema->type->tp_dict)->ma_version_tag==schema->clock&&
    offset<=Py_TYPE(field)->tp_basicsize-(Py_ssize_t)sizeof(PyObject*)){
        PyObject *current=*(PyObject**)(((char*)field)+offset);
        if(current)return Py_NewRef(current);
    }
    return PyObject_GetAttr(field,PyTuple_GET_ITEM(c->fixed,name?4:3));
}
/* The row already retains the original own-slot declaration. At entry the
 * complete record metadata was checked against its original seal; a fresh
 * class-dictionary version comparison before each read conserves that proof.
 * The name must be the same current Field.name. Any change/foreign behavior
 * retains the literal generic attribute read. No instance value is retained. */
static PyObject *receipt_member_attr(PyObject *value,PyObject *name,PyObject *row,uint64_t original_clock){
    PyTypeObject *type=Py_TYPE(value);
    PyObject *descriptor=PyTuple_GET_ITEM(row,3);
    if(PyUnicode_CheckExact(name)&&name==PyTuple_GET_ITEM(row,1)&&Py_TYPE(descriptor)==&PyMemberDescr_Type&&
    PyDescr_TYPE(descriptor)==type&&type->tp_getattro==PyObject_GenericGetAttr&&
    type->tp_dictoffset==0&&PyDict_CheckExact(type->tp_dict)&&
    ((PyDictObject*)type->tp_dict)->ma_version_tag==original_clock){
        PyMemberDef *member=((PyMemberDescrObject*)descriptor)->d_member;
        if(member->type==T_OBJECT_EX&&member->offset>=(Py_ssize_t)sizeof(PyObject)&&
        member->offset<=type->tp_basicsize-(Py_ssize_t)sizeof(PyObject*)){
            PyObject *current=*(PyObject**)(((char*)value)+member->offset);
            if(current)return Py_NewRef(current);
        }
    }
    return PyObject_GetAttr(value,name);
}
/* Join only the uninterrupted positive own-slot prefix. All metadata/value
 * reads stay in original order. Exact Unicode-only hints lookup cannot call a
 * foreign key; no allocation or callback separates these reads. Unknown state
 * declines before dispatch, retaining the literal original prefix below. */
static int receipt_field_prefix(ReceiptConversion *c,PyObject *value,PyObject *field,PyObject *row,uint64_t clock,PyObject *hints,PyObject **member_out,PyObject **hint_out){
    ReceiptFieldGeometry *schema=&c->fields;
    PyTypeObject *type=Py_TYPE(value);
    Py_ssize_t name_offset=schema->offsets[1];
    if(name_offset<(Py_ssize_t)sizeof(PyObject)||Py_TYPE(field)!=schema->type||
    schema->type->tp_getattro!=PyObject_GenericGetAttr||!PyDict_CheckExact(schema->type->tp_dict)||
    ((PyDictObject*)schema->type->tp_dict)->ma_version_tag!=schema->clock||
    name_offset>schema->type->tp_basicsize-(Py_ssize_t)sizeof(PyObject*)||
    type->tp_getattro!=PyObject_GenericGetAttr||type->tp_dictoffset!=0||
    !PyDict_CheckExact(type->tp_dict)||((PyDictObject*)type->tp_dict)->ma_version_tag!=clock||
    !PyDict_CheckExact(hints)||((PyDictObject*)hints)->ma_keys->dk_kind!=DICT_KEYS_UNICODE)return 0;
    PyObject *name=*(PyObject**)(((char*)field)+name_offset);
    if(name!=PyTuple_GET_ITEM(row,1)||!PyUnicode_CheckExact(name))return 0;
    PyObject *descriptor=PyTuple_GET_ITEM(row,3);
    if(Py_TYPE(descriptor)!=&PyMemberDescr_Type||PyDescr_TYPE(descriptor)!=type)return 0;
    PyMemberDef *slot=((PyMemberDescrObject*)descriptor)->d_member;
    if(slot->type!=T_OBJECT_EX||slot->offset<(Py_ssize_t)sizeof(PyObject)||
    slot->offset>type->tp_basicsize-(Py_ssize_t)sizeof(PyObject*))return 0;
    PyObject *member=*(PyObject**)(((char*)value)+slot->offset);
    if(!member)return 0;
    Py_INCREF(member);
    name=*(PyObject**)(((char*)field)+name_offset);
    if(name!=PyTuple_GET_ITEM(row,1)){
        Py_DECREF(member);
        return 0;
    }
    PyObject *hint=PyDict_GetItemWithError(hints,name);
    if(!hint){
        Py_DECREF(member);
        return PyErr_Occurred()?-1:0;
    }
    Py_INCREF(hint);
    *member_out=member;
    *hint_out=hint;
    return 1;
}
static PyObject *receipt_fields(PyObject *value,PyObject *defs,PyObject *hints,ReceiptConversion *c){
    Py_ssize_t n=PyTuple_GET_SIZE(defs);
    uint64_t original_clock=((PyDictObject*)Py_TYPE(value)->tp_dict)->ma_version_tag;
    unsigned char active[128];
    if(n<0||n>128){
        PyErr_SetString(PyExc_TypeError,"bounded original receipt fields required");
        return NULL;
    }
    for(Py_ssize_t i=0;i<n;i++){
        PyObject *row=PyTuple_GET_ITEM(defs,i),*flag=receipt_field_attr(c,PyTuple_GET_ITEM(row,0),0);
        if(!flag){
            return NULL;
        }
        active[i]=flag==PyTuple_GET_ITEM(row,4);
        Py_DECREF(flag);
    }
    PyObject *out=PyDict_New();
    if(!out){
        return NULL;
    }
    for(Py_ssize_t i=0;i<n;i++){
        if(!active[i])continue;
        PyObject *row=PyTuple_GET_ITEM(defs,i),*field=PyTuple_GET_ITEM(row,0),*name=NULL,*member=NULL,*hint=NULL,*encoded=NULL;
        if(Py_TYPE(value)==(PyTypeObject*)PyTuple_GET_ITEM(c->fixed,0)){
            name=receipt_field_attr(c,field,1);
            if(!name)goto error;
            int skip=PyObject_RichCompareBool(name,PyTuple_GET_ITEM(c->fixed,5),Py_EQ);
            Py_CLEAR(name);
            if(skip<0)goto error;
            if(skip){
                PyObject *effect=PyObject_GetAttr(value,PyTuple_GET_ITEM(c->fixed,5));
                if(!effect)goto error;
                skip=effect==Py_None;
                Py_DECREF(effect);
                if(skip)continue;
            }
        }
        int prefix=receipt_field_prefix(c,value,field,row,original_clock,hints,&member,&hint);
        if(prefix<0)goto error;
        if(!prefix){
            name=receipt_field_attr(c,field,1);
            if(!name)goto error;
            member=receipt_member_attr(value,name,row,original_clock);
            Py_CLEAR(name);
            if(!member)goto error;
            name=receipt_field_attr(c,field,1);
            if(!name)goto error;
            hint=PyObject_GetItem(hints,name);
            Py_CLEAR(name);
            if(!hint)goto error;
        }
        if(member==Py_None)encoded=Py_NewRef(Py_None);
        else{
            PyObject *spec=PyTuple_GET_ITEM(c->specs,i);
            int same=receipt_equivalent(c,hint,PyTuple_GET_ITEM(row,2),spec);
            if(same<0)goto error;
            if(!same){
                if(hint==(PyObject*)&PyUnicode_Type||hint==(PyObject*)&PyLong_Type||hint==(PyObject*)&PyBool_Type)encoded=Py_NewRef(member);
                else encoded=receipt_call(c,0,member,hint);
            }
            else{
                long kind=PyLong_AsLong(PyTuple_GET_ITEM(spec,0));
                if(kind==1)encoded=Py_NewRef(member);
                else if(kind==2||kind==3){
                    PyObject *selected=PyTuple_GET_ITEM(spec,1);
                    int yes=PyObject_IsInstance(member,selected);
                    if(yes<0)goto error;
                    if(!yes){
                        PyErr_Format(PyExc_TypeError,"Value does not match repository evidence union: %R",hint);
                        goto error;
                    }
                    encoded=kind==2?Py_NewRef(member):receipt_call(c,0,member,selected);
                }
                else if(kind==4)encoded=receipt_iter(member);
                else if(kind==5)encoded=PyObject_GetAttr(member,PyTuple_GET_ITEM(c->fixed,6));
                else if(kind==6)encoded=receipt_call(c,1,member,NULL);
                else encoded=receipt_call(c,0,member,hint);
            }
        }
        if(!encoded)goto error;
        name=receipt_field_attr(c,field,1);
        if(!name)goto error;
        if(PyDict_SetItem(out,name,encoded)<0)goto error;
        Py_CLEAR(name);
        Py_CLEAR(member);
        Py_CLEAR(hint);
        Py_CLEAR(encoded);
        continue;
        error:
        Py_XDECREF(name);
        Py_XDECREF(member);
        Py_XDECREF(hint);
        Py_XDECREF(encoded);
        Py_DECREF(out);
        return NULL;
    }
    if(receipt_conversion_auth(c)<0){
        Py_DECREF(out);
        return NULL;
    }
    return out;
}
/* Positive exact-record recursion replaces repeated Python entry, never fields
 * or lazy hints. Unsupported/mutable eligibility keeps the original delegate. */
static Py_ssize_t graph_attempts,graph_direct,graph_continuations;
static PyObject *receipt_direct_record(ReceiptConversion *c,PyObject *value,PyObject *hint){
    graph_attempts++;
    if(PyTuple_GET_SIZE(c->fixed)!=14||c->depth>=16||value==Py_None)Py_RETURN_NOTIMPLEMENTED;
    PyThreadState *thread=PyThreadState_Get();
    if(thread->c_profilefunc||thread->c_tracefunc||thread->py_recursion_remaining<128||thread->c_recursion_remaining<128)Py_RETURN_NOTIMPLEMENTED;
    for(int n=0;n<PY_MONITORING_TOOL_IDS;n++)if(thread->interp->monitoring_tool_names[n])Py_RETURN_NOTIMPLEMENTED;
    if(thread->interp->gc.callbacks&&PyList_GET_SIZE(thread->interp->gc.callbacks))Py_RETURN_NOTIMPLEMENTED;
    if(Py_TYPE(hint)!=&PyType_Type||Py_TYPE(value)!=(PyTypeObject*)hint)Py_RETURN_NOTIMPLEMENTED;
    Py_ssize_t index=receipt_record_index(c->config,hint);
    if(index<0||!receipt_metadata(c->config,index))Py_RETURN_NOTIMPLEMENTED;
    PyObject *extra=PyTuple_GET_ITEM(c->fixed,13),*wrapper=PyTuple_GET_ITEM(extra,0),*type=PyTuple_GET_ITEM(extra,1),*inner=PyTuple_GET_ITEM(extra,2);
    PyObject *ns=PyModule_GetDict(PyTuple_GET_ITEM(c->config,0));
    if(literal_lookup(ns,&PyId__type_hints)!=wrapper||
    ((PyTypeObject*)type)->tp_getattro!=PyObject_GenericGetAttr||
    strcmp(((PyTypeObject*)type)->tp_name,"functools._lru_cache_wrapper")||
    !receipt_clock_matches(((PyTypeObject*)type)->tp_dict,PyTuple_GET_ITEM(extra,4))||
    PyFunction_GET_CODE(inner)!=PyTuple_GET_ITEM(extra,3)||PyFunction_GET_DEFAULTS(inner)||PyFunction_GET_KW_DEFAULTS(inner))Py_RETURN_NOTIMPLEMENTED;
    if(receipt_conversion_auth(c)<0)return NULL;
    PyObject *regs=PyTuple_GET_ITEM(c->config,6),*registry=PyTuple_GET_ITEM(regs,0);
    if(!receipt_registries(c->config,registry,PyTuple_GET_ITEM(regs,1),PyTuple_GET_ITEM(regs,2)))Py_RETURN_NOTIMPLEMENTED;
    PyObject *record=PyTuple_GET_ITEM(PyTuple_GET_ITEM(c->config,1),index),*entry=PyTuple_GET_ITEM(record,3);
    if(PyDict_GetItemWithError(registry,PyTuple_GET_ITEM(record,4))!=entry)Py_RETURN_NOTIMPLEMENTED;
    PyObject *hints=PyObject_CallOneArg(wrapper,hint);
    if(!hints)return NULL;
    if(receipt_conversion_auth(c)<0){
        Py_DECREF(hints);
        return NULL;
    }
    PyObject *out;
    if(receipt_registries(c->config,registry,PyTuple_GET_ITEM(regs,1),PyTuple_GET_ITEM(regs,2))&&
    PyDict_GetItemWithError(registry,PyTuple_GET_ITEM(record,4))==entry&&
    receipt_metadata(c->config,index)&&PyDict_CheckExact(hints)){
        PyObject *pair=PyTuple_GET_ITEM(entry,2),*function=PyTuple_GET_ITEM(pair,0);
        if(PyFunction_GET_CODE(function)!=PyTuple_GET_ITEM(pair,1)||
        PyFunction_GET_DEFAULTS(function)||PyFunction_GET_KW_DEFAULTS(function)){
            Py_DECREF(hints);
            PyErr_SetString(PyExc_TypeError,"Original receipt compiler code/defaults required");
            return NULL;
        }
        graph_direct++;
        ReceiptConversion child=*c;
        child.specs=PyTuple_GET_ITEM(record,1);
        child.depth=c->depth+1;
        out=receipt_fields(value,PyTuple_GET_ITEM(record,0),hints,&child);
    }
    else{
        graph_continuations++;
        PyObject *continuation=PyTuple_GET_ITEM(PyTuple_GET_ITEM(PyTuple_GET_ITEM(c->config,2),2),1);
        PyObject *args[5]={
            value,hint,registry,entry,hints
        };
        PyObject *pin=PyTuple_GET_ITEM(PyTuple_GET_ITEM(c->config,2),2);
        if(PyDict_GetItemWithError(ns,PyTuple_GET_ITEM(pin,0))!=continuation||
        PyFunction_GET_CODE(continuation)!=PyTuple_GET_ITEM(pin,2)||
        PyFunction_GET_DEFAULTS(continuation)||PyFunction_GET_KW_DEFAULTS(continuation)){
            Py_DECREF(hints);
            PyErr_SetString(PyExc_TypeError,"original native receipt delegate required");
            return NULL;
        }
        out=PyObject_Vectorcall(continuation,args,5,NULL);
        if(out&&(PyDict_GetItemWithError(ns,PyTuple_GET_ITEM(pin,0))!=continuation||
        PyFunction_GET_CODE(continuation)!=PyTuple_GET_ITEM(pin,2)||
        PyFunction_GET_DEFAULTS(continuation)||PyFunction_GET_KW_DEFAULTS(continuation))){
            Py_DECREF(out);
            out=NULL;
            PyErr_SetString(PyExc_TypeError,"original native receipt delegate required");
        }
    }
    Py_DECREF(hints);
    if(out&&receipt_conversion_auth(c)<0){
        Py_DECREF(out);
        return NULL;
    }
    return out;
}
/* Exact original tuple-record iteration joins the existing fresh record
 * recursion. No hint/field/value snapshot survives a child or this invocation. */
static PyObject *receipt_direct_sequence(ReceiptConversion*c,PyObject*value,PyObject*hint){
    if(PyTuple_GET_SIZE(c->fixed)!=14||c->depth>=16||!PyTuple_CheckExact(value)||Py_TYPE(hint)!=&Py_GenericAliasType||Py_TYPE(hint)!=(PyTypeObject*)PyTuple_GET_ITEM(c->fixed,2))Py_RETURN_NOTIMPLEMENTED;
    PyThreadState *thread=PyThreadState_Get();
    if(thread->c_profilefunc||thread->c_tracefunc||thread->py_recursion_remaining<128||thread->c_recursion_remaining<128)Py_RETURN_NOTIMPLEMENTED;
    for(int n=0;n<PY_MONITORING_TOOL_IDS;n++)if(thread->interp->monitoring_tool_names[n])Py_RETURN_NOTIMPLEMENTED;
    if(thread->interp->gc.callbacks&&PyList_GET_SIZE(thread->interp->gc.callbacks))Py_RETURN_NOTIMPLEMENTED;
    if(receipt_conversion_auth(c)<0)return NULL;
    PyObject *origin=PyObject_GetAttr(hint,PyTuple_GET_ITEM(c->fixed,8));
    if(!origin)return NULL;
    int tuple_origin=origin==(PyObject*)&PyTuple_Type;
    Py_DECREF(origin);
    if(!tuple_origin)Py_RETURN_NOTIMPLEMENTED;
    PyObject *args=PyObject_GetAttr(hint,PyTuple_GET_ITEM(c->fixed,7));
    if(!args)return NULL;
    if(!tuple_size(args,2)||PyTuple_GET_ITEM(args,1)!=Py_Ellipsis||Py_TYPE(PyTuple_GET_ITEM(args,0))!=&PyType_Type||receipt_record_index(c->config,PyTuple_GET_ITEM(args,0))<0){
        Py_DECREF(args);
        Py_RETURN_NOTIMPLEMENTED;
    }
    PyObject *iterator=PyObject_GetIter(value);
    if(!iterator){
        Py_DECREF(args);
        return NULL;
    }
    PyObject *out=PyList_New(0),*item=NULL;
    if(!out){
        Py_DECREF(iterator);
        Py_DECREF(args);
        return NULL;
    }
    ReceiptConversion child=*c;
    child.depth=c->depth+1;
    while((item=PyIter_Next(iterator))){
        PyObject *encoded=receipt_call(&child,0,item,PyTuple_GET_ITEM(args,0));
        Py_DECREF(item);
        if(!encoded)goto error;
        int okay=PyList_Append(out,encoded);
        Py_DECREF(encoded);
        if(okay<0)goto error;
    }
    if(PyErr_Occurred())goto error;
    if(receipt_conversion_auth(c)<0)goto error;
    Py_DECREF(iterator);
    Py_DECREF(args);
    return out;
    error:
    Py_DECREF(out);
    Py_DECREF(iterator);
    Py_DECREF(args);
    return NULL;
}
static PyObject *convert_receipt(PyObject *self,PyObject *args){
    COST_BEGIN(3);
    (void)self;
    PyObject *object,*value,*entry,*registry,*hints;
    if(!PyArg_ParseTuple(args,"OOOOO:convert_receipt",&object,&value,&entry,&registry,&hints))COST_RETURN(NULL);
    NativeConfig *s=receipt_context(object,1);
    if(!s)COST_RETURN(NULL);
    if(receipt_auth(s->config)<0)COST_RETURN(NULL);
    Py_ssize_t index=receipt_record_index(s->config,(PyObject*)Py_TYPE(value));
    PyObject *regs=PyTuple_GET_ITEM(s->config,6);
    if(index<0||!receipt_registries(s->config,registry,PyTuple_GET_ITEM(regs,1),PyTuple_GET_ITEM(regs,2))||
    !receipt_metadata(s->config,index)||!PyDict_CheckExact(hints))COST_RETURN(Py_NewRef(Py_NotImplemented));
    PyObject *r=PyTuple_GET_ITEM(PyTuple_GET_ITEM(s->config,1),index);
    if(entry!=PyTuple_GET_ITEM(r,3))COST_RETURN(Py_NewRef(Py_NotImplemented));
    PyObject *pair=PyTuple_GET_ITEM(entry,2),*fn=PyTuple_GET_ITEM(pair,0);
    if(PyFunction_GET_CODE(fn)!=PyTuple_GET_ITEM(pair,1)||PyFunction_GET_DEFAULTS(fn)||PyFunction_GET_KW_DEFAULTS(fn)){
        PyErr_SetString(PyExc_TypeError,"Original receipt compiler code/defaults required");
        COST_RETURN(NULL);
    }
    ReceiptAuthProof auth_proof={0};
    ReceiptConversion c={
        s->config,PyTuple_GET_ITEM(r,1),PyTuple_GET_ITEM(s->config,3),0,{0},&auth_proof
    };
    if(receipt_field_geometry(c.fixed,&c.fields)<0)COST_RETURN(NULL);
    COST_RETURN(receipt_fields(value,PyTuple_GET_ITEM(r,0),hints,&c));
}
/* Generic fresh detached copying for the receiving owner's existing finite
 * dataclass/tuple walker. Declarations and original functions only; no values,
 * owner handles, authorization, cross-domain imports or copy memo retained. */
static _Py_Identifier PyId_name={
    "name",-1
};
static PyTypeObject PreparationCopyContextType={
    PyVarObject_HEAD_INIT(NULL,0)
    .tp_name="aware_workspace_sdk._tree_native._PreparationCopyContext",
    .tp_basicsize=sizeof(NativeConfig),
    .tp_flags=Py_TPFLAGS_DEFAULT|Py_TPFLAGS_HAVE_GC,
    .tp_dealloc=(destructor)destroy_context,
    .tp_traverse=(traverseproc)traverse_context,
    .tp_clear=(inquiry)clear_context,
    .tp_new=no_construct,
    .tp_weaklistoffset=offsetof(NativeConfig,weakrefs),
};
static PyObject *preparation_copy(PyObject *,PyObject *);
static int preparation_fields_profile(PyObject *);
static int preparation_copy_auth(PyObject *config){
    PyObject *native=PyTuple_GET_ITEM(config,6),*module=PyCFunction_GET_SELF(native);
    if(!PyModule_CheckExact(module)||
    (!receipt_clock_matches(PyModule_GetDict(module),PyTuple_GET_ITEM(config,11))&&
    (!keys_exact(PyModule_GetDict(module),&PyUnicode_Type)||
    PyDict_GetItemString(PyModule_GetDict(module),"copy_preparation")!=native))){
        PyErr_SetString(PyExc_TypeError,"original native preparation export required");
        return -1;
    }
    const int delegates[]={
        2,4,9
    };
    for(int j=0;j<3;j++){
        int i=delegates[j];
        PyObject *function=PyTuple_GET_ITEM(config,i);
        if(Py_TYPE(function)!=&PyFunction_Type||PyFunction_GET_CODE(function)!=PyTuple_GET_ITEM(config,i+1)||
        PyFunction_GET_DEFAULTS(function)||PyFunction_GET_KW_DEFAULTS(function)){
            PyErr_SetString(PyExc_TypeError,"original preparation copy delegate required");
            return -1;
        }
    }
    return 0;
}
/* Optional translation of the build-qualified stock fields() snapshot only.
 * Configuration contains declarations, never observations or field values.
 * Uncertain namespaces, slots, tracing, collections or descriptors delegate to
 * the literal original function before any observable field-name access. */
static PyObject *preparation_fields_config(PyObject *function){
    int matches=preparation_fields_profile(function);
    if(matches<0)return NULL;
    if(!matches)return Py_NewRef(Py_None);
    PyObject *ns=PyFunction_GET_GLOBALS(function),*builtins=((PyFunctionObject*)function)->func_builtins;
    if(!PyDict_CheckExact(ns)||!DK_IS_UNICODE(((PyDictObject*)ns)->ma_keys)||
    !PyDict_CheckExact(builtins)||!DK_IS_UNICODE(((PyDictObject*)builtins)->ma_keys))return Py_NewRef(Py_None);
    PyObject *field=PyDict_GetItemString(ns,"Field"),*sentinel=PyDict_GetItemString(ns,"_FIELD"),
    *name=PyDict_GetItemString(ns,"_FIELDS"),*get=PyDict_GetItemString(builtins,"getattr");
    if(!field||Py_TYPE(field)!=&PyType_Type||!sentinel||!name||!PyUnicode_CheckExact(name)||
    PyUnicode_CompareWithASCIIString(name,"__dataclass_fields__")||
    !get||!PyCFunction_Check(get)||!PyModule_CheckExact(PyCFunction_GET_SELF(get))||
    PyModule_GetDict(PyCFunction_GET_SELF(get))!=builtins||strcmp(((PyCFunctionObject*)get)->m_ml->ml_name,"getattr")||
    PyDict_GetItemString(builtins,"tuple")!=(PyObject*)&PyTuple_Type)return Py_NewRef(Py_None);
    PyObject *shadow=PyDict_GetItemString(ns,"getattr");
    if(shadow&&shadow!=get)return Py_NewRef(Py_None);
    shadow=PyDict_GetItemString(ns,"tuple");
    if(shadow&&shadow!=(PyObject*)&PyTuple_Type)return Py_NewRef(Py_None);
    PyObject *descriptor=PyDict_GetItemString(((PyTypeObject*)field)->tp_dict,"_field_type");
    if(!descriptor||Py_TYPE(descriptor)!=&PyMemberDescr_Type||PyDescr_TYPE(descriptor)!=(PyTypeObject*)field||
    ((PyTypeObject*)field)->tp_getattro!=PyObject_GenericGetAttr)return Py_NewRef(Py_None);
    PyMemberDef *member=((PyMemberDescrObject*)descriptor)->d_member;
    if(member->type!=T_OBJECT_EX||member->offset<(Py_ssize_t)sizeof(PyObject)||
    member->offset>((PyTypeObject*)field)->tp_basicsize-(Py_ssize_t)sizeof(PyObject*))return Py_NewRef(Py_None);
    /* Hold all borrowed namespace/descriptor values across allocation. */
    PyObject *held[]={
        Py_NewRef(ns),Py_NewRef(builtins),Py_NewRef(field),Py_NewRef(descriptor),Py_NewRef(sentinel),Py_NewRef(name),Py_NewRef(get)
    };
    PyObject *version=PyLong_FromUnsignedLongLong(((PyDictObject*)((PyTypeObject*)field)->tp_dict)->ma_version_tag);
    PyObject *clocks=version?Py_BuildValue("(KK)",(unsigned long long)((PyDictObject*)ns)->ma_version_tag,(unsigned long long)((PyDictObject*)builtins)->ma_version_tag):NULL;
    PyObject *out=clocks?PyTuple_Pack(9,ns,builtins,field,descriptor,version,sentinel,name,get,clocks):NULL;
    Py_XDECREF(clocks);
    Py_XDECREF(version);
    for(int i=0;i<7;i++)Py_DECREF(held[i]);
    return out;
}
static PyObject *preparation_fields_snapshot(PyObject *config,PyObject *value){
    PyObject *proof=PyTuple_GET_ITEM(config,12);
    if(proof==Py_None)Py_RETURN_NOTIMPLEMENTED;
    PyThreadState *thread=PyThreadState_Get();
    if(thread->c_tracefunc||thread->c_profilefunc)Py_RETURN_NOTIMPLEMENTED;
    /* Stock fields enters Python before consuming flags. Pending/near-threshold
     * collection must retain that entrance so ordinary finalizers can run in
     * their original order. This fast branch allocates only one GC tuple. */
    struct _gc_runtime_state *gc=&thread->interp->gc;
    if(gc->collecting||_Py_atomic_load_relaxed(&thread->interp->ceval.gc_scheduled)||
    (gc->enabled&&gc->generations[0].threshold>0&&
    gc->generations[0].count>=gc->generations[0].threshold-8))Py_RETURN_NOTIMPLEMENTED;
    for(int i=0;i<PY_MONITORING_TOOL_IDS;i++)if(thread->interp->monitoring_tool_names[i])Py_RETURN_NOTIMPLEMENTED;
    if(thread->interp->gc.callbacks&&PyList_GET_SIZE(thread->interp->gc.callbacks))Py_RETURN_NOTIMPLEMENTED;
    PyObject *ns=PyTuple_GET_ITEM(proof,0),*builtins=PyTuple_GET_ITEM(proof,1),*field=PyTuple_GET_ITEM(proof,2),
    *descriptor=PyTuple_GET_ITEM(proof,3),*sentinel=PyTuple_GET_ITEM(proof,5),*name=PyTuple_GET_ITEM(proof,6),
    *get=PyTuple_GET_ITEM(proof,7);
    if(PyFunction_GET_GLOBALS(PyTuple_GET_ITEM(config,2))!=ns||((PyFunctionObject*)PyTuple_GET_ITEM(config,2))->func_builtins!=builtins||
    !receipt_clock_matches(((PyTypeObject*)field)->tp_dict,PyTuple_GET_ITEM(proof,4))||
    ((PyTypeObject*)field)->tp_getattro!=PyObject_GenericGetAttr)Py_RETURN_NOTIMPLEMENTED;
    PyObject *clocks=PyTuple_GET_ITEM(proof,8);
    if(!receipt_clock_matches(ns,PyTuple_GET_ITEM(clocks,0))){
        if(!DK_IS_UNICODE(((PyDictObject*)ns)->ma_keys)||
        PyDict_GetItemString(ns,"_FIELD")!=sentinel||PyDict_GetItemString(ns,"_FIELDS")!=name)Py_RETURN_NOTIMPLEMENTED;
        PyObject *shadow=PyDict_GetItemString(ns,"getattr");
        if(shadow&&shadow!=get)Py_RETURN_NOTIMPLEMENTED;
        shadow=PyDict_GetItemString(ns,"tuple");
        if(shadow&&shadow!=(PyObject*)&PyTuple_Type)Py_RETURN_NOTIMPLEMENTED;
    }
    if(!receipt_clock_matches(builtins,PyTuple_GET_ITEM(clocks,1))&&
    (!DK_IS_UNICODE(((PyDictObject*)builtins)->ma_keys)||PyDict_GetItemString(builtins,"getattr")!=get||
    PyDict_GetItemString(builtins,"tuple")!=(PyObject*)&PyTuple_Type))Py_RETURN_NOTIMPLEMENTED;
    PyTypeObject *kind=Py_TYPE(value);
    if(kind->tp_getattro!=PyObject_GenericGetAttr||kind->tp_dictoffset!=0||
    !PyDict_CheckExact(kind->tp_dict)||!DK_IS_UNICODE(((PyDictObject*)kind->tp_dict)->ma_keys))Py_RETURN_NOTIMPLEMENTED;
    PyObject *metadata=PyDict_GetItemWithError(kind->tp_dict,name);
    if(!metadata||!PyDict_CheckExact(metadata)||PyDict_GET_SIZE(metadata)>128)Py_RETURN_NOTIMPLEMENTED;
    Py_ssize_t position=0;
    PyObject *key,*item;
    while(PyDict_Next(metadata,&position,&key,&item)){
        if(Py_TYPE(item)!=(PyTypeObject*)field)Py_RETURN_NOTIMPLEMENTED;
        PyMemberDef *slot=((PyMemberDescrObject*)descriptor)->d_member;
        if(!*(PyObject**)(((char*)item)+slot->offset))Py_RETURN_NOTIMPLEMENTED;
    }
    /* Metadata is exact; its flag getter is the original own member descriptor.
     * Gather the snapshot afresh without calling a generator or user code. */
    PyObject *selected[128];
    Py_ssize_t count=0;
    position=0;
    PyMemberDef *member=((PyMemberDescrObject*)descriptor)->d_member;
    while(PyDict_Next(metadata,&position,&key,&item)){
        PyObject *flag=*(PyObject**)(((char*)item)+member->offset);
        if(flag==sentinel)selected[count++]=Py_NewRef(item);
    }
    PyObject *out=PyTuple_New(count);
    if(!out){
        for(Py_ssize_t i=0;i<count;i++)Py_DECREF(selected[i]);
        return NULL;
    }
    for(Py_ssize_t i=0;i<count;i++)PyTuple_SET_ITEM(out,i,selected[i]);
    return out;
}
static PyObject *make_preparation_copy(PyObject *self,PyObject *args){
    PyObject *known,*counts,*atomic,*fields,*walk,*converters,*unknown;
    if(!PyArg_ParseTuple(args,"OOOOOOO:make_preparation_copy",&known,&counts,&atomic,&fields,&walk,&converters,&unknown))return NULL;
    if(!bounded_tuple(known,64)||!tuple_size(counts,PyTuple_GET_SIZE(known))||!tuple_size(converters,PyTuple_GET_SIZE(known))||!(PySet_CheckExact(atomic)||PyFrozenSet_CheckExact(atomic))||Py_TYPE(fields)!=&PyFunction_Type||
    Py_TYPE(unknown)!=&PyFunction_Type||PyFunction_GET_DEFAULTS(unknown)||PyFunction_GET_KW_DEFAULTS(unknown)||
    Py_TYPE(walk)!=&PyFunction_Type||PyFunction_GET_DEFAULTS(fields)||PyFunction_GET_KW_DEFAULTS(fields)||
    PyFunction_GET_DEFAULTS(walk)||PyFunction_GET_KW_DEFAULTS(walk)){
        PyErr_SetString(PyExc_TypeError,"original preparation copy declarations required");
        return NULL;
    }
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(known);i++)if(Py_TYPE(PyTuple_GET_ITEM(known,i))!=&PyType_Type){
        PyErr_SetString(PyExc_TypeError,"exact preparation declaration classes required");
        return NULL;
    }
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(counts);i++)if(!PyLong_CheckExact(PyTuple_GET_ITEM(counts,i))||PyLong_AsLong(PyTuple_GET_ITEM(counts,i))<0||PyLong_AsLong(PyTuple_GET_ITEM(counts,i))>128){
        PyErr_SetString(PyExc_TypeError,"bounded preparation field counts required");
        return NULL;
    }
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(converters);i++){
        PyObject *row=PyTuple_GET_ITEM(converters,i);
        if(!tuple_size(row,4)||PyTuple_GET_ITEM(row,0)!=PyTuple_GET_ITEM(known,i)||
        PyTuple_GET_ITEM(row,1)!=PyTuple_GET_ITEM(counts,i)||Py_TYPE(PyTuple_GET_ITEM(row,2))!=&PyFunction_Type||
        !PyCode_Check(PyTuple_GET_ITEM(row,3))){
            PyErr_SetString(PyExc_TypeError,"original preparation converter declarations required");
            return NULL;
        }
    }
    if(!keys_exact(PyModule_GetDict(self),&PyUnicode_Type)){
        PyErr_SetString(PyExc_TypeError,"original native preparation namespace required");
        return NULL;
    }
    PyObject *native=PyDict_GetItemString(PyModule_GetDict(self),"copy_preparation");
    if(!native||!PyCFunction_Check(native)||PyCFunction_GET_SELF(native)!=self||
    PyCFunction_GET_FUNCTION(native)!=(PyCFunction)preparation_copy){
        PyErr_SetString(PyExc_TypeError,"original native preparation export required");
        return NULL;
    }
    /* Preserve the entrance code/export association across GC allocations. */
    PyObject *field_code=Py_NewRef(PyFunction_GET_CODE(fields)),*walk_code=Py_NewRef(PyFunction_GET_CODE(walk)),*unknown_code=Py_NewRef(PyFunction_GET_CODE(unknown));
    Py_INCREF(native);
    NativeConfig *context=PyObject_GC_New(NativeConfig,&PreparationCopyContextType);
    if(!context){
        Py_DECREF(field_code);
        Py_DECREF(walk_code);
        Py_DECREF(unknown_code);
        Py_DECREF(native);
        return NULL;
    }
    context->phase=0;
    context->config=NULL;
    context->weakrefs=NULL;
    PyObject_GC_Track(context);
    PyObject *snapshot=preparation_fields_config(fields);
    PyObject *clock=snapshot?PyLong_FromUnsignedLongLong(((PyDictObject*)PyModule_GetDict(self))->ma_version_tag):NULL;
    if(clock){
        context->config=PyTuple_Pack(13,known,atomic,fields,field_code,walk,walk_code,native,counts,converters,unknown,unknown_code,clock,snapshot);
        Py_DECREF(clock);
    }
    Py_XDECREF(snapshot);
    Py_DECREF(field_code);
    Py_DECREF(walk_code);
    Py_DECREF(unknown_code);
    if(!context->config){
        Py_DECREF(native);
        Py_DECREF(context);
        return NULL;
    }
    /* Never seal a clock over a substituted export or mutable delegate. */
    if(!keys_exact(PyModule_GetDict(self),&PyUnicode_Type)||PyDict_GetItemString(PyModule_GetDict(self),"copy_preparation")!=native||preparation_copy_auth(context->config)<0){
        Py_DECREF(native);
        Py_DECREF(context);
        if(!PyErr_Occurred())PyErr_SetString(PyExc_TypeError,"original preparation copy declaration required");
        return NULL;
    }
    Py_DECREF(native);
    context->phase=2;
    return (PyObject*)context;
}
static PyObject *preparation_copy_delegate(PyObject *config,int index,PyObject *value){
    if(preparation_copy_auth(config)<0)return NULL;
    PyObject *out=PyObject_CallOneArg(PyTuple_GET_ITEM(config,index),value);
    if(out&&preparation_copy_auth(config)<0){
        Py_DECREF(out);
        return NULL;
    }
    return out;
}
static PyObject *preparation_copy_walk(PyObject *config,PyObject *value,int depth){
    if(depth>=16)return preparation_copy_delegate(config,4,value);
    PyObject *kind=(PyObject*)Py_TYPE(value);
    int atomic=PySet_Contains(PyTuple_GET_ITEM(config,1),kind);
    if(atomic<0)return NULL;
    if(atomic)return Py_NewRef(value);
    if(Py_EnterRecursiveCall(" while calling a Python object"))return NULL;
    PyObject *out=NULL;
    if(PyTuple_CheckExact(value)){
        PyObject *items=PyList_New(0);
        if(!items)goto done;
        for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(value);i++){
            PyObject *child=preparation_copy_walk(config,PyTuple_GET_ITEM(value,i),depth+1);
            if(!child||PyList_Append(items,child)<0){
                Py_XDECREF(child);
                Py_CLEAR(items);
                break;
            }
            Py_DECREF(child);
        }
        if(items){
            out=PyList_AsTuple(items);
            Py_DECREF(items);
        }
        goto done;
    }
    PyObject *known=PyTuple_GET_ITEM(config,0);
    Py_ssize_t match=-1;
    for(Py_ssize_t i=0;i<PyTuple_GET_SIZE(known);i++)if(kind==PyTuple_GET_ITEM(known,i))match=i;
    if(match<0){
        out=preparation_copy_delegate(config,9,value);
        goto done;
    }
    if(preparation_copy_auth(config)<0)goto done;
    PyObject *fields=preparation_fields_snapshot(config,value);
    if(fields==Py_NotImplemented){
        Py_DECREF(fields);
        fields=preparation_copy_delegate(config,2,value);
    }
    else if(fields&&preparation_copy_auth(config)<0)Py_CLEAR(fields);
    if(!fields)goto done;
    Py_ssize_t count=PyObject_Size(fields);
    if(count<0){
        Py_DECREF(fields);
        goto done;
    }
    int compiled_count=count==PyLong_AsSsize_t(PyTuple_GET_ITEM(PyTuple_GET_ITEM(config,7),match));
    out=PyDict_New();
    if(!out){
        Py_DECREF(fields);
        goto done;
    }
    if(compiled_count){
        PyObject *row=PyTuple_GET_ITEM(PyTuple_GET_ITEM(config,8),match),*function=PyTuple_GET_ITEM(row,2);
        if(PyFunction_GET_CODE(function)!=PyTuple_GET_ITEM(row,3)||PyFunction_GET_DEFAULTS(function)||PyFunction_GET_KW_DEFAULTS(function)){
            Py_DECREF(fields);
            Py_CLEAR(out);
            PyErr_SetString(PyExc_TypeError,"original preparation converter required");
            goto done;
        }
    }
    PyObject *attribute=_PyUnicode_FromId(&PyId_name);
    if(!attribute){
        Py_DECREF(fields);
        Py_CLEAR(out);
        goto done;
    }
    PyObject *iterator=compiled_count?NULL:PyObject_GetIter(fields);
    if(!compiled_count&&!iterator){
        Py_DECREF(fields);
        Py_CLEAR(out);
        goto done;
    }
    for(Py_ssize_t i=0;!compiled_count||i<count;i++){
        PyObject *field=NULL,*index=NULL,*key=NULL,*name=NULL,*member=NULL,*child=NULL;
        if(compiled_count){
            if(PyTuple_CheckExact(fields))field=Py_NewRef(PyTuple_GET_ITEM(fields,i));
            else{
                index=PyLong_FromSsize_t(i);
                if(index)field=PyObject_GetItem(fields,index);
            }
        }
        else{
            field=PyIter_Next(iterator);
            if(!field){
                if(PyErr_Occurred())Py_CLEAR(out);
                break;
            }
        }
        if(field)key=PyObject_GetAttr(field,attribute);
        if(key&&compiled_count&&!PyTuple_CheckExact(fields)){
            Py_CLEAR(field);
            field=PyObject_GetItem(fields,index);
        }
        if(key&&field)name=PyObject_GetAttr(field,attribute);
        Py_XDECREF(field);
        Py_XDECREF(index);
        if(name)member=PyObject_GetAttr(value,name);
        Py_XDECREF(name);
        if(member){
            int direct=compiled_count?PySet_Contains(PyTuple_GET_ITEM(config,1),(PyObject*)Py_TYPE(member)):0;
            if(direct>=0)child=direct?Py_NewRef(member):preparation_copy_walk(config,member,depth+1);
        }
        Py_XDECREF(member);
        if(!key||!child||PyDict_SetItem(out,key,child)<0){
            Py_XDECREF(key);
            Py_XDECREF(child);
            Py_CLEAR(out);
            break;
        }
        Py_DECREF(key);
        Py_DECREF(child);
    }
    Py_XDECREF(iterator);
    Py_DECREF(fields);
    done:
    Py_LeaveRecursiveCall();
    return out;
}
static PyObject *preparation_copy(PyObject *self,PyObject *args){
    (void)self;
    PyObject *object,*value;
    if(!PyArg_ParseTuple(args,"OO:copy_preparation",&object,&value))return NULL;
    if(Py_TYPE(object)!=&PreparationCopyContextType||((NativeConfig*)object)->phase!=2){
        PyErr_SetString(PyExc_TypeError,"original preparation copy context required");
        return NULL;
    }
    PyObject *config=((NativeConfig*)object)->config;
    if(preparation_copy_auth(config)<0)return NULL;
    PyObject *out=preparation_copy_walk(config,value,0);
    if(out&&preparation_copy_auth(config)<0){
        Py_DECREF(out);
        return NULL;
    }
    return out;
}
static int index_json_classify(PyObject *v){
    if(v==Py_None)return 0;
    if(PyBool_Check(v))return 1;
    if(PyLong_CheckExact(v))return 2;
    if(PyUnicode_CheckExact(v))return 3;
    if(PyList_CheckExact(v)||PyTuple_CheckExact(v))return 4;
    if(PyDict_CheckExact(v))return 5;
    return -1;
}
/* Exact tuples and exact lists have identical stock JSON array text. This
 * changes only a pure formatting key; aliases remain fully traversed and the
 * original serializer retains every unsupported/subclass/cycle case. */
static Py_ssize_t index_json_sequence_size(PyObject *value){
    return PyTuple_CheckExact(value)?PyTuple_GET_SIZE(value):PyList_GET_SIZE(value);
}
static PyObject *index_json_sequence_item(PyObject *value,Py_ssize_t index){
    return PyTuple_CheckExact(value)?PyTuple_GET_ITEM(value,index):PyList_GET_ITEM(value,index);
}
static int index_json_integer_ok(PyObject *v){
    int overflow=0;
    PyLong_AsLongLongAndOverflow(v,&overflow);
    if(PyErr_Occurred()){
        PyErr_Clear();
        return 0;
    }
    if(overflow<0)return 0;
    if(!overflow)return 1;
    (void)PyLong_AsUnsignedLongLong(v);
    if(!PyErr_Occurred())return 1;
    PyErr_Clear();
    /* The SDK permits exactly 2**64 as well. No giant-int digit-policy bypass. */
    PyObject *limit=PyLong_FromString("18446744073709551616",NULL,10);
    if(limit==NULL)return -1;
    int equal=PyObject_RichCompareBool(v,limit,Py_EQ);
    Py_DECREF(limit);
    return equal;
}
#define BYTE_LIMIT 33554432
static Py_ssize_t index_json_utf8_size(PyObject*v){
    Py_ssize_t n=PyUnicode_GET_LENGTH(v);
    if(PyUnicode_IS_ASCII(v))return n;
    Py_ssize_t z=0;
    int k=PyUnicode_KIND(v);
    void*d=PyUnicode_DATA(v);
    for(Py_ssize_t j=0;j<n;j++){
        Py_UCS4 u=PyUnicode_READ(k,d,j);
        z+=u<128?1:u<2048?2:u<65536?3:4;
    }
    return z;
}
static int index_json_byte_count(PyObject*v,Py_ssize_t*z,int depth){
    if(depth>32)return 0;
    int k=index_json_classify(v);
    if(k<0)return 0;
    *z+=k==1?2:1;
    if(k==2){
        int ok=index_json_integer_ok(v);
        if(ok<=0)return ok;
        *z+=9;
    }
    else if(k==3)*z+=8+index_json_utf8_size(v);
    else if(k==4){
        *z+=8;
        for(Py_ssize_t j=0;j<index_json_sequence_size(v);j++){
            int ok=index_json_byte_count(index_json_sequence_item(v,j),z,depth+1);
            if(ok<=0)return ok;
        }
    }
    else if(k==5){
        *z+=8;
        Py_ssize_t p=0;
        PyObject*a,*b;
        while(PyDict_Next(v,&p,&a,&b)){
            if(!PyUnicode_CheckExact(a))return 0;
            int ok=index_json_byte_count(a,z,depth+1);
            if(ok<=0)return ok;
            ok=index_json_byte_count(b,z,depth+1);
            if(ok<=0)return ok;
        }
    }
    return*z<=BYTE_LIMIT;
}
static void index_json_put64(char**p,uint64_t v){
    for(int j=0;j<8;j++){
        *(*p)++=(char)(v&255);
        v>>=8;
    }
}
static uint64_t index_json_get64(const char**p){
    uint64_t v=0;
    for(int j=0;j<8;j++)v|=(uint64_t)(unsigned char)*(*p)++<<(j*8);
    return v;
}
static void index_json_encode_text(PyObject*v,char**p){
    Py_ssize_t n=PyUnicode_GET_LENGTH(v);
    index_json_put64(p,(uint64_t)index_json_utf8_size(v));
    if(PyUnicode_IS_ASCII(v)){
        memcpy(*p,PyUnicode_DATA(v),n);
        *p+=n;
        return;
    }
    int k=PyUnicode_KIND(v);
    void*d=PyUnicode_DATA(v);
    for(Py_ssize_t j=0;j<n;j++){
        Py_UCS4 u=PyUnicode_READ(k,d,j);
        if(u<128)*(*p)++=u;
        else if(u<2048){
            *(*p)++=0xc0|(u>>6);
            *(*p)++=0x80|(u&63);
        }
        else if(u<65536){
            *(*p)++=0xe0|(u>>12);
            *(*p)++=0x80|((u>>6)&63);
            *(*p)++=0x80|(u&63);
        }
        else{
            *(*p)++=0xf0|(u>>18);
            *(*p)++=0x80|((u>>12)&63);
            *(*p)++=0x80|((u>>6)&63);
            *(*p)++=0x80|(u&63);
        }
    }
}
static void index_json_byte_fill(PyObject*v,char**p){
    int k=index_json_classify(v);
    *(*p)++=(char)k;
    if(k==1)*(*p)++=v==Py_True?1:0;
    else if(k==2){
        int over=0;
        long long a=PyLong_AsLongLongAndOverflow(v,&over);
        if(over>0){
            unsigned long long b=PyLong_AsUnsignedLongLong(v);
            if(PyErr_Occurred()){
                PyErr_Clear();
                *(*p)++=2;
                index_json_put64(p,0);
            }
            else{
                *(*p)++=0;
                index_json_put64(p,b);
            }
        }
        else{
            *(*p)++=a<0?1:0;
            index_json_put64(p,(uint64_t)a);
        }
    }
    else if(k==3)index_json_encode_text(v,p);
    else if(k==4){
        Py_ssize_t n=index_json_sequence_size(v);
        index_json_put64(p,(uint64_t)n);
        for(Py_ssize_t j=0;j<n;j++)index_json_byte_fill(index_json_sequence_item(v,j),p);
    }
    else if(k==5){
        index_json_put64(p,(uint64_t)PyDict_GET_SIZE(v));
        Py_ssize_t pos=0;
        PyObject*a,*b;
        while(PyDict_Next(v,&pos,&a,&b)){
            index_json_byte_fill(a,p);
            index_json_byte_fill(b,p);
        }
    }
}
static PyObject *index_json_binary_key(PyObject*self,PyObject*v){
    (void)self;
    Py_ssize_t z=0;
    int ok=index_json_byte_count(v,&z,0);
    if(ok<0)return NULL;
    if(!ok)Py_RETURN_NOTIMPLEMENTED;
    PyObject*k=PyBytes_FromStringAndSize(NULL,z);
    if(!k)return NULL;
    char*p=PyBytes_AS_STRING(k);
    index_json_byte_fill(v,&p);
    if(p!=PyBytes_AS_STRING(k)+z){
        Py_DECREF(k);
        PyErr_SetString(PyExc_SystemError,"binary accounting mismatch");
        return NULL;
    }
    return k;
}
static Py_UCS4 index_json_read_char(const unsigned char**q){
    Py_UCS4 u=*(*q)++;
    if(u>=0xf0){
        u=(u&7)<<18;
        u|=(*(*q)++&63)<<12;
        u|=(*(*q)++&63)<<6;
        u|=*(*q)++&63;
    }
    else if(u>=0xe0){
        u=(u&15)<<12;
        u|=(*(*q)++&63)<<6;
        u|=*(*q)++&63;
    }
    else if(u>=0xc0){
        u=(u&31)<<6;
        u|=*(*q)++&63;
    }
    return u;
}
static PyObject *index_json_decode_text(const char**p){
    Py_ssize_t bytes=(Py_ssize_t)index_json_get64(p),n=0;
    const unsigned char*start=(const unsigned char*)*p,*end=start+bytes,*q=start;
    Py_UCS4 m=0;
    while(q<end){
        Py_UCS4 u=index_json_read_char(&q);
        if(u>m)m=u;
        n++;
    }
    PyObject*v=PyUnicode_New(n,m);
    if(!v)return NULL;
    int k=PyUnicode_KIND(v);
    void*d=PyUnicode_DATA(v);
    q=start;
    for(Py_ssize_t j=0;j<n;j++)PyUnicode_WRITE(k,d,j,index_json_read_char(&q));
    *p=(const char*)end;
    return v;
}
static PyObject *index_json_byte_restore(const char**p){
    int k=(unsigned char)*(*p)++;
    if(k==0)return Py_NewRef(Py_None);
    if(k==1)return Py_NewRef(*(*p)++?Py_True:Py_False);
    if(k==2){
        int sign=*(*p)++;
        uint64_t v=index_json_get64(p);
        if(sign==1)return PyLong_FromLongLong((int64_t)v);
        if(sign==2)return PyLong_FromString("18446744073709551616",NULL,10);
        return PyLong_FromUnsignedLongLong(v);
    }
    if(k==3)return index_json_decode_text(p);
    Py_ssize_t n=(Py_ssize_t)index_json_get64(p);
    if(k==4){
        PyObject*out=PyList_New(n);
        if(!out)return NULL;
        for(Py_ssize_t j=0;j<n;j++){
            PyObject*x=index_json_byte_restore(p);
            if(!x){
                Py_DECREF(out);
                return NULL;
            }
            PyList_SET_ITEM(out,j,x);
        }
        return out;
    }
    PyObject*out=PyDict_New();
    if(!out)return NULL;
    for(Py_ssize_t j=0;j<n;j++){
        PyObject*a=index_json_byte_restore(p),*b=a?index_json_byte_restore(p):NULL;
        if(!a||!b||PyDict_SetItem(out,a,b)<0){
            Py_XDECREF(a);
            Py_XDECREF(b);
            Py_DECREF(out);
            return NULL;
        }
        Py_DECREF(a);
        Py_DECREF(b);
    }
    return out;
}
typedef struct {
    PyObject *function,*code,*defaults,*kwdefaults,*globals,*builtins,*closure;
    uint64_t kwversion,globalversion,builtinversion;
}
index_json_FunctionPin;
typedef struct {
    PyObject_HEAD int phase;
    PyObject *weakrefs;
    PyObject *json,*encoder,*jd,*ed,*cls,*cd,*mro,*bases,*factory,*escape,*cache;
    uint64_t jv,ev,cv;
    PyObject *fd,*fmro,*fbases,*kw_names,*separators,*tree_kw_names,*tree_escape;
    uint64_t fv;
    newfunc new_slot;
    initproc init_slot;
    ternaryfunc call_slot;
    allocfunc alloc_slot;
    index_json_FunctionPin f[5];
    int ascii,nan;
    Py_ssize_t used,budget,hits,misses,fallbacks,tree_hits,tree_misses,tree_fallbacks;
}
index_json_State;
static uint64_t index_json_version(PyObject *d){
    return d&&PyDict_CheckExact(d)?((PyDictObject*)d)->ma_version_tag:0;
}
static void index_json_release_function(index_json_FunctionPin *p){
    Py_CLEAR(p->function);
    Py_CLEAR(p->code);
    Py_CLEAR(p->defaults);
    Py_CLEAR(p->kwdefaults);
    Py_CLEAR(p->globals);
    Py_CLEAR(p->builtins);
    Py_CLEAR(p->closure);
}
static int index_json_json_traverse(index_json_State*s,visitproc visit,void*arg){
    for(int i=0;i<5;i++){
        index_json_FunctionPin*p=&s->f[i];
        Py_VISIT(p->function);
        Py_VISIT(p->code);
        Py_VISIT(p->defaults);
        Py_VISIT(p->kwdefaults);
        Py_VISIT(p->globals);
        Py_VISIT(p->builtins);
        Py_VISIT(p->closure);
    }
    Py_VISIT(s->json);
    Py_VISIT(s->encoder);
    Py_VISIT(s->jd);
    Py_VISIT(s->ed);
    Py_VISIT(s->cls);
    Py_VISIT(s->cd);
    Py_VISIT(s->mro);
    Py_VISIT(s->bases);
    Py_VISIT(s->factory);
    Py_VISIT(s->escape);
    Py_VISIT(s->cache);
    Py_VISIT(s->fd);
    Py_VISIT(s->fmro);
    Py_VISIT(s->fbases);
    Py_VISIT(s->kw_names);
    Py_VISIT(s->separators);
    Py_VISIT(s->tree_kw_names);
    Py_VISIT(s->tree_escape);
    return 0;
}
static int index_json_json_clear(index_json_State*s){
    s->phase=3;
    for(int i=0;i<5;i++)index_json_release_function(&s->f[i]);
    Py_CLEAR(s->json);
    Py_CLEAR(s->encoder);
    Py_CLEAR(s->jd);
    Py_CLEAR(s->ed);
    Py_CLEAR(s->cls);
    Py_CLEAR(s->cd);
    Py_CLEAR(s->mro);
    Py_CLEAR(s->bases);
    Py_CLEAR(s->factory);
    Py_CLEAR(s->escape);
    Py_CLEAR(s->cache);
    Py_CLEAR(s->fd);
    Py_CLEAR(s->fmro);
    Py_CLEAR(s->fbases);
    Py_CLEAR(s->kw_names);
    Py_CLEAR(s->separators);
    Py_CLEAR(s->tree_kw_names);
    Py_CLEAR(s->tree_escape);
    s->used=0;
    return 0;
}
static void index_json_cleanup(index_json_State*s){
    if(!s)return;
    index_json_json_clear(s);
    PyObject_GC_Del(s);
}
static void index_json_json_destroy(index_json_State*s){
    PyObject_GC_UnTrack(s);
    if(s->weakrefs)PyObject_ClearWeakRefs((PyObject*)s);
    index_json_cleanup(s);
}
static PyTypeObject index_json_JsonContextType={
    PyVarObject_HEAD_INIT(NULL,0)
    .tp_name="aware_workspace_sdk._tree_native._JsonContext",.tp_basicsize=sizeof(index_json_State),
    .tp_flags=Py_TPFLAGS_DEFAULT|Py_TPFLAGS_HAVE_GC,.tp_dealloc=(destructor)index_json_json_destroy,
    .tp_traverse=(traverseproc)index_json_json_traverse,.tp_clear=(inquiry)index_json_json_clear,.tp_new=no_construct,
    .tp_weaklistoffset=offsetof(index_json_State,weakrefs),
};
static index_json_State*json_context(PyObject*object){
    if(Py_TYPE(object)!=&index_json_JsonContextType){
        PyErr_SetString(PyExc_TypeError,"original canonical formatting context required");
        return NULL;
    }
    index_json_State*s=(index_json_State*)object;
    if(s->phase!=2){
        PyErr_SetString(PyExc_RuntimeError,"canonical formatting context retired");
        return NULL;
    }
    return s;
}
static int index_json_pin_function(index_json_FunctionPin *p,PyObject *obj){
    if(!obj||!PyFunction_Check(obj))return 0;
    PyFunctionObject *f=(PyFunctionObject*)obj;
    p->function=Py_NewRef(obj);
    p->code=Py_NewRef(f->func_code);
    p->defaults=Py_XNewRef(f->func_defaults);
    p->kwdefaults=Py_XNewRef(f->func_kwdefaults);
    p->globals=Py_NewRef(f->func_globals);
    p->builtins=Py_NewRef(f->func_builtins);
    p->closure=Py_XNewRef(f->func_closure);
    p->kwversion=index_json_version(p->kwdefaults);
    p->globalversion=index_json_version(p->globals);
    p->builtinversion=index_json_version(p->builtins);
    return 1;
}
static int index_json_function_current(index_json_FunctionPin *p){
    PyFunctionObject *f=(PyFunctionObject*)p->function;
    return f->func_code==p->code&&f->func_defaults==p->defaults&&f->func_kwdefaults==p->kwdefaults&&f->func_globals==p->globals&&f->func_builtins==p->builtins&&f->func_closure==p->closure&&index_json_version(p->kwdefaults)==p->kwversion&&index_json_version(p->globals)==p->globalversion&&index_json_version(p->builtins)==p->builtinversion;
}
static int index_json_eligible(index_json_State *s){
    if(s->phase!=2||!PyModule_CheckExact(s->json)||!PyModule_CheckExact(s->encoder)||Py_TYPE(s->cls)!=&PyType_Type||Py_TYPE(s->factory)!=&PyType_Type)return 0;
    PyThreadState *t=PyThreadState_Get();
    PyInterpreterState *i=t->interp;
    /* Conservative headroom: bounded primitive nesting <=32, no callbacks. */
    if(t->c_profilefunc||t->c_tracefunc||t->py_recursion_remaining<640||t->c_recursion_remaining<640)return 0;
    if(_PyInterpreterState_GetEvalFrameFunc(i)!=_PyEval_EvalFrameDefault)return 0;
    for(int n=0;n<PY_MONITORING_TOOL_IDS;n++){
        if(i->monitoring_tool_names[n])return 0;
        for(int e=0;e<_PY_MONITORING_EVENTS;e++)if(i->monitoring_callables[n][e]&&i->monitoring_callables[n][e]!=Py_None)return 0;
    }
    if(i->gc.callbacks&&PyList_GET_SIZE(i->gc.callbacks))return 0;
    if(PyModule_GetDict(s->json)!=s->jd||PyModule_GetDict(s->encoder)!=s->ed||index_json_version(s->jd)!=s->jv||index_json_version(s->ed)!=s->ev)return 0;
    PyTypeObject *c=(PyTypeObject*)s->cls;
    if(c->tp_dict!=s->cd||c->tp_mro!=s->mro||c->tp_bases!=s->bases||index_json_version(s->cd)!=s->cv)return 0;
    PyTypeObject *f=(PyTypeObject*)s->factory;
    if(f->tp_dict!=s->fd||f->tp_mro!=s->fmro||f->tp_bases!=s->fbases||index_json_version(s->fd)!=s->fv||f->tp_new!=s->new_slot||f->tp_init!=s->init_slot||f->tp_call!=s->call_slot||f->tp_alloc!=s->alloc_slot)return 0;
    for(int n=0;n<5;n++)if(!index_json_function_current(&s->f[n]))return 0;
    return 1;
}
#ifdef WORKSPACE_JSON_PROFILE_COUNT
static PyObject*index_json_profile_model(PyObject*value,int depth){
    if(depth>32){
        PyErr_SetString(PyExc_TypeError,"JSON declaration depth exceeds build profile");
        return NULL;
    }
    if(PyCode_Check(value)){
        PyObject*out=PyList_New(WORKSPACE_JSON_PROFILE_FIELD_COUNT+1);
        if(!out)return NULL;
        PyObject*tag=PyUnicode_FromString("code");
        if(!tag){
            Py_DECREF(out);
            return NULL;
        }
        PyList_SET_ITEM(out,0,tag);
        for(int i=0;i<WORKSPACE_JSON_PROFILE_FIELD_COUNT;i++){
            PyObject*field=PyObject_GetAttrString(value,index_json_profile_fields[i]);
            PyObject*model=field?index_json_profile_model(field,depth+1):NULL;
            Py_XDECREF(field);
            if(!model){
                Py_DECREF(out);
                return NULL;
            }
            PyList_SET_ITEM(out,i+1,model);
        }
        return out;
    }
    if(PyBytes_CheckExact(value)){
        Py_ssize_t n=PyBytes_GET_SIZE(value);
        if(n>131072){
            PyErr_SetString(PyExc_TypeError,"JSON bytecode exceeds build profile");
            return NULL;
        }
        PyObject*hex=PyUnicode_New(n*2,127);
        if(!hex)return NULL;
        const char*alphabet="0123456789abcdef";
        const unsigned char*p=(const unsigned char*)PyBytes_AS_STRING(value);
        for(Py_ssize_t i=0;i<n;i++){
            PyUnicode_1BYTE_DATA(hex)[i*2]=alphabet[p[i]>>4];
            PyUnicode_1BYTE_DATA(hex)[i*2+1]=alphabet[p[i]&15];
        }
        PyObject*out=Py_BuildValue("[sO]","bytes",hex);
        Py_DECREF(hex);
        return out;
    }
    if(PyTuple_CheckExact(value)){
        Py_ssize_t n=PyTuple_GET_SIZE(value);
        if(n>4096){
            PyErr_SetString(PyExc_TypeError,"JSON tuple exceeds build profile");
            return NULL;
        }
        PyObject*out=PyList_New(n+1);
        if(!out)return NULL;
        PyObject*tag=PyUnicode_FromString("tuple");
        if(!tag){
            Py_DECREF(out);
            return NULL;
        }
        PyList_SET_ITEM(out,0,tag);
        for(Py_ssize_t i=0;i<n;i++){
            PyObject*model=index_json_profile_model(PyTuple_GET_ITEM(value,i),depth+1);
            if(!model){
                Py_DECREF(out);
                return NULL;
            }
            PyList_SET_ITEM(out,i+1,model);
        }
        return out;
    }
    if(PyDict_CheckExact(value)){
        Py_ssize_t n=PyDict_GET_SIZE(value);
        if(n>128){
            PyErr_SetString(PyExc_TypeError,"JSON defaults exceed build profile");
            return NULL;
        }
        PyObject*out=PyList_New(1);
        if(!out)return NULL;
        PyObject*tag=PyUnicode_FromString("dict");
        if(!tag){
            Py_DECREF(out);
            return NULL;
        }
        PyList_SET_ITEM(out,0,tag);
        Py_ssize_t pos=0;
        PyObject*k,*v;
        while(PyDict_Next(value,&pos,&k,&v)){
            Py_INCREF(k);
            Py_INCREF(v);
            PyObject*key=index_json_profile_model(k,depth+1);
            PyObject*item=key?index_json_profile_model(v,depth+1):NULL;
            Py_DECREF(k);
            Py_DECREF(v);
            PyObject*pair=item?PyList_New(2):NULL;
            if(!key||!item||!pair){
                Py_XDECREF(key);
                Py_XDECREF(item);
                Py_XDECREF(pair);
                Py_DECREF(out);
                return NULL;
            }
            PyList_SET_ITEM(pair,0,key);
            PyList_SET_ITEM(pair,1,item);
            int failed=PyList_Append(out,pair)<0;
            Py_DECREF(pair);
            if(failed){
                Py_DECREF(out);
                return NULL;
            }
        }
        return out;
    }
    if(value==Py_None||PyBool_Check(value)||PyLong_CheckExact(value)||PyUnicode_CheckExact(value))return Py_NewRef(value);
    PyErr_SetString(PyExc_TypeError,"unsupported JSON declaration");
    return NULL;
}
_Static_assert(sizeof(index_json_profiles)/sizeof(index_json_profiles[0])==WORKSPACE_JSON_PROFILE_COUNT,"complete profile pointer table required");
_Static_assert(sizeof(index_json_profile_sizes)/sizeof(index_json_profile_sizes[0])==WORKSPACE_JSON_PROFILE_COUNT,"complete profile size table required");
static int index_json_profile_matches(index_json_FunctionPin*p,int ordinal){
    if(ordinal<0||ordinal>=WORKSPACE_JSON_PROFILE_COUNT){
        PyErr_SetString(PyExc_ValueError,"bounded original declaration profile required");
        return -1;
    }
    PyObject*code=index_json_profile_model(p->code,0);
    PyObject*defaults=code?index_json_profile_model(p->defaults?p->defaults:Py_None,0):NULL;
    PyObject*kw=defaults?index_json_profile_model(p->kwdefaults?p->kwdefaults:Py_None,0):NULL;
    if(!code||!defaults||!kw){
        Py_XDECREF(code);
        Py_XDECREF(defaults);
        Py_XDECREF(kw);
        if(PyErr_ExceptionMatches(PyExc_TypeError)||PyErr_ExceptionMatches(PyExc_ValueError)){
            PyErr_Clear();
            return 0;
        }
        return -1;
    }
    PyObject*model=PyList_New(3);
    if(!model){
        Py_DECREF(code);
        Py_DECREF(defaults);
        Py_DECREF(kw);
        return -1;
    }
    PyList_SET_ITEM(model,0,code);
    PyList_SET_ITEM(model,1,defaults);
    PyList_SET_ITEM(model,2,kw);
    PyObject*key=index_json_binary_key(NULL,model);
    Py_DECREF(model);
    if(!key)return -1;
    int same=key!=Py_NotImplemented&&PyBytes_GET_SIZE(key)==(Py_ssize_t)index_json_profile_sizes[ordinal]&&
    !memcmp(PyBytes_AS_STRING(key),index_json_profiles[ordinal],index_json_profile_sizes[ordinal]);
    Py_DECREF(key);
    return same;
}
#endif
static int preparation_fields_profile(PyObject *function){
#if defined(WORKSPACE_JSON_PROFILE_COUNT) && WORKSPACE_JSON_PROFILE_COUNT > 5
    index_json_FunctionPin pin={
        0
    };
    pin.code=PyFunction_GET_CODE(function);
    pin.defaults=PyFunction_GET_DEFAULTS(function);
    pin.kwdefaults=PyFunction_GET_KW_DEFAULTS(function);
    return index_json_profile_matches(&pin,5);
#else
    (void)function;
    return 0;
#endif
}
static int index_json_stock_class(PyObject*cls){
    if(Py_TYPE(cls)!=&PyType_Type)return 0;
    PyTypeObject*t=(PyTypeObject*)cls;
    PyObject*d=t->tp_dict;
    if(t->tp_base!=&PyBaseObject_Type||t->tp_getattro!=PyObject_GenericGetAttr||
    t->tp_setattro!=PyObject_GenericSetAttr||t->tp_new!=PyBaseObject_Type.tp_new||
    !keys_exact(d,&PyUnicode_Type)||PyDict_GET_SIZE(d)!=10)return 0;
    const char*names[]={
        "__module__","__doc__","item_separator","key_separator","__init__","default","encode","iterencode","__dict__","__weakref__"
    };
    for(int i=0;i<10;i++)if(!PyDict_GetItemString(d,names[i]))return 0;
    for(int i=0;i<4;i++)if(!PyUnicode_CheckExact(PyDict_GetItemString(d,names[i])))return 0;
    for(int i=8;i<10;i++){
        PyObject*descriptor=PyDict_GetItemString(d,names[i]);
        if(Py_TYPE(descriptor)!=&PyGetSetDescr_Type||PyDescr_TYPE(descriptor)!=t)return 0;
    }
    return 1;
}
static int index_json_stock_factory(PyObject*factory,PyObject*escape){
    if(Py_TYPE(factory)!=&PyType_Type||!PyCFunction_Check(escape))return 0;
    PyTypeObject*t=(PyTypeObject*)factory;
    if(strcmp(t->tp_name,"_json.Encoder")||!keys_exact(t->tp_dict,&PyUnicode_Type))return 0;
    PyObject*call=literal_lookup(t->tp_dict,&PyId___call__),*constructor=literal_lookup(t->tp_dict,&PyId___new__);
    if(!call||Py_TYPE(call)!=&PyWrapperDescr_Type||PyDescr_TYPE(call)!=t||
    ((PyWrapperDescrObject*)call)->d_wrapped!=(void*)t->tp_call||
    !constructor||!PyCFunction_Check(constructor)||PyCFunction_GET_SELF(constructor)!=factory)return 0;
    const char*members[]={
        "markers","default","encoder","indent","key_separator","item_separator","sort_keys","skipkeys"
    };
    for(int i=0;i<8;i++){
        PyObject*member=PyDict_GetItemString(t->tp_dict,members[i]);
        if(!member||Py_TYPE(member)!=&PyMemberDescr_Type||PyDescr_TYPE(member)!=t)return 0;
    }
    PyObject*module=PyCFunction_GET_SELF(escape);
    if(!PyModule_CheckExact(module)||!keys_exact(PyModule_GetDict(module),&PyUnicode_Type)||
    literal_lookup(PyModule_GetDict(module),&PyId_make_encoder)!=factory||
    literal_lookup(PyModule_GetDict(module),&PyId_encode_basestring_ascii)!=escape)return 0;
    return 1;
}
static int index_json_stock_builtins(PyObject*d){
    if(!keys_exact(d,&PyUnicode_Type))return 0;
    const char*names[]={
        "str","int","float","list","tuple","dict","ValueError","TypeError"
    };
    PyObject*types[]={
        (PyObject*)&PyUnicode_Type,(PyObject*)&PyLong_Type,(PyObject*)&PyFloat_Type,
        (PyObject*)&PyList_Type,(PyObject*)&PyTuple_Type,(PyObject*)&PyDict_Type,PyExc_ValueError,PyExc_TypeError
    };
    for(int i=0;i<8;i++)if(PyDict_GetItemString(d,names[i])!=types[i])return 0;
    PyObject*function=literal_lookup(d,&PyId_isinstance);
    if(!function||!PyCFunction_Check(function))return 0;
    PyObject*name=PyObject_GetAttrString(function,"__name__");
    if(!name)return -1;
    int same=PyUnicode_CheckExact(name)&&PyUnicode_CompareWithASCIIString(name,"isinstance")==0;
    Py_DECREF(name);
    return same;
}
static int index_json_global_builtins(PyObject*globals,PyObject*builtins){
    const char*names[]={
        "str","int","float","list","tuple","dict","ValueError","TypeError","isinstance","repr"
    };
    if(!keys_exact(globals,&PyUnicode_Type))return 0;
    for(int i=0;i<10;i++){
        PyObject*value=PyDict_GetItemString(globals,names[i]);
        if(value&&value!=PyDict_GetItemString(builtins,names[i]))return 0;
    }
    return 1;
}
static PyObject *index_json_make(PyObject *self,PyObject *args){
    (void)self;
    PyObject *json,*encoder;
    int ascii,nan;
    Py_ssize_t budget;
    if(!PyArg_ParseTuple(args,"OOiin",&json,&encoder,&ascii,&nan,&budget))return NULL;
    if(!PyModule_CheckExact(json)||!PyModule_CheckExact(encoder)||budget<0||budget>16777216||ascii!=1||nan!=1){
        PyErr_SetString(PyExc_TypeError,"exact modules and fixed finite profile required");
        return NULL;
    }
    index_json_State *s=PyObject_GC_New(index_json_State,&index_json_JsonContextType);
    if(!s)return NULL;
    memset((char*)s+sizeof(PyObject),0,sizeof(index_json_State)-sizeof(PyObject));
    s->json=Py_NewRef(json);
    s->encoder=Py_NewRef(encoder);
    s->jd=Py_NewRef(PyModule_GetDict(json));
    s->ed=Py_NewRef(PyModule_GetDict(encoder));
    s->ascii=ascii;
    s->nan=nan;
    s->budget=budget;
    if(!keys_exact(s->jd,&PyUnicode_Type)||!keys_exact(s->ed,&PyUnicode_Type))goto invalid;
    PyObject *c=literal_lookup(s->jd,&PyId_JSONEncoder),*factory=literal_lookup(s->ed,&PyId_c_make_encoder),*escape=PyDict_GetItemString(s->ed,ascii?"encode_basestring_ascii":"encode_basestring");
    if(!c||!factory||!escape||!index_json_stock_class(c)||!index_json_stock_factory(factory,escape))goto invalid;
    s->cls=Py_NewRef(c);
    s->factory=Py_NewRef(factory);
    s->escape=Py_NewRef(escape);
    s->cd=Py_NewRef(((PyTypeObject*)c)->tp_dict);
    s->mro=Py_NewRef(((PyTypeObject*)c)->tp_mro);
    s->bases=Py_NewRef(((PyTypeObject*)c)->tp_bases);
    const char *names[]={
        "__init__","encode","iterencode","default"
    };
    if(!index_json_pin_function(&s->f[0],literal_lookup(s->jd,&PyId_dumps)))goto invalid;
    for(int n=0;n<4;n++){
        PyObject *f=PyDict_GetItemString(s->cd,names[n]);
        if(!f||!index_json_pin_function(&s->f[n+1],f))goto invalid;
    }
    s->fd=Py_NewRef(((PyTypeObject*)factory)->tp_dict);
    s->fmro=Py_NewRef(((PyTypeObject*)factory)->tp_mro);
    s->fbases=Py_NewRef(((PyTypeObject*)factory)->tp_bases);
    s->fv=index_json_version(s->fd);
    s->new_slot=((PyTypeObject*)factory)->tp_new;
    s->init_slot=((PyTypeObject*)factory)->tp_init;
    s->call_slot=((PyTypeObject*)factory)->tp_call;
    s->alloc_slot=((PyTypeObject*)factory)->tp_alloc;
    if(s->init_slot!=PyBaseObject_Type.tp_init||!s->new_slot||!s->call_slot)goto invalid;
    if(s->f[0].globals!=s->jd||literal_lookup(s->ed,&PyId_JSONEncoder)!=c)goto invalid;
    for(int i=1;i<5;i++)if(s->f[i].globals!=s->ed)goto invalid;
    for(int i=0;i<5;i++)if(!index_json_global_builtins(s->f[i].globals,s->f[i].builtins))goto invalid;
    PyObject*infinity=literal_lookup(s->ed,&PyId_INFINITY);
    if(!infinity||!PyFloat_CheckExact(infinity)||!Py_IS_INFINITY(PyFloat_AS_DOUBLE(infinity))||PyFloat_AS_DOUBLE(infinity)<0)goto invalid;
    for(int i=0;i<5;i++){
        int stock=index_json_stock_builtins(s->f[i].builtins);
        if(stock<0){
            index_json_cleanup(s);
            return NULL;
        }
        if(!stock)goto invalid;
    }
    /* The tree profile shares this same bounded formatting-only cache. */
    PyObject *tree_escape=literal_lookup(s->ed,&PyId_encode_basestring);
    if(tree_escape&&PyCFunction_Check(tree_escape)&&PyCFunction_GET_FLAGS(tree_escape)==METH_O&&
    PyCFunction_GET_SELF(tree_escape)==PyCFunction_GET_SELF(s->escape)&&
    !strcmp(((PyCFunctionObject*)tree_escape)->m_ml->ml_name,"encode_basestring")&&
    literal_lookup(PyModule_GetDict(PyCFunction_GET_SELF(s->escape)),&PyId_encode_basestring)==tree_escape)
    s->tree_escape=Py_NewRef(tree_escape);
    s->tree_kw_names=Py_BuildValue("(ssss)","ensure_ascii","allow_nan","sort_keys","separators");
    if(!s->tree_kw_names){
        index_json_cleanup(s);
        return NULL;
    }
    s->separators=Py_BuildValue("(ss)",",",":");
    s->kw_names=ascii&&nan?Py_BuildValue("(ss)","sort_keys","separators"):Py_BuildValue("(ssss)","ensure_ascii","allow_nan","sort_keys","separators");
    if(!s->separators||!s->kw_names){
        index_json_cleanup(s);
        return NULL;
    }
    s->cache=PyDict_New();
    if(!s->cache){
        index_json_cleanup(s);
        return NULL;
    }
    s->jv=index_json_version(s->jd);
    s->ev=index_json_version(s->ed);
    s->cv=index_json_version(s->cd);
#ifdef WORKSPACE_JSON_PROFILE_COUNT
    for(int i=0;i<5;i++){
        int match=index_json_profile_matches(&s->f[i],i);
        if(match<=0){
            index_json_cleanup(s);
            if(match<0)return NULL;
            Py_RETURN_NONE;
        }
    }
    for(int i=0;i<5;i++)if(!index_json_function_current(&s->f[i])){
        index_json_cleanup(s);
        Py_RETURN_NONE;
    }
#else
    index_json_cleanup(s);
    Py_RETURN_NONE;
#endif
    s->phase=2;
    PyObject_GC_Track(s);
    return (PyObject*)s;
    invalid:index_json_cleanup(s);
    Py_RETURN_NONE;
}
static PyObject *index_json_literal_call(index_json_State*s,PyObject*callee,PyObject*value){
    PyObject *stack[3]={
        value,Py_True,s->separators
    };
    return PyObject_Vectorcall(callee,stack,1,s->kw_names);
}
static PyObject *canonical_key_text(PyObject *,int,int);
/* Invocation-local formatting snapshots only. Keys are produced in the
 * original full preflight, with no GC-tracked allocations or Python dispatch.
 * A collection or an actual Python serializer call invalidates all remaining
 * snapshots. Every subsequent key then takes the original fresh traversal. */
#define INDEX_STAGE_BYTES (8*1024*1024)
#define INDEX_STAGE_ITEMS 4096
typedef struct {
    PyObject *sequence;
    Py_ssize_t start,count;
} index_json_StageGroup;
typedef struct {
    PyObject **keys,**texts;
    Py_ssize_t length,bytes,epochs[3];
    index_json_StageGroup groups[7];
    int group_count,valid,prefetch;
} index_json_Stage;
static void index_json_stage_clear(index_json_Stage *stage){
    for(Py_ssize_t j=0;j<stage->length;j++){
        Py_XDECREF(stage->keys[j]);
        if(stage->texts)Py_XDECREF(stage->texts[j]);
    }
    PyMem_Free(stage->keys);PyMem_Free(stage->texts);
    stage->keys=NULL;stage->texts=NULL;stage->length=0;stage->valid=0;
}
static int index_json_stage_live(index_json_Stage *stage){
    if(!stage||!stage->valid)return 0;
    struct _gc_runtime_state *gc=&PyThreadState_Get()->interp->gc;
    for(int j=0;j<3;j++)if(stage->epochs[j]!=gc->generation_stats[j].collections){stage->valid=0;return 0;}
    return 1;
}
static PyObject *index_json_stage_take(index_json_Stage *stage,index_json_StageGroup *group,Py_ssize_t ordinal,PyObject **text){
    if(!group||!index_json_stage_live(stage)||ordinal<0||ordinal>=group->count)return NULL;
    Py_ssize_t index=group->start+ordinal;
    PyObject *key=stage->keys[index];stage->keys[index]=NULL;
    if(stage->texts){*text=stage->texts[index];stage->texts[index]=NULL;}
    return key;
}
static index_json_StageGroup *index_json_stage_group(index_json_Stage *stage,PyObject *value){
    if(!index_json_stage_live(stage))return NULL;
    for(int j=0;j<stage->group_count;j++)if(stage->groups[j].sequence==value)return &stage->groups[j];
    return NULL;
}
/* Positive signed64 integers avoid the original overflow-exception allocation.
 * The original full preflight handles the SDK's unsigned/sentinel cases. */
static int index_json_stage_count(PyObject *value,Py_ssize_t *bytes,int depth,int *native_supported){
    if(depth>32)return 0;
    int kind=index_json_classify(value);
    if(kind<0)return 0;
    *bytes+=kind==1?2:1;
    if(kind==2){
        int overflow=0;(void)PyLong_AsLongLongAndOverflow(value,&overflow);
        if(PyErr_Occurred())return -1;
        if(overflow)return 0;
        *bytes+=9;
    }else if(kind==3)*bytes+=8+index_json_utf8_size(value);
    else if(kind==4){
        *bytes+=8;
        for(Py_ssize_t j=0;j<index_json_sequence_size(value);j++){
            int ok=index_json_stage_count(index_json_sequence_item(value,j),bytes,depth+1,native_supported);
            if(ok<=0)return ok;
        }
    }else if(kind==5){
        if(native_supported&&PyDict_GET_SIZE(value)>8192)*native_supported=0;
        *bytes+=8;
        Py_ssize_t position=0;PyObject *key,*member;
        while(PyDict_Next(value,&position,&key,&member)){
            if(!PyUnicode_CheckExact(key))return 0;
            int ok=index_json_stage_count(key,bytes,depth+1,native_supported);if(ok<=0)return ok;
            ok=index_json_stage_count(member,bytes,depth+1,native_supported);if(ok<=0)return ok;
        }
    }
    return *bytes<=BYTE_LIMIT;
}
/* Inspect only the original private closed cache before doing an extra lookup.
 * No caller key hash/equality or destructor is dispatched during capture. */
static int index_json_stage_cache_closed(index_json_State *s){
    if(!PyDict_CheckExact(s->cache)||PyDict_GET_SIZE(s->cache)>4096)return 0;
    Py_ssize_t position=0;PyObject *key,*entry;
    while(PyDict_Next(s->cache,&position,&key,&entry))
        if(!PyBytes_CheckExact(key)||!tuple_size(entry,2)||
        !PyUnicode_CheckExact(PyTuple_GET_ITEM(entry,0))||!PyLong_CheckExact(PyTuple_GET_ITEM(entry,1)))return 0;
    return 1;
}
static int index_json_stage_preflight(PyObject *value,index_json_Stage *stage,index_json_State *s){
    const char *mutation[]={"contract_ref","contract_version","repository_binding_ref","records"};
    const char *delta[]={"contract_ref","version","repository_binding_ref","sequence","bodies","captures","deltas"};
    if(!PyDict_CheckExact(value))return 0;
    Py_ssize_t count=PyDict_GET_SIZE(value)==4?4:7;
    const char **names=count==4?mutation:delta;
    if(PyDict_GET_SIZE(value)!=count)return 0;
    Py_ssize_t position=0;PyObject *key,*member;
    while(PyDict_Next(value,&position,&key,&member))if(!PyUnicode_CheckExact(key))return 0;
    for(Py_ssize_t j=0;j<count;j++)if(PyDict_GetItemString(value,names[j])==NULL)return 0;
    Py_ssize_t bytes=9;position=0;
    while(PyDict_Next(value,&position,&key,&member)){
        int ok=index_json_stage_count(key,&bytes,1,NULL);if(ok<=0)return ok;
        if(!PyList_CheckExact(member)){ok=index_json_stage_count(member,&bytes,1,NULL);if(ok<=0)return ok;continue;}
        bytes+=9;if(bytes>BYTE_LIMIT)return 0;
        index_json_StageGroup *group=&stage->groups[stage->group_count++];
        group->sequence=member;group->start=stage->length;
        int capture=1;
        for(Py_ssize_t j=0;j<PyList_GET_SIZE(member);j++){
            PyObject *item=PyList_GET_ITEM(member,j);
            Py_ssize_t prior=bytes;
            int native_supported=1;
            ok=index_json_stage_count(item,&bytes,2,&native_supported);if(ok<=0)return ok;
            Py_ssize_t size=bytes-prior;
            if(!capture||size>INDEX_STAGE_BYTES-stage->bytes||stage->length>=INDEX_STAGE_ITEMS){capture=0;continue;}
            if(!stage->keys){stage->keys=PyMem_Calloc(INDEX_STAGE_ITEMS,sizeof(PyObject*));if(!stage->keys){PyErr_NoMemory();return -1;}}
            PyObject *snapshot=PyBytes_FromStringAndSize(NULL,size);if(!snapshot)return -1;
            char *cursor=PyBytes_AS_STRING(snapshot);index_json_byte_fill(item,&cursor);
            if(cursor!=PyBytes_AS_STRING(snapshot)+size){Py_DECREF(snapshot);PyErr_SetString(PyExc_SystemError,"staged primitive key accounting mismatch");return -1;}
            Py_ssize_t index=stage->length++;
            stage->keys[index]=snapshot;stage->bytes+=size;group->count++;
            if(index==0){
                stage->prefetch=-1;
                if(PyDict_GET_SIZE(s->cache)&&index_json_stage_cache_closed(s)){
                    PyObject *existing=PyDict_GetItemWithError(s->cache,snapshot);
                    if(PyErr_Occurred())return -1;
                    if(!existing)stage->prefetch=1;
                }
            }
            if(stage->prefetch>0&&native_supported&&index!=0){
                PyObject *existing=PyDict_GetItemWithError(s->cache,snapshot);
                if(PyErr_Occurred())return -1;
                if(existing){
                    if(!stage->texts){stage->texts=PyMem_Calloc(INDEX_STAGE_ITEMS,sizeof(PyObject*));if(!stage->texts){PyErr_NoMemory();return -1;}}
                    stage->texts[index]=Py_NewRef(PyTuple_GET_ITEM(existing,0));
                }
            }
        }
    }
    struct _gc_runtime_state *gc=&PyThreadState_Get()->interp->gc;
    for(int j=0;j<3;j++)stage->epochs[j]=gc->generation_stats[j].collections;
    stage->valid=1;return 1;
}
static PyObject*index_json_render_value(index_json_State*s,PyObject*value,int keep,index_json_Stage*stage,index_json_StageGroup*group,Py_ssize_t ordinal){
    PyObject*prefetched=NULL;
    PyObject*key=index_json_stage_take(stage,group,ordinal,&prefetched);
    if(!key)key=index_json_binary_key(NULL,value);
    if(!key)return NULL;
    if(key==Py_NotImplemented){
        Py_DECREF(key);
        PyErr_SetString(PyExc_TypeError,"canonical formatting input changed");
        return NULL;
    }
    PyObject*entry=keep?PyDict_GetItemWithError(s->cache,key):NULL;
    if(entry){
        s->hits++;
        PyObject*out=Py_NewRef(PyTuple_GET_ITEM(entry,0));
        Py_DECREF(key);
        Py_XDECREF(prefetched);
        return out;
    }
    if(PyErr_Occurred()){
        Py_DECREF(key);
        Py_XDECREF(prefetched);
        return NULL;
    }
    if(!index_json_eligible(s)){
        Py_DECREF(key);
        Py_XDECREF(prefetched);
        PyErr_SetString(PyExc_TypeError,"canonical serializer changed before rendering");
        return NULL;
    }
    /* This same-call text matched the fresh complete key before an earlier
     * insertion evicted it. Only keys known to have a callback-free native
     * renderer can use it; every original miss auth/cache/counter step stays. */
    PyObject *text=prefetched?prefetched:(s->ascii?canonical_key_text(key,0,1):Py_NewRef(Py_NotImplemented));
    prefetched=NULL;
    if(text==Py_NotImplemented){
        Py_DECREF(text);
        if(stage)stage->valid=0;
        const char*p=PyBytes_AS_STRING(key);
        PyObject*snapshot=index_json_byte_restore(&p);
        if(!snapshot){
            Py_DECREF(key);
            return NULL;
        }
        if(p!=PyBytes_AS_STRING(key)+PyBytes_GET_SIZE(key)){
            Py_DECREF(snapshot);
            Py_DECREF(key);
            PyErr_SetString(PyExc_SystemError,"canonical key length differs");
            return NULL;
        }
        if(!index_json_eligible(s)){
            Py_DECREF(snapshot);
            Py_DECREF(key);
            PyErr_SetString(PyExc_TypeError,"canonical serializer changed before rendering");
            return NULL;
        }
        text=index_json_literal_call(s,s->f[0].function,snapshot);
        Py_DECREF(snapshot);
    }
    if(!text){
        Py_DECREF(key);
        Py_XDECREF(prefetched);
        return NULL;
    }
    if(!index_json_eligible(s)||!PyUnicode_CheckExact(text)){
        Py_DECREF(key);
        Py_DECREF(text);
        PyErr_SetString(PyExc_TypeError,"canonical serializer changed during rendering");
        return NULL;
    }
    s->misses++;
    Py_ssize_t charge=PyBytes_GET_SIZE(key)+512+PyUnicode_KIND(text)*(PyUnicode_GET_LENGTH(text)+1);
    if(keep&&charge<=s->budget){
        while(s->used+charge>s->budget||PyDict_GET_SIZE(s->cache)>=4096){
            Py_ssize_t pos=0;
            PyObject*k,*v;
            if(!PyDict_Next(s->cache,&pos,&k,&v))break;
            Py_ssize_t previous=PyLong_AsSsize_t(PyTuple_GET_ITEM(v,1));
            if(PyDict_DelItem(s->cache,k)<0){
                Py_DECREF(key);
                Py_DECREF(text);
                return NULL;
            }
            s->used-=previous;
        }
        PyObject*size=PyLong_FromSsize_t(charge),*record=size?PyTuple_Pack(2,text,size):NULL;
        Py_XDECREF(size);
        if(!record||PyDict_SetItem(s->cache,key,record)<0){
            Py_XDECREF(record);
            Py_DECREF(key);
            Py_DECREF(text);
            return NULL;
        }
        Py_DECREF(record);
        s->used+=charge;
    }
    Py_DECREF(key);
    return text;
}
static int index_json_index_shape(PyObject*value){
    const char*mutation[]={
        "contract_ref","contract_version","repository_binding_ref","records"
    };
    const char*delta[]={
        "contract_ref","version","repository_binding_ref","sequence","bodies","captures","deltas"
    };
    if(!PyDict_CheckExact(value))return 0;
    const char**names=PyDict_GET_SIZE(value)==4?mutation:delta;
    Py_ssize_t count=PyDict_GET_SIZE(value)==4?4:7;
    if(PyDict_GET_SIZE(value)!=count)return 0;
    Py_ssize_t pos=0;
    PyObject*k,*v;
    while(PyDict_Next(value,&pos,&k,&v))if(!PyUnicode_CheckExact(k))return 0;
    for(Py_ssize_t j=0;j<count;j++)if(PyDict_GetItemString(value,names[j])==NULL)return 0;
    Py_ssize_t bytes=0;
    return index_json_byte_count(value,&bytes,0);
}
static PyObject*index_json_call_index_formatter(PyObject*self,PyObject*args){
    COST_BEGIN(4);
    (void)self;
    PyObject*object,*callee,*value,*module;
    if(!PyArg_ParseTuple(args,"OOOO:index_json_call_index_formatter",&object,&callee,&value,&module))COST_RETURN(NULL);
    index_json_State*s=json_context(object);
    if(!s)COST_RETURN(NULL);
    index_json_Stage stage={0};
    int shape=0;
    if(callee==s->f[0].function&&module==s->json&&index_json_eligible(s)){
        if(s->ascii)shape=index_json_stage_preflight(value,&stage,s);
        if(shape==0){index_json_stage_clear(&stage);shape=index_json_index_shape(value);}
    }
    if(shape<0){index_json_stage_clear(&stage);COST_RETURN(NULL);}
    if(!shape){
        index_json_stage_clear(&stage);
        s->fallbacks++;
        COST_RETURN(index_json_literal_call(s,callee,value));
    }
    PyObject*keys=PyDict_Keys(value),*parts=NULL,*comma=NULL,*colon=NULL,*text=NULL;
    if(!keys){index_json_stage_clear(&stage);COST_RETURN(NULL);}
    if(PyList_Sort(keys)<0)goto done;
    parts=PyList_New(0);
    comma=PyUnicode_FromString(",");
    colon=PyUnicode_FromString(":");
    if(!parts||!comma||!colon)goto done;
    PyObject*piece=PyUnicode_FromString("{");
    if(!piece)goto done;
    if(PyList_Append(parts,piece)<0){
        Py_DECREF(piece);
        goto done;
    }
    Py_DECREF(piece);
    for(Py_ssize_t i=0;i<PyList_GET_SIZE(keys);i++){
        if(!index_json_eligible(s)){
            PyErr_SetString(PyExc_TypeError,"canonical serializer changed during composition");
            goto done;
        }
        PyObject*key=PyList_GET_ITEM(keys,i),*member=PyDict_GetItemWithError(value,key);
        if(!member){
            if(!PyErr_Occurred())PyErr_SetString(PyExc_TypeError,"canonical index changed during composition");
            goto done;
        }
        Py_INCREF(member);
        if(i&&PyList_Append(parts,comma)<0){
            Py_DECREF(member);
            goto done;
        }
        piece=index_json_render_value(s,key,0,&stage,NULL,0);
        if(!piece){
            Py_DECREF(member);
            goto done;
        }
        int failed=PyList_Append(parts,piece)<0||PyList_Append(parts,colon)<0;
        Py_DECREF(piece);
        if(failed){
            Py_DECREF(member);
            goto done;
        }
        if(PyList_CheckExact(member)){
            piece=PyUnicode_FromString("[");
            if(!piece){
                Py_DECREF(member);
                goto done;
            }
            failed=PyList_Append(parts,piece)<0;
            Py_DECREF(piece);
            if(failed){
                Py_DECREF(member);
                goto done;
            }
            index_json_StageGroup *group=index_json_stage_group(&stage,member);
            Py_ssize_t count=PyList_GET_SIZE(member);
            for(Py_ssize_t j=0;j<count;j++){
                if(PyList_GET_SIZE(member)!=count){
                    Py_DECREF(member);
                    PyErr_SetString(PyExc_TypeError,"canonical sequence changed during composition");
                    goto done;
                }
                if(j&&PyList_Append(parts,comma)<0){
                    Py_DECREF(member);
                    goto done;
                }
                piece=index_json_render_value(s,PyList_GET_ITEM(member,j),1,&stage,group,j);
                if(!piece){
                    Py_DECREF(member);
                    goto done;
                }
                failed=PyList_Append(parts,piece)<0;
                Py_DECREF(piece);
                if(failed){
                    Py_DECREF(member);
                    goto done;
                }
            }
            piece=PyUnicode_FromString("]");
        }
        else piece=index_json_render_value(s,member,0,&stage,NULL,0);
        Py_DECREF(member);
        if(!piece)goto done;
        failed=PyList_Append(parts,piece)<0;
        Py_DECREF(piece);
        if(failed)goto done;
    }
    piece=PyUnicode_FromString("}");
    if(!piece)goto done;
    int failed=PyList_Append(parts,piece)<0;
    Py_DECREF(piece);
    if(failed)goto done;
    piece=PyUnicode_FromString("");
    if(!piece)goto done;
    text=PyUnicode_Join(piece,parts);
    Py_DECREF(piece);
    if(text&&!index_json_eligible(s)){
        Py_CLEAR(text);
        PyErr_SetString(PyExc_TypeError,"canonical serializer changed after composition");
    }
    done:Py_DECREF(keys);
    Py_XDECREF(parts);
    Py_XDECREF(comma);
    Py_XDECREF(colon);
    index_json_stage_clear(&stage);
    COST_RETURN(text);
}
/* Complete fresh primitive traversal precedes every descriptive tree cache hit.
 * 0xff cannot collide with a store key's original primitive tags 0..5. */
static int tree_json_eligible(index_json_State *s){
    return index_json_eligible(s)&&s->tree_escape&&
    literal_lookup(s->ed,&PyId_encode_basestring)==s->tree_escape;
}
static PyObject *tree_json_literal(index_json_State *s,PyObject *callee,PyObject *value,PyObject *owner_names){
    if(owner_names){
        PyObject *stack[5]={
            value,Py_True,Py_False,s->separators,Py_False
        };
        return PyObject_Vectorcall(callee,stack,1,owner_names);
    }
    PyObject *stack[5]={
        value,Py_False,Py_False,Py_True,s->separators
    };
    return PyObject_Vectorcall(callee,stack,1,s->tree_kw_names);
}
/* Render the freshly captured, private primitive key without reconstructing a
 * second DTO graph. There is no Python dispatch while the writer is active. */
typedef struct {
    const char *key,*value,*name;
    Py_ssize_t name_length;
}
tree_json_Field;
static void tree_json_skip(const char **cursor){
    int tag=(unsigned char)*(*cursor)++;
    if(tag==1)(*cursor)++;
    else if(tag==2)(*cursor)+=9;
    else if(tag==3){
        uint64_t length=index_json_get64(cursor);
        (*cursor)+=length;
    }
    else if(tag==4||tag==5){
        uint64_t count=index_json_get64(cursor);
        for(uint64_t i=0;i<count;i++){
            tree_json_skip(cursor);
            if(tag==5)tree_json_skip(cursor);
        }
    }
}
static int tree_json_field_order(const void *left,const void *right){
    const tree_json_Field *a=left,*b=right;
    Py_ssize_t n=a->name_length<b->name_length?a->name_length:b->name_length;
    int order=memcmp(a->name,b->name,n);
    if(order)return order;
    return (a->name_length>b->name_length)-(a->name_length<b->name_length);
}
static int tree_json_ascii(_PyUnicodeWriter *writer,const char *text,Py_ssize_t length){
    return _PyUnicodeWriter_WriteASCIIString(writer,text,length);
}
static int tree_json_string(_PyUnicodeWriter *writer,const char **cursor,int ascii){
    static const char hex[]="0123456789abcdef";
    uint64_t length=index_json_get64(cursor);
    const unsigned char *current=(const unsigned char *)*cursor,*end=current+length;
    *cursor=(const char *)end;
    if(tree_json_ascii(writer,"\"",1)<0)return -1;
    while(current<end){
        const unsigned char *start=current;
        while(current<end&&*current>=32&&*current<(ascii?127:128)&&*current!='"'&&*current!='\\')current++;
        if(current>start&&tree_json_ascii(writer,(const char *)start,current-start)<0)return -1;
        if(current==end)break;
        unsigned char byte=*current++;
        if(byte=='"'||byte=='\\'){
            char escaped[2]={
                '\\',(char)byte
            };
            if(tree_json_ascii(writer,escaped,2)<0)return -1;
        }
        else if(byte<32){
            char escape=byte==8?'b':byte==12?'f':byte==10?'n':byte==13?'r':byte==9?'t':0;
            if(escape){
                char escaped[2]={
                    '\\',escape
                };
                if(tree_json_ascii(writer,escaped,2)<0)return -1;
            }
            else{
                char escaped[6]={
                    '\\','u','0','0',hex[byte>>4],hex[byte&15]
                };
                if(tree_json_ascii(writer,escaped,6)<0)return -1;
            }
        }
        else if(byte==127){
            if(tree_json_ascii(writer,"\\u007f",6)<0)return -1;
        }
        else{
            /* Input is our own surrogate-pass UTF-8, never external bytes. */
            Py_UCS4 character;
            if(byte<224){
                character=((byte&31)<<6)|(current[0]&63);
                current++;
            }
            else if(byte<240){
                character=((byte&15)<<12)|((current[0]&63)<<6)|(current[1]&63);
                current+=2;
            }
            else{
                character=((byte&7)<<18)|((current[0]&63)<<12)|((current[1]&63)<<6)|(current[2]&63);
                current+=3;
            }
            if(ascii){
                Py_UCS4 units[2]={
                    character,0
                };
                int count=1;
                if(character>0xffff){
                    character-=0x10000;
                    units[0]=0xd800+(character>>10);
                    units[1]=0xdc00+(character&1023);
                    count=2;
                }
                for(int k=0;k<count;k++){
                    Py_UCS4 unit=units[k];
                    char escaped[6]={
                        '\\','u',hex[(unit>>12)&15],hex[(unit>>8)&15],hex[(unit>>4)&15],hex[unit&15]
                    };
                    if(tree_json_ascii(writer,escaped,6)<0)return -1;
                }
            }
            else if(_PyUnicodeWriter_WriteChar(writer,character)<0)return -1;
        }
    }
    return tree_json_ascii(writer,"\"",1)<0?-1:1;
}
static int tree_json_write(_PyUnicodeWriter *writer,const char **cursor,int depth,int ascii){
    if(depth>32)return 0;
    int tag=(unsigned char)*(*cursor)++;
    if(tag==0)return tree_json_ascii(writer,"null",4)<0?-1:1;
    if(tag==1){
        int truth=*(*cursor)++;
        return tree_json_ascii(writer,truth?"true":"false",truth?4:5)<0?-1:1;
    }
    if(tag==2){
        unsigned char sign=(unsigned char)*(*cursor)++;
        uint64_t value=index_json_get64(cursor);
        char buffer[32];
        int length;
        if(sign==2){
            memcpy(buffer,"18446744073709551616",20);
            length=20;
        }
        else if(sign==1){
            long long signed_value;
            memcpy(&signed_value,&value,sizeof(value));
            length=PyOS_snprintf(buffer,sizeof(buffer),"%lld",signed_value);
        }
        else length=PyOS_snprintf(buffer,sizeof(buffer),"%llu",(unsigned long long)value);
        return tree_json_ascii(writer,buffer,length)<0?-1:1;
    }
    if(tag==3)return tree_json_string(writer,cursor,ascii);
    uint64_t count=index_json_get64(cursor);
    if(tag==4){
        if(tree_json_ascii(writer,"[",1)<0)return -1;
        for(uint64_t i=0;i<count;i++){
            if(i&&tree_json_ascii(writer,",",1)<0)return -1;
            int status=tree_json_write(writer,cursor,depth+1,ascii);
            if(status<=0)return status;
        }
        return tree_json_ascii(writer,"]",1)<0?-1:1;
    }
    /* Larger dictionaries retain the literal original serializer. Closed tree
     * records use only a small finite number of fields. This is no new quota. */
    if(tag!=5||count>8192)return 0;
    tree_json_Field *fields=count?PyMem_Malloc((size_t)count*sizeof(*fields)):NULL;
    if(count&&!fields){
        PyErr_NoMemory();
        return -1;
    }
    for(uint64_t i=0;i<count;i++){
        fields[i].key=*cursor;
        const char *key=*cursor+1;
        fields[i].name_length=(Py_ssize_t)index_json_get64(&key);
        fields[i].name=key;
        tree_json_skip(cursor);
        fields[i].value=*cursor;
        tree_json_skip(cursor);
    }
    if(count>1)qsort(fields,(size_t)count,sizeof(*fields),tree_json_field_order);
    int status=tree_json_ascii(writer,"{",1)<0?-1:1;
    for(uint64_t i=0;status>0&&i<count;i++){
        if(i&&tree_json_ascii(writer,",",1)<0){
            status=-1;
            break;
        }
        const char *key=fields[i].key;
        status=tree_json_write(writer,&key,depth+1,ascii);
        if(status>0&&tree_json_ascii(writer,":",1)<0)status=-1;
        const char *value=fields[i].value;
        if(status>0)status=tree_json_write(writer,&value,depth+1,ascii);
    }
    PyMem_Free(fields);
    if(status<=0)return status;
    return tree_json_ascii(writer,"}",1)<0?-1:1;
}
static PyObject *canonical_key_text(PyObject *key,int offset,int ascii){
    const char *cursor=PyBytes_AS_STRING(key)+offset;
    _PyUnicodeWriter writer;
    _PyUnicodeWriter_Init(&writer);
    writer.overallocate=1;
    if(_PyUnicodeWriter_Prepare(&writer,PyBytes_GET_SIZE(key)-offset,127)<0){
        _PyUnicodeWriter_Dealloc(&writer);
        return NULL;
    }
    int status=tree_json_write(&writer,&cursor,0,ascii);
    if(status<=0){
        _PyUnicodeWriter_Dealloc(&writer);
        if(status==0)Py_RETURN_NOTIMPLEMENTED;
        return NULL;
    }
    if(cursor!=PyBytes_AS_STRING(key)+PyBytes_GET_SIZE(key)){
        _PyUnicodeWriter_Dealloc(&writer);
        PyErr_SetString(PyExc_SystemError,"canonical tree key length differs");
        return NULL;
    }
    return _PyUnicodeWriter_Finish(&writer);
}
static PyObject *tree_json_key_text(PyObject *key){
    return canonical_key_text(key,1,0);
}
static PyObject *tree_json_call(PyObject *self,PyObject *args){
    COST_BEGIN(5);
    (void)self;
    PyObject *object,*callee,*value,*module,*owner_names=NULL;
    if(!PyArg_ParseTuple(args,"OOOO|O:call_tree_formatter",&object,&callee,&value,&module,&owner_names))COST_RETURN(NULL);
    if(owner_names){
        const char *names[]={
            "sort_keys","ensure_ascii","separators","allow_nan"
        };
        if(!tuple_size(owner_names,4)){
            PyErr_SetString(PyExc_TypeError,"original owner formatting keywords required");
            COST_RETURN(NULL);
        }
        for(int i=0;i<4;i++)if(!PyUnicode_CheckExact(PyTuple_GET_ITEM(owner_names,i))||
        PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(owner_names,i),names[i])!=0){
            PyErr_SetString(PyExc_TypeError,"original owner formatting keywords required");
            COST_RETURN(NULL);
        }
    }
    index_json_State *s=json_context(object);
    if(!s)COST_RETURN(NULL);
    if(callee!=s->f[0].function||module!=s->json||!tree_json_eligible(s)){
        s->fallbacks++;
        s->tree_fallbacks++;
        COST_RETURN(tree_json_literal(s,callee,value,owner_names));
    }
    Py_ssize_t length=0;
    int supported=index_json_byte_count(value,&length,0);
    if(supported<0)COST_RETURN(NULL);
    if(!supported){
        s->fallbacks++;
        s->tree_fallbacks++;
        COST_RETURN(tree_json_literal(s,callee,value,owner_names));
    }
    PyObject *key=PyBytes_FromStringAndSize(NULL,length+1);
    if(!key)COST_RETURN(NULL);
    char *key_cursor=PyBytes_AS_STRING(key);
    *key_cursor++=(char)255;
    index_json_byte_fill(value,&key_cursor);
    PyObject *entry=PyDict_GetItemWithError(s->cache,key);
    if(entry){
        s->hits++;
        s->tree_hits++;
        PyObject *out=Py_NewRef(PyTuple_GET_ITEM(entry,0));
        Py_DECREF(key);
        COST_RETURN(out);
    }
    if(PyErr_Occurred()){
        Py_DECREF(key);
        COST_RETURN(NULL);
    }
    if(!tree_json_eligible(s)){
        Py_DECREF(key);
        PyErr_SetString(PyExc_TypeError,"canonical tree serializer changed before formatting");
        COST_RETURN(NULL);
    }
    PyObject *text=tree_json_key_text(key);
    if(text==Py_NotImplemented){
        Py_DECREF(text);
        Py_DECREF(key);
        s->fallbacks++;
        s->tree_fallbacks++;
        COST_RETURN(tree_json_literal(s,callee,value,owner_names));
    }
    if(!text){
        Py_DECREF(key);
        COST_RETURN(NULL);
    }
    if(!tree_json_eligible(s)||!PyUnicode_CheckExact(text)){
        Py_DECREF(key);
        Py_DECREF(text);
        PyErr_SetString(PyExc_TypeError,"canonical tree serializer changed during formatting");
        COST_RETURN(NULL);
    }
    s->misses++;
    s->tree_misses++;
    Py_ssize_t charge=PyBytes_GET_SIZE(key)+512+PyUnicode_KIND(text)*(PyUnicode_GET_LENGTH(text)+1);
    if(charge<=s->budget){
        while(s->used+charge>s->budget||PyDict_GET_SIZE(s->cache)>=4096){
            Py_ssize_t pos=0;
            PyObject *old_key,*old_entry;
            if(!PyDict_Next(s->cache,&pos,&old_key,&old_entry))break;
            Py_ssize_t previous=PyLong_AsSsize_t(PyTuple_GET_ITEM(old_entry,1));
            if(PyDict_DelItem(s->cache,old_key)<0){
                Py_DECREF(key);
                Py_DECREF(text);
                COST_RETURN(NULL);
            }
            s->used-=previous;
        }
        PyObject *size=PyLong_FromSsize_t(charge),*record=size?PyTuple_Pack(2,text,size):NULL;
        Py_XDECREF(size);
        if(!record||PyDict_SetItem(s->cache,key,record)<0){
            Py_XDECREF(record);
            Py_DECREF(key);
            Py_DECREF(text);
            COST_RETURN(NULL);
        }
        Py_DECREF(record);
        s->used+=charge;
    }
    Py_DECREF(key);
    if(!tree_json_eligible(s)){
        Py_DECREF(text);
        PyErr_SetString(PyExc_TypeError,"canonical tree serializer changed after formatting");
        COST_RETURN(NULL);
    }
    COST_RETURN(text);
}
static PyObject*index_json_index_formatter_stats(PyObject*self,PyObject*object){
    (void)self;
    index_json_State*s=json_context(object);
    if(!s)return NULL;
    return Py_BuildValue("{s:n,s:n,s:n,s:n,s:n,s:n,s:n,s:n}","entries",PyDict_GET_SIZE(s->cache),"charged_bytes",s->used,"hits",s->hits,"misses",s->misses,"fallbacks",s->fallbacks,"tree_hits",s->tree_hits,"tree_misses",s->tree_misses,"tree_fallbacks",s->tree_fallbacks);
}
static PyObject *receipt_graph_stats(PyObject *self,PyObject *unused){
    (void)self;
    (void)unused;
    return Py_BuildValue("{s:n,s:n,s:n}","attempts",graph_attempts,"direct_records",graph_direct,"posthint_continuations",graph_continuations);
}
#ifdef WORKSPACE_FORMATTER_COSTS
static PyObject *literal_lookup_probe(PyObject *self,PyObject *args){
    (void)self;
    PyObject *mapping;
    int original;
    if(!PyArg_ParseTuple(args,"Op:literal_lookup_probe",&mapping,&original))return NULL;
    if(!PyDict_CheckExact(mapping)){
        PyErr_SetString(PyExc_TypeError,"exact diagnostic dictionary required");
        return NULL;
    }
    PyObject *value=original?PyDict_GetItemString(mapping,"values"):literal_lookup(mapping,&PyId_values);
    if(PyErr_Occurred())return NULL;
    return value?Py_NewRef(value):Py_NewRef(Py_None);
}
#endif
/* Pure lossless bytes codec: no payload, owner or authorization reuse. */
#define RDX_LIMIT ((Py_ssize_t)32*1024*1024)
#define RDX_ANCHOR 16
#define RDX_BUCKETS 131072U
static uint64_t rdx_hash(const unsigned char *p){
    uint64_t a,b;
    memcpy(&a,p,8);memcpy(&b,p+8,8);
    a^=b+UINT64_C(0x9e3779b97f4a7c15)+(a<<6)+(a>>2);
    a^=a>>30;a*=UINT64_C(0xbf58476d1ce4e5b9);a^=a>>27;
    return a;
}
static void rdx_u64(unsigned char *p,uint64_t n){
    for(int i=7;i>=0;i--){p[i]=(unsigned char)n;n>>=8;}
}
static int rdx_literal(unsigned char *out,Py_ssize_t cap,Py_ssize_t *used,
                       const unsigned char *bytes,Py_ssize_t length,uint32_t *count){
    if(!length)return 1;
    if(length>cap-*used-9)return 0;
    out[(*used)++]=0;rdx_u64(out+*used,(uint64_t)length);*used+=8;
    memcpy(out+*used,bytes,(size_t)length);*used+=length;(*count)++;return 1;
}
static int rdx_copy(unsigned char *out,Py_ssize_t cap,Py_ssize_t *used,
                    Py_ssize_t offset,Py_ssize_t length,uint32_t *count){
    if(cap-*used<17)return 0;
    out[(*used)++]=1;rdx_u64(out+*used,(uint64_t)length);*used+=8;
    rdx_u64(out+*used,(uint64_t)offset);*used+=8;(*count)++;return 1;
}
static PyObject *index_bytes_delta(PyObject *self,PyObject *args){
    (void)self;
    PyObject *previous,*current;
    if(!PyArg_ParseTuple(args,"OO:index_bytes_delta",&previous,&current))return NULL;
    if(!PyBytes_CheckExact(previous)||!PyBytes_CheckExact(current)){
        PyErr_SetString(PyExc_TypeError,"exact previous/current index bytes required");return NULL;
    }
    Py_ssize_t m=PyBytes_GET_SIZE(previous),n=PyBytes_GET_SIZE(current);
    if(m>RDX_LIMIT||n>RDX_LIMIT)Py_RETURN_NONE;
    const unsigned char *old=(const unsigned char *)PyBytes_AS_STRING(previous);
    const unsigned char *now=(const unsigned char *)PyBytes_AS_STRING(current);
    PyObject *result=PyBytes_FromStringAndSize(NULL,n+64);
    if(!result)return NULL;
    unsigned char *out=(unsigned char *)PyBytes_AS_STRING(result);
    memcpy(out,"RDX1",4);rdx_u64(out+4,(uint64_t)n);
    Py_ssize_t used=16,cap=n+64,cursor=0,literal=0;
    uint32_t count=0,*heads=NULL,*links=NULL;
    Py_ssize_t stride=(m+65535)/65536;if(stride<32)stride=32;
    Py_ssize_t entries=m>=RDX_ANCHOR?(m-RDX_ANCHOR)/stride+1:0;
    if(entries){
        heads=PyMem_Malloc(RDX_BUCKETS*sizeof(uint32_t));
        links=PyMem_Malloc((size_t)entries*sizeof(uint32_t));
        if(!heads||!links){PyErr_NoMemory();goto error;}
        memset(heads,0xff,RDX_BUCKETS*sizeof(uint32_t));
        for(Py_ssize_t i=0;i<entries;i++){
            uint32_t bucket=(uint32_t)rdx_hash(old+i*stride)&(RDX_BUCKETS-1);
            links[i]=heads[bucket];heads[bucket]=(uint32_t)i;
        }
    }
    while(entries&&cursor<=n-RDX_ANCHOR){
        uint32_t bucket=(uint32_t)rdx_hash(now+cursor)&(RDX_BUCKETS-1);
        Py_ssize_t best=-1,distance=PY_SSIZE_T_MAX;
        uint32_t node=heads[bucket];
        for(int probes=0;node!=UINT32_MAX&&probes<128;probes++,node=links[node]){
            Py_ssize_t pos=(Py_ssize_t)node*stride;
            if(memcmp(old+pos,now+cursor,RDX_ANCHOR))continue;
            Py_ssize_t delta=pos>cursor?pos-cursor:cursor-pos;
            if(delta<distance){best=pos;distance=delta;if(!delta)break;}
        }
        if(best<0){cursor++;continue;}
        Py_ssize_t begin=cursor,source=best;
        while(begin>literal&&source>0&&now[begin-1]==old[source-1]){begin--;source--;}
        Py_ssize_t end=cursor+RDX_ANCHOR,oldend=best+RDX_ANCHOR;
        while(end+64<=n&&oldend+64<=m&&!memcmp(now+end,old+oldend,64)){end+=64;oldend+=64;}
        while(end<n&&oldend<m&&now[end]==old[oldend]){end++;oldend++;}
        if(!rdx_literal(out,cap,&used,now+literal,begin-literal,&count)||
           !rdx_copy(out,cap,&used,source,end-begin,&count))goto fallback;
        cursor=literal=end;
        if(PyErr_CheckSignals()<0)goto error;
    }
    if(!rdx_literal(out,cap,&used,now+literal,n-literal,&count))goto fallback;
    if(used>n+(n?25:16))goto fallback;
    out[12]=(unsigned char)(count>>24);out[13]=(unsigned char)(count>>16);
    out[14]=(unsigned char)(count>>8);out[15]=(unsigned char)count;
    PyMem_Free(heads);PyMem_Free(links);
    if(_PyBytes_Resize(&result,used)<0)return NULL;
    return result;
fallback:
    PyMem_Free(heads);PyMem_Free(links);Py_DECREF(result);Py_RETURN_NONE;
error:
    PyMem_Free(heads);PyMem_Free(links);Py_DECREF(result);return NULL;
}

static PyMethodDef methods[]={
    {"ascii_paths_last",_PyCFunction_CAST(ascii_paths_last),METH_FASTCALL,"Fresh whole ASCII path batch or original ordered loop."},
    {"index_bytes_delta",index_bytes_delta,METH_VARARGS,"Pure bounded lossless index bytes delta."},
    {
        "make_preparation_copy",make_preparation_copy,METH_VARARGS,"Bind original detached copy declarations."
    },
    {
        "copy_preparation",preparation_copy,METH_VARARGS,"Fresh original dataclass/tuple copying."
    },
    {
        "receipt_graph_stats",receipt_graph_stats,METH_NOARGS,"Descriptive graph traversal counters only."
    },
#ifdef WORKSPACE_FORMATTER_COSTS
    {
        "literal_lookup_probe",literal_lookup_probe,METH_VARARGS,"Diagnostic original/identifier lookup parity only."
    },
    {
        "read_cost_counters",cost_read,METH_NOARGS,"Diagnostic aggregate counters only."
    },
    {
        "reset_cost_counters",cost_reset,METH_NOARGS,"Reset aggregate counters before fixture entry."
    },
#endif
    {"ascii_path_positive",_PyCFunction_CAST(ascii_path_positive),METH_FASTCALL,"Pure positive-only ASCII path grammar; false retains original validation."},
    {
        "new_context",new_context,METH_NOARGS,"Create an unsealed metadata-only context."
    },
    {
        "seal",seal,METH_VARARGS,"Seal one original declaration once."
    },
    {
        "convert_root",convert_root,METH_VARARGS,"Fresh descriptive root field traversal."
    },
    {
        "verify",verify,METH_O,"Recheck original declaration references."
    },
    {
        "receipt_prelude",receipt_prelude,METH_VARARGS,"Fresh original receipt metadata prelude."
    },
    {
        "new_receipt_context",new_receipt_context,METH_NOARGS,"Create a declaration-only receipt context."
    },
    {
        "seal_receipts",seal_receipts,METH_VARARGS,"Seal original receipt declarations once."
    },
    {
        "convert_receipt",convert_receipt,METH_VARARGS,"Fresh original receipt field traversal."
    },
    {
        "make_index_formatter",index_json_make,METH_VARARGS,"Create one bounded descriptive canonical text memo."
    },
    {
        "call_index_formatter",index_json_call_index_formatter,METH_VARARGS,"Fresh-key same-format index text or literal original call."
    },
    {
        "index_formatter_stats",index_json_index_formatter_stats,METH_O,"Detached formatting counters only."
    },
    {
        "call_tree_formatter",tree_json_call,METH_VARARGS,"Fresh complete canonical tree text with original false/false profile."
    },
    {
        NULL,NULL,0,NULL
    }
};
static struct PyModuleDef definition={
    PyModuleDef_HEAD_INIT,
    .m_name="_tree_native",
    .m_size=-1,
    .m_methods=methods,
};
PyMODINIT_FUNC PyInit__tree_native(void) {
    /* Internal CPython layouts are used only for this exact compiled patch. */
    if(Py_Version!=PY_VERSION_HEX){
        PyErr_SetString(PyExc_ImportError,"native tree metadata requires its exact CPython build patch");
        return NULL;
    }
    if(PyInterpreterState_GetID(PyInterpreterState_Get())!=0){
        PyErr_SetString(PyExc_ImportError,"native tree metadata requires the main interpreter");
        return NULL;
    }
    if(PyType_Ready(&ContextType)<0 || PyType_Ready(&ReceiptContextType)<0 || PyType_Ready(&PreparationCopyContextType)<0 || PyType_Ready(&index_json_JsonContextType)<0)return NULL;
    PyObject*module=PyModule_Create(&definition);
    if(!module)return NULL;
#ifdef WORKSPACE_JSON_PROFILE_COUNT
    int abi=1;
#else
    int abi=0;
#endif
    if(PyModule_AddIntConstant(module,"ASCII_PATH_BATCH_ABI",1)<0){Py_DECREF(module);return NULL;}
    if(PyModule_AddIntConstant(module,"RECEIPT_DIRECT_RECORD_ABI",1)<0){
        Py_DECREF(module);
        return NULL;
    }
    if(PyModule_AddIntConstant(module,"OWNER_FORMATTER_ABI",1)<0){
        Py_DECREF(module);
        return NULL;
    }
    if(PyModule_AddIntConstant(module,"TREE_FORMATTER_ABI",abi)<0){
        Py_DECREF(module);
        return NULL;
    }
    if(PyModule_AddIntConstant(module,"INDEX_FORMATTER_ABI",abi)<0){
        Py_DECREF(module);
        return NULL;
    }
    if(PyModule_AddIntConstant(module,"INDEX_BYTES_DELTA_ABI",1)<0){Py_DECREF(module);return NULL;}
    if(PyModule_AddIntConstant(module,"ASCII_PATH_POSITIVE_ABI",2)<0){Py_DECREF(module);return NULL;}
    return module;
}
