#!/bin/bash

sudo Rscript ./install_r_packages.r RKorAPClient

pytest \
    --cov-append \
    KorAPClient/tests
