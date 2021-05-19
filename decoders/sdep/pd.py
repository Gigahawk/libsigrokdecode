
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
from binascii import hexlify


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
        ('msg_type', 'Message Type'),
        ('cmd_id', 'Command ID'),
        ('payload_len', 'Payload Length'),
        ('payload', 'Payload'),
    )
    annotation_rows = (
        ('mosi_packets', 'MOSI Packets', (0, 1, 2, 3,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.mosi_state = 'START'
        self.mosi_command_id = [None, None]
        self.mosi_command_id_ss = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def decode(self, ss, es, data):
        ptype, mosi, miso = data
        if ptype != 'DATA':
            return

        if self.mosi_state == 'START' and mosi == 0x10:
            self.put(ss, es, self.out_ann, [0, ['Command', 'cmd']])
            self.mosi_state = 'COMMAND_ID1'
            return

        if self.mosi_state == 'COMMAND_ID1':
            self.mosi_command_id[0] = mosi
            self.mosi_state = 'COMMAND_ID2'
            self.mosi_command_id_ss = ss
            return

        if self.mosi_state == 'COMMAND_ID2':
            self.mosi_command_id[1] = mosi
            cmd_id = hexlify(bytes(reversed(self.mosi_command_id))).decode()
            self.put(self.mosi_command_id_ss, es, self.out_ann, [1, ['Command ID: 0x{}'.format(cmd_id), 'cmd_id: {}'.format(cmd_id)]])
            self.mosi_state = 'PAYLOAD_LEN'
            return

        if self.mosi_state == 'PAYLOAD_LEN':
            more = int(bool(mosi & 0x80))
            payload_len = mosi & 0b11111
            self.put(ss, es, self.out_ann, [2, ['Payload Length: {}, More: {}'.format(payload_len, more), 'len: {}, more: {}'.format(payload_len, more)]])
            self.mosi_state = 'PAYLOAD'
            self.payload_len = payload_len
            return

        if self.mosi_state == 'PAYLOAD':
            self.payload_len -= 1
            self.put(ss, es, self.out_ann, [3, [chr(mosi)]])
            if self.payload_len == 0:
                self.mosi_state = 'START'
            return
