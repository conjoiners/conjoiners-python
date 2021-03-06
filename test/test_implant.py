import conjoiners
from unittest import TestCase

class ImplantTest(TestCase):

    class Test(object):
        pass

    iyes = Test()
    ino = Test()
    conjoiners.implant(iyes, "./conf_implant.json", "test_implant")

    def test_no_implant(self):
        self.ino.test_value = "no_implant_value"
        self.assertEqual(self.ino.test_value, "no_implant_value")

    def test_implant(self):
        self.iyes.test_value = "implant_value"
        self.assertEquals(self.iyes.test_value, "implant_value")

if __name__ == '__main__':
    unittest.main()
