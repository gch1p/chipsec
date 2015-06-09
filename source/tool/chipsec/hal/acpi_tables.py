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




# -------------------------------------------------------------------------------
#
# CHIPSEC: Platform Hardware Security Assessment Framework
# (c) 2010-2012 Intel Corporation
#
# -------------------------------------------------------------------------------

"""
HAL component decoding various ACPI tables
"""

__version__ = '0.1'

import struct
from collections import namedtuple


def HEX_STRING(_str):
    return (''.join('%02x ' % ord(c) for c in _str))

########################################################################################################
#
# DMAR Table
#
########################################################################################################

ACPI_TABLE_FORMAT_DMAR = '=BB10s'
ACPI_TABLE_SIZE_DMAR   = struct.calcsize(ACPI_TABLE_FORMAT_DMAR)
class ACPI_TABLE_DMAR( namedtuple('ACPI_TABLE_DMAR', 'HostAddrWidth Flags Reserved dmar_structures') ):
    __slots__ = ()
    def __str__(self):
        _str = """------------------------------------------------------------------
  DMAR Table Contents
------------------------------------------------------------------
  Host Address Width  : %d
  Flags               : 0x%02X
  Reserved            : %s
""" % ( self.HostAddrWidth, self.Flags, ''.join('%02x ' % ord(c) for c in self.Reserved) )
        _str += "\n  Remapping Structures:\n"
        for st in self.dmar_structures: _str += str(st)
        return _str

def _parse_ACPI_table_DMAR( table_content ):  
    dmar_structs = []

    off = ACPI_TABLE_SIZE_DMAR
    struct_fmt = '=HH'
    while off < len(table_content) - 1:
        (_type,length) = struct.unpack( struct_fmt, table_content[ off : off + struct.calcsize(struct_fmt) ] )
        if 0 == length: break
        dmar_structs.append( _get_structure_DMAR( _type, table_content[ off : off + length ] ) )
        off += length

    table = ACPI_TABLE_DMAR( *struct.unpack_from( ACPI_TABLE_FORMAT_DMAR, table_content ), dmar_structures=dmar_structs )
    return table

DMAR_STRUCTURE_DRHD = 0x00
DMAR_STRUCTURE_RMRR = 0x01
DMAR_STRUCTURE_ATSR = 0x02
DMAR_STRUCTURE_RHSA = 0x03
DMAR_STRUCTURE_ANDD = 0x04

def _get_structure_DMAR( _type, DataStructure ):
    if   DMAR_STRUCTURE_DRHD == _type: return _get_DMAR_structure_DRHD( DataStructure )
    elif DMAR_STRUCTURE_RMRR == _type: return _get_DMAR_structure_RMRR( DataStructure )
    elif DMAR_STRUCTURE_ATSR == _type: return _get_DMAR_structure_ATSR( DataStructure )
    elif DMAR_STRUCTURE_RHSA == _type: return _get_DMAR_structure_RHSA( DataStructure )
    elif DMAR_STRUCTURE_ANDD == _type: return _get_DMAR_structure_ANDD( DataStructure )
    else:                              return ("\n  Unknown DMAR structure 0x%02X\n" % _type)


#
# DMAR Device Scope
#

DMAR_DS_TYPE_PCI_ENDPOINT     = 0x1
DMAR_DS_TYPE_PCIPCI_BRIDGE    = 0x2
DMAR_DS_TYPE_IOAPIC           = 0x3
DMAR_DS_TYPE_MSI_CAPABLE_HPET = 0x4
DMAR_DS_TYPE_ACPI_NAMESPACE   = 0x5
DMAR_DS_TYPE ={
  DMAR_DS_TYPE_PCI_ENDPOINT     : 'PCI Endpoint Device',
  DMAR_DS_TYPE_PCIPCI_BRIDGE    : 'PCI-PCI Bridge',
  DMAR_DS_TYPE_IOAPIC           : 'I/O APIC Device',
  DMAR_DS_TYPE_MSI_CAPABLE_HPET : 'MSI Capable HPET',
  DMAR_DS_TYPE_ACPI_NAMESPACE   : 'ACPI Namaspace Device'
}

ACPI_TABLE_DMAR_DeviceScope_FORMAT = '=BBHBB'
ACPI_TABLE_DMAR_DeviceScope_SIZE   = struct.calcsize(ACPI_TABLE_DMAR_DeviceScope_FORMAT)
class ACPI_TABLE_DMAR_DeviceScope( namedtuple('ACPI_TABLE_DMAR_DeviceScope', 'Type Length Reserved EnumerationID StartBusNum Path') ):
    __slots__ = ()
    def __str__(self):
        return """      %s (%02X): Len: 0x%02X, Rsvd: 0x%04X, Enum ID: 0x%02X, Start Bus#: 0x%02X, Path: %s
""" % ( DMAR_DS_TYPE[self.Type], self.Type, self.Length, self.Reserved, self.EnumerationID, self.StartBusNum, ''.join('%02x ' % ord(c) for c in self.Path) )


#
# DMAR DMA Remapping Hardware Unit Definition (DRHD) Structure
#
ACPI_TABLE_DMAR_DRHD_FORMAT = '=HHBBHQ'
class ACPI_TABLE_DMAR_DRHD( namedtuple('ACPI_TABLE_DMAR_DRHD', 'Type Length Flags Reserved SegmentNumber RegisterBaseAddr DeviceScope') ):
    __slots__ = ()
    def __str__(self):
        _str = """
  DMA Remapping Hardware Unit Definition (0x%04X):
    Length                : 0x%04X
    Flags                 : 0x%02X
    Reserved              : 0x%02X
    Segment Number        : 0x%04X
    Register Base Address : 0x%016X
""" % ( self.Type, self.Length, self.Flags, self.Reserved, self.SegmentNumber, self.RegisterBaseAddr )
        _str += '    Device Scope          :\n'
        for ds in self.DeviceScope: _str += str(ds)
        return _str

def _get_DMAR_structure_DRHD( structure ):  
    device_scope = []
    fmt          = '=BB'
    step         = struct.calcsize(fmt)
    off          = struct.calcsize(ACPI_TABLE_DMAR_DRHD_FORMAT)
    while off < len(structure) - 1:
        (_type,length) = struct.unpack( fmt, structure[off:off+step] )
        if 0 == length: break
        path_sz = length - ACPI_TABLE_DMAR_DeviceScope_SIZE
        f = ACPI_TABLE_DMAR_DeviceScope_FORMAT + ('%ds' % path_sz)
        device_scope.append( ACPI_TABLE_DMAR_DeviceScope( *struct.unpack_from(f,structure[off:off+length]) ) )
        off += length
    return ACPI_TABLE_DMAR_DRHD( *struct.unpack_from( ACPI_TABLE_DMAR_DRHD_FORMAT, structure ), DeviceScope=device_scope )

#
# DMAR Reserved Memory Range Reporting (RMRR) Structure
#
ACPI_TABLE_DMAR_RMRR_FORMAT = '=HHHHQQ'
class ACPI_TABLE_DMAR_RMRR( namedtuple('ACPI_TABLE_DMAR_RMRR', 'Type Length Reserved SegmentNumber RMRBaseAddr RMRLimitAddr DeviceScope') ):
    __slots__ = ()
    def __str__(self):
        _str = """
  Reserved Memory Range (0x%04X):
    Length                : 0x%04X
    Reserved              : 0x%04X
    Segment Number        : 0x%04X
    Reserved Memory Base  : 0x%016X
    Reserved Memory Limit : 0x%016X
""" % ( self.Type, self.Length, self.Reserved, self.SegmentNumber, self.RMRBaseAddr, self.RMRLimitAddr )
        _str += '    Device Scope          :\n'
        for ds in self.DeviceScope: _str += str(ds)
        return _str

def _get_DMAR_structure_RMRR( structure ):  
    device_scope = []
    fmt          = '=HH'
    step         = struct.calcsize(fmt)
    off          = struct.calcsize(ACPI_TABLE_DMAR_RMRR_FORMAT)
    while off < len(structure) - 1:
        (_type,length) = struct.unpack( fmt, structure[off:off+step] )
        if 0 == length: break
        path_sz = length - ACPI_TABLE_DMAR_DeviceScope_SIZE
        f = ACPI_TABLE_DMAR_DeviceScope_FORMAT + ('%ds' % path_sz)
        device_scope.append( ACPI_TABLE_DMAR_DeviceScope( *struct.unpack_from(f,structure[off:off+length]) ) )
        off += length
    return ACPI_TABLE_DMAR_RMRR( *struct.unpack_from( ACPI_TABLE_DMAR_RMRR_FORMAT, structure ), DeviceScope=device_scope )


#
# DMAR Root Port ATS Capability Reporting (ATSR) Structure
#
ACPI_TABLE_DMAR_ATSR_FORMAT = '=HHBBH'
class ACPI_TABLE_DMAR_ATSR( namedtuple('ACPI_TABLE_DMAR_ATSR', 'Type Length Flags Reserved SegmentNumber DeviceScope') ):
    __slots__ = ()
    def __str__(self):
        _str = """
  Root Port ATS Capability (0x%04X):
    Length                : 0x%04X
    Flags                 : 0x%02X
    Reserved (0)          : 0x%02X
    Segment Number        : 0x%04X
""" % ( self.Type, self.Length, self.Flags, self.Reserved, self.SegmentNumber )
        _str += '    Device Scope          :\n'
        for ds in self.DeviceScope: _str += str(ds)
        return _str

def _get_DMAR_structure_ATSR( structure ):  
    device_scope = []
    fmt          = '=HH'
    step         = struct.calcsize(fmt)
    off          = struct.calcsize(ACPI_TABLE_DMAR_ATSR_FORMAT)
    while off < len(structure) - 1:
        (_type,length) = struct.unpack( fmt, structure[off:off+step] )
        if 0 == length: break
        path_sz = length - ACPI_TABLE_DMAR_DeviceScope_SIZE
        f = ACPI_TABLE_DMAR_DeviceScope_FORMAT + ('%ds' % path_sz)
        device_scope.append( ACPI_TABLE_DMAR_DeviceScope( *struct.unpack_from(f,structure[off:off+length]) ) )
        off += length
    return ACPI_TABLE_DMAR_ATSR( *struct.unpack_from( ACPI_TABLE_DMAR_ATSR_FORMAT, structure ), DeviceScope=device_scope )

#
# DMAR Remapping Hardware Status Affinity (RHSA) Structure
#
ACPI_TABLE_DMAR_RHSA_FORMAT = '=HHIQI'
class ACPI_TABLE_DMAR_RHSA( namedtuple('ACPI_TABLE_DMAR_RHSA', 'Type Length Reserved RegisterBaseAddr ProximityDomain') ):
    __slots__ = ()
    def __str__(self):
        return """
  Remapping Hardware Status Affinity (0x%04X):
    Length                : 0x%04X
    Reserved (0)          : 0x%08X
    Register Base Address : 0x%016X
    Proximity Domain      : 0x%08X
""" % ( self.Type, self.Length, self.Reserved, self.RegisterBaseAddr, self.ProximityDomain )

def _get_DMAR_structure_RHSA( structure ):  
    return ACPI_TABLE_DMAR_RHSA( *struct.unpack_from( ACPI_TABLE_DMAR_RHSA_FORMAT, structure ) )

#
# DMAR ACPI Name-space Device Declaration (ANDD) Structure
#
ACPI_TABLE_DMAR_ANDD_FORMAT = '=HH3sB'
ACPI_TABLE_DMAR_ANDD_SIZE   = struct.calcsize(ACPI_TABLE_DMAR_ANDD_FORMAT)
assert(8 == ACPI_TABLE_DMAR_ANDD_SIZE)
class ACPI_TABLE_DMAR_ANDD( namedtuple('ACPI_TABLE_DMAR_ANDD', 'Type Length Reserved ACPIDevNum ACPIObjectName') ):
    __slots__ = ()
    def __str__(self):
        return """
  Remapping Hardware Status Affinity (0x%04X):
    Length                : 0x%04X
    Reserved (0)          : %s
    Register Base Address : 0x%016X
    ACPI Device Number    : 0x%02X
    ACPI Object Name      : %s
""" % ( self.Type, self.Length, ''.join('%02x ' % ord(c) for c in self.Reserved), self.ACPIDevNum, self.ACPIObjectName )

def _get_DMAR_structure_ANDD( structure ):  
    sz = struct.calcsize('=H')
    length = struct.unpack( '=H', structure[sz:sz+sz] )
    f = ACPI_TABLE_DMAR_ANDD_FORMAT + ('%ds' % (length - ACPI_TABLE_DMAR_ANDD_SIZE))
    return ACPI_TABLE_DMAR_ANDD( *struct.unpack_from( f, structure ) )


########################################################################################################
#
# APIC Table
#
########################################################################################################

ACPI_TABLE_FORMAT_APIC = '=II'
ACPI_TABLE_SIZE_APIC   = struct.calcsize(ACPI_TABLE_FORMAT_APIC)
class ACPI_TABLE_APIC( namedtuple('ACPI_TABLE_APIC', 'LAPICBase Flags apic_structures') ):
    __slots__ = ()
    def __str__(self):
        apic_str = """------------------------------------------------------------------
  APIC Table Contents
------------------------------------------------------------------
  Local APIC Base  : 0x%016X
  Flags            : 0x%08X
""" % ( self.LAPICBase, self.Flags )
        apic_str += "\n  Interrupt Controller Structures:\n"
        for st in self.apic_structures: apic_str += str(st)
        return apic_str

# APIC Table Structures
ACPI_TABLE_APIC_PROCESSOR_LAPIC_FORMAT            = '<BBBBI'    
ACPI_TABLE_APIC_IOAPIC_FORMAT                     = '<BBBBII'    
ACPI_TABLE_APIC_INTERRUPT_SOURSE_OVERRIDE_FORMAT  = '<BBBBIH'    
ACPI_TABLE_APIC_NMI_SOURCE_FORMAT                 = '<BBHI'    
ACPI_TABLE_APIC_LAPIC_NMI_FORMAT                  = '<BBBHB'    
ACPI_TABLE_APIC_LAPIC_ADDRESS_OVERRIDE_FORMAT     = '<BBHQ'    
ACPI_TABLE_APIC_IOSAPIC_FORMAT                    = '<BBBBIQ'    
ACPI_TABLE_APIC_PROCESSOR_LSAPIC_FORMAT           = '<BBBBBHII'    
ACPI_TABLE_APIC_PLATFORM_INTERRUPT_SOURCES_FORMAT = '<BBHBBBII'    
ACPI_TABLE_APIC_PROCESSOR_Lx2APIC_FORMAT          = '<BBHIII'    
ACPI_TABLE_APIC_Lx2APIC_NMI_FORMAT                = '<BBHIB3s'    
ACPI_TABLE_APIC_GICC_CPU_FORMAT                   = '<BBHIIIIIQQQQIQQ'    
ACPI_TABLE_APIC_GIC_DISTRIBUTOR_FORMAT            = '<BBHIQII'    
ACPI_TABLE_APIC_GIC_MSI_FORMAT                    = '<BBHIQIHH'    
ACPI_TABLE_APIC_GIC_REDISTRIBUTOR_FORMAT          = '<BBHQI'    


class ACPI_TABLE_APIC_PROCESSOR_LAPIC(namedtuple('ACPI_TABLE_APIC_PROCESSOR_LAPIC', 'Type Length ACPIProcID APICID Flags')):
    __slots__ = ()
    def __str__(self):
        return """
  Processor Local APIC (0x00)
    Type         : 0x%02X
    Length       : 0x%02X
    ACPI Proc ID : 0x%02X
    APIC ID      : 0x%02X
    Flags        : 0x%02X
"""%( self.Type, self.Length, self.ACPIProcID, self.APICID, self.Flags )

class ACPI_TABLE_APIC_IOAPIC(namedtuple('ACPI_TABLE_APIC_IOAPIC', 'Type Length IOAPICID Reserved IOAPICAddr GlobalSysIntBase')):
    __slots__ = ()
    def __str__(self):
        return """
  I/O APIC (0x01)
    Type                : 0x%02X
    Length              : 0x%02X
    Reserved            : 0x%02X 
    I/O APIC ID         : 0x%02X
    I/O APIC Base       : 0x%02X
    Global Sys Int Base : 0x%02X
"""%( self.Type, self.Length, self.IOAPICID, self.Reserved, self.IOAPICAddr, self.GlobalSysIntBase )
     
class ACPI_TABLE_APIC_INTERRUPT_SOURSE_OVERRIDE(namedtuple('ACPI_TABLE_APIC_INTERRUPT_SOURSE_OVERRIDE', 'Type Length Bus Source GlobalSysIntBase Flags')):
    __slots__ = ()
    def __str__(self):
        return """
  Interrupt Source Override (0x02)
    Type                : 0x%02X
    Length              : 0x%02X
    Bus                 : 0x%02X
    Source              : 0x%02X
    Global Sys Int Base : 0x%02X
    Flags               : 0x%02X
"""%( self.Type, self.Length, self.Bus, self.Source, self.GlobalSysIntBase, self.Flags )

class ACPI_TABLE_APIC_NMI_SOURCE(namedtuple('ACPI_TABLE_APIC_NMI_SOURCE', 'Type Length Flags GlobalSysIntBase')):
    __slots__ = ()
    def __str__(self):
        return """
  Non-maskable Interrupt (NMI) Source (0x03)
    Type                : 0x%02X
    Length              : 0x%02X
    Flags               : 0x%02X
    Global Sys Int Base : 0x%02X
"""%( self.Type, self.Length, self.Flags, self.GlobalSysIntBase )

class ACPI_TABLE_APIC_LAPIC_NMI(namedtuple('ACPI_TABLE_APIC_LAPIC_NMI', 'Type Length ACPIProcessorID Flags LocalAPICLINT')):
    __slots__ = ()
    def __str__(self):
        return """
  Local APIC NMI (0x04)
    Type              : 0x%02X
    Length            : 0x%02X
    ACPI Processor ID : 0x%02X
    Flags             : 0x%02X
    Local APIC LINT   : 0x%02X
"""%( self.Type, self.Length, self.ACPIProcessorID, self.Flags, self.LocalAPICLINT )

class ACPI_TABLE_APIC_LAPIC_ADDRESS_OVERRIDE(namedtuple('ACPI_TABLE_APIC_LAPIC_ADDRESS_OVERRIDE', 'Type Length Reserved LocalAPICAddress')):
    __slots__ = ()
    def __str__(self):
        return """
  Local APIC Address Override (0x05)
    Type               : 0x%02X
    Length             : 0x%02X
    Reserved           : 0x%02X
    Local APIC Address : 0x%02X
"""%( self.Type, self.Length, self.Reserved, self.LocalAPICAddress )

class ACPI_TABLE_APIC_IOSAPIC(namedtuple('ACPI_TABLE_APIC_IOSAPIC', 'Type Length IOAPICID Reserved GlobalSysIntBase IOSAPICAddress')):
    __slots__ = ()
    def __str__(self):
        return """
  I/O SAPIC (0x06)
    Type                : 0x%02X
    Length              : 0x%02X
    IO APIC ID          : 0x%02X
    Reserved            : 0x%02X
    Global Sys Int Base : 0x%02X
    IO SAPIC Address    : 0x%02X
"""%( self.Type, self.Length, self.IOAPICID, self.Reserved, self.GlobalSysIntBase, self.IOSAPICAddress )

class ACPI_TABLE_APIC_PROCESSOR_LSAPIC(namedtuple('ACPI_TABLE_APIC_PROCESSOR_LSAPIC', 'Type Length ACPIProcID LocalSAPICID LocalSAPICEID Reserved Flags ACPIProcUIDValue ACPIProcUIDString'), ):
    __slots__ = ()
    def __str__(self):
        return """
  Local SAPIC (0x07)    
    Type                 : 0x%02X
    Length               : 0x%02X
    ACPI Proc ID         : 0x%02X
    Local SAPIC ID       : 0x%02X
    Local SAPIC EID      : 0x%02X
    Reserved             : 0x%02X
    Flags                : 0x%02X
    ACPI Proc UID Value  : 0x%02X
    ACPI Proc UID String : 0x%02X
"""%( self.Type, self.Length, self.ACPIProcID, self.LocalSAPICID, self.LocalSAPICEID, self.Reserved, self.Flags, self.ACPIProcUIDValue, self.ACPIProcUIDString )

class ACPI_TABLE_APIC_PLATFORM_INTERRUPT_SOURCES(namedtuple('ACPI_TABLE_APIC_PLATFORM_INTERRUPT_SOURCES', 'Type Length Flags InterruptType ProcID ProcEID IOSAPICVector GlobalSystemInterrupt PlatIntSourceFlags')):
    __slots__ = ()
    def __str__(self):
        return """
  Platform Interrupt Sources (0x08)
    Type                    : 0x%02X
    Length                  : 0x%02X
    Flags                   : 0x%02X
    Interrupt Type          : 0x%02X
    Proc ID                 : 0x%02X
    Proc EID                : 0x%02X
    I/O SAPIC Vector        : 0x%02X
    Global System Interrupt : 0x%02X
    Plat Int Source Flags   : 0x%02X
"""%( self.Type, self.Length, self.Flags, self.InterruptType, self.ProcID, self.ProcEID, self.IOSAPICVector, self.GlobalSystemInterrupt, self.PlatIntSourceFlags )

class ACPI_TABLE_APIC_PROCESSOR_Lx2APIC(namedtuple('ACPI_TABLE_APIC_PROCESSOR_Lx2APIC', 'Type Length Reserved x2APICID Flags ACPIProcUID')):
    __slots__ = ()
    def __str__(self):
        return """
  Processor Local x2APIC (0x09)
    Type          : 0x%02X
    Length        : 0x%02X
    Reserved      : 0x%02X
    x2APIC ID     : 0x%02X
    Flags         : 0x%02X
    ACPI Proc UID : 0x%02X
"""%( self.Type, self.Length, self.Reserved, self.x2APICID, self.Flags, self.ACPIProcUID )

class ACPI_TABLE_APIC_Lx2APIC_NMI(namedtuple('ACPI_TABLE_APIC_Lx2APIC_NMI', 'Type Length Flags ACPIProcUID Localx2APICLINT Reserved')):
    __slots__ = ()
    def __str__(self):
        return """
  Local x2APIC NMI (0x0A)
    Type              : 0x%02X
    Length            : 0x%02X
    Flags             : 0x%02X
    ACPI Proc UID     : 0x%02X
    Local x2APIC LINT : 0x%02X
    Reserved          : 0x%02X
"""%( self.Type, self.Length, self.Flags, self.ACPIProcUID, self.Localx2APICLINT, self.Reserved )

class ACPI_TABLE_APIC_GICC_CPU(namedtuple('ACPI_TABLE_APIC_GICC_CPU', 'Type Length Reserved CPUIntNumber ACPIProcUID Flags ParkingProtocolVersion PerformanceInterruptGSIV ParkedAddress PhysicalAddress GICV GICH VGICMaintenanceINterrupt GICRBaseAddress MPIDR')):
    __slots__ = ()
    def __str__(self):
        return """
  GICC CPU Interface Structure (0x0B)
    Type                       : 0x%02X
    Length                     : 0x%02X
    Reserved                   : 0x%02X
    CPU Int Number             : 0x%02X
    ACPI Proc UID              : 0x%02X
    Flags                      : 0x%02X
    Parking Protocol Version   : 0x%02X
    Performance Interrupt GSIV : 0x%02X
    Parked Address             : 0x%02X
    Physical Address           : 0x%02X
    GICV                       : 0x%02X
    GICH                       : 0x%02X
    VGIC Maintenance INterrupt : 0x%02X
    GICR Base Address          : 0x%02X
    MPIDR                      : 0x%02X
"""%( self.Type, self.Length, self.Reserved, self.CPUIntNumber, self.ACPIProcUID, self.Flags, self.ParkingProtocolVersion, self.PerformanceInterruptGSIV, self.ParkedAddress, self.PhysicalAddress, self.GICV, self.GICH, self.VGICMaintenanceINterrupt, self.GICRBaseAddress, self.MPIDR )

class ACPI_TABLE_APIC_GIC_DISTRIBUTOR(namedtuple('ACPI_TABLE_APIC_GIC_DISTRIBUTOR', 'Type Length Reserved GICID PhysicalBaseAddress SystemVectorBase Reserved2 ')):
    __slots__ = ()
    def __str__(self):
        return """
  GICD GIC Distributor Structure (0x0C)
    Type                  : 0x%02X
    Length                : 0x%02X
    Reserved              : 0x%02X
    GICID                 : 0x%02X
    Physical Base Address : 0x%02X
    System Vector Base    : 0x%02X
    Reserved              : 0x%02X
"""%( self.Type, self.Length, self.Reserved, self.GICID, self.PhysicalBaseAddress, self.SystemVectorBase, self.Reserved2 )

class ACPI_TABLE_APIC_GIC_MSI(namedtuple('ACPI_TABLE_APIC_GIC_MSI', 'Type Length Reserved GICMSIFrameID PhysicalBaseAddress Flags SPICount SPIBase')):
    __slots__ = ()
    def __str__(self):
        return """
  GICv2m MSI Frame (0x0D)
    Type                  : 0x%02X
    Length                : 0x%02X
    Reserved              : 0x%02X
    GIC MSI Frame ID      : 0x%02X
    Physical Base Address : 0x%02X
    Flags                 : 0x%02X
    SPI Count             : 0x%02X
    SPI Base              : 0x%02X
"""%( self.Type, self.Length, self.Reserved, self.GICMSIFrameID, self.PhysicalBaseAddress, self.Flags, self.SPICount, self.SPIBase )

class ACPI_TABLE_APIC_GIC_REDISTRIBUTOR(namedtuple('ACPI_TABLE_APIC_GIC_REDISTRIBUTOR', 'Type Length Reserved DiscoverRangeBaseAdd DiscoverRangeLength')):
    __slots__ = ()
    def __str__(self):
        return """
  GICR Redistributor Structure (0x0E)
    Type                  : 0x%02X
    Length                : 0x%02X
    Reserved              : 0x%02X
    Discover Range Base   : 0x%02X
    Discover Range Length : 0x%02X
"""%( self.Type, self.Length, self.Reserved, self.DiscoverRangeBaseAdd, self.DiscoverRangeLength )


def _parse_ACPI_table_APIC( table_content ):  
    apic_structs = []

    cont = 8
    while cont < len(table_content) - 1:
        (value,length) = struct.unpack( '=BB', table_content[ cont : cont + 2 ] )
        if 0 == length: break
        apic_structs.append( _get_structure_APIC( value, table_content[ cont : cont + length ] ) )
        cont += length

    table = ACPI_TABLE_APIC( *struct.unpack_from( ACPI_TABLE_FORMAT_APIC, table_content ), apic_structures=apic_structs )
    return table

def _get_structure_APIC( value, DataStructure ):
    if   0x00 == value: return ACPI_TABLE_APIC_PROCESSOR_LAPIC( *struct.unpack_from( ACPI_TABLE_APIC_PROCESSOR_LAPIC_FORMAT, DataStructure ))
    elif 0x01 == value: return ACPI_TABLE_APIC_IOAPIC( *struct.unpack_from( ACPI_TABLE_APIC_IOAPIC_FORMAT, DataStructure ))
    elif 0x02 == value: return ACPI_TABLE_APIC_INTERRUPT_SOURSE_OVERRIDE( *struct.unpack_from( ACPI_TABLE_APIC_INTERRUPT_SOURSE_OVERRIDE_FORMAT, DataStructure ))
    elif 0x03 == value: return ACPI_TABLE_APIC_NMI_SOURCE( *struct.unpack_from( ACPI_TABLE_APIC_NMI_SOURCE_FORMAT, DataStructure ))
    elif 0x04 == value: return ACPI_TABLE_APIC_LAPIC_NMI( *struct.unpack_from( ACPI_TABLE_APIC_LAPIC_NMI_FORMAT, DataStructure ))
    elif 0x05 == value: return ACPI_TABLE_APIC_LAPIC_ADDRESS_OVERRIDE( *struct.unpack_from( ACPI_TABLE_APIC_LAPIC_ADDRESS_OVERRIDE_FORMAT, DataStructure ))
    elif 0x06 == value: return ACPI_TABLE_APIC_IOSAPIC( *struct.unpack_from( ACPI_TABLE_APIC_IOSAPIC_FORMAT, DataStructure ))
    elif 0x07 == value: return ACPI_TABLE_APIC_PROCESSOR_LSAPIC( *struct.unpack_from( "%s%ss"%(ACPI_TABLE_APIC_PROCESSOR_LSAPIC_FORMAT,str(len(DataStructure)-16)), DataStructure ))
    elif 0x08 == value: return ACPI_TABLE_APIC_PLATFORM_INTERRUPT_SOURCES( *struct.unpack_from( ACPI_TABLE_APIC_PLATFORM_INTERRUPT_SOURCES_FORMAT, DataStructure ))
    elif 0x09 == value: return ACPI_TABLE_APIC_PROCESSOR_Lx2APIC( *struct.unpack_from( ACPI_TABLE_APIC_PROCESSOR_Lx2APIC_FORMAT, DataStructure ))
    elif 0x0A == value: return ACPI_TABLE_APIC_Lx2APIC_NMI( *struct.unpack_from( ACPI_TABLE_APIC_Lx2APIC_NMI_FORMAT, DataStructure ))
    elif 0x0B == value: return ACPI_TABLE_APIC_GICC_CPU( *struct.unpack_from( ACPI_TABLE_APIC_GICC_CPU_FORMAT, DataStructure ))
    elif 0x0C == value: return ACPI_TABLE_APIC_GIC_DISTRIBUTOR( *struct.unpack_from( ACPI_TABLE_APIC_GIC_DISTRIBUTOR_FORMAT, DataStructure ))
    elif 0x0D == value: return ACPI_TABLE_APIC_GIC_MSI( *struct.unpack_from( ACPI_TABLE_APIC_GIC_MSI_FORMAT, DataStructure ))
    elif 0x0E == value: return ACPI_TABLE_APIC_GIC_REDISTRIBUTOR( *struct.unpack_from( ACPI_TABLE_APIC_GIC_REDISTRIBUTOR_FORMAT, DataStructure ))
    else:
        DataStructure = ''.join(x.encode('hex') for x in DataStructure)
        return """
Reserved ....................................%s"
         %s"
""" % (value, DataStructure)

        