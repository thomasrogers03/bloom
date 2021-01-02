// Copyright 2020 Thomas Rogers
// SPDX-License-Identifier: Apache-2.0

#include "common.h"

typedef struct
{
    uint16_t blocking : 1;
    uint16_t translucent : 1;
    uint16_t xflip : 1;
    uint16_t yflip : 1;
    uint16_t facing : 2;
    uint16_t one_sided : 1;
    uint16_t centring : 1;
    uint16_t blocking2 : 1;
    uint16_t translucent_rev : 1;
    uint16_t reserved : 3;
    uint16_t poly_blue : 1;
    uint16_t poly_green : 1;
    uint16_t invisible : 1;
} Stat;

typedef struct
{
    int32_t position_x;
    int32_t position_y;
    int32_t position_z;
    Stat stat;
    int16_t picnum;
    int8_t shade;
    uint8_t palette;
    uint8_t clip_distance;
    uint8_t filler;
    uint8_t repeat_x;
    uint8_t repeat_y;
    int8_t offset_x;
    int8_t offset_y;
    int16_t sector_index;
    int16_t status_number;
    int16_t theta;
    int16_t owner;
    int16_t velocity_x;
    int16_t velocity_y;
    int16_t velocity_z;
    int16_t tags[3];
} BuildSprite;

typedef struct
{
    uint16_t sprite_actor_index : 14;
    uint16_t state : 1;
    uint16_t unknown2 : 1;

    uint8_t unknown3;
    uint8_t unknown4;

    uint32_t tx_id : 10;
    uint32_t rx_id : 10;
    uint32_t cmd : 8;
    uint32_t going_on : 1;
    uint32_t going_off : 1;
    uint32_t wave : 2;

    uint32_t busy_time : 12;
    uint32_t wait_time : 12;
    uint32_t rest_state : 1;
    uint32_t interruptable : 1;
    uint32_t unknown5 : 5;
    uint32_t launch_T : 1;

    uint8_t drop_item;

    uint16_t decoupled : 1;
    uint16_t one_shot : 1;
    uint16_t unknown6 : 1;
    uint16_t key : 3;
    uint16_t push : 1;
    uint16_t vector : 1;
    uint16_t impact : 1;
    uint16_t pickup : 1;
    uint16_t touch : 1;
    uint16_t sight : 1;
    uint16_t proximity : 1;
    uint16_t unknown7 : 2;
    uint16_t launch_1 : 1;

    uint8_t launch_2 : 1;
    uint8_t launch_3 : 1;
    uint8_t launch_4 : 1;
    uint8_t launch_5 : 1;
    uint8_t launch_S : 1;
    uint8_t launch_B : 1;
    uint8_t launch_C : 1;
    uint8_t dude_lockout : 1;

    uint16_t data1;
    uint16_t data2;
    uint16_t data3;
    uint8_t unknown8;

    uint8_t unknown9 : 5;
    uint8_t locked : 1;
    uint8_t unknown10 : 2;

    uint32_t respawn : 2;
    uint32_t data4 : 16;
    uint32_t unknown11 : 6;
    uint32_t lock_msg : 8;

    uint8_t unknown12;

    uint8_t unknown13 : 4;
    uint8_t dude_deaf : 1;
    uint8_t dude_ambush : 1;
    uint8_t dude_guard : 1;
    uint8_t reserved : 1;

    uint8_t unknown14[26];
} BloodSpriteData;

static PyObject *
sprites_load_sprites(PyObject *self, PyObject *args)
{
    PyObject *sprite_constructor;
    PyObject *data_bytes;
    uint64_t offset;
    uint64_t count;
    uint8_t key;

    if (!PyArg_ParseTuple(args, "OSKKb", &sprite_constructor, &data_bytes, &offset, &count, &key))
    {
        return NULL;
    }

    char *data = PyBytes_AsString(data_bytes);

    PyObject *result_sprites = PyList_New(count);
    PyObject *result = PyTuple_New(2);
    for (size_t index = 0; index < count; ++index)
    {
        crypt_buffer(&data[offset], sizeof(BuildSprite), key);

        const BuildSprite &sprite = *reinterpret_cast<const BuildSprite *>(&data[offset]);
        offset += sizeof(BuildSprite);

        PyObject *py_sprite = PyObject_Call(sprite_constructor, PyTuple_New(0), NULL);
        PyObject *py_build_sprite = PyObject_GetAttrString(py_sprite, "sprite");

        PyObject_SetAttrString(py_build_sprite, "position_x", PyLong_FromLong(sprite.position_x));
        PyObject_SetAttrString(py_build_sprite, "position_y", PyLong_FromLong(sprite.position_y));
        PyObject_SetAttrString(py_build_sprite, "position_z", PyLong_FromLong(sprite.position_z));
        PyObject_SetAttrString(py_build_sprite, "picnum", PyLong_FromLong(sprite.picnum));
        PyObject_SetAttrString(py_build_sprite, "shade", PyLong_FromLong(sprite.shade));
        PyObject_SetAttrString(py_build_sprite, "palette", PyLong_FromLong(sprite.palette));
        PyObject_SetAttrString(py_build_sprite, "clip_distance", PyLong_FromLong(sprite.clip_distance));
        PyObject_SetAttrString(py_build_sprite, "filler", PyLong_FromLong(sprite.filler));
        PyObject_SetAttrString(py_build_sprite, "repeat_x", PyLong_FromLong(sprite.repeat_x));
        PyObject_SetAttrString(py_build_sprite, "repeat_y", PyLong_FromLong(sprite.repeat_y));
        PyObject_SetAttrString(py_build_sprite, "offset_x", PyLong_FromLong(sprite.offset_x));
        PyObject_SetAttrString(py_build_sprite, "offset_y", PyLong_FromLong(sprite.offset_y));
        PyObject_SetAttrString(py_build_sprite, "sector_index", PyLong_FromLong(sprite.sector_index));
        PyObject_SetAttrString(py_build_sprite, "status_number", PyLong_FromLong(sprite.status_number));
        PyObject_SetAttrString(py_build_sprite, "theta", PyLong_FromLong(sprite.theta));
        PyObject_SetAttrString(py_build_sprite, "owner", PyLong_FromLong(sprite.owner));
        PyObject_SetAttrString(py_build_sprite, "velocity_x", PyLong_FromLong(sprite.velocity_x));
        PyObject_SetAttrString(py_build_sprite, "velocity_y", PyLong_FromLong(sprite.velocity_y));
        PyObject_SetAttrString(py_build_sprite, "velocity_z", PyLong_FromLong(sprite.velocity_z));

        load_int_list(PyObject_GetAttrString(py_build_sprite, "tags"), sprite.tags);

        PyObject *py_sprite_stat = PyObject_GetAttrString(py_build_sprite, "stat");

        PyObject_SetAttrString(py_sprite_stat, "blocking", PyLong_FromLong(sprite.stat.blocking));
        PyObject_SetAttrString(py_sprite_stat, "translucent", PyLong_FromLong(sprite.stat.translucent));
        PyObject_SetAttrString(py_sprite_stat, "xflip", PyLong_FromLong(sprite.stat.xflip));
        PyObject_SetAttrString(py_sprite_stat, "yflip", PyLong_FromLong(sprite.stat.yflip));
        PyObject_SetAttrString(py_sprite_stat, "facing", PyLong_FromLong(sprite.stat.facing));
        PyObject_SetAttrString(py_sprite_stat, "one_sided", PyLong_FromLong(sprite.stat.one_sided));
        PyObject_SetAttrString(py_sprite_stat, "centring", PyLong_FromLong(sprite.stat.centring));
        PyObject_SetAttrString(py_sprite_stat, "blocking2", PyLong_FromLong(sprite.stat.blocking2));
        PyObject_SetAttrString(py_sprite_stat, "translucent_rev", PyLong_FromLong(sprite.stat.translucent_rev));
        PyObject_SetAttrString(py_sprite_stat, "reserved", PyLong_FromLong(sprite.stat.reserved));
        PyObject_SetAttrString(py_sprite_stat, "poly_blue", PyLong_FromLong(sprite.stat.poly_blue));
        PyObject_SetAttrString(py_sprite_stat, "poly_green", PyLong_FromLong(sprite.stat.poly_green));
        PyObject_SetAttrString(py_sprite_stat, "invisible", PyLong_FromLong(sprite.stat.invisible));

        if (sprite.tags[2] > 0)
        {
            const BloodSpriteData &sprite_data = *reinterpret_cast<const BloodSpriteData *>(&data[offset]);
            offset += sizeof(BloodSpriteData);

            PyObject *py_sprite_data = PyObject_GetAttrString(py_sprite, "data");

            PyObject_SetAttrString(py_sprite_data, "sprite_actor_index", PyLong_FromLong(sprite_data.sprite_actor_index));
            PyObject_SetAttrString(py_sprite_data, "state", PyLong_FromLong(sprite_data.state));
            PyObject_SetAttrString(py_sprite_data, "unknown2", PyLong_FromLong(sprite_data.unknown2));
            PyObject_SetAttrString(py_sprite_data, "unknown3", PyLong_FromLong(sprite_data.unknown3));
            PyObject_SetAttrString(py_sprite_data, "unknown4", PyLong_FromLong(sprite_data.unknown4));
            PyObject_SetAttrString(py_sprite_data, "tx_id", PyLong_FromLong(sprite_data.tx_id));
            PyObject_SetAttrString(py_sprite_data, "rx_id", PyLong_FromLong(sprite_data.rx_id));
            PyObject_SetAttrString(py_sprite_data, "cmd", PyLong_FromLong(sprite_data.cmd));
            PyObject_SetAttrString(py_sprite_data, "going_on", PyLong_FromLong(sprite_data.going_on));
            PyObject_SetAttrString(py_sprite_data, "going_off", PyLong_FromLong(sprite_data.going_off));
            PyObject_SetAttrString(py_sprite_data, "wave", PyLong_FromLong(sprite_data.wave));
            PyObject_SetAttrString(py_sprite_data, "busy_time", PyLong_FromLong(sprite_data.busy_time));
            PyObject_SetAttrString(py_sprite_data, "wait_time", PyLong_FromLong(sprite_data.wait_time));
            PyObject_SetAttrString(py_sprite_data, "rest_state", PyLong_FromLong(sprite_data.rest_state));
            PyObject_SetAttrString(py_sprite_data, "interruptable", PyLong_FromLong(sprite_data.interruptable));
            PyObject_SetAttrString(py_sprite_data, "unknown5", PyLong_FromLong(sprite_data.unknown5));
            PyObject_SetAttrString(py_sprite_data, "launch_T", PyLong_FromLong(sprite_data.launch_T));
            PyObject_SetAttrString(py_sprite_data, "drop_item", PyLong_FromLong(sprite_data.drop_item));
            PyObject_SetAttrString(py_sprite_data, "decoupled", PyLong_FromLong(sprite_data.decoupled));
            PyObject_SetAttrString(py_sprite_data, "one_shot", PyLong_FromLong(sprite_data.one_shot));
            PyObject_SetAttrString(py_sprite_data, "unknown6", PyLong_FromLong(sprite_data.unknown6));
            PyObject_SetAttrString(py_sprite_data, "key", PyLong_FromLong(sprite_data.key));
            PyObject_SetAttrString(py_sprite_data, "push", PyLong_FromLong(sprite_data.push));
            PyObject_SetAttrString(py_sprite_data, "vector", PyLong_FromLong(sprite_data.vector));
            PyObject_SetAttrString(py_sprite_data, "impact", PyLong_FromLong(sprite_data.impact));
            PyObject_SetAttrString(py_sprite_data, "pickup", PyLong_FromLong(sprite_data.pickup));
            PyObject_SetAttrString(py_sprite_data, "touch", PyLong_FromLong(sprite_data.touch));
            PyObject_SetAttrString(py_sprite_data, "sight", PyLong_FromLong(sprite_data.sight));
            PyObject_SetAttrString(py_sprite_data, "proximity", PyLong_FromLong(sprite_data.proximity));
            PyObject_SetAttrString(py_sprite_data, "unknown7", PyLong_FromLong(sprite_data.unknown7));
            PyObject_SetAttrString(py_sprite_data, "launch_1", PyLong_FromLong(sprite_data.launch_1));
            PyObject_SetAttrString(py_sprite_data, "launch_2", PyLong_FromLong(sprite_data.launch_2));
            PyObject_SetAttrString(py_sprite_data, "launch_3", PyLong_FromLong(sprite_data.launch_3));
            PyObject_SetAttrString(py_sprite_data, "launch_4", PyLong_FromLong(sprite_data.launch_4));
            PyObject_SetAttrString(py_sprite_data, "launch_5", PyLong_FromLong(sprite_data.launch_5));
            PyObject_SetAttrString(py_sprite_data, "launch_S", PyLong_FromLong(sprite_data.launch_S));
            PyObject_SetAttrString(py_sprite_data, "launch_B", PyLong_FromLong(sprite_data.launch_B));
            PyObject_SetAttrString(py_sprite_data, "launch_C", PyLong_FromLong(sprite_data.launch_C));
            PyObject_SetAttrString(py_sprite_data, "dude_lockout", PyLong_FromLong(sprite_data.dude_lockout));
            PyObject_SetAttrString(py_sprite_data, "data1", PyLong_FromLong(sprite_data.data1));
            PyObject_SetAttrString(py_sprite_data, "data2", PyLong_FromLong(sprite_data.data2));
            PyObject_SetAttrString(py_sprite_data, "data3", PyLong_FromLong(sprite_data.data3));
            PyObject_SetAttrString(py_sprite_data, "unknown8", PyLong_FromLong(sprite_data.unknown8));
            PyObject_SetAttrString(py_sprite_data, "unknown9", PyLong_FromLong(sprite_data.unknown9));
            PyObject_SetAttrString(py_sprite_data, "locked", PyLong_FromLong(sprite_data.locked));
            PyObject_SetAttrString(py_sprite_data, "unknown10", PyLong_FromLong(sprite_data.unknown10));
            PyObject_SetAttrString(py_sprite_data, "respawn", PyLong_FromLong(sprite_data.respawn));
            PyObject_SetAttrString(py_sprite_data, "data4", PyLong_FromLong(sprite_data.data4));
            PyObject_SetAttrString(py_sprite_data, "unknown11", PyLong_FromLong(sprite_data.unknown11));
            PyObject_SetAttrString(py_sprite_data, "lock_msg", PyLong_FromLong(sprite_data.lock_msg));
            PyObject_SetAttrString(py_sprite_data, "unknown12", PyLong_FromLong(sprite_data.unknown12));
            PyObject_SetAttrString(py_sprite_data, "unknown13", PyLong_FromLong(sprite_data.unknown13));
            PyObject_SetAttrString(py_sprite_data, "dude_deaf", PyLong_FromLong(sprite_data.dude_deaf));
            PyObject_SetAttrString(py_sprite_data, "dude_ambush", PyLong_FromLong(sprite_data.dude_ambush));
            PyObject_SetAttrString(py_sprite_data, "dude_guard", PyLong_FromLong(sprite_data.dude_guard));
            PyObject_SetAttrString(py_sprite_data, "reserved", PyLong_FromLong(sprite_data.reserved));

            load_int_list(PyObject_GetAttrString(py_sprite_data, "unknown14"), sprite_data.unknown14);
        }

        PyList_SetItem(result_sprites, index, py_sprite);
    }

    PyTuple_SetItem(result, 0, result_sprites);
    PyTuple_SetItem(result, 1, PyLong_FromLong(offset));
    return result;
}

static PyMethodDef SpritesMethods[] = {
    {"load_sprites",
     sprites_load_sprites,
     METH_VARARGS,
     "Load sprites for a map."},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef spritesmodule = {
    PyModuleDef_HEAD_INIT,
    "bloom.native.loader.sprites",
    "bloom native map loading",
    -1,
    SpritesMethods};

PyMODINIT_FUNC
PyInit_sprites(void)
{
    return PyModule_Create(&spritesmodule);
}
