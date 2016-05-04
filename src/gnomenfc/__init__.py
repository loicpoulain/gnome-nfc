#!/usr/bin/env python

import sys
sys.path.insert(1, '@pythondir@')

from NfcApp import *

if __name__ == "__main__":
    app = NfcApp(package="@PACKAGE@", version="@VERSION@")
    app.run()
