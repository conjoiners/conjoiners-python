"""
Conjoiners module
"""
__version__ = '0.1'

#
# This file is part of conjoiners
#
# Copyright (c) 2013 by Pavlo Baron (pb at pbit dot org)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import gevent
import zmq.green as zmq
import time
import json

IMPLANTS = "conjoiners_implants"
CTX = "conjoiners_ctx"
EXTS = "conjoiners_ext_sock"
BIND_PFX = "inproc://conjoiners_internal"
RECV = "conjoiners_recv_objs"
SET = "set_"

# TODO: add "interested in" to conf - only these fields will be broadcasted
# to this conjoiner (or filtered by it)

# wrapper function
def implant(o, cfg_file, my_name):
    f = open(cfg_file, "r")
    conf = json.load(f)

    # overridden getter
    def get_it(self, n):
        # simply return the current value
        # TODO: check if have to take care of thready-safety of unimpletnted objects here
        if self.__dict__.has_key(n):
            return self.__dict__[n]
        else:
            return None

    # overridden setter
    def set_it(self, n, v):
        # simply update the current value
        # TODO: check if have to take care of thread-safety of unimpletnted objects here
        self.__dict__[n] = v
        if id(self) in self.__class__.__dict__[IMPLANTS]:
            # multicast
            ext_sock = ensure_external_bind(self)
            ext_sock.send_json(pack_payload_single(n, v), zmq.NOBLOCK)

    # override setter and getter
    def ensure_hook():
        # TODO: store previous setter/getter. Call them afterwards
        # attention: concurrent write?
        setattr(o.__class__, "__getattr__", get_it)
        setattr(o.__class__, "__setattr__", set_it)

    # what's my url?
    def my_url():
        for c in conf["conjoiners"]:
            if c["name"] == my_name:
                return c["url"]

        return None

    # connect to other conjoiners
    def ensure_conjoiners_connect(self, ctx):

        # greenlet function
        def recv_objs(sock):
            while True:
                try:
                    payload = sock.recv_json(flags=zmq.NOBLOCK)
                    payload = internalize_payload(payload)
                    n, v = unpack_payload_single(payload)
                    self.__dict__[n] = v
                except:
                    pass # do nothing when no messages available

                gevent.sleep(0)

        # connect and collect greenlet (not used yet)
        for c in conf["conjoiners"]:
            if c["name"] != my_name:
                con = ctx.socket(zmq.SUB)
                con.setsockopt(zmq.RCVTIMEO, conf["recv_timeout"])
                con.setsockopt(zmq.SUBSCRIBE, '')
                con.connect(c["url"])
                gevent.spawn(recv_objs, con)

    # bind to the external url
    def ensure_external_bind(o, ctx=None):
        if not ctx:
            ctx = ensure_ctx()

        if not o.__dict__.has_key(EXTS):
            ext_sock = ctx.socket(zmq.PUB)
            ext_sock.bind(my_url())
            o.__dict__[EXTS] = ext_sock
        else:
            ext_sock = o.__dict__[EXTS]

        return ext_sock

    # collect implants in the class
    def ensure_implants():
        if not o.__class__.__dict__.has_key(IMPLANTS):
            setattr(o.__class__, IMPLANTS, [id(o)])
        else:
            o.__class__.__dict__[IMPLANTS].append(id(o))

    # create one 0mq context per instance
    def ensure_ctx():
        if not o.__dict__.has_key(CTX):
            ctx = zmq.Context()
            o.__dict__[CTX] = ctx
        else:
            ctx = o.__dict__[CTX]

        return ctx

    # encode key
    def key_n(n):
        return "%s%s" % (SET, n)

    # adapt external payload to match internal requirements
    def internalize_payload(payload):
        payload["time"] = int(time.time())

        return payload

    # pack one single value set into a bigger payload
    def pack_payload_single(n, v):
        return {"sender": my_name, "time": int(time.time()), key_n(n): v}

    # unpack one single value set from a bigger payload
    def unpack_payload_single(payload, n=None):
        if n:
            k = key_n(n)

            return (n, payload[k])
        else:
            for k, v in payload.iteritems():
                if k.startswith(SET):
                    v = payload[k]
                    k = k.replace(SET, "")

                    return (k, v)

        return (None, None)

    # do actually implant
    ctx = ensure_ctx()
    ensure_external_bind(o, ctx)
    ensure_conjoiners_connect(o, ctx)
    ensure_implants()
    ensure_hook()
