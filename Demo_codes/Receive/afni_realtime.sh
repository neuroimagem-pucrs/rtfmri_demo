#!/bin/tcsh

setenv AFNI_REALTIME_Registration  	3D:_realtime
setenv AFNI_REALTIME_Base_Image    	2
setenv AFNI_REALTIME_Graph         	Realtime
setenv AFNI_REALTIME_MP_HOST_PORT  	localhost:53214
setenv AFNI_REALTIME_SEND_VER      	YES
setenv AFNI_REALTIME_SHOW_TIMES    	YES
setenv AFNI_REALTIME_Mask_Vals     	Motion_Only
setenv AFNI_REALTIME_Function 	   	FIM
setenv AFNI_TRUSTHOST		   	localhost

setenv RECEIVED_IMAGES_DIR_BASE		imagesAFNI
setenv RECEIVED_IMAGES_DIR		`date +%Y-%m-%d.%H:%M:%S`

if ( ! -d $RECEIVED_IMAGES_DIR_BASE ) mkdir $RECEIVED_IMAGES_DIR_BASE
endif

cd $RECEIVED_IMAGES_DIR_BASE

afni 	-rt 					\
	-yesplugouts				\
	-orient	RAI				\
	-ignore 3 &

