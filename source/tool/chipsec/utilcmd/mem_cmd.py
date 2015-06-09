#!/usr/local/bin/python
#CHIPSEC: Platform Security Assessment Framework
#Copyright (c) 2010-2015, Intel Corporation
# 
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; Version 2.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#Contact information:
#chipsec@intel.com
#



"""
The mem command provides direct access to read and write physical memory.
"""

__version__ = '1.0'

import os
import sys
import time

import chipsec_util

from chipsec.logger     import *
from chipsec.file       import *



# Physical Memory
def mem(argv):
    """
    >>> chipsec_util mem <phys_addr_hi> <phys_addr_lo> <length> [value]

    Examples:

    >>> chipsec_util mem 0x0 0x41E 0x20
    >>> chipsec_util mem 0x0 0xA0000 4 0x9090CCCC
    >>> chipsec_util mem 0x0 0xFED40000 0x4
    >>> chipsec_util mem allocate 0x1000
    """
    phys_address_hi = 0
    phys_address_lo = 0
    phys_address    = 0
    size = 0x100

    if 3 > len(argv):
        print mem.__doc__
        return

    op = argv[2]
    t = time.time()

    if 'allocate' == op and 4 == len(argv):
        size = int(argv[3],16)
        (va, pa) = chipsec_util._cs.mem.alloc_physical_mem( size )
        logger().log( '[CHIPSEC] Allocated %X bytes of physical memory: VA = 0x%016X, PA = 0x%016X' % (size, va, pa) )
        return

    if 4 > len(argv):
        print mem.__doc__
        return
    else:
        phys_address_hi = int(argv[2],16)
        phys_address_lo = int(argv[3],16)
        phys_address = ((phys_address_hi<<32) | phys_address_lo)

    if 6 == len(argv):
        value = int(argv[5],16)
        logger().log( '[CHIPSEC] Writing: PA = 0x%016X <- 0x%08X' % (phys_address, value) )
        chipsec_util._cs.mem.write_physical_mem_dword( phys_address, value )
    else:
        if 5 == len(argv): size = int(argv[4],16)
        out_buf = chipsec_util._cs.mem.read_physical_mem( phys_address, size )
        logger().log( '[CHIPSEC] Reading: PA = 0x%016X, len = 0x%X, output:' % (phys_address, len(out_buf)) )
        print_buffer( out_buf )

    logger().log( "[CHIPSEC] (mem) time elapsed %.3f" % (time.time()-t) )

chipsec_util.commands['mem'] = {'func' : mem, 'start_driver' : True, 'help' : mem.__doc__  }
