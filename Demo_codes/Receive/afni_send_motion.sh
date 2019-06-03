#!/bin/tcsh

set maskset = rt.__001+orig

plugout_drive -com "SETENV AFNI_REALTIME_Mask_Dset $maskset" -quit
