import conjoiners
from unittest import TestCase
import gevent

class ReactTest(TestCase):

    class Test(object):
        def onTransenlightenment(self):
            self.b = self.a + 1

    cj1 = Test()
    cj2 = Test()
    conjoiners.implant(cj1, "./conf_react.json", "test")
    conjoiners.implant(cj2, "./conf_react.json", "test2")

    def test_send(self):
        self.cj1.a = 1
        gevent.sleep(1)
        self.assertEquals(self.cj2.b, 2)

if __name__ == '__main__':
    unittest.main()
