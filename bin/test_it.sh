#!/bin/sh

cd ../test
python -m unittest -v test_implant.ImplantTest
python -m unittest -v test_conjoiner.ConjoinerTest
