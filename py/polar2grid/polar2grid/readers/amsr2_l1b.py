#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2016 Space Science and Engineering Center (SSEC),
#  University of Wisconsin-Madison.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
# input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
#     Written by David Hoese    August 2016
#     University of Wisconsin-Madison
#     Space Science and Engineering Center
#     1225 West Dayton Street
#     Madison, WI  53706
#     david.hoese@ssec.wisc.edu
"""AMSR2 L1B files contain various parameters from the GCOM-W1 AMSR2
instrument. This reader can be used by specifying the reader name
``amsr2_l1b`` to the ``polar2grid.sh`` script.
Supported files usually have the following naming scheme::

    GW1AM2_201607201808_128A_L1DLBTBR_1110110.h5

This reader's default remapping algorithm is ``nearest`` for nearest
neighbor resampling due to the instruments scan pattern and swath shape.
The ``--distance_upper_bound`` flag defaults to 12.

Currently this reader provides only the following datasets:

+---------------------------+-----------------------------------------------------------+
| Product Name              | Description                                               |
+===========================+===========================================================+
| btemp_36.5v               | Brightness Temperature 36.5GHz Polarization Vertical      |
+---------------------------+-----------------------------------------------------------+
| btemp_36.5h               | Brightness Temperature 36.5GHz Polarization Horizontal    |
+---------------------------+-----------------------------------------------------------+
| btemp_89.0av              | Brightness Temperature 89.0GHz A Polarization Vertical    |
+---------------------------+-----------------------------------------------------------+
| btemp_89.0ah              | Brightness Temperature 89.0GHz A Polarization Horizontal  |
+---------------------------+-----------------------------------------------------------+
| btemp_89.0bv              | Brightness Temperature 89.0GHz B Polarization Vertical    |
+---------------------------+-----------------------------------------------------------+
| btemp_89.0bh              | Brightness Temperature 89.0GHz B Polarization Horizontal  |
+---------------------------+-----------------------------------------------------------+

Special AMSR2 Naval Research Lab (NRL) PNG Scaling
--------------------------------------------------

A common use case for the AMSR2 L1B reader is to generate PNG images similar
to those generated by the U.S. Naval Research Lab (NRL) with a colormap and
coastlines. This requires using an alternate non-default scaling configuration
provided in the tarball. It can be used by providing the
``--rescale-configs $POLAR2GRID_HOME/rescale_configs/amsr2_png.ini``
flag when generating AMSR2 L1B GeoTIFFs.
Once this rescaling has been done, colormap files can be found in 
``$POLAR2GRID_HOME/colormaps`` which can then be applied using the
the `add_colormap.sh` script.

See the :ref:`util_add_coastlines` and :ref:`util_add_colormap` documentation
for more information on generating these NRL-like PNGs.

"""
__docformat__ = "restructuredtext en"

import sys

import logging
from polar2grid.readers import ReaderWrapper, main

LOG = logging.getLogger(__name__)

DEFAULT_CHANNELS = [
    # "btemp_10.7v",
    # "btemp_10.7h",
    "btemp_36.5v",
    "btemp_36.5h",
    "btemp_89.0av",
    "btemp_89.0ah",
    "btemp_89.0bv",
    "btemp_89.0bh",
]


class Frontend(ReaderWrapper):
    FILE_EXTENSIONS = [".h5"]
    DEFAULT_READER_NAME = "amsr2_l1b"
    DEFAULT_DATASETS = DEFAULT_CHANNELS
    PRIMARY_FILE_TYPE = "amsr2_l1b"


def add_frontend_argument_groups(parser):
    """Add command line arguments to an existing parser.

    :returns: list of group titles added
    """
    from polar2grid.core import ExtendAction
    # Set defaults for other components that may be used in polar2grid processing
    parser.set_defaults(fornav_D=10, fornav_d=1, remap_method="nearest", distance_upper_bound=12)

    # Use the append_const action to handle adding products to the list
    group_title = "Frontend Initialization"
    group = parser.add_argument_group(title=group_title, description="swath extraction initialization options")
    group.add_argument("--list-products", dest="list_products", action="store_true",
                       help="List available frontend products and exit")
    # group.add_argument("--no-tc", dest="use_terrain_corrected", action="store_false",
    #                    help="Don't use terrain-corrected navigation")
    # group.add_argument("--day-fraction", dest="day_fraction", type=float, default=float(os.environ.get("P2G_DAY_FRACTION", 0.10)),
    #                    help="Fraction of day required to produce reflectance products (default 0.10)")
    # group.add_argument("--night-fraction", dest="night_fraction", type=float, default=float(os.environ.get("P2G_NIGHT_FRACTION", 0.10)),
    #                    help="Fraction of night required to product products like fog (default 0.10)")
    # group.add_argument("--sza-threshold", dest="sza_threshold", type=float, default=float(os.environ.get("P2G_SZA_THRESHOLD", 100)),
    #                    help="Angle threshold of solar zenith angle used when deciding day or night (default 100)")
    # group.add_argument("--dnb-saturation-correction", action="store_true",
    #                    help="Enable dynamic DNB saturation correction (normally used for aurora scenes)")
    group_title = "Frontend Swath Extraction"
    group = parser.add_argument_group(title=group_title, description="swath extraction options")
    group.add_argument("-p", "--products", dest="products", nargs="+", default=None, action=ExtendAction,
                       help="Specify frontend products to process")
    return ["Frontend Initialization", "Frontend Swath Extraction"]

if __name__ == "__main__":
    sys.exit(main(description="Extract VIIRS L1B swath data into binary files",
                  add_argument_groups=add_frontend_argument_groups))
