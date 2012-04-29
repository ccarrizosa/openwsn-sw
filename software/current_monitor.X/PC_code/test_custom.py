# -*- coding: utf-8 -*-
import usb.core
import usb.util
import time;
 
dev = usb.core.find(idVendor=0x04D8, idProduct=0x000A)
 
if dev is None:
    raise ValueError('Device not found');
 
try:
    dev.set_configuration();
except usb.core.USBError:
    print "Couldn't set configuration (prob b/c of usb->serial driver)"
     
 
cfg = dev.get_active_configuration();
interface_number = cfg[ (2,0) ].bInterfaceNumber

intf = usb.util.find_descriptor( cfg, bInterfaceNumber = interface_number )

ep_out = usb.util.find_descriptor( intf, custom_match = \
                                            lambda e: \
                                                usb.util.endpoint_direction(e.bEndpointAddress) ==\
                                                usb.util.ENDPOINT_OUT )
                                                
ep_in = usb.util.find_descriptor( intf, custom_match = \
                                            lambda e: \
                                                usb.util.endpoint_direction(e.bEndpointAddress) ==\
                                                usb.util.ENDPOINT_IN )                                                
                                                
seq_no = 0;
iLow_avg = 0;
iLow_sum = 0;
iLow_smp = 0;
iRaw_sum = 0;
iRaw_smp = 0;

while(True):
    seq_no += 1;
    packet = chr((seq_no&0xFF)) + chr((seq_no>>8)&0xFF) + '\x01\x01\x00\x30';
    packet = packet + '\x00'*(64-len(packet))
    ep_out.write(packet)
    dat = ep_in.read(64);
    #print ''.join([' %02X'%i for i in dat])
    iLow_raw = dat[5] + (dat[6]<<8);
    iHigh_raw = dat[7] + (dat[8]<<8);
    
    iHigh = ((iHigh_raw - 1) * 3.3/1024 / 10.34   )
    vThresh = 0.75;
    tCalibrate = 0;
    #iLow = ((vThresh*10e-9)/((iLow_raw-tCalibrate) * 4/48000000.)   - 0)
    # from MATLAB polyfit
    iLow = -0.000044361198738*iLow_raw + 0.008737874605678;
    if (iLow_smp < 10 or abs(iLow-iLow_avg) < 10e-3):
        iLow_sum += iLow;
        iLow_smp += 1;
        iLow_avg = iLow_sum / iLow_smp;
        iRaw_sum += iLow_raw
        iRaw_smp += 1;
    #iLow_avg = 0.9*iLow_avg + 0.1*iLow;
    print 'Low: %10.2fuA (%6d / %8.2fA) / %10.2fAuA (%4d samps)   High: %10.2fmA (%6d)'%(iLow*1e6,iLow_raw,1.*iRaw_sum/iRaw_smp,iLow_avg*1e6,iLow_smp,iHigh*1e3,iHigh_raw)
    time.sleep(.1);