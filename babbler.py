#!/usr/bin/env python3

import sys

from app import App


if __name__ == "__main__":
    try:
        App("config.ini").mainloop()
    except Exception as ex:
        sys.exit(ex)
