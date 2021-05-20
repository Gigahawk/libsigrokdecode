
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

class SdepStateMachine:
    def __init__(self, annotations):
        self.annotations = annotations
        self.reset()

    def reset(self):
        self.state = 'START'
        self.command_id = [None, None]
        self.command_id_ss = None
        self.payload_len = None
        self.ss = None
        self.es = None

    def message_type(self, code):
        if code == 0x10:
            return ['Command', 'cmd']
        if code == 0x20:
            return ['Response', 'rsp']
        if code == 0x40:
            return ['Alert', 'alr']
        if code == 0x80:
            return ['Error', 'err']
        return None

    def decode(self, ss, es, b):
        if self.state == 'START':
            message_type = self.message_type(b)
            if not message_type:
                return None, None
            self.state = 'COMMAND_ID1'
            self.ss = ss
            self.es = es
            return self.annotations[0], message_type

        if self.state == 'COMMAND_ID1':
            self.command_id[0] = b
            self.state = 'COMMAND_ID2'
            self.ss = ss
            return None, None

        if self.state == 'COMMAND_ID2':
            self.command_id[1] = b
            cmd_id = hexlify(bytes(reversed(self.command_id))).decode()
            self.state = 'PAYLOAD_LEN'
            self.es = es
            return (
                self.annotations[1],
                [
                    'Command ID: 0x{}'.format(cmd_id),
                    'cmd_id: {}'.format(cmd_id)
                ]
            )

        if self.state == 'PAYLOAD_LEN':
            more = int(bool(b & 0x80))
            payload_len = b & 0b11111
            self.payload_len = payload_len
            self.state = 'PAYLOAD'
            self.ss = ss
            self.es = es
            return (
                self.annotations[2],
                [
                    'Payload Length: {}, More: {}'.format(payload_len, more),
                    'len: {}, more: {}'.format(payload_len, more)
                ]
            )

        if self.state == 'PAYLOAD':
            self.payload_len -= 1
            char = repr(chr(b)).strip("'")
            if self.payload_len <= 0:
                self.state = 'START'
            self.ss = ss
            self.es = es
            return self.annotations[3], char

MOSI_ROWS = (0, 1, 2, 3)
MISO_ROWS = (4, 5, 6, 7)

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
        ('mosi_msg_type', 'MOSI Message Type'),
        ('mosi_cmd_id', 'MOSI Command ID'),
        ('mosi_payload_len', 'MOSI Payload Length'),
        ('mosi_payload', 'MOSI Payload'),
        ('miso_msg_type', 'MISO Message Type'),
        ('miso_cmd_id', 'MISO Command ID'),
        ('miso_payload_len', 'MISO Payload Length'),
        ('miso_payload', 'MISO Payload'),
    )
    annotation_rows = (
        ('mosi_packets', 'MOSI Packets', MISO_ROWS),
        ('miso_packets', 'MISO Packets', MOSI_ROWS),
    )

    def __init__(self):
        self.reset()

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def reset(self):
        self.mosi_state_machine = SdepStateMachine(MOSI_ROWS)
        self.miso_state_machine = SdepStateMachine(MISO_ROWS)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def decode(self, ss, es, data):
        ptype, mosi, miso = data
        if ptype != 'DATA':
            return
        self.put(ss, es, self.out_ann, [0, ['a']])

        mosi_anno, mosi_data = self.mosi_state_machine.decode(ss, es, mosi)
        miso_anno, miso_data = self.miso_state_machine.decode(ss, es, miso)

        if mosi_anno:
            self.put(
                self.mosi_state_machine.ss,
                self.mosi_state_machine.es,
                self.out_ann, [mosi_anno, mosi_data])
        if miso_anno:
            self.put(
                self.miso_state_machine.ss,
                self.miso_state_machine.es,
                self.out_ann, [miso_anno, miso_data])
