// Copyright 2020 Thomas Rogers
// SPDX-License-Identifier: Apache-2.0

#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <cstdint>

typedef struct
{
    uint16_t blocking : 1;
    uint16_t bottom_swap : 1;
    uint16_t align : 1;
    uint16_t xflip : 1;
    uint16_t masking : 1;
    uint16_t one_way : 1;
    uint16_t blocking2 : 1;
    uint16_t translucent : 1;
    uint16_t yflip : 1;
    uint16_t translucent_rev : 1;
    uint16_t reserved : 4;
    uint16_t poly_blue : 1;
    uint16_t poly_green : 1;
} Stat;

typedef struct
{
    int32_t position_x;
    int32_t position_y;
    int16_t point2_index;
    int16_t other_side_wall_index;
    int16_t other_side_sector_index;
    Stat stat;
    int16_t picnum;
    int16_t over_picnum;
    int8_t shade;
    uint8_t palette;
    uint8_t repeat_x;
    uint8_t repeat_y;
    uint8_t panning_x;
    uint8_t panning_y;
    int16_t tags[3];
} BuildWall;

typedef struct
{
    uint8_t data1;

    uint8_t data2 : 6;
    uint8_t state : 1;
    uint8_t data3 : 1;

    uint8_t data4[2];
    int16_t data;

    uint16_t tx_id : 10;
    uint16_t data5 : 6;

    uint32_t rx_id : 10;
    uint32_t cmd : 8;
    uint32_t going_on : 1;
    uint32_t going_off : 1;
    uint32_t busy_time : 12;

    uint32_t wait_time : 12;
    uint32_t rest_state : 1;
    uint32_t interruptable : 1;
    uint32_t pan_always : 1;
    uint32_t panx : 7;
    uint32_t data8 : 1;
    uint32_t pany : 7;
    uint32_t data9 : 1;
    uint32_t decoupled : 1;

    uint8_t one_shot : 1;
    uint8_t data10 : 1;
    uint8_t key : 3;
    uint8_t push : 1;
    uint8_t vector : 1;
    uint8_t reserved : 1;

    uint8_t data11[2];

    uint8_t data12 : 2;
    uint8_t locked : 1;
    uint8_t dude_lockout : 1;
    uint8_t data13 : 4;

    uint8_t data14[4];
} BloodWallData;

static struct PyModuleDef wallmodule = {
    PyModuleDef_HEAD_INIT,
    "bloom.map_data.wall",
    NULL,
    -1,
    NULL};

inline void crypt_buffer(char *data, size_t length, uint8_t key)
{
    for (size_t index = 0; index < length; ++index)
    {
        data[index] ^= (key + index) & 0xFF;
    }
}

static PyObject *
loader_load_walls(PyObject *self, PyObject *args)
{
    PyObject *wall_constructor;
    PyObject *data_bytes;
    uint64_t offset;
    uint64_t count;
    uint8_t key;

    if (!PyArg_ParseTuple(args, "OSKKb", &wall_constructor, &data_bytes, &offset, &count, &key))
    {
        return NULL;
    }

    char *data = PyBytes_AsString(data_bytes);

    PyObject *result = PyList_New(count);
    for (size_t index = 0; index < count; ++index)
    {
        crypt_buffer(&data[offset], sizeof(BuildWall), key);

        const BuildWall &wall = *reinterpret_cast<const BuildWall *>(&data[offset]);
        offset += sizeof(BuildWall);

        PyObject *py_wall = PyObject_Call(wall_constructor, PyTuple_New(0), NULL);
        PyObject *py_build_wall = PyObject_GetAttrString(py_wall, "wall");

        PyObject_SetAttrString(py_build_wall, "position_x", PyLong_FromLong(wall.position_x));
        PyObject_SetAttrString(py_build_wall, "position_y", PyLong_FromLong(wall.position_y));

        if (wall.tags[2] > 0)
        {
            const BloodWallData &wall_data = *reinterpret_cast<const BloodWallData *>(&data[offset]);
            offset += sizeof(BloodWallData);

            PyObject *py_wall_data = PyObject_GetAttrString(py_wall, "data");
        }

        PyList_SetItem(result, index, py_wall);
    }

    return result;
}

static PyMethodDef LoaderMethods[] = {
    {"load_walls",
     loader_load_walls,
     METH_VARARGS,
     "Load walls for a map."},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef loadermodule = {
    PyModuleDef_HEAD_INIT,
    "bloom.native.loader",
    "bloom native map loading",
    -1,
    LoaderMethods};

PyMODINIT_FUNC
PyInit_loader(void)
{
    return PyModule_Create(&loadermodule);
}
