# conjoiners - multi-platform / multi-language reactive programming library

conjoiners is a library aiming to enable reactive programming for
existing (or new) systems written in different languages and running
on different platforms. conjoiners is minimally invasive in its
programming model, but complex behind the scenes.

Idea and first implementations are done by me, Pavlo Baron (pavlobaron).

This is the Python implementation. General project description can be
found in the [conjoiners repository](https://github.com/conjoiners/conjoiners).

## How does it work?

conjoiners for Python follows the conjoiners simplicity of use an
non-invasiveness. In order to add an implant to an object, you call:

    import conjoiners
    conjoiners.implant(cj1, "./test_conf.json", "test")

The first parameter of the implant function is the object itself. The
second is the nest configuration file path. The third is the name of
this conjoiner that can be found in the configuration.

From here, any time you set a field value in this object, a
transenlightenment will be propagated to all known conjoiners. Any
time you access a value, it will return the most current one,
eventually set through a transenlightenment from other
conjoiner. That's basically it.

Internally, conjoiners for Python works through monkey patching the
object provided to the implant function call. There is also a weird
part switching between the class of the object and object itself. This is because it's
not possible in Python to dynamically add setters/getters to objects,
only to classes.

Also, in order to avoid synchronisation and concurrent reads / writes
of object's field values, an internal 0MQ socket pair is used to queue
writes. Reads are done from the queue before the internally stored
value is being asked. This way, writes can frequently happen, but a
read will still independently return the value seen when the read was
done.

I didn't implement yet the part emptying the queue based on time,
though I have internal time in the message payload. Some more research
and work needs to be done at this point. Right now, only one message
will be received from the queue.

This library brings pyzmq as dependency.

To run the tests, just run bin/test_it.sh. Look there for complete,
yet simple examples.
