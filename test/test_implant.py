import conjoiners
from unittest import TestCase
import time

class ImplantTest(TestCase):

    class Test(object):
        pass

    iyes = Test()
    ino = Test()
    conjoiners.implant(iyes, "./test_conf.json", "test")

    def test_no_implant(self):
        self.ino.test_value = "no_implant_value"
        self.assertEqual(self.ino.test_value, "no_implant_value")

    def test_implant(self):
        self.iyes.test_value = "implant_value"
        self.assertEquals(self.iyes.test_value, "implant_value")

if __name__ == '__main__':
    unittest.main()
