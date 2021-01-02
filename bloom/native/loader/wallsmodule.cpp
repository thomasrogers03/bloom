// Copyright 2020 Thomas Rogers
// SPDX-License-Identifier: Apache-2.0

#include "common.h"

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

static PyObject *
walls_load_walls(PyObject *self, PyObject *args)
{
    static const BloodWallData empty_wall_data = {0};

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

    PyObject *result_walls = PyList_New(count);
    PyObject *result = PyTuple_New(2);
    for (size_t index = 0; index < count; ++index)
    {
        crypt_buffer(&data[offset], sizeof(BuildWall), key);

        const BuildWall &wall = *reinterpret_cast<const BuildWall *>(&data[offset]);
        offset += sizeof(BuildWall);

        PyObject *py_wall = PyObject_Call(wall_constructor, PyTuple_New(0), NULL);
        PyObject *py_build_wall = PyObject_GetAttrString(py_wall, "wall");

        PyObject_SetAttrString(py_build_wall, "position_x", PyLong_FromLong(wall.position_x));
        PyObject_SetAttrString(py_build_wall, "position_x", PyLong_FromLong(wall.position_x));
        PyObject_SetAttrString(py_build_wall, "position_y", PyLong_FromLong(wall.position_y));
        PyObject_SetAttrString(py_build_wall, "point2_index", PyLong_FromLong(wall.point2_index));
        PyObject_SetAttrString(py_build_wall, "other_side_wall_index", PyLong_FromLong(wall.other_side_wall_index));
        PyObject_SetAttrString(py_build_wall, "other_side_sector_index", PyLong_FromLong(wall.other_side_sector_index));
        PyObject_SetAttrString(py_build_wall, "picnum", PyLong_FromLong(wall.picnum));
        PyObject_SetAttrString(py_build_wall, "over_picnum", PyLong_FromLong(wall.over_picnum));
        PyObject_SetAttrString(py_build_wall, "shade", PyLong_FromLong(wall.shade));
        PyObject_SetAttrString(py_build_wall, "palette", PyLong_FromLong(wall.palette));
        PyObject_SetAttrString(py_build_wall, "repeat_x", PyLong_FromLong(wall.repeat_x));
        PyObject_SetAttrString(py_build_wall, "repeat_y", PyLong_FromLong(wall.repeat_y));
        PyObject_SetAttrString(py_build_wall, "panning_x", PyLong_FromLong(wall.panning_x));
        PyObject_SetAttrString(py_build_wall, "panning_y", PyLong_FromLong(wall.panning_y));

        load_int_list(PyObject_GetAttrString(py_build_wall, "tags"), wall.tags);

        PyObject *py_wall_stat = PyObject_GetAttrString(py_build_wall, "stat");

        PyObject_SetAttrString(py_wall_stat, "blocking", PyLong_FromLong(wall.stat.blocking));
        PyObject_SetAttrString(py_wall_stat, "bottom_swap", PyLong_FromLong(wall.stat.bottom_swap));
        PyObject_SetAttrString(py_wall_stat, "align", PyLong_FromLong(wall.stat.align));
        PyObject_SetAttrString(py_wall_stat, "xflip", PyLong_FromLong(wall.stat.xflip));
        PyObject_SetAttrString(py_wall_stat, "masking", PyLong_FromLong(wall.stat.masking));
        PyObject_SetAttrString(py_wall_stat, "one_way", PyLong_FromLong(wall.stat.one_way));
        PyObject_SetAttrString(py_wall_stat, "blocking2", PyLong_FromLong(wall.stat.blocking2));
        PyObject_SetAttrString(py_wall_stat, "translucent", PyLong_FromLong(wall.stat.translucent));
        PyObject_SetAttrString(py_wall_stat, "yflip", PyLong_FromLong(wall.stat.yflip));
        PyObject_SetAttrString(py_wall_stat, "translucent_rev", PyLong_FromLong(wall.stat.translucent_rev));
        PyObject_SetAttrString(py_wall_stat, "reserved", PyLong_FromLong(wall.stat.reserved));
        PyObject_SetAttrString(py_wall_stat, "poly_blue", PyLong_FromLong(wall.stat.poly_blue));
        PyObject_SetAttrString(py_wall_stat, "poly_green", PyLong_FromLong(wall.stat.poly_green));

        const BloodWallData *wall_data_ptr = &empty_wall_data;
        if (wall.tags[2] > 0)
        {
            wall_data_ptr = reinterpret_cast<const BloodWallData *>(&data[offset]);
            offset += sizeof(BloodWallData);
        }
        const BloodWallData &wall_data = *wall_data_ptr;

        PyObject *py_wall_data = PyObject_GetAttrString(py_wall, "data");

        PyObject_SetAttrString(py_wall_data, "data1", PyLong_FromLong(wall_data.data1));
        PyObject_SetAttrString(py_wall_data, "data2", PyLong_FromLong(wall_data.data2));
        PyObject_SetAttrString(py_wall_data, "state", PyLong_FromLong(wall_data.state));
        PyObject_SetAttrString(py_wall_data, "data3", PyLong_FromLong(wall_data.data3));

        load_int_list(PyObject_GetAttrString(py_wall_data, "data4"), wall_data.data4);

        PyObject_SetAttrString(py_wall_data, "data", PyLong_FromLong(wall_data.data));
        PyObject_SetAttrString(py_wall_data, "tx_id", PyLong_FromLong(wall_data.tx_id));
        PyObject_SetAttrString(py_wall_data, "data5", PyLong_FromLong(wall_data.data5));
        PyObject_SetAttrString(py_wall_data, "rx_id", PyLong_FromLong(wall_data.rx_id));
        PyObject_SetAttrString(py_wall_data, "cmd", PyLong_FromLong(wall_data.cmd));
        PyObject_SetAttrString(py_wall_data, "going_on", PyLong_FromLong(wall_data.going_on));
        PyObject_SetAttrString(py_wall_data, "going_off", PyLong_FromLong(wall_data.going_off));
        PyObject_SetAttrString(py_wall_data, "busy_time", PyLong_FromLong(wall_data.busy_time));
        PyObject_SetAttrString(py_wall_data, "wait_time", PyLong_FromLong(wall_data.wait_time));
        PyObject_SetAttrString(py_wall_data, "rest_state", PyLong_FromLong(wall_data.rest_state));
        PyObject_SetAttrString(py_wall_data, "interruptable", PyLong_FromLong(wall_data.interruptable));
        PyObject_SetAttrString(py_wall_data, "pan_always", PyLong_FromLong(wall_data.pan_always));
        PyObject_SetAttrString(py_wall_data, "panx", PyLong_FromLong(wall_data.panx));
        PyObject_SetAttrString(py_wall_data, "data8", PyLong_FromLong(wall_data.data8));
        PyObject_SetAttrString(py_wall_data, "pany", PyLong_FromLong(wall_data.pany));
        PyObject_SetAttrString(py_wall_data, "data9", PyLong_FromLong(wall_data.data9));
        PyObject_SetAttrString(py_wall_data, "decoupled", PyLong_FromLong(wall_data.decoupled));
        PyObject_SetAttrString(py_wall_data, "one_shot", PyLong_FromLong(wall_data.one_shot));
        PyObject_SetAttrString(py_wall_data, "data10", PyLong_FromLong(wall_data.data10));
        PyObject_SetAttrString(py_wall_data, "key", PyLong_FromLong(wall_data.key));
        PyObject_SetAttrString(py_wall_data, "push", PyLong_FromLong(wall_data.push));
        PyObject_SetAttrString(py_wall_data, "vector", PyLong_FromLong(wall_data.vector));
        PyObject_SetAttrString(py_wall_data, "reserved", PyLong_FromLong(wall_data.reserved));

        load_int_list(PyObject_GetAttrString(py_wall_data, "data11"), wall_data.data11);

        PyObject_SetAttrString(py_wall_data, "data12", PyLong_FromLong(wall_data.data12));
        PyObject_SetAttrString(py_wall_data, "locked", PyLong_FromLong(wall_data.locked));
        PyObject_SetAttrString(py_wall_data, "dude_lockout", PyLong_FromLong(wall_data.dude_lockout));
        PyObject_SetAttrString(py_wall_data, "data13", PyLong_FromLong(wall_data.data13));

        PyList_SetItem(result_walls, index, py_wall);
    }

    PyTuple_SetItem(result, 0, result_walls);
    PyTuple_SetItem(result, 1, PyLong_FromLong(offset));
    return result;
}

static PyMethodDef WallsMethods[] = {
    {"load_walls",
     walls_load_walls,
     METH_VARARGS,
     "Load walls for a map."},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef wallsmodule = {
    PyModuleDef_HEAD_INIT,
    "bloom.native.loader.walls",
    "bloom native map loading",
    -1,
    WallsMethods};

PyMODINIT_FUNC
PyInit_walls(void)
{
    return PyModule_Create(&wallsmodule);
}
