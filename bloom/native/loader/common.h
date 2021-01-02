#pragma once

#include <Python.h>
#include <cstdint>

template <typename T, size_t N>
inline void load_int_list(PyObject *py_list, T (&list)[N])
{
    for (size_t index = 0; index < N; ++index)
    {
        PyList_SetItem(py_list, index, PyLong_FromLong(list[index]));
    }
}

inline void crypt_buffer(char *data, size_t length, uint8_t key)
{
    for (size_t index = 0; index < length; ++index)
    {
        data[index] ^= (key + index) & 0xFF;
    }
}
