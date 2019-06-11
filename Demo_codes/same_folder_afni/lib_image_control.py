#!/usr/bin/env python

#-------------------------------------------------------------------------------------
# Description:  This lib was to developed to provide a quality
#                control system of image acquisition in fMRI exams.
#
# Author:   Maicon Diogo Much [MDM]
#
# Date:     08/09/15
#
# Revision: --/--/-- - Description/Author
#       08/09/15 - First Release/[MDM]
#-------------------------------------------------------------------------------------

#Tests if libraries was installed--------------------------------------------------------------------------
import module_test_lib                          #for test if lib exists
import psutil
import netifaces as ni
g_testlibs = ['gc', 'numpy', 'wx', 'matplotlib']
if module_test_lib.num_import_failures(g_testlibs,details=0):
   print """
     -- for details, consider xmat_tool -test_libs
     -- also, many computations do not require the GUI
        (e.g. 'xmat_tool -load_xmat X.xmat.1D -show_cormat_warnings')
   """
   sys.exit(1)

#Libraries--------------------------------------------------------------------------
import matplotlib           as mpl              #MatPlotLib
mpl.use('WXAgg')
import matplotlib.pyplot    as plt              #PyPlot
from matplotlib.patches     import Rectangle    #Rectangles
from PIL                    import Image                  
import numpy                as np               #Numerical
import sys, os                                  #for wx
import numpy                as N
import wx
import time
import lib_afni1D           as LAD              #lib for deal with 1D files

#set some resource font values------------------------------------------------------
mpl.rc('axes',titlesize=11)
mpl.rc('axes',labelsize=9)
mpl.rc('xtick',labelsize=8)
mpl.rc('ytick',labelsize=7)
mpl.rcParams['toolbar'] = 'None'
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import afni_util as UTIL

#FONT DESCRIPTION OF PYTHON TEXT TITLE------------------------------------------------
fonttitle = {'family' : 'sans-serif',
        'color'  : 'black',
        'weight' : 'bold',
        'size'   : 14,
        }

#FONT DESCRIPTION OF PYTHON TR TEXT__--------------------------------------------
fontTR = {'family' : 'sans-serif',
              'color'  : 'black',
              'weight' : 'bold',
               'size'   : 30,
        }

#FONT DESCRIPTION OF PYTHON TR TEXT__--------------------------------------------
fontNumber = {'family' : 'sans-serif',
              'color'  : 'RED',
              'weight' : 'bold',
               'size'   : 25,
        }

#FONT DESCRIPTION OF PYTHON TR TEXT__--------------------------------------------
fontTRNumber = {'family' : 'sans-serif',
              'color'  : 'black',
              'weight' : 'bold',
               'size'   : 25,
        }

#FONT DESCRIPTION OF PYTHON GENERAL TEXT__--------------------------------------------
fontmediun = {'family' : 'sans-serif',
              'color'  : 'black',
              'weight' : 'normal',
               'size'   : 10,
        }

#FONT DESCRIPTION OF PYTHON TEXT TITLE------------------------------------------------
fonttitlePanel = {'family' : 'sans-serif',
        'color'  : 'black',
        'weight' : 'bold',
        'size'   : 18,
        }

#Main plotting canvas class---------------------------------------------

class CanvasFrame(wx.Frame):
   """create a main plotting canvas
        title   : optional window title
        verb    : verbose level (default 1)
   """
   def __init__(self, title='', verb=1):
      #Make a figure and axes with dimensions as desired------------------------------------
      wx.Frame.__init__(self, None, -1, title, size=(400,300),style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)          #400x300 window
      self.verb     = verb
      self.figure   = Figure(figsize=(5,5))                             
      self.AxisRT   = self.figure.add_axes([0.1, 0.05, 0.2, 0.6])
      self.canvas   = FigureCanvas(self, -1, self.figure)
      self.sizer    = wx.BoxSizer(wx.VERTICAL)
      self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
      self.SetSizer(self.sizer)
      self.Fit()
      self.ax               = None
      
      pic = wx.Icon("brain.ico", wx.BITMAP_TYPE_ICO)
      self.SetIcon(pic)
      
      #Maximum euclidean norm of derivate of motion
      self.TRESHOLDRT       = 0.9
      #Number of motions that is acceptable
      self.NMotion          = 15
      #Number of TR's
      self.TRNumber         = 4
      #Number of motions in the exam
      self.ACCmotionstatus  = 0
      #Euclidean motion of derivative of motion values
      self.eucMotion = 0
      #open file that contain data to display
      self.adata = LAD.Afni1D('motion.1D', verb=self.verb)
      #write none values to file
      self.adata.mat[0][0] = 0
      self.adata.mat[0][1] = 0
      self.adata.write('motion.1D',overwrite=1)
      #Variable that indicate when excessive motion is detected
      self.MotionDetected   = 0
      #counter to blink Excessive motion text
      self.counter          = 0
      #Color Map
      self.colobarRT        = 0
      #Maximum and Minimun Values
      self.normRT           = 0 
      #Boundaries
      self.bounds           = 0
      #Real Time Bargraph
      self.bargraphRT       = 0
      #rectangle to fill real time bar
      self.rectangleRT      = 0
      #Color map to accumulative head motion
      self.colobarACC       = 0
      #Maximun and minimun values of acc head motion
      self.normACC          = 0
      #Boudn of acc bar
      self.boundsACC        = 0
      #Accumulative bar
      self.bargraphACC      = 0
      #Accumulated motion
      self.motiondetectionacc  = 0
      
      #CREATE SOME TEXTS--------------------------------------------------------------------
      self.AxisRT.text(-0.4, 1.48, 'fMRI Motion Viewer', fontdict=fonttitle)
      
      self.MotionConfig = self.AxisRT.text(-0.4, 1.4, 'Accumulated motion: 0.00 mm', fontdict=fontmediun)
      self.NMotionsConfig = self.AxisRT.text(-0.4, 1.32,'Head motion trend: Waiting...', fontdict=fontmediun)
      
      self.AxisRT.text(-0.1, 1.15, 'RT Head Motion', fontdict=fontmediun)
      self.MotionLimitText = self.AxisRT.text(-0.3, 1, "- - - mm", fontdict=fontTRNumber)
      
      self.AxisRT.text(2.8, 1.31, 'TR', fontdict=fontmediun)
      self.TRNumberText = self.AxisRT.text(3.3, 1.3, self.TRNumber, fontdict=fontTR)

      #ni.ifaddresses('eth0')
      #ip = ni.ifaddresses('eth0')[2][0]['addr']
      #print ip  # should print "192.168.100.37"

      ip = "localhost"
      print ip

      self.IP = self.AxisRT.text(2.3, 1.48, 'Running on: 192.168.1.76', fontdict=fontmediun)
      self.IP.set_text('Running on: %s' % ip)
        
#       #REAL TIME HEAD MOTION BAR------------------------------------------------------------
      #self.colobarRT    = mpl.colors.ListedColormap(['c', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
      #self.normRT       = mpl.colors.Normalize(vmin=0, vmax=5.0)
      #self.bounds       = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4.0, 4.5, 5]
      #self.normRT       = mpl.colors.BoundaryNorm(self.bounds, self.colobarRT.N)
      #self.bargraphRT   = mpl.colorbar.ColorbarBase(self.AxisRT, self.colobarRT,
       #                                 self.normRT,
       #                                 orientation='vertical')
      #self.bargraphRT.set_label('Real Time Head Motion')
      
      #Rectangle to fill the bar------------------------------------------------------------
      self.rectangleRT    = Rectangle((0.0, 0), 1, 1, facecolor='white')
      currentAxis         = self.figure.gca()
      currentAxis.add_patch(self.rectangleRT)
      
      #ACCUMULATIVE HEAD MOTION BAR---------------------------------------------------------
      self.AxisACC        = self.figure.add_axes([0.6, 0.05, 0.2, 0.6]) 
      
      #self.colobarACC   = mpl.colors.ListedColormap(['c', 'y', 'r'])
      #self.normACC      = mpl.colors.Normalize(vmin=0, vmax=25)
      
      #self.boundsACC    = [0, 5, 10, 15, 20, 25]
      #self.normACC      = mpl.colors.BoundaryNorm(self.boundsACC, self.colobarACC.N)
      #self.bargraphACC  = mpl.colorbar.ColorbarBase(self.AxisACC, cmap=self.colobarACC,
      #                             norm=self.normACC,
      #                             orientation='vertical')
      #self.bargraphACC.set_label('Number of motions detected')
      
      self.AxisACC.text(-0.1, 1.15, 'TR with motion', fontdict=fontmediun)
      self.NMotionText = self.AxisACC.text(0.18, 1, "- - -", fontdict=fontTRNumber)
      
      #Rectangle to fill the bar------------------------------------------------------------
      self.rectangleACC    = Rectangle((0.0, 0), 1, 1, facecolor='white')
      currentAxis          = self.figure.gca()
      currentAxis.add_patch(self.rectangleACC)
      
      #Excessive motion text----------------------------------------------------------------
      self.textExcessive = self.figure.text(0.1, 0.5, 'Excessive motion. Stop the Scan!', color='white', 
          bbox=dict(facecolor='red', edgecolor='red'))
      self.textExcessive.set_size('x-large')
      self.textExcessive.set_visible(False)
      
      TIMER_ID = 100  # pick a number
      self.timer = wx.Timer(self, TIMER_ID)
      self.Bind(wx.EVT_TIMER, self.OnTimer)
      
      # Add a panel so it looks correct on all platforms
      self.panel = wx.Panel(self, size=(400,400),pos=(0,0))
      
      self.labelInitText = wx.StaticText(self.panel, wx.ID_ANY, 'Please insert the exam info:', (85, 50), (160, -1), wx.ALIGN_CENTER)
      font2 = wx.Font(12, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)
      self.labelInitText.SetFont(font2)
      self.labelInitText.SetForegroundColour((47,79,79)) # set text color
      
      self.TitlePanel = wx.StaticText(self.panel,-1,'fMRI Motion Viewer', (110, 10), (400, -1), wx.ALIGN_CENTER)
      font = wx.Font(14, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)
      self.TitlePanel.SetFont(font)
      self.TitlePanel.SetForegroundColour((0,191,255)) # set text color
      
      self.labelInputOne = wx.StaticText(self.panel, wx.ID_ANY, 'Head Motion Limit [0 - 2.0]', (85, 80), (160, -1), wx.ALIGN_CENTER)
      font2 = wx.Font(12, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)
      self.labelInputOne.SetFont(font2)
      self.labelInputOne.SetForegroundColour((47,79,79)) # set text color
      self.inputTxtOne = wx.TextCtrl(self.panel,wx.ID_ANY,'',pos=(85,100))
      self.inputTxtOne.WriteText('0.9')
      
      self.labelInputTwo = wx.StaticText(self.panel, wx.ID_ANY, 'Acceptable Head Motions [0 - 20]', (85, 140), (160, -1), wx.ALIGN_CENTER)
      self.labelInputTwo.SetFont(font2)
      self.labelInputTwo.SetForegroundColour((47,79,79)) # set text color
      self.inputTxtTwo = wx.TextCtrl(self.panel, wx.ID_ANY, '',pos=(85,160))
      self.inputTxtTwo.WriteText('15')
      
      self.labelHelp = wx.TextCtrl(parent = self.panel, id = -1, pos = (20, 210), size = (360, 100), style = wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_AUTO_URL)
      self.labelHelp.AppendText("Note: This system was developed to detect excessive head motion in fMRI exams. For this it calculates the Euclidean norm of derivative of six degrees of freedom of the head.\n")
      
      self.okBtn = wx.Button(self.panel, wx.ID_ANY, 'Start   ',(85, 340), (60, -1), wx.ALIGN_CENTER)
      self.cancelBtn = wx.Button(self.panel, wx.ID_ANY, 'Quit   ',(255, 340), (60, -1), wx.ALIGN_CENTER)
      #self.HelpBtn = wx.Button(self.panel, wx.ID_ANY, 'Help  ',(255, 320), (60, -1), wx.ALIGN_CENTER)
      self.Bind(wx.EVT_BUTTON, self.onOK, self.okBtn)
      self.Bind(wx.EVT_BUTTON, self.onCancel, self.cancelBtn)
      self.Bind(wx.EVT_CLOSE, self.onCancel)  #Bind the EVT_CLOSE event to closeWindow()

      self.Show(True)

   def onOK(self, event):
        self.NMotion = int(self.inputTxtTwo.GetValue())
        self.TRESHOLDRT = float(self.inputTxtOne.GetValue())
        
        if self.TRESHOLDRT == 0.1:
           self.colobarRT    = mpl.colors.ListedColormap(['r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 0.2:    
           self.colobarRT    = mpl.colors.ListedColormap(['y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 0.3:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 0.4:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 0.5:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 0.6:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 0.7:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 0.8:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 0.9:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.0:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.1:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.2:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.3:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.4:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.5:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.6:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.7:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.8:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 1.9:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r'])
        elif self.TRESHOLDRT == 2.0:    
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'y', 'r', 'r'])
        else: 
           self.colobarRT    = mpl.colors.ListedColormap(['c', 'c', 'c', 'y', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        #REAL TIME HEAD MOTION BAR------------------------------------------------------------self.TRNumberText.set_text('%d' % self.TRNumber)
        self.normRT       = mpl.colors.Normalize(vmin=0, vmax=2.0)
        self.bounds       = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0]
        self.normRT       = mpl.colors.BoundaryNorm(self.bounds, self.colobarRT.N)
        self.bargraphRT   = mpl.colorbar.ColorbarBase(self.AxisRT, self.colobarRT,
                                       self.normRT,
                                       orientation='vertical')
        self.bargraphRT.set_label('Real Time Head Motion')
        
        if self.NMotion == 1:
           self.colobarACC    = mpl.colors.ListedColormap(['r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 2:    
           self.colobarACC    = mpl.colors.ListedColormap(['y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 3:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 4:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 5:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 6:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 7:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 8:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 9:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 10:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 11:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 12:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 13:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 14:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 15:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 16:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 17:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 18:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r', 'r'])
        elif self.NMotion == 19:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'r', 'r', 'r'])
        elif self.NMotion == 20:    
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'y', 'y', 'y', 'y', 'r', 'r'])
        else: 
           self.colobarACC    = mpl.colors.ListedColormap(['c', 'c', 'c', 'y', 'y', 'y', 'y', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'])

        self.normACC      = mpl.colors.Normalize(vmin=0, vmax=20)
      
        self.boundsACC    = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
        self.normACC      = mpl.colors.BoundaryNorm(self.boundsACC, self.colobarACC.N)
        self.bargraphACC  = mpl.colorbar.ColorbarBase(self.AxisACC, cmap=self.colobarACC,
                                     norm=self.normACC,
                                     orientation='vertical')
        self.bargraphACC.set_label('Number of motions detected')
        
        #N-MOTIONS TRESHOLD-------------------------------------------------------------------
        self.pointsACC = np.ones(5)
        self.AxisACC.plot((self.NMotion/20.0) * self.pointsACC, linestyle='-', color='blue', linewidth=3)
        
        #self.MotionConfig.set_text('Head Motion Limit: %2.1f' % float(self.inputTxtOne.GetValue()))
        #self.NMotionsConfig.set_text('Acceptable Head Motions: %d' % int(self.inputTxtTwo.GetValue()))
             
        #Treshold configured to RT Motion bar-------------------------------------------------
        self.points       = np.ones(5)
        self.AxisRT.plot((self.TRESHOLDRT/2.0)*self.points, linestyle='-', color='blue', linewidth=3)
        
        self.timer.Start(100)    # 1 second interval  
        self.panel.Show(False)

   def onCancel(self, event):  
      PROCNAME = "afni"
      for proc in psutil.process_iter():
         # check whether the process name matches
	 if proc.name() == PROCNAME:
            proc.kill()	
      PROCNAME = "python"
      for proc in psutil.process_iter():
         # check whether the process name matches
	 if proc.name() == PROCNAME:
            proc.kill()
      PROCNAME = "demo.2.fback.4"
      for proc in psutil.process_iter():
         # check whether the process name matches
	 if proc.name() == PROCNAME:
            proc.kill()
      PROCNAME = "demo.2.fback.1"
      for proc in psutil.process_iter():
         # check whether the process name matches
	 if proc.name() == PROCNAME:
            proc.kill()
      self.Destroy()
        
   def cb_keypress(self, event):
      if event.key == 'q':
         self.Close()
         
   def set_TR(self, data):
      self.TRNumber = data
      self.TRNumberText.set_text('%d' % self.TRNumber)
      
   def set_ACCmotionBar(self, data):
      self.rectangleACC.set_y(data)

   def set_limits(self, xmin=1.0, xmax=0.0, ymin=1.0, ymax=0.0):
      """if xmin < xmax: apply, and similarly for y"""
      if xmin < xmax:
         self.xmin = xmin
         self.xmax = xmax
         if self.verb > 2: print '-- resetting xlimits to:', xmin, xmax
      if ymin < ymax:
         self.ymin = ymin
         self.ymax = ymax
         if self.verb > 2: print '-- resetting ylimits to:', ymin, ymax

   def plot_data(self, data, title=''):
      """plot data
         style can be 'graph' or 'bar'"""
      if self.ax == None:
         self.ax = self.rectangleRT.set_y(data/2.0)
         self.MotionLimitText.set_text('%1.2f mm' % data)
      
      print data
      
      if data > self.TRESHOLDRT:
         self.ACCmotionstatus += 1
         self.NMotionText.set_text("%3d" % self.ACCmotionstatus)
         if self.ACCmotionstatus < 26:
             self.rectangleACC.set_y(self.ACCmotionstatus/20.0)
             
             if self.ACCmotionstatus >= self.NMotion and self.TRNumber <= 30:
                 self.MotionDetected = 1

      #else: 
      #   self.textExcessive.set_visible(False)
         
      self.canvas.draw()

   def exit(self):
      PROCNAME = "afni"
      for proc in psutil.process_iter():
         # check whether the process name matches
	 if proc.name() == PROCNAME:
            proc.kill()	
      self.Destroy()
      
   def OnTimer(self, event):
      self.adata = LAD.Afni1D('motion.1D', verb=self.verb)
      #print '-- TR: %d' % self.adata.mat[0][0]
      if self.adata.mat[0][0] != self.TRNumber:  
          self.eucMotion = self.adata.mat[0][1]
          self.set_TR(self.adata.mat[0][0])
          self.motiondetectionacc = self.motiondetectionacc + self.eucMotion
          self.MotionConfig.set_text('Accumulated motion: %2.2f mm' % float(self.motiondetectionacc))
          print '-- Euclidean Motion: %f' % self.adata.mat[0][1]
          self.plot_data(self.eucMotion)

#      if self.TRNumber == 30 and self.motiondetectionacc < (self.TRESHOLDRT*17):
      if self.TRNumber == 30 and self.ACCmotionstatus < self.NMotion:
         self.NMotionsConfig.set_text('Head motion trend: PASS')
#      elif self.TRNumber == 30 and self.motiondetectionacc > (self.TRESHOLDRT*17):
      elif self.TRNumber <= 30 and self.ACCmotionstatus > self.NMotion:
         self.NMotionsConfig.set_text('Head motion trend: FAIL')
      elif self.TRNumber < 30:
         self.NMotionsConfig.set_text('Head motion trend: Analyzing...') 


      if self.TRNumber <= 2:
         self.textExcessive.set_visible(False)
         self.ACCmotionstatus = 0
         self.rectangleACC.set_y(self.ACCmotionstatus/20.0)
         self.MotionDetected = 0 
         self.NMotionText.set_text("%3d" % self.ACCmotionstatus)   
         self.motiondetectionacc = 0 
         self.MotionConfig.set_text('Accumulated motion: 0.00')
         self.NMotionsConfig.set_text('Head motion trend: Waiting...')

      if self.MotionDetected == 1:
          #self.counter += 1
          #if self.counter < 10:
              self.textExcessive.set_visible(True)
          #elif self.counter < 20:
          #    self.textExcessive.set_visible(False)
          #else:
          #    self.counter = 0           
def main():

    wx_app = wx.App()
    demo_frame = CanvasFrame(title='Brain Institute - BraIns - Porto Alegre')
    demo_frame.EnableCloseButton(True)
    demo_frame.Show(True)
    wx_app.MainLoop()

if __name__ == '__main__':
   sys.exit(main())

