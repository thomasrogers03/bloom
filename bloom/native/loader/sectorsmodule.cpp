// Copyright 2020 Thomas Rogers
// SPDX-License-Identifier: Apache-2.0

#define PY_SSIZE_T_CLEAN

#include "common.h"

typedef struct
{
    uint16_t parallax : 1;
    uint16_t groudraw : 1;
    uint16_t swapxy : 1;
    uint16_t expand : 1;
    uint16_t xflip : 1;
    uint16_t yflip : 1;
    uint16_t align : 1;
    uint16_t masking : 2;
    uint16_t reserved : 7;
} Stat;

typedef struct
{
    int16_t first_wall_index;
    int16_t wall_count;
    int32_t ceiling_z;
    int32_t floor_z;
    Stat ceiling_stat;
    Stat floor_stat;

    int16_t ceiling_picnum;
    int16_t ceiling_heinum;
    int8_t ceiling_shade;
    uint8_t ceiling_palette;
    uint8_t ceiling_xpanning;
    uint8_t ceiling_ypanning;
    int16_t floor_picnum;
    int16_t floor_heinum;
    int8_t floor_shade;
    uint8_t floor_palette;
    uint8_t floor_xpanning;
    uint8_t floor_ypanning;
    uint8_t visibility;
    uint8_t filler;
    int16_t tags[3];
} BuildSector;

typedef struct
{

    uint8_t unknown;

    uint8_t data2 : 6;
    uint8_t state : 1;
    uint8_t unknown2 : 1;

    uint8_t unknown3[2];

    uint16_t data;

    uint16_t tx_id : 10;
    uint16_t on_wave : 3;
    uint16_t off_wave : 3;

    uint32_t rx_id : 10;
    uint32_t cmd : 8;
    uint32_t send_at_on : 1;
    uint32_t send_at_off : 1;
    uint32_t on_busy_time : 8;
    uint32_t compressed2 : 4;

    uint8_t on_wait_time;

    uint32_t unknown4 : 5;
    uint32_t interruptable : 1;
    uint32_t light_amplitude : 8;
    uint32_t light_frequency : 8;
    uint32_t on_wait_set : 1;
    uint32_t off_wait_set : 1;
    uint32_t light_phase : 8;

    uint8_t light_wave : 4;
    uint8_t shade_always : 1;
    uint8_t light_floor : 1;
    uint8_t light_ceiling : 1;
    uint8_t light_walls : 1;

    uint8_t unknown5;

    uint8_t pan_always : 1;
    uint8_t pan_floor : 1;
    uint8_t pan_ceiling : 1;
    uint8_t drag : 1;
    uint8_t underwater : 1;
    uint8_t depth : 3;

    uint32_t speed : 8;
    uint32_t angle : 11;
    uint32_t unknown6 : 1;
    uint32_t decoupled : 1;
    uint32_t one_shot : 1;
    uint32_t unknown7 : 1;
    uint32_t key : 3;
    uint32_t trigger_push : 1;
    uint32_t trigger_vector : 1;
    uint32_t reserved : 1;
    uint32_t trigger_enter : 1;
    uint32_t trigger_exit : 1;
    uint32_t trigger_wall_push : 1;

    uint32_t colour_lights : 1;
    uint32_t unknown8 : 1;
    uint32_t off_busy_time : 8;
    uint32_t unknown9 : 4;
    uint32_t off_wait_time : 8;
    uint32_t unknown10 : 2;
    uint32_t unknown11 : 4;
    uint32_t ceiling_palette2 : 4;

    int32_t ceiling_zmotion[2];
    int32_t floor_zmotion[2];
    int16_t markers[2];

    uint8_t crush : 1;
    uint8_t unknown12 : 7;

    uint8_t unknown13[2];

    uint8_t unknown14 : 1;
    uint8_t damage_type : 3;
    uint8_t flooring_palette2 : 4;

    uint32_t unknown15 : 8;
    uint32_t locked : 1;
    uint32_t wind_vel : 10;
    uint32_t wind_ang : 11;
    uint32_t wind_always : 1;
    uint32_t dude_lockout : 1;

    uint32_t theta : 11;
    uint32_t z_range : 5;
    uint32_t speed2 : 11;
    uint32_t unknown16 : 1;
    uint32_t move_always : 1;
    uint32_t bob_floor : 1;
    uint32_t bob_ceiling : 1;
    uint32_t rotate : 1;
} BloodSectorData;

static void load_stat(PyObject *py_stat, const Stat &stat)
{
    PyObject_SetAttrString(py_stat, "parallax", PyLong_FromLong(stat.parallax));
    PyObject_SetAttrString(py_stat, "groudraw", PyLong_FromLong(stat.groudraw));
    PyObject_SetAttrString(py_stat, "swapxy", PyLong_FromLong(stat.swapxy));
    PyObject_SetAttrString(py_stat, "expand", PyLong_FromLong(stat.expand));
    PyObject_SetAttrString(py_stat, "xflip", PyLong_FromLong(stat.xflip));
    PyObject_SetAttrString(py_stat, "yflip", PyLong_FromLong(stat.yflip));
    PyObject_SetAttrString(py_stat, "align", PyLong_FromLong(stat.align));
    PyObject_SetAttrString(py_stat, "masking", PyLong_FromLong(stat.masking));
    PyObject_SetAttrString(py_stat, "reserved", PyLong_FromLong(stat.reserved));
}

static PyObject *
sectors_load_sectors(PyObject *self, PyObject *args)
{
    PyObject *sector_constructor;
    PyObject *data_bytes;
    uint64_t offset;
    uint64_t count;
    uint8_t key;

    if (!PyArg_ParseTuple(args, "OSKKb", &sector_constructor, &data_bytes, &offset, &count, &key))
    {
        return NULL;
    }

    char *data = PyBytes_AsString(data_bytes);

    PyObject *result_sectors = PyList_New(count);
    PyObject *result = PyTuple_New(2);
    for (size_t index = 0; index < count; ++index)
    {
        crypt_buffer(&data[offset], sizeof(BuildSector), key);

        const BuildSector &sector = *reinterpret_cast<const BuildSector *>(&data[offset]);
        offset += sizeof(BuildSector);

        PyObject *py_sector = PyObject_Call(sector_constructor, PyTuple_New(0), NULL);
        PyObject *py_build_sector = PyObject_GetAttrString(py_sector, "sector");

        PyObject_SetAttrString(py_build_sector, "first_wall_index", PyLong_FromLong(sector.first_wall_index));
        PyObject_SetAttrString(py_build_sector, "wall_count", PyLong_FromLong(sector.wall_count));
        PyObject_SetAttrString(py_build_sector, "ceiling_z", PyLong_FromLong(sector.ceiling_z));
        PyObject_SetAttrString(py_build_sector, "floor_z", PyLong_FromLong(sector.floor_z));

        PyObject_SetAttrString(py_build_sector, "ceiling_picnum", PyLong_FromLong(sector.ceiling_picnum));
        PyObject_SetAttrString(py_build_sector, "ceiling_heinum", PyLong_FromLong(sector.ceiling_heinum));
        PyObject_SetAttrString(py_build_sector, "ceiling_shade", PyLong_FromLong(sector.ceiling_shade));
        PyObject_SetAttrString(py_build_sector, "ceiling_palette", PyLong_FromLong(sector.ceiling_palette));
        PyObject_SetAttrString(py_build_sector, "ceiling_xpanning", PyLong_FromLong(sector.ceiling_xpanning));
        PyObject_SetAttrString(py_build_sector, "ceiling_ypanning", PyLong_FromLong(sector.ceiling_ypanning));
        PyObject_SetAttrString(py_build_sector, "floor_picnum", PyLong_FromLong(sector.floor_picnum));
        PyObject_SetAttrString(py_build_sector, "floor_heinum", PyLong_FromLong(sector.floor_heinum));
        PyObject_SetAttrString(py_build_sector, "floor_shade", PyLong_FromLong(sector.floor_shade));
        PyObject_SetAttrString(py_build_sector, "floor_palette", PyLong_FromLong(sector.floor_palette));
        PyObject_SetAttrString(py_build_sector, "floor_xpanning", PyLong_FromLong(sector.floor_xpanning));
        PyObject_SetAttrString(py_build_sector, "floor_ypanning", PyLong_FromLong(sector.floor_ypanning));
        PyObject_SetAttrString(py_build_sector, "visibility", PyLong_FromLong(sector.visibility));
        PyObject_SetAttrString(py_build_sector, "filler", PyLong_FromLong(sector.filler));

        load_int_list(PyObject_GetAttrString(py_build_sector, "tags"), sector.tags);

        load_stat(PyObject_GetAttrString(py_build_sector, "floor_stat"), sector.floor_stat);
        load_stat(PyObject_GetAttrString(py_build_sector, "ceiling_stat"), sector.ceiling_stat);

        if (sector.tags[2] > 0)
        {
            const BloodSectorData &sector_data = *reinterpret_cast<const BloodSectorData *>(&data[offset]);
            offset += sizeof(BloodSectorData);

            PyObject *py_sector_data = PyObject_GetAttrString(py_sector, "data");

            PyObject_SetAttrString(py_sector_data, "unknown", PyLong_FromLong(sector_data.unknown));
            PyObject_SetAttrString(py_sector_data, "data2", PyLong_FromLong(sector_data.data2));
            PyObject_SetAttrString(py_sector_data, "state", PyLong_FromLong(sector_data.state));
            PyObject_SetAttrString(py_sector_data, "unknown2", PyLong_FromLong(sector_data.unknown2));

            load_int_list(PyObject_GetAttrString(py_sector_data, "unknown3"), sector_data.unknown3);

            PyObject_SetAttrString(py_sector_data, "data", PyLong_FromLong(sector_data.data));
            PyObject_SetAttrString(py_sector_data, "tx_id", PyLong_FromLong(sector_data.tx_id));
            PyObject_SetAttrString(py_sector_data, "on_wave", PyLong_FromLong(sector_data.on_wave));
            PyObject_SetAttrString(py_sector_data, "off_wave", PyLong_FromLong(sector_data.off_wave));
            PyObject_SetAttrString(py_sector_data, "rx_id", PyLong_FromLong(sector_data.rx_id));
            PyObject_SetAttrString(py_sector_data, "cmd", PyLong_FromLong(sector_data.cmd));
            PyObject_SetAttrString(py_sector_data, "send_at_on", PyLong_FromLong(sector_data.send_at_on));
            PyObject_SetAttrString(py_sector_data, "send_at_off", PyLong_FromLong(sector_data.send_at_off));
            PyObject_SetAttrString(py_sector_data, "on_busy_time", PyLong_FromLong(sector_data.on_busy_time));
            PyObject_SetAttrString(py_sector_data, "compressed2", PyLong_FromLong(sector_data.compressed2));
            PyObject_SetAttrString(py_sector_data, "on_wait_time", PyLong_FromLong(sector_data.on_wait_time));
            PyObject_SetAttrString(py_sector_data, "unknown4", PyLong_FromLong(sector_data.unknown4));
            PyObject_SetAttrString(py_sector_data, "interruptable", PyLong_FromLong(sector_data.interruptable));
            PyObject_SetAttrString(py_sector_data, "light_amplitude", PyLong_FromLong(sector_data.light_amplitude));
            PyObject_SetAttrString(py_sector_data, "light_frequency", PyLong_FromLong(sector_data.light_frequency));
            PyObject_SetAttrString(py_sector_data, "on_wait_set", PyLong_FromLong(sector_data.on_wait_set));
            PyObject_SetAttrString(py_sector_data, "off_wait_set", PyLong_FromLong(sector_data.off_wait_set));
            PyObject_SetAttrString(py_sector_data, "light_phase", PyLong_FromLong(sector_data.light_phase));
            PyObject_SetAttrString(py_sector_data, "light_wave", PyLong_FromLong(sector_data.light_wave));
            PyObject_SetAttrString(py_sector_data, "shade_always", PyLong_FromLong(sector_data.shade_always));
            PyObject_SetAttrString(py_sector_data, "light_floor", PyLong_FromLong(sector_data.light_floor));
            PyObject_SetAttrString(py_sector_data, "light_ceiling", PyLong_FromLong(sector_data.light_ceiling));
            PyObject_SetAttrString(py_sector_data, "light_walls", PyLong_FromLong(sector_data.light_walls));
            PyObject_SetAttrString(py_sector_data, "unknown5", PyLong_FromLong(sector_data.unknown5));
            PyObject_SetAttrString(py_sector_data, "pan_always", PyLong_FromLong(sector_data.pan_always));
            PyObject_SetAttrString(py_sector_data, "pan_floor", PyLong_FromLong(sector_data.pan_floor));
            PyObject_SetAttrString(py_sector_data, "pan_ceiling", PyLong_FromLong(sector_data.pan_ceiling));
            PyObject_SetAttrString(py_sector_data, "drag", PyLong_FromLong(sector_data.drag));
            PyObject_SetAttrString(py_sector_data, "underwater", PyLong_FromLong(sector_data.underwater));
            PyObject_SetAttrString(py_sector_data, "depth", PyLong_FromLong(sector_data.depth));
            PyObject_SetAttrString(py_sector_data, "speed", PyLong_FromLong(sector_data.speed));
            PyObject_SetAttrString(py_sector_data, "angle", PyLong_FromLong(sector_data.angle));
            PyObject_SetAttrString(py_sector_data, "unknown6", PyLong_FromLong(sector_data.unknown6));
            PyObject_SetAttrString(py_sector_data, "decoupled", PyLong_FromLong(sector_data.decoupled));
            PyObject_SetAttrString(py_sector_data, "one_shot", PyLong_FromLong(sector_data.one_shot));
            PyObject_SetAttrString(py_sector_data, "unknown7", PyLong_FromLong(sector_data.unknown7));
            PyObject_SetAttrString(py_sector_data, "key", PyLong_FromLong(sector_data.key));
            PyObject_SetAttrString(py_sector_data, "trigger_push", PyLong_FromLong(sector_data.trigger_push));
            PyObject_SetAttrString(py_sector_data, "trigger_vector", PyLong_FromLong(sector_data.trigger_vector));
            PyObject_SetAttrString(py_sector_data, "reserved", PyLong_FromLong(sector_data.reserved));
            PyObject_SetAttrString(py_sector_data, "trigger_enter", PyLong_FromLong(sector_data.trigger_enter));
            PyObject_SetAttrString(py_sector_data, "trigger_exit", PyLong_FromLong(sector_data.trigger_exit));
            PyObject_SetAttrString(py_sector_data, "trigger_wall_push", PyLong_FromLong(sector_data.trigger_wall_push));
            PyObject_SetAttrString(py_sector_data, "colour_lights", PyLong_FromLong(sector_data.colour_lights));
            PyObject_SetAttrString(py_sector_data, "unknown8", PyLong_FromLong(sector_data.unknown8));
            PyObject_SetAttrString(py_sector_data, "off_busy_time", PyLong_FromLong(sector_data.off_busy_time));
            PyObject_SetAttrString(py_sector_data, "unknown9", PyLong_FromLong(sector_data.unknown9));
            PyObject_SetAttrString(py_sector_data, "off_wait_time", PyLong_FromLong(sector_data.off_wait_time));
            PyObject_SetAttrString(py_sector_data, "unknown10", PyLong_FromLong(sector_data.unknown10));
            PyObject_SetAttrString(py_sector_data, "unknown11", PyLong_FromLong(sector_data.unknown11));
            PyObject_SetAttrString(py_sector_data, "ceiling_palette2", PyLong_FromLong(sector_data.ceiling_palette2));

            load_int_list(PyObject_GetAttrString(py_sector_data, "ceiling_zmotion"), sector_data.ceiling_zmotion);
            load_int_list(PyObject_GetAttrString(py_sector_data, "floor_zmotion"), sector_data.floor_zmotion);
            load_int_list(PyObject_GetAttrString(py_sector_data, "markers"), sector_data.markers);

            PyObject_SetAttrString(py_sector_data, "crush", PyLong_FromLong(sector_data.crush));
            PyObject_SetAttrString(py_sector_data, "unknown12", PyLong_FromLong(sector_data.unknown12));

            load_int_list(PyObject_GetAttrString(py_sector_data, "unknown13"), sector_data.unknown13);

            PyObject_SetAttrString(py_sector_data, "unknown14", PyLong_FromLong(sector_data.unknown14));
            PyObject_SetAttrString(py_sector_data, "damage_type", PyLong_FromLong(sector_data.damage_type));
            PyObject_SetAttrString(py_sector_data, "flooring_palette2", PyLong_FromLong(sector_data.flooring_palette2));
            PyObject_SetAttrString(py_sector_data, "unknown15", PyLong_FromLong(sector_data.unknown15));
            PyObject_SetAttrString(py_sector_data, "locked", PyLong_FromLong(sector_data.locked));
            PyObject_SetAttrString(py_sector_data, "wind_vel", PyLong_FromLong(sector_data.wind_vel));
            PyObject_SetAttrString(py_sector_data, "wind_ang", PyLong_FromLong(sector_data.wind_ang));
            PyObject_SetAttrString(py_sector_data, "wind_always", PyLong_FromLong(sector_data.wind_always));
            PyObject_SetAttrString(py_sector_data, "dude_lockout", PyLong_FromLong(sector_data.dude_lockout));
            PyObject_SetAttrString(py_sector_data, "theta", PyLong_FromLong(sector_data.theta));
            PyObject_SetAttrString(py_sector_data, "z_range", PyLong_FromLong(sector_data.z_range));
            PyObject_SetAttrString(py_sector_data, "speed2", PyLong_FromLong(sector_data.speed2));
            PyObject_SetAttrString(py_sector_data, "unknown16", PyLong_FromLong(sector_data.unknown16));
            PyObject_SetAttrString(py_sector_data, "move_always", PyLong_FromLong(sector_data.move_always));
            PyObject_SetAttrString(py_sector_data, "bob_floor", PyLong_FromLong(sector_data.bob_floor));
            PyObject_SetAttrString(py_sector_data, "bob_ceiling", PyLong_FromLong(sector_data.bob_ceiling));
            PyObject_SetAttrString(py_sector_data, "rotate", PyLong_FromLong(sector_data.rotate));
        }

        PyList_SetItem(result_sectors, index, py_sector);
    }

    PyTuple_SetItem(result, 0, result_sectors);
    PyTuple_SetItem(result, 1, PyLong_FromLong(offset));
    return result;
}

static PyMethodDef SectorsMethods[] = {
    {"load_sectors",
     sectors_load_sectors,
     METH_VARARGS,
     "Load sectors for a map."},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef sectorsmodule = {
    PyModuleDef_HEAD_INIT,
    "bloom.native.loader.sectors",
    "bloom native map loading",
    -1,
    SectorsMethods};

PyMODINIT_FUNC
PyInit_sectors(void)
{
    return PyModule_Create(&sectorsmodule);
}
