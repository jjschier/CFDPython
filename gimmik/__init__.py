# -*- coding: utf-8 -*-

import pkgutil
import re

from mako.template import Template
import numpy as np

from gimmik._version import __version__


def generate_mm(mat, dtype, platform, alpha=1.0, beta=0.0, tol=1e-10,
                funcn='gimmik_mm'):
    # Data type
    dtype = np.dtype(dtype).type
    if dtype == np.float32:
        dtype = 'float'
    elif dtype == np.float64:
        dtype = 'double'
    else:
        raise ValueError('Invalid floating point data type')

    # Multiply the matrix through by alpha
    mat = alpha*mat

    # Clamp small elements
    mat[abs(mat) < tol] = 0

    # Coalesce similar elements
    amfl = np.abs(mat.flat)
    amix = np.argsort(amfl)

    i, ix = 0, amix[0]
    for j, jx in enumerate(amix[1:], start=1):
        if amfl[jx] - amfl[ix] >= tol:
            if j - i > 1:
                amfl[amix[i:j]] = np.median(amfl[amix[i:j]])
            i, ix = j, jx

    if i != j:
        amfl[amix[i:]] = np.median(amfl[amix[i:]])

    # Fix up the signs and assign
    mat.flat = np.copysign(amfl, mat.flat)

    # Load and render the template
    tpl = pkgutil.get_data(__name__, 'kernels/{0}.mako'.format(platform))
    src = Template(tpl).render(dtype=dtype, mat=mat, beta=beta, funcn=funcn)

    # At single precision suffix all floating point constants by 'f'
    if dtype == 'float':
        src = re.sub(r'(?=\d*[.eE])(?=\.?\d)\d*\.?\d*(?:[eE][+-]?\d+)?',
                     r'\g<0>f', src)

    # Return the source
    return src
