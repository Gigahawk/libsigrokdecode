
##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019-2020 Philip Åkesson <philip.akesson@gmail.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd


class Decoder(srd.Decoder):
    api_version = 3
    id = 'sdep'
    name = 'SDEP'
    longname = 'Simple Data Exchange Protocol'
    desc = 'Bus netural data exchange protocol used by Adafruit modules'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['Adafruit']
    annotations = (
        ('packet_type', 'Packet type'),
    )
    annotation_rows = (
        ('data', 'Data', (0,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.mosi_state = 'START'

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def decode(self, ss, es, data):
        ptype, mosi, miso = data
        self.put(ss, es, self.out_ann, [0, ['AAAA', 'AA']])