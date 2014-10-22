#!/usr/bin/env python
# encoding: utf-8
# Copyright (C) 2014 Space Science and Engineering Center (SSEC),
# University of Wisconsin-Madison.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file is part of the polar2grid software package. Polar2grid takes
# satellite observation data, remaps it, and writes it to a file format for
#     input into another program.
# Documentation: http://www.ssec.wisc.edu/software/polar2grid/
#
# Written by David Hoese    October 2014
# University of Wisconsin-Madison
# Space Science and Engineering Center
# 1225 West Dayton Street
# Madison, WI  53706
# david.hoese@ssec.wisc.edu
"""Connect various polar2grid components together to go from satellite data to output imagery format.

:author:       David Hoese (davidh)
:author:       Ray Garcia (rayg)
:contact:      david.hoese@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2014 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2014
:license:      GNU GPLv3

"""
__docformat__ = "restructuredtext en"

# from polar2grid.mirs import Frontend, add_frontend_argument_groups
from polar2grid.viirs.swath import Frontend as VIIRSFrontend, add_frontend_argument_groups as add_viirs_arguments
from polar2grid.remap import Remapper, add_remap_argument_groups
from polar2grid.gtiff_backend import Backend2 as GTiffBackend, add_backend_argument_groups as add_gtiff_arguments

import os
import sys
import logging

FRONTENDS = {
    "viirs": (add_viirs_arguments, VIIRSFrontend),
}


BACKENDS = {
    "gtiff": (add_gtiff_arguments, GTiffBackend),
}


def main(argv=sys.argv[1:]):
    # from argparse import ArgumentParser
    # init_parser = ArgumentParser(description="Extract swath data, remap it, and write it to a new file format")
    from polar2grid.core.script_utils import setup_logging, create_basic_parser, create_exc_handler, rename_log_file
    from argparse import ArgumentError
    parser = create_basic_parser(description="Extract swath data, remap it, and write it to a new file format")
    parser.add_argument("frontend", choices=FRONTENDS.keys(),
                        help="Specify the swath extractor to use to read data (additional arguments are determined after this is specified)")
    parser.add_argument("backend", choices=BACKENDS.keys(),
                        help="Specify the backend to use to write data output (additional arguments are determined after this is specified)")
    # don't include the help flag
    argv_without_help = [x for x in argv if x not in ["-h", "--help"]]
    args, remaining_args = parser.parse_known_args(argv_without_help)
    glue_name = args.frontend + "2" + args.backend
    LOG = logging.getLogger(glue_name)

    # add_frontend_arguments(parser)
    group_titles = []
    group_titles += FRONTENDS[args.frontend][0](parser)
    group_titles += add_remap_argument_groups(parser)
    group_titles += BACKENDS[args.backend][0](parser)
    parser.add_argument('-f', dest='data_files', nargs="+", default=[],
                        help="List of one or more data files")
    parser.add_argument('-d', dest='data_dirs', nargs="+", default=[],
                        help="Data directories to look for input data files")
    args = parser.parse_args(argv, subgroup_titles=group_titles)

    # Logs are renamed once data the provided start date is known
    rename_log = False
    if args.log_fn is None:
        rename_log = True
        args.log_fn = glue_name + "_fail.log"
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    setup_logging(console_level=levels[min(3, args.verbosity)], log_filename=args.log_fn)
    sys.excepthook = create_exc_handler(LOG.name)
    LOG.debug("Starting script with arguments: %s", " ".join(sys.argv))


    # Frontend
    LOG.info("Initializing swath extractor...")
    list_products = args.subgroup_args["Frontend Initialization"].pop("list_products")
    f = FRONTENDS[args.frontend][1](args.data_files + args.data_dirs, **args.subgroup_args["Frontend Initialization"])
    if list_products:
        print("\n".join(f.available_product_names))
        return 0

    LOG.info("Initializing remapping...")
    remapper = Remapper(**args.subgroup_args["Remapping Initialization"])
    remap_kwargs = args.subgroup_args["Remapping"]
    LOG.info("Initializing backend...")
    backend = BACKENDS[args.backend][1](**args.subgroup_args["Backend Initialization"])

    LOG.info("Extracting swaths from data files available...")
    scene = f.create_scene(**args.subgroup_args["Frontend Swath Extraction"])
    if args.keep_intermediate:
        scene.save(glue_name + "_swath_scene.json")

    # Rename the log file
    if rename_log:
        rename_log_file(glue_name + scene.get_begin_time().strftime("_%Y%m%d_%H%M%S.log"))

    # Remap
    gridded_scenes = {}
    # TODO: Grid determination
    for grid_name in remap_kwargs.pop("forced_grids"):
        LOG.info("Remapping to grid %s", grid_name)
        gridded_scene = remapper.remap_scene(scene, grid_name, **remap_kwargs)
        gridded_scenes[grid_name] = gridded_scene
        if args.keep_intermediate:
            gridded_scene.save(glue_name + "_gridded_scene_" + grid_name + ".json")

        # Backend
        try:
            LOG.info("Creating output from data mapped to grid %s", grid_name)
            backend.create_output_from_scene(gridded_scene, **args.subgroup_args["Backend Output Creation"])
        except StandardError:
            LOG.error("Could not create output, see log for more info.")
            LOG.debug("Backend exception: ", exc_info=True)
            continue

    return 0

if __name__ == "__main__":
    sys.exit(main())
