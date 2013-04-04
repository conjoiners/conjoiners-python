import conjoiners
from unittest import TestCase
import gevent

class ConjoinerTest(TestCase):

    class Test(object):
        pass

    cj1 = Test()
    cj2 = Test()
    conjoiners.implant(cj1, "./conf_conjoiner.json", "test")
    conjoiners.implant(cj2, "./conf_conjoiner.json", "test2")

    def test_send(self):
        self.cj1.test_value = "test_value"
        gevent.sleep(1)
        self.assertEquals(self.cj2.test_value, "test_value")

if __name__ == '__main__':
    unittest.main()
