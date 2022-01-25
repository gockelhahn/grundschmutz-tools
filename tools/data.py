#!/usr/bin/env python
# download BSI IT-Grundschutz-Kompendium and
# convert it into structural json based machine-readable data

from tools.BSI import BSI


def main() -> None:
    bsi = BSI()
    bsi.setup()


if __name__ == '__main__':
    main()
