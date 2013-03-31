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
GRLS = "conjoiners_ext_greenlets"
INTS = "conjoiners_int_sock"
INTC = "conjoiners_int_connect"
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
        if not id(self) in o.__class__.__dict__[IMPLANTS]:
            # simply return the current value
            # TODO: check if have to take care of thready-safety of unimpletnted objects here
            return self.__dict__[n]
        else:
            # TODO: A transporter takes protocol, name and address and
            # combines the url itself - for now it's hardcoded for 0mq, later then
            # rabbit and rest!
            _int_sock, int_connect = ensure_internal_pair(self, n)
            try:
                _n, v = unpack_payload_single(int_connect.recv_pyobj(conf["recv_timeout"]), n)
                # TODO: multi msgs
                # this can be done based on time in the payload
                # or up to a maximum of messages.
                # in case of time: get the current time and recieve all
                # <= this time. This might mean receiving one more (check is done
                # afterwards), but this is not bad. The newer ones arrived while
                # receiving will not be received and stay in the queue
                # until the next get. (how to test this? quickcheck would be great here)

                # always store current value
                self.__dict__[n] = v
            except:
                if self.__dict__.has_key(n):
                    # just return the current value
                    v = self.__dict__[n]
                else:
                    v = None

            return v

    # overridden setter    
    def set_it(self, n, v):
        # what if it gets implanted right after this check?
        if not id(self) in o.__class__.__dict__[IMPLANTS]:
            # simply update the current value
            # TODO: check if have to take care of thread-safety of unimpletnted objects here
            self.__dict__[n] = v
        else:
            # propagate on the internal queue
            int_sock, _int_connect = ensure_internal_pair(self, n)
            payload = pack_payload_single(n, v)
            int_sock.send_pyobj(payload, zmq.NOBLOCK)

            # multicast
            ext_sock = ensure_external_bind(self)
            ext_sock.send_json(payload, zmq.NOBLOCK)

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
    def ensure_conjoiners_connect(ctx):

        # greenlet function
        def recv_objs(sock):
            while True:
                try:
                    payload = internalize_payload(sock.recv_json(conf["recv_timeout"]))
                    n, _v = unpack_payload_single(payload)
                    int_sock, _int_connect = ensure_internal_pair(o, n)
                    int_sock.send_pyobj(payload, zmq.NOBLOCK)
                except:
                    pass # do nothing when no messages available

                gevent.sleep(0)

        # connect and collect greenlet (not used yet)
        if not o.__dict__.has_key(GRLS):
            grls = []
            for c in conf["conjoiners"]:
                if c["name"] != my_name:
                    con = ctx.socket(zmq.SUB)
                    con.RCVTIMEO = conf["recv_timeout"]
                    con.connect(c["url"])
                    con.setsockopt(zmq.SUBSCRIBE, '')
                    grls.append(gevent.spawn(recv_objs, con))

            o.__dict__[GRLS] = grls

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

    # bind and connect to the internal queue
    def ensure_internal_pair(self, n):
        if not self.__dict__.has_key(INTS):
            ctx = ensure_ctx()
            int_sock = ctx.socket(zmq.PUSH)
            int_connect = ctx.socket(zmq.PULL)
            url = "%s_%s_%s" % (BIND_PFX, id(self), n)
            int_sock.bind(url)
            int_connect.RCVTIMEO = conf["recv_timeout"]
            int_connect.connect(url)
            self.__dict__[INTS] = int_sock
            self.__dict__[INTC] = int_connect
        else:
            int_sock = self.__dict__[INTS]
            int_connect = self.__dict__[INTC]

        return (int_sock, int_connect)

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
    ensure_conjoiners_connect(ctx)
    ensure_implants()
    ensure_hook()
