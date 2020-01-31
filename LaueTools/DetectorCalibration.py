from __future__ import absolute_import
r"""
DetectorCalibration.py is a GUI for microdiffraction Laue Pattern simulation to help visually
to match and exp. and theo. Laue patterns for mainly Detector geometry Calibration purpose.

This module belongs to the open source LaueTools project
with a free code repository at at gitlab.esrf.fr

(former version with python 2.7 at https://sourceforge.net/projects/lauetools/)

or for python3 and 2 in

https://gitlab.esrf.fr/micha/lauetools

J. S. Micha August 2019
mailto: micha --+at-+- esrf --+dot-+- fr
"""
import os
import time
import copy
import sys
import math
import numpy as np

import wx

if wx.__version__ < "4.":
    WXPYTHON4 = False
else:
    WXPYTHON4 = True
    wx.OPEN = wx.FD_OPEN
    wx.CHANGE_DIR = wx.FD_CHANGE_DIR

    def sttip(argself, strtip):
        return wx.Window.SetToolTip(argself, wx.ToolTip(strtip))

    wx.Window.SetToolTipString = sttip

from matplotlib.ticker import FuncFormatter

from matplotlib import __version__ as matplotlibversion
from matplotlib.backends.backend_wxagg import (FigureCanvasWxAgg as FigCanvas,
                                                NavigationToolbar2WxAgg as NavigationToolbar)

from matplotlib.figure import Figure

if sys.version_info.major == 3:
    from . import dict_LaueTools as DictLT
    from . import LaueGeometry as F2TC
    from . import indexingAnglesLUT as INDEX
    from . import indexingImageMatching as IIM
    from . import matchingrate
    from . import lauecore as LAUE
    from . import findorient as FindO
    from . import FitOrient as FitO
    from . import spotslinkeditor as SLE
    from . import LaueSpotsEditor as LSEditor
    from . import generaltools as GT
    from . import IOLaueTools as IOLT
    from . import CrystalParameters as CP
    from . import DetectorParameters as DP
    from . ResultsIndexationGUI import RecognitionResultCheckBox
    from . import OpenSpotsListFileGUI as OSLFGUI
    from . import orientations as ORI

else:

    import dict_LaueTools as DictLT
    import LaueGeometry as F2TC
    import indexingAnglesLUT as INDEX
    import indexingImageMatching as IIM
    import matchingrate
    import lauecore as LAUE
    import findorient as FindO
    import FitOrient as FitO
    import spotslinkeditor as SLE
    import LaueSpotsEditor as LSEditor
    import generaltools as GT
    import IOLaueTools as IOLT
    import CrystalParameters as CP
    import DetectorParameters as DP
    from ResultsIndexationGUI import RecognitionResultCheckBox
    import OpenSpotsListFileGUI as OSLFGUI
    import orientations as ORI


DEG = DictLT.DEG
PI = DictLT.PI
CST_ENERGYKEV = DictLT.CST_ENERGYKEV

# --- sub class panels
class PlotRangePanel(wx.Panel):
    """
    class for panel dealing with plot range and kf_direction
    """
    def __init__(self, parent):
        """
        """
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.mainframe = parent.GetParent().GetParent()
        self.mainframeparent = parent.GetParent().GetParent().GetParent()

        print("mainframe in PlotRangePanel", self.mainframe)

        openbtn = wx.Button(self, -1, "Import Spots List", (5, 5), (200, 60))
        openbtn.Bind(wx.EVT_BUTTON, self.opendata)

        pos5b = 75

        t1 = wx.StaticText(self, -1, "2theta Range:", (2, pos5b))
        t2 = wx.StaticText(self, -1, "Chi Range:", (2, pos5b + 30))

        self.mean2theta = wx.TextCtrl(self, -1, "90", (120, pos5b), (40, -1))
        self.meanchi = wx.TextCtrl(self, -1, "0", (120, pos5b + 30), (40, -1))
        wx.StaticText(self, -1, "+/-", (170, pos5b))
        wx.StaticText(self, -1, "+/-", (170, pos5b + 30))
        self.range2theta = wx.TextCtrl(self, -1, "45", (200, pos5b))
        self.rangechi = wx.TextCtrl(self, -1, "40", (200, pos5b + 30))

        self.mean2theta.Bind(wx.EVT_TEXT, self.set_init_plot_True)
        self.meanchi.Bind(wx.EVT_TEXT, self.set_init_plot_True)
        self.range2theta.Bind(wx.EVT_TEXT, self.set_init_plot_True)
        self.rangechi.Bind(wx.EVT_TEXT, self.set_init_plot_True)

        self.shiftChiOrigin = wx.CheckBox(
            self, -1, "Shift Chi origin of Exp. Data", (2, pos5b + 60))
        self.shiftChiOrigin.SetValue(False)

        t5 = wx.StaticText(self, -1, "SpotSize", (2, pos5b+90))
        self.spotsizefactor = wx.TextCtrl(self, -1, "1.", (200, pos5b+90))

        # Warning button id is 52
        b3 = wx.Button(self, 52, "Update Plot", (5, pos5b+130), (200, 60))

        # tooltips
        tp1 = "raw central value (deg) of 2theta on CCD camera (kf scattered vector is defined by 2theta and chi)"
        tp2 = "raw central value (deg) of chi on CCD camera (kf scattered vector is defined by 2theta and chi)"
        tp3 = "range amplitude (deg) around the central 2theta value"
        tp4 = "range amplitude (deg) around the central chi value"

        tp5 = "Set experimental spots radius"

        tpb3 = "Replot simulated Laue spots"

        t1.SetToolTipString(tp1)
        self.mean2theta.SetToolTipString(tp1)

        t2.SetToolTipString(tp2)
        self.meanchi.SetToolTipString(tp2)

        t5.SetToolTipString(tp5)
        self.meanchi.SetToolTipString(tp3)

        self.range2theta.SetToolTipString(tp3)
        self.rangechi.SetToolTipString(tp4)

        self.shiftChiOrigin.SetToolTipString(
            "Check to shift the chi angles of experimental spots by the central chi value")

        b3.SetToolTipString(tpb3)

    def set_init_plot_True(self, _):
        print("reset init_plot to True")
        self.mainframe.init_plot = True

    def opendata(self, evt):
        """import list of spots
        """
        OSLFGUI.OnOpenPeakList(self.mainframe)

        selectedFile = self.mainframe.DataPlot_filename

        print("Selected file ", selectedFile)

        self.mainframe.initialParameter["dirname"] = self.mainframe.dirname
        self.mainframe.initialParameter["filename"] = selectedFile

        # prefix_filename, extension_filename = self.DataPlot_filename.split('.')
        prefix_filename = selectedFile.rsplit(".", 1)[0]

        # get PeakListDatFileName
        # cor file have been created from .dat  if name is dat_#######.cor
        if prefix_filename.startswith("dat_"):
            CalibrationFile = prefix_filename[4:] + ".dat"

            if not CalibrationFile in os.listdir(self.mainframe.dirname):
                wx.MessageBox('%s corresponding to the .dat file (all peaks properties) of %s is missing. \nPlease, change the name of %s (remove "dat_" for instance) to work with %s but without peaks properties (shape, size, Imax, etc...)'%(CalibrationFile, selectedFile, selectedFile, selectedFile),'Info')
                raise ValueError('%s corresponding to .dat file of %s is missing. Change the name of %s (remove "dat_" for instance)'%(CalibrationFile,selectedFile,selectedFile))

        else:
            CalibrationFile = selectedFile

        print("Calibrating with file: %s" % CalibrationFile)

        self.mainframe.filename = CalibrationFile

        self.mainframe.CCDParam = self.mainframe.defaultParam
        self.mainframe.ccdparampanel.pixelsize_txtctrl.SetValue(str(self.mainframe.pixelsize))
        self.mainframe.ccdparampanel.detectordiameter_txtctrl.SetValue(str(self.mainframe.detectordiameter))

        self.mainframe.update_data(evt)


class CrystalParamPanel(wx.Panel):
    """
    class for crystal simulation parameters
    """

    def __init__(self, parent):
        """
        """
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.mainframe = parent.GetParent().GetParent()

        self.UBmatrix = np.eye(3)

        # print("self.mainframe in CrystalParamPanel", self.mainframe)
        # widgets layout
        pos6 = 10
        deltaposx = 2
        t1 = wx.StaticText(self, -1, "Energy min/max(keV): ", (deltaposx, pos6 - 5))
        self.eminC = wx.SpinCtrl(
            self, -1, "5", (150 + deltaposx, pos6 - 5), (60, -1), min=5, max=149)
        self.emaxC = wx.SpinCtrl(
            self, -1, "22", (180 + deltaposx + 50, pos6 - 5), (60, -1), min=6, max=150)

        pos7 = pos6 + 60
        self.listsorted_materials = sorted(DictLT.dict_Materials.keys())
        t2 = wx.StaticText(self, -1, "Element", (deltaposx, pos7 - 30))
        self.comboElem = wx.ComboBox(self, -1, "Si", (150 + deltaposx, pos7 - 30),
                                        choices=self.listsorted_materials,
                                        style=wx.CB_READONLY)

        t3 = wx.StaticText(self, -1, "Tmatrix", (deltaposx, pos7))  # in sample Frame columns are a*,b*,c* expressed in is,js,ks vector frame
        self.comboBmatrix = wx.ComboBox(self,
                                            2424,
                                            "Identity",
                                            (150 + deltaposx, pos7),
                                            choices=sorted(DictLT.dict_Transforms.keys()),
                                            style=wx.CB_READONLY)

        pos7b = pos7 + 30
        t4 = wx.StaticText(self, -1, "Orient Matrix (UB)", (deltaposx, pos7b))
        self.comboMatrix = wx.ComboBox(self,
                                        2525,
                                        "Identity",
                                        (150 + deltaposx, pos7b),
                                        choices=list(DictLT.dict_Rot.keys()))

        self.btn_mergeUB = wx.Button(self, -1, "set UB with B", (deltaposx + 400, pos7b))

        pos7c = pos7 + 65
        t5 = wx.StaticText(self, -1, "Extinctions", (deltaposx, pos7c))
        self.comboExtinctions = wx.ComboBox(self,
                                            -1,
                                            "Diamond",
                                            (150 + deltaposx, pos7c),
                                            choices=list(DictLT.dict_Extinc.keys()))

        self.comboExtinctions.Bind(wx.EVT_COMBOBOX, self.mainframe.OnChangeExtinc)
        #         self.comboTransforms.Bind(wx.EVT_COMBOBOX, self.mainframe.OnChangeTransforms)

        pos7d = pos7 + 100
        vertical_shift = 7
        b1 = wx.Button(self, 1010, "Enter UB", (deltaposx, pos7d + vertical_shift), (100, 40))
        b2 = wx.Button(self, 1011, "Store UB", (deltaposx + 120, pos7d + vertical_shift), (100, 40))
        btn_sortUBsname = wx.Button(self, 1011, "sort UBs name",
                                    (deltaposx + 240, pos7d + vertical_shift), (120, 40))
        
        btnReloadMaterials = wx.Button( self, -1, "Reload Materials",
                                    (deltaposx + 370, pos7d + vertical_shift), (120, 40))

        # warning button id =52 is common with an other button
        b3 = wx.Button(self, 52, "Replot Simul.", (deltaposx, pos7d + 60), (400, 40))

        # event handling
        self.emaxC.Bind(wx.EVT_SPINCTRL, self.mainframe.OnCheckEmaxValue)
        self.eminC.Bind(wx.EVT_SPINCTRL, self.mainframe.OnCheckEminValue)
        self.comboElem.Bind(wx.EVT_COMBOBOX, self.mainframe.OnChangeElement)
        self.Bind(wx.EVT_COMBOBOX, self.mainframe.OnChangeBMatrix, id=2424)
        self.btn_mergeUB.Bind( wx.EVT_BUTTON, self.mainframe.onSetOrientMatrix_with_BMatrix)
        self.Bind(wx.EVT_COMBOBOX, self.mainframe.OnChangeMatrix, id=2525)
        self.Bind(wx.EVT_BUTTON, self.mainframe.EnterMatrix, id=1010)
        btn_sortUBsname.Bind(wx.EVT_BUTTON, self.onSortUBsname)

        btnReloadMaterials.Bind(wx.EVT_BUTTON, self.OnLoadMaterials)

        # tootips
        tp1 = "Energy minimum and maximum for simulated Laue Pattern spots"

        tp2 = "Element or material label (key of in Material dictionary)"

        #        tp3 = 'Matrix B in formula relating q vector = kf-ki and reciprocal vector nodes G*.\n'
        #        tp3 += 'q = U B B0 G* where U is the orientation matrix where B0 is the initial unit cell basis vectors orientation given by dictionary of elements.\n'
        #        tp3 += 'Each column of B0 is a reciprocal unit cell basis vector (among a*, b* and c*) expressed in Lauetools frame.\n'
        #        tp3 += 'B can then correspond to an initial state of rotation (to describe twin operation) or strain of the initial unit cell.'
        #
        tp3 = "The columns of the U*B*B0 matrix are the components of astar, bstar and cstar vectors (forming the Rstar frame) in the Rlab frame. \n"
        tp3 += "U is a pure rotation matrix \n"
        tp3 += "B is a triangular up matrix (strain + rotation), usually close to Identity (within 1e-3) \n"
        tp3 += 'B0 gives the initial shape of the reciprocal unit cell, as calculated from the lattice parameters defined by the "Material or Structure" parameter. \n'
        tp3 += "The columns of B0 are the components of astar bstar cstar on Rstar0.\n"
        tp3 += "Rstar0 is the cartesian frame built by orthonormalizing Rstar with Schmidt process. \n"
        tp3 += "Matrix T allows to apply a transform to a U*B0 matrix (preferably without B) via the formula U*T*B0 : \n"
        tp3 += "For example :\n"
        tp3 += "T = U2 (pure rotation) allows to switch to a twin orientation. \n"
        tp3 += "T = Eps (pure strain, symmetric) or T=B (triangular up) allows to change the shape of the unit cell. \n"

        #        tp3 = 'Matrix B in formula relating q vector = kf-ki and reciprocal vector nodes G*.\n'
        #        tp3 += 'q = U B B0 G* where U is the orientation matrix where B0 is the initial unit cell basis vectors orientation given by dictionary of elements.\n'
        #        tp3 += 'Each column of B0 is a reciprocal unit cell basis vector (among a*, b* and c*) expressed in Lauetools frame.\n'
        #        tp3 += 'B can then correspond to an initial state of rotation (to describe twin operation) or strain of the initial unit cell.'

        tp4 = "Orientation (and strained) Matrix UB. see explanations for B0 matrix"
        tp5 = "Set Extinctions rules due to special atoms positions in the unit cell"

        tpb1 = "Enter the 9 numerical elements for orientation matrix UB (not UB*B0 !)"
        tpb2 = "Store current orientation matrix UB in LaueToolsGUI"
        tpb3 = "Replot simulated Laue spots"

        # OR
        tpsetub = "inject current T transformation matrix into current UB matrix\n"
        tpsetub += "and reset T matrix to Identity.\n"
        tpsetub += "UB_new = UB_old * T \n"
        tpsetub += "typical use : UB_old = pure rotation U, T1 = twin transform, T2 = shear strain\n"

        # as UB*B. From q=UB B B0 G* to q= UBnew B0 G*'

        t1.SetToolTipString(tp1)
        t2.SetToolTipString(tp2)
        self.comboElem.SetToolTipString(tp2)
        t3.SetToolTipString(tp3)
        self.comboBmatrix.SetToolTipString(tp3)

        t4.SetToolTipString(tp4)
        self.comboMatrix.SetToolTipString(tp4)

        t5.SetToolTipString(tp5)
        self.comboExtinctions.SetToolTipString(tp5)

        b1.SetToolTipString(tpb1)
        b2.SetToolTipString(tpb2)
        b3.SetToolTipString(tpb3)

        self.btn_mergeUB.SetToolTipString(tpsetub)

        tipsportUBs = 'Sort Orientation Matrix name by alphabetical order'
        btn_sortUBsname.SetToolTipString(tipsportUBs)

        tipreloadMat = 'Reload Materials from dict_Materials file'
        btnReloadMaterials.SetToolTipString(tipreloadMat)

    def onSortUBsname(self, _):
        listrot = list(DictLT.dict_Rot.keys())
        listrot = sorted(listrot, key=str.lower)
        self.comboMatrix.Clear()
        self.comboMatrix.AppendItems(listrot)

    def OnLoadMaterials(self, _):
        # self.mainframe.GetParent().OnLoadMaterials(1)
        # loadedmaterials = self.mainframe.GetParent().dict_Materials

        wcd = "All files(*)|*|dict_Materials files(*.dat)|*.mat"
        _dir = os.getcwd()
        open_dlg = wx.FileDialog(
                                self,
                                message="Choose a file",
                                defaultDir=_dir,
                                defaultFile="",
                                wildcard=wcd,
                                style=wx.OPEN
                            )
        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()

            try:
                loadedmaterials = DictLT.readDict(path)

                DictLT.dict_Materials = loadedmaterials

            except IOError as error:
                dlg = wx.MessageDialog(self, "Error opening file\n" + str(error))
                dlg.ShowModal()

            except UnicodeDecodeError as error:
                dlg = wx.MessageDialog(self, "Error opening file\n" + str(error))
                dlg.ShowModal()

            except ValueError as error:
                dlg = wx.MessageDialog(self, "Error opening file: Something went wrong when parsing materials line\n" + str(error))
                dlg.ShowModal()

        open_dlg.Destroy()

        self.mainframe.dict_Materials = loadedmaterials
        self.comboElem.Clear()
        elements_keys = sorted(loadedmaterials.keys())
        self.comboElem.AppendItems(elements_keys)

        if self.mainframe.GetParent():
            self.mainframe.GetParent().dict_Materials = loadedmaterials


class CCDParamPanel(wx.Panel):
    """
    class panel for CCD detector parameters
    """

    # ----------------------------------------------------------------------
    def __init__(self, parent):
        """
        """
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.mainframe = parent.GetParent().GetParent()

        # print("self.mainframe in CCDParamPanel", self.mainframe)

        self.init_pixelsize = self.mainframe.pixelsize
        self.init_detectordiameter = self.mainframe.detectordiameter

        #         wx.Button(self, 101, 'Set CCD Param.', (5, 5))
        #         self.Bind(wx.EVT_BUTTON, self.mainframe.OnInputParam, id=101)

        txtpixelsize = wx.StaticText(self, -1, "Pixelsize")
        txtdetdiam = wx.StaticText(self, -1, "Det. diameter")

        self.pixelsize_txtctrl = wx.TextCtrl(self, -1, str(self.mainframe.pixelsize))
        self.detectordiameter_txtctrl = wx.TextCtrl(
            self, -1, str(self.mainframe.detectordiameter)
        )

        btnaccept = wx.Button(self, -1, "Accept")
        btnaccept.Bind(wx.EVT_BUTTON, self.onAccept)

        if WXPYTHON4:
            grid = wx.GridSizer(2, 10, 10)
        else:
            grid = wx.GridSizer(3, 2)

        grid.Add(txtpixelsize)
        grid.Add(self.pixelsize_txtctrl)
        grid.Add(txtdetdiam)
        grid.Add(self.detectordiameter_txtctrl)
        grid.Add(btnaccept)
        grid.Add(wx.StaticText(self, -1, ""))

        self.SetSizer(grid)

    def onAccept(self, evt):
        print("accept")
        ps = float(self.pixelsize_txtctrl.GetValue())
        detdiam = float(self.detectordiameter_txtctrl.GetValue())

        self.mainframe.pixelsize = ps
        self.mainframe.detectordiameter = detdiam

        print("new self.mainframe.pixelsize", self.mainframe.pixelsize)

        self.mainframe._replot(evt)


class DetectorParametersDisplayPanel(wx.Panel):
    """
    class panel to display and modify CCD parameters
    """
    def __init__(self, parent):
        """
        """
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.granparent = parent.GetParent()

        self.CCDParam = self.granparent.CCDParam

        sizetxtctrl = wx.Size(70, -1)

        # current values
        self.act_distance = wx.TextCtrl(self, -1, str(self.CCDParam[0]), size=sizetxtctrl,
                                                style=wx.TE_PROCESS_ENTER)
        self.act_Xcen = wx.TextCtrl(self, -1, str(self.CCDParam[1]), size=sizetxtctrl,
                                                style=wx.TE_PROCESS_ENTER)
        self.act_Ycen = wx.TextCtrl(self, -1, str(self.CCDParam[2]), size=sizetxtctrl,
                                                style=wx.TE_PROCESS_ENTER)
        self.act_Ang1 = wx.TextCtrl(self, -1, str(self.CCDParam[3]), size=sizetxtctrl,
                                                style=wx.TE_PROCESS_ENTER)
        self.act_Ang2 = wx.TextCtrl(self, -1, str(self.CCDParam[4]), size=sizetxtctrl,
                                                style=wx.TE_PROCESS_ENTER)

        self.act_distance.Bind(wx.EVT_TEXT_ENTER, self.granparent.OnSetCCDParams)
        self.act_Xcen.Bind(wx.EVT_TEXT_ENTER, self.granparent.OnSetCCDParams)
        self.act_Ycen.Bind(wx.EVT_TEXT_ENTER, self.granparent.OnSetCCDParams)
        self.act_Ang1.Bind(wx.EVT_TEXT_ENTER, self.granparent.OnSetCCDParams)
        self.act_Ang2.Bind(wx.EVT_TEXT_ENTER, self.granparent.OnSetCCDParams)

        resultstxt = wx.StaticText(self, -1, "Refined Value")
        currenttxt = wx.StaticText(self, -1, "Current&Set Value")

        # values resulting from model refinement
        self.act_distance_r = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY, size=sizetxtctrl
        )
        self.act_Xcen_r = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY, size=sizetxtctrl
        )
        self.act_Ycen_r = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY, size=sizetxtctrl
        )
        self.act_Ang1_r = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY, size=sizetxtctrl
        )
        self.act_Ang2_r = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY, size=sizetxtctrl
        )

        if WXPYTHON4:
            grid = wx.GridSizer(6, 2, 2)
        else:
            grid = wx.GridSizer(3, 6)

        grid.Add(wx.StaticText(self, -1, ""))
        for txt in DictLT.CCD_CALIBRATION_PARAMETERS[:5]:
            grid.Add(wx.StaticText(self, -1, txt), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        grid.Add(currenttxt)
        for txtctrl in [self.act_distance,
                        self.act_Xcen,
                        self.act_Ycen,
                        self.act_Ang1,
                        self.act_Ang2]:
            grid.Add(txtctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            txtctrl.SetToolTipString("Current and Set new value (press enter)")
            txtctrl.SetSize(sizetxtctrl)

        grid.Add(resultstxt)
        for txtctrl in [self.act_distance_r,
                        self.act_Xcen_r,
                        self.act_Ycen_r,
                        self.act_Ang1_r,
                        self.act_Ang2_r]:
            grid.Add(txtctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            txtctrl.SetToolTipString("Fit result value")

        self.SetSizer(grid)

        # tooltips
        resultstxt.SetToolTipString("CCD detector plane parameters resulting from the best refined model"
        )
        currenttxt.SetToolTipString('Current CCD detector plane parameters. New parameters value can be entered in the corresponding field and accepted by pressing the "Accept" button'
        )


class MoveCCDandXtal(wx.Panel):
    """
    class panel to move CCD camera and crystal
    """
    # ----------------------------------------------------------------------
    def __init__(self, parent):
        """
        """
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.mainframe = parent.GetParent().GetParent()

        # print("self.mainframe in CCDParamPanel", self.mainframe)

        wx.StaticText(self, -1, "Sample-Detector Distance", (5, 10))
        wx.Button(self, 10, "-", (5, 30), (20, -1))
        wx.Button(self, 11, "+", (35, 30), (20, -1))
        wx.StaticText(self, -1, "step(mm)", (65, 30))
        self.stepdistance = wx.TextCtrl(self, -1, "0.5", (150, 30), (30, -1))
        self.cb_dd = wx.CheckBox(self, -1, "fit", (195, 30))
        self.cb_dd.SetValue(True)

        pos2 = 60
        wx.StaticText(self, -1, "X center", (5, pos2))
        wx.Button(self, 20, "-", (5, pos2 + 20), (20, -1))
        wx.Button(self, 21, "+", (35, pos2 + 20), (20, -1))
        wx.StaticText(self, -1, "step(pixel)", (65, pos2 + 20))
        self.stepXcen = wx.TextCtrl(self, -1, "20.", (150, pos2 + 20), (30, -1))
        self.cb_Xcen = wx.CheckBox(self, -1, "fit", (195, pos2 + 20))
        self.cb_Xcen.SetValue(True)

        pos3 = 110
        wx.StaticText(self, -1, "Y center", (5, pos3))
        wx.Button(self, 30, "-", (5, pos3 + 20), (20, -1))
        wx.Button(self, 31, "+", (35, pos3 + 20), (20, -1))
        wx.StaticText(self, -1, "step(pixel)", (65, pos3 + 20))
        self.stepYcen = wx.TextCtrl(self, -1, "20.", (150, pos3 + 20), (30, -1))
        self.cb_Ycen = wx.CheckBox(self, -1, "fit", (195, pos3 + 20))
        self.cb_Ycen.SetValue(True)

        pos4 = 160
        wx.StaticText(self, -1, "Angle xbet", (5, pos4))
        wx.Button(self, 40, "-", (5, pos4 + 20), (20, -1))
        wx.Button(self, 41, "+", (35, pos4 + 20), (20, -1))
        wx.StaticText(self, -1, "step(deg)", (65, pos4 + 20))
        self.stepang1 = wx.TextCtrl(self, -1, "1.", (150, pos4 + 20), (30, -1))
        self.cb_angle1 = wx.CheckBox(self, -1, "fit", (195, pos4 + 20))
        self.cb_angle1.SetValue(True)

        pos5 = 210
        wx.StaticText(self, -1, "Angle xgam", (5, pos5))
        wx.Button(self, 50, "-", (5, pos5 + 20), (20, -1))
        wx.Button(self, 51, "+", (35, pos5 + 20), (20, -1))
        wx.StaticText(self, -1, "step(deg)", (65, pos5 + 20))
        self.stepang2 = wx.TextCtrl(self, -1, "1.", (150, pos5 + 20), (30, -1))
        self.cb_angle2 = wx.CheckBox(self, -1, "fit", (195, pos5 + 20))
        self.cb_angle2.SetValue(True)

        # Angles buttons - crystal orientation
        posx = 280
        a1 = wx.StaticText(self, -1, "Angle 1", (posx, 10))
        wx.Button(self, 1000, "-", (posx, 30), (20, -1))
        wx.Button(self, 1100, "+", (posx + 30, 30), (20, -1))
        # wx.StaticText(self, -1, 'step(deg)',(960, 30))
        self.angle1 = wx.TextCtrl(self, -1, "1.", (posx + 80, 30), (35, -1))
        self.cb_theta1 = wx.CheckBox(self, -1, "fit", (posx + 130, 30))
        self.cb_theta1.SetValue(True)

        wx.StaticText(self, -1, "step(deg)", (posx + 100, 10))

        pos2 = 60
        a2 = wx.StaticText(self, -1, "Angle2", (posx, pos2))
        wx.Button(self, 2000, "-", (posx, pos2 + 20), (20, -1))
        wx.Button(self, 2100, "+", (posx + 30, pos2 + 20), (20, -1))
        # wx.StaticText(self, -1, 'step(deg)',(960, pos2+20))
        self.angle2 = wx.TextCtrl(self, -1, "1.", (posx + 80, pos2 + 20), (35, -1))
        self.cb_theta2 = wx.CheckBox(self, -1, "fit", (posx + 130, pos2 + 30))
        self.cb_theta2.SetValue(True)

        pos3 = 110
        a3 = wx.StaticText(self, -1, "Angle 3", (posx, pos3))
        wx.Button(self, 3000, "-", (posx, pos3 + 20), (20, -1))
        wx.Button(self, 3100, "+", (posx + 30, pos3 + 20), (20, -1))
        # wx.StaticText(self, -1, 'step(deg)',(960, pos3+20))
        self.angle3 = wx.TextCtrl(self, -1, "1.", (posx + 80, pos3 + 20), (35, -1))
        self.cb_theta3 = wx.CheckBox(self, -1, "fit", (posx + 130, pos3 + 30))
        self.cb_theta3.SetValue(True)

        self.EnableRotationLabel = "Select\nAxis\nand\nRotate"
        self.rotatebtn = wx.Button(
            self, -1, self.EnableRotationLabel, (posx, 180), (100, 100)
        )
        self.rotatebtn.Bind(wx.EVT_BUTTON, self.OnActivateRotation)
        stepangletxt = wx.StaticText(self, -1, "step(deg)", (posx + 100, 180))
        self.stepanglerot = wx.TextCtrl(self, -1, "10.", (posx + 100, 210), (35, -1))

        self.listofparamfitctrl = [
                                    self.cb_dd,
                                    self.cb_Xcen,
                                    self.cb_Ycen,
                                    self.cb_angle1,
                                    self.cb_angle2,  # detector param
                                    self.cb_theta1,
                                    self.cb_theta2,
                                    self.cb_theta3,
                                ]  # delta angle of orientation

        # tooltips
        a3.SetToolTipString("Angle 3: angle around z axis")
        a2.SetToolTipString("Angle 2: angle around y axis (horizontal and perp. to incoming beam)"
        )
        a1.SetToolTipString("Angle 1: angle around x axis (// incoming beam")

        rottip = ("Rotate crystal such as rotating the Laue Pattern around a selected axis.\n"
        )
        rottip += 'Click on a point in plot to select an invariant Laue spot by rotation. Then press "+" or "-" keys to rotation the pattern.\n'
        rottip += "Step angle can be adjusted (default 10 degrees).\n"
        rottip += "Press the Rotate button to disable the rotation and enable other functionnalities."
        self.rotatebtn.SetToolTipString(rottip)
        stepangletxt.SetToolTipString(rottip)
        self.stepanglerot.SetToolTipString(rottip)

    def OnActivateRotation(self, _):

        self.mainframe.RotationActivated = not self.mainframe.RotationActivated

        # clear previous rotation axis
        self.mainframe.SelectedRotationAxis = None

        if self.mainframe.RotationActivated:
            print("Activate Rotation around axis")
            self.rotatebtn.SetLabel("DISABLE\nRotation\naround\nselected Axis")
        else:
            print("Disable Rotation around axis")
            self.rotatebtn.SetLabel(self.EnableRotationLabel)


class StrainXtal(wx.Panel):
    """
    class panel to strain crystal
    """
    def __init__(self, parent):
        """
        """
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.mainframe = parent.GetParent().GetParent()

        # print("self.mainframe in CCDParamPanel", self.mainframe)

        self.key_material = self.mainframe.crystalparampanel.comboElem.GetValue()
        self.key_material_initparams_in_dict = copy.copy(DictLT.dict_Materials[self.key_material])
        self.lattice_parameters = copy.copy(DictLT.dict_Materials[self.key_material][1])

        if WXPYTHON4:
            grid = wx.FlexGridSizer(7, 10, 10)
        else:
            grid = wx.FlexGridSizer(7, 7)

        self.lattice_parameters_key = ["a", "b", "c", "alpha", "beta", "gamma"]

        self.dict_keyparam = {}
        for k, key_param in enumerate(self.lattice_parameters_key):
            self.dict_keyparam[key_param] = k

        self.lattice_parameters_dict = {}
        for k, key_param in enumerate(self.lattice_parameters_key):
            self.lattice_parameters_dict[key_param] = self.lattice_parameters[k]

        grid.Add(wx.StaticText(self, -1, ""))
        grid.Add(wx.StaticText(self, -1, "Current"))
        grid.Add(wx.StaticText(self, -1, ""))
        grid.Add(wx.StaticText(self, -1, ""))
        grid.Add(wx.StaticText(self, -1, "step"))
        grid.Add(wx.StaticText(self, -1, ""))
        grid.Add(wx.StaticText(self, -1, ""))

        units_list = ["Angstrom", "Angstrom", "Angstrom", "Degree", "Degree", "Degree"]

        for k, key_param in enumerate(self.lattice_parameters_key):

            minusbtn = wx.Button(self, -1, "-", size=(40, 30))
            plusbtn = wx.Button(self, -1, "+", size=(40, 30))
            stepctrl = wx.TextCtrl(self, -1, "0.05", size=(60, 30))
            fitchckbox = wx.CheckBox(self, -1, "fit")
            fitchckbox.SetValue(True)
            fitchckbox.Disable()
            currentctrl = wx.TextCtrl(self, -1, str(self.lattice_parameters_dict[key_param]),
                size=(60, -1), style=wx.TE_PROCESS_ENTER)

            setattr(self, "minusbtn_%s" % key_param, minusbtn)
            setattr(self, "plusbtn_%s" % key_param, plusbtn)
            setattr(self, "stepctrl_%s" % key_param, stepctrl)
            setattr(self, "fitchckbox_%s" % key_param, fitchckbox)
            setattr(self, "currentctrl_%s" % key_param, currentctrl)

            getattr(self, "minusbtn_%s" % key_param, minusbtn).myname = ("minusbtn_%s" % key_param)
            getattr(self, "plusbtn_%s" % key_param, plusbtn).myname = ("minusbtn_%s" % key_param)
            getattr(self, "currentctrl_%s" % key_param, currentctrl).myname = ("currentctrl_%s" % key_param)

            grid.Add(wx.StaticText(self, -1, key_param), 0)
            grid.Add(currentctrl, 0)
            grid.Add(minusbtn, 5)
            grid.Add(plusbtn, 10)
            grid.Add(stepctrl, 15)
            grid.Add(fitchckbox, 30)
            grid.Add(wx.StaticText(self, -1, "    %s" % units_list[k]), 30)

            #             print "'minusbtn_%s' % key_param", 'minusbtn_%s' % key_param
            #             print k
            #             print getattr(self, 'minusbtn_%s' % key_param)

            getattr(self, "plusbtn_%s" % key_param).Bind(
                wx.EVT_BUTTON, lambda event: self.ModifyLatticeParamsStep(event, "+"))
            getattr(self, "minusbtn_%s" % key_param).Bind(
                wx.EVT_BUTTON, lambda event: self.ModifyLatticeParamsStep(event, "-"))
            getattr(self, "currentctrl_%s" % key_param).Bind(wx.EVT_TEXT_ENTER,
                                                            self.ModifyLatticeParams)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(wx.StaticText(self, -1, "Crystal Lattice Parameters"), 0, wx.EXPAND)
        vbox.Add(grid, 0, wx.EXPAND)

        self.SetSizer(vbox)

    def update_latticeparameters(self):

        self.key_material = self.mainframe.crystalparampanel.comboElem.GetValue()
        self.key_material_initparams_in_dict = copy.copy(DictLT.dict_Materials[self.key_material])
        self.lattice_parameters = copy.copy(DictLT.dict_Materials[self.key_material][1])

        for k, key_param in enumerate(self.lattice_parameters_key):
            self.lattice_parameters_dict[key_param] = self.lattice_parameters[k]
            getattr(self, "currentctrl_%s" % key_param).SetValue(str(self.lattice_parameters[k]))

    def ModifyLatticeParamsStep(self, event, sign_of_step):
        """
        modify lattice parameters according to event.name and sign
        """

        #         print "sign_of_step", sign_of_step
        name = event.GetEventObject().myname
        #         print "name", name

        key_param = name.split("_")[-1]

        self.lattice_parameters_dict[key_param] = float(getattr(self,
                                                        "currentctrl_%s" % key_param).GetValue())

        if sign_of_step == "+":
            stepsign = 1.0
        elif sign_of_step == "-":
            stepsign = -1.0

        #         print "modify lattice parameter: %s and initial value: %.2f" % (key_param, self.lattice_parameters_dict[key_param])
        self.lattice_parameters_dict[key_param] += stepsign * float(getattr(self,
                                                            "stepctrl_%s" % key_param).GetValue()
        )

        # now building or updating an element in dict_Materials
        if "strained" not in self.key_material:
            new_key_material = "strained_%s" % self.key_material
        else:
            new_key_material = self.key_material

        DictLT.dict_Materials[new_key_material] = self.key_material_initparams_in_dict
        # update label
        DictLT.dict_Materials[new_key_material][0] = new_key_material

        if (self.mainframe.crystalparampanel.comboElem.FindString(new_key_material) == -1):
            print("adding new material in comboelement list")
            self.mainframe.crystalparampanel.comboElem.Append(new_key_material)

        new_lattice_params = []
        for _key_param in self.lattice_parameters_key:
            new_lattice_params.append(self.lattice_parameters_dict[_key_param])

        #         print "from self.lattice_parameters_dict", self.lattice_parameters_dict

        DictLT.dict_Materials[new_key_material][1] = new_lattice_params

        print("new lattice parameters", new_lattice_params)
        print("for material: %s" % new_key_material)

        getattr(self,
                "currentctrl_%s" % key_param).SetValue(str(self.lattice_parameters_dict[key_param]))

        self.mainframe.crystalparampanel.comboElem.SetValue(new_key_material)
        self.mainframe._replot(1)

    def ModifyLatticeParams(self, event):

        #         print "sign_of_step", sign_of_step

        name = event.GetEventObject().myname
        #         print "name", name

        key_param = name.split("_")[-1]

        self.lattice_parameters_dict[key_param] = float(getattr(self,
                                                        "currentctrl_%s" % key_param).GetValue())

        if "strained" not in self.key_material:
            new_key_material = "strained_%s" % self.key_material
        else:
            new_key_material = self.key_material

        DictLT.dict_Materials[new_key_material] = self.key_material_initparams_in_dict
        DictLT.dict_Materials[new_key_material][0] = new_key_material

        if (self.mainframe.crystalparampanel.comboElem.FindString(new_key_material) == -1):
            print("adding new material in comboelement list")
            self.mainframe.crystalparampanel.comboElem.Append(new_key_material)

        new_lattice_params = []
        for _key_param in self.lattice_parameters_key:
            new_lattice_params.append(self.lattice_parameters_dict[_key_param])

        DictLT.dict_Materials[new_key_material][1] = new_lattice_params

        print("new lattice parameters", new_lattice_params)
        print("for material: %s" % new_key_material)

        getattr(self, "currentctrl_%s" % key_param).SetValue(str(self.lattice_parameters_dict[key_param]))

        self.mainframe.crystalparampanel.comboElem.SetValue(new_key_material)
        self.mainframe._replot(1)

    def OnActivateRotation(self, _):

        self.mainframe.RotationActivated = not self.mainframe.RotationActivated

        if self.mainframe.RotationActivated:
            print("Activate Rotation around axis")
        else:
            print("Disable Rotation around axis")
            self.mainframe.SelectedRotationAxis = None


class TextFrame(wx.Frame):
    def __init__(self, parent, _id, strexpression, index=0):
        wx.Frame.__init__(self, parent, _id, "Matrix Store and Save", size=(500, 250))

        self.parent = parent
        self.index = index

        #         print "my parent is ", parent
        panel = wx.Panel(self, -1)
        matrixLabel = wx.StaticText(panel, -1, "Matrix Elements:")
        matrixText = wx.TextCtrl( panel, -1, strexpression, size=(490, 100),
                                                        style=wx.TE_MULTILINE | wx.TE_READONLY)
        #         matrixText.SetInsertionPoint(0)

        storeLabel = wx.StaticText(panel, -1, "Stored Matrix name: ")
        self.storeText = wx.TextCtrl(
            panel, -1, "storedMatrix_%d" % self.index, size=(175, -1)
        )

        saveLabel = wx.StaticText(panel, -1, "Save Matrix filename: ")
        self.saveText = wx.TextCtrl(panel, -1, "SavedMatrix_%d" % self.index, size=(175, -1))

        btnstore = wx.Button(panel, -1, "Store (in GUI)")
        btnsave = wx.Button(panel, -1, "Save (on Hard Disk)")
        btnquit = wx.Button(panel, -1, "Quit")

        btnstore.Bind(wx.EVT_BUTTON, self.onStore)
        btnsave.Bind(wx.EVT_BUTTON, self.onSave)
        btnquit.Bind(wx.EVT_BUTTON, self.onQuit)

        sizer6 = wx.FlexGridSizer(cols=3, hgap=6, vgap=6)
        sizer6.AddMany([storeLabel, self.storeText, btnstore, saveLabel, self.saveText, btnsave])

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(matrixLabel)
        vbox.Add(matrixText)
        vbox.Add(sizer6)
        vbox.Add(btnquit)
        panel.SetSizer(vbox)

    def onStore(self, _):

        matrix_name = str(self.storeText.GetValue())

        UBmatrix = np.array(self.parent.crystalparampanel.UBmatrix)

        DictLT.dict_Rot[matrix_name] = UBmatrix
        self.parent.crystalparampanel.comboMatrix.Append(matrix_name)

    def onSave(self, _):
        matrixfilename = str(self.storeText.GetValue())

        UBmatrix = np.array(self.parent.crystalparampanel.UBmatrix)

        np.savetxt(matrixfilename, UBmatrix, delimiter=",")

        _file = open(matrixfilename + "_list", "w")
        text = ("[[%.17f,%.17f,%.17f],\n[%.17f,%.17f,%.17f],\n[%.17f,%.17f,%.17f]]"
            % tuple(np.ravel(UBmatrix).tolist()))
        _file.write(text)
        _file.close()

    def onQuit(self, _):
        self.Close()


# --- -----------------  Calibration Board
class MainCalibrationFrame(wx.Frame):
    """
    Class to display calibration tools on data
    """
    def __init__(self, parent, _id, title, initialParameter,
                file_peaks="Cu_near_28May08_0259.peaks",
                starting_param=[71, 1039.42, 1095, 0.0085, -0.981],
                pixelsize=165.0 / 2048,
                datatype="2thetachi",
                dim=(2048, 2048),  # for MARCCD 165,
                kf_direction="Z>0",
                fliprot="no",
                data_added=None):

        wx.Frame.__init__(self, parent, _id, title, size=(1200, 830))

        self.parent = parent

        self.initialParameter = initialParameter

        self.starting_param = starting_param
        # 5 parameters defining Detector Plane and frame
        self.CCDParam = self.initialParameter["CCDParam"]
        # to interact with LaueToolsGUI
        self.defaultParam = self.CCDParam
        self.detectordiameter = self.initialParameter["detectordiameter"]
        self.CCDLabel = self.initialParameter["CCDLabel"]
        self.kf_direction = kf_direction
        self.kf_direction_from_file = kf_direction
        self.filename = file_peaks # could be .dat or .cor file
        # to interact with LaueToolsGUI
        self.DataPlot_filename = self.filename

        self.pixelsize = pixelsize
        self.framedim = dim
        self.fliprot = fliprot

        self.data_theo = data_added
        self.tog = 0
        self.datatype = datatype

        self.dict_Materials = initialParameter["dict_Materials"]

        self.points = []  # to store points
        self.selectionPoints = []
        self.twopoints = []
        self.threepoints = []
        self.sixpoints = []
        self.nbclick = 1
        self.nbsuccess = 0
        self.nbclick_dist = 1
        self.nbclick_zone = 1

        self.dirname = initialParameter["dirname"]

        self.recognition_possible = True
        self.toshow = []
        self.current_matrix = []
        self.deltamatrix = np.eye(3)
        self.manualmatrixinput = None

        # for plot spots annotation
        self.drawnAnnotations_exp = {}
        self.links_exp = []

        self.drawnAnnotations_theo = {}
        self.links_theo = []

        self.RotationActivated = False
        self.SelectedRotationAxis = None

        self.savedindex = 0
        self.storedmatrixindex = 0
        self.savedmatrixindex = 0

        # for fitting procedure  initial model (pairs of simul and exp; spots)----
        self.linkedspots = []
        self.linkExpMiller = []
        self.linkResidues = None
        # savings of refined model
        self.linkedspotsAfterFit = None
        self.linkExpMillerAfterFit = None
        self.linkIntensityAfterFit = None
        self.residues_fitAfterFit = None

        self.SpotsData = None

        # save previous result to undo goto fit results-----------------
        self.previous_CCDParam = copy.copy(self.CCDParam)
        self.previous_UBmatrix = np.eye(3)

        self.setwidgets()

    def setwidgets(self):
        # drag laue pattern
        self.press = None

        # BUTTONS, PLOT and CONTROL
        #        self.plotPanel = wxmpl.PlotPanel(self, -1, size=Size, autoscaleUnzoom=False)
        self.panel = wx.Panel(self)

        self.nb = wx.Notebook(self.panel, -1, style=0)

        self.plotrangepanel = PlotRangePanel(self.nb)
        self.crystalparampanel = CrystalParamPanel(self.nb)
        self.ccdparampanel = CCDParamPanel(self.nb)
        self.moveccdandxtal = MoveCCDandXtal(self.nb)
        self.strainxtal = StrainXtal(self.nb)

        self.nb.AddPage(self.plotrangepanel, "Plot Range")
        self.nb.AddPage(self.crystalparampanel, "Crystal Param")
        self.nb.AddPage(self.ccdparampanel, "CCD Param")
        self.nb.AddPage(self.moveccdandxtal, "Move CCD and Xtal")
        self.nb.AddPage(self.strainxtal, "Strain Xtal")

        # Create the mpl Figure and FigCanvas objects.
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.figsizex, self.figsizey = 4, 3
        self.fig = Figure((self.figsizex, self.figsizey), dpi=self.dpi)
        self.fig.set_size_inches(self.figsizex, self.figsizey, forward=True)
        self.canvas = FigCanvas(self.panel, -1, self.fig)
        self.init_plot = True

        self.axes = self.fig.add_subplot(111)

        self.toolbar = NavigationToolbar(self.canvas)

        self.sb = self.CreateStatusBar()

        self.cidpress = self.fig.canvas.mpl_connect("button_press_event", self.onClick)
        self.fig.canvas.mpl_connect("key_press_event", self.onKeyPressed)
        self.cidrelease = self.fig.canvas.mpl_connect("button_release_event", self.onRelease)
        self.cidmotion = self.fig.canvas.mpl_connect("motion_notify_event", self.onMotion)

        self.Bind(wx.EVT_BUTTON, self.OnStoreMatrix, id=1011)  # in crytalparampanel

        self.btnsavecalib = wx.Button(self.panel, 1012, "Save Calib", (1050, 600), (100, 40))# calibration parameters + orientation UBmatrix
        self.Bind(wx.EVT_BUTTON, self.OnSaveCalib, id=1012)

        self.btnsaveresults = wx.Button(self.panel, 1013, "Save Results", (1050, 700), (100, 40))  # produces file with results
        self.Bind(wx.EVT_BUTTON, self.OnWriteResults, id=1013)

        self.startfit = wx.Button(self.panel, 505, "Start FIT", size=(150, 60))  # (950, 200), )
        self.Bind(wx.EVT_BUTTON, self.StartFit, id=505)

        self.cb_gotoresults = wx.CheckBox(self.panel, -1, "GOTO fit results")  # , (970, 280))
        self.use_weights = wx.CheckBox(self.panel, -1, "use weights")  # , (970, 310))
        self.use_weights.SetValue(False)
        self.cb_gotoresults.SetValue(True)

        self.undogotobtn = wx.Button(self.panel, -1, "Undo\nlast\nGOTO", size=(80, 60))  # ,(950, 200), )
        self.undogotobtn.Bind(wx.EVT_BUTTON, self.OnUndoGoto)

        # replot simul button (one button in two panels)
        self.Bind(wx.EVT_BUTTON, self._replot, id=52)

        self.Bind(wx.EVT_BUTTON, self.OnDecreaseDistance, id=10)
        self.Bind(wx.EVT_BUTTON, self.OnIncreaseDistance, id=11)
        self.Bind(wx.EVT_BUTTON, self.OnDecreaseXcen, id=20)
        self.Bind(wx.EVT_BUTTON, self.OnIncreaseXcen, id=21)
        self.Bind(wx.EVT_BUTTON, self.OnDecreaseYcen, id=30)
        self.Bind(wx.EVT_BUTTON, self.OnIncreaseYcen, id=31)
        self.Bind(wx.EVT_BUTTON, self.OnDecreaseang1, id=40)
        self.Bind(wx.EVT_BUTTON, self.OnIncreaseang1, id=41)
        self.Bind(wx.EVT_BUTTON, self.OnDecreaseang2, id=50)
        self.Bind(wx.EVT_BUTTON, self.OnIncreaseang2, id=51)
        self.Bind(wx.EVT_BUTTON, self.OnDecreaseAngle1, id=1000)
        self.Bind(wx.EVT_BUTTON, self.OnIncreaseAngle1, id=1100)
        self.Bind(wx.EVT_BUTTON, self.OnDecreaseAngle2, id=2000)
        self.Bind(wx.EVT_BUTTON, self.OnIncreaseAngle2, id=2100)
        self.Bind(wx.EVT_BUTTON, self.OnDecreaseAngle3, id=3000)
        self.Bind(wx.EVT_BUTTON, self.OnIncreaseAngle3, id=3100)

        self.btnmanuallinks = wx.Button(self.panel, -1, "Manual Links", size=(-1, 40))
        self.btnmanuallinks.Bind(wx.EVT_BUTTON, self.OnLinkSpots)
        self.btnmanuallinks.Enable(False)

        self.btnautolinks = wx.Button(self.panel, -1, "Auto. Links", size=(150, 40))
        self.btnautolinks.Bind(wx.EVT_BUTTON, self.OnLinkSpotsAutomatic)

        self.txtangletolerance = wx.StaticText(self.panel, -1, "Angle Tolerance(deg)")
        self.AngleMatchingTolerance = wx.TextCtrl(self.panel, -1, "0.5")

        self.btnshowlinks = wx.Button(self.panel, -1, "Filter Links")
        self.btnshowlinks.Bind(wx.EVT_BUTTON, self.OnShowAndFilter)

        self.btnswitchspace = wx.Button(self.panel, 102, "Switch Space", size=(150, 40))
        self.Bind(wx.EVT_BUTTON, self.OnSwitchPlot, id=102)

        self.btn_label_theospot = wx.ToggleButton(self.panel, 104, "Label Exp. spot", size=(150, 40))
        self.btn_label_expspot = wx.ToggleButton(self.panel, 106, "Label Simul. spot", size=(150, 40))

        self.resetAnnotationBtn = wx.Button(self.panel, -1, "Reset Labels", size=(100, 40))
        self.resetAnnotationBtn.Bind(wx.EVT_BUTTON, self.OnResetAnnotations)

        self.defaultColor = self.GetBackgroundColour()
        # print "self.defaultColor",self.defaultColor
        self.p2S, self.p3S = 0, 0

        self.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleLabelExp, id=104)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleLabelSimul, id=106)

        self.parametersdisplaypanel = DetectorParametersDisplayPanel(self.panel)
        self.Bind(wx.EVT_BUTTON, self.OnSetCCDParams, id=159)

        self.txtresidues = wx.StaticText(self.panel, -1, "Mean Residues (pix)   ")
        self.txtnbspots = wx.StaticText(self.panel, -1, "Nbspots")
        self.act_residues = wx.TextCtrl(self.panel, -1, "", style=wx.TE_READONLY)
        self.nbspots_in_fit = wx.TextCtrl(self.panel, -1, "", style=wx.TE_READONLY)

        self.incrementfile = wx.CheckBox(self.panel, -1, "increment saved filenameindex")

        self.layout()

        self.ReadExperimentData()
        self._replot(wx.EVT_IDLE)
        self.display_current()

        # tooltips
        self.plotrangepanel.SetToolTipString("Set plot and spots display parameters")
        self.moveccdandxtal.SetToolTipString("Change manually and fit (by checking corresponding "
                                        "boxes) the 5 CCD parameters and rotate the crystal "
                                        "around 3 elementary angles")
        self.crystalparampanel.SetToolTipString(
            "set crystal parameters for laue spots simulation")
        self.ccdparampanel.SetToolTipString("Set new CCD camera parameters")

        self.btnmanuallinks.SetToolTipString("Build manually a list of associations or links "
                                                "between close simulated and experimental spots")
        self.btnautolinks.SetToolTipString("Build automatically a list of associations or links "
                                        "between close simulated and experimental spots "
                                        "within 'Angle Tolerance'")

        tp1 = "Maximum separation angle (degree) to associate (link) automatically pair of spots (exp. and theo)"
        self.txtangletolerance.SetToolTipString(tp1)
        self.AngleMatchingTolerance.SetToolTipString(tp1)

        self.btnshowlinks.SetToolTipString('Browse and filter links resulting from "Auto. Links"')

        self.btnswitchspace.SetToolTipString("switch between different spots coordinates: "
                    "2theta,chi ; Gnomonic projection coordinates ; X,Y pixel position on Camera")
        self.btn_label_theospot.SetToolTipString("Display on plot data related to selected (by clicking) experimental spot: index, intensity")
        self.btn_label_expspot.SetToolTipString("Display on plot data related to selected "
                    "(by clicking) theoretical (simulated) spot: #index, hkl miller indices, Energy")
        self.resetAnnotationBtn.SetToolTipString("Reset exp or theo. spot displayed labels on plot")

        self.parametersdisplaypanel.SetToolTipString("View or modifiy current CCD detector plane parameters")

        tpresidues = "Mean residues in pixel over distances between exp. and best refined model spots positions"
        self.txtresidues.SetToolTipString(tpresidues)
        self.act_residues.SetToolTipString(tpresidues)

        tpnb = "Nb of spots associations used for model refinement"
        self.txtnbspots.SetToolTipString(tpnb)
        self.nbspots_in_fit.SetToolTipString(tpnb)

        self.btnsavecalib.SetToolTipString("Save .det file containing current CCD parameters and "
                            "current crystal orientation")
        self.btnsaveresults.SetToolTipString("Save .fit file containing indexed spots used to "
                                "refine the CCD detector plane and pixel frame parameters.")

        tpfit = "Start fitting procedure to refine checked parameters related to crystal orientation and CCD detector plane.\n"
        tpfit += "The model predicts the positions of theoretical spots (red hollow circle).\n"
        tpfit += "Distances between pair of spots (experimental and theoretical) are minimized by a least squares refinement procedures.\n"
        tpfit += 'Spots associations are either build manually ("Manual Links") or automatically ("Auto. Links").'

        self.startfit.SetToolTipString(tpfit)

        self.cb_gotoresults.SetToolTipString("Update CCD parameters and crystal orientation according to the fit results")
        self.use_weights.SetToolTipString("Refine the model by Weighting each separation distance between exp. and modeled spots positions by experimental intensity")

        self.incrementfile.SetToolTipString("If Checked, increment filename avoiding overwritten file")

    def layout(self):
        # LAYOUT
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.toolbar, 0, wx.EXPAND)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(self.btnswitchspace, 0, wx.ALL, 5)
        btnSizer.Add(self.btnmanuallinks, 0, wx.ALL, 5)
        btnSizer.Add(self.btnautolinks, 0, wx.ALL, 5)
        btnSizer.Add(self.txtangletolerance, 0, wx.ALL, 5)
        btnSizer.Add(self.AngleMatchingTolerance, 0, wx.ALL, 5)
        btnSizer.Add(self.btnshowlinks, 0, wx.ALL, 5)
        btnSizer.Add(wx.StaticText(self.panel, -1, "              "), 0, wx.ALL, 5)
        btnSizer.Add(self.btnsaveresults, 0, wx.ALL, 5)
        btnSizer.Add(self.btnsavecalib, 0, wx.ALL, 5)

        btnSizer.AddSpacer(5)

        hboxlabel = wx.BoxSizer(wx.HORIZONTAL)
        hboxlabel.Add(self.btn_label_theospot, 0, wx.ALL, 0)
        hboxlabel.Add(self.btn_label_expspot, 0, wx.ALL, 0)
        hboxlabel.Add(self.resetAnnotationBtn, 0, wx.ALL, 0)

        hboxfit = wx.BoxSizer(wx.HORIZONTAL)
        hboxfit.Add(self.startfit, 0, wx.ALL, 0)
        hboxfit.Add(self.use_weights, 0, wx.ALL, 0)
        hboxfit.Add(self.cb_gotoresults, 0, wx.ALL, 0)
        hboxfit.Add(self.undogotobtn, 0, wx.ALL, 0)

        vboxfit2 = wx.BoxSizer(wx.VERTICAL)
        vboxfit2.Add(self.txtresidues, 0, wx.ALL, 0)
        vboxfit2.Add(self.act_residues, 0, wx.ALL, 0)

        vboxfit3 = wx.BoxSizer(wx.VERTICAL)
        vboxfit3.Add(self.txtnbspots, 0, wx.ALL, 0)
        vboxfit3.Add(self.nbspots_in_fit, 0, wx.ALL, 0)

        hboxfit2 = wx.BoxSizer(wx.HORIZONTAL)
        hboxfit2.Add(vboxfit2, 0, wx.ALL, 0)
        hboxfit2.Add(vboxfit3, 0, wx.ALL, 0)
        hboxfit2.Add(wx.StaticText(self.panel, -1, "              "), 0, wx.EXPAND)
        hboxfit2.Add(self.incrementfile, 0, wx.ALL, 0)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(hboxlabel, 0, wx.ALL, 0)
        vbox2.Add(self.nb, 0, wx.EXPAND, 0)
        vbox2.Add(self.parametersdisplaypanel, 0, wx.EXPAND, 0)
        vbox2.Add(wx.StaticLine(self.panel, -1, size=(-1,10), style=wx.LI_HORIZONTAL),
                                                                0, wx.EXPAND|wx.ALL, 5)
        vbox2.Add(hboxfit, 0, wx.EXPAND, 0)
        vbox2.Add(hboxfit2, 0, wx.EXPAND, 0)

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.vbox, 1, wx.EXPAND)
        self.hbox.Add(vbox2, 1, wx.EXPAND)

        vboxgeneral = wx.BoxSizer(wx.VERTICAL)
        vboxgeneral.Add(self.hbox, 1, wx.EXPAND)
        vboxgeneral.Add(btnSizer, 0, wx.EXPAND)

        self.panel.SetSizer(vboxgeneral)
        vboxgeneral.Fit(self)
        self.Layout()

    def ReadExperimentData(self):
        """
        - open self.filename (self.dirname)
        - take into account:
        self.CCDParam
        self.pixelsize
        self.kf_direction

        - set exp. spots attributes:
        self.twicetheta, self.chi = chi
        self.Data_I
        self.filename
        self.data = (self.twicetheta, self.chi, self.Data_I, self.filename)
        self.Data_index_expspot
        self.data_x, self.data_y
        """
        extension = self.filename.split(".")[-1]

        print("self.CCDParam in ReadExperimentData()", self.CCDParam)
        filepath = os.path.join(self.dirname, self.filename)
        print('filepath',filepath)

        if extension in ("dat", "DAT"):
            colI = 3
            col2theta = 0
            colChi = 1

            (twicetheta,
                chi,
                dataintensity,
                data_x,
                data_y,
            ) = F2TC.Compute_data2thetachi(filepath,
                                            (col2theta, colChi, colI),
                                            0,
                                            param=self.CCDParam,
                                            pixelsize=self.pixelsize,
                                            kf_direction=self.kf_direction)
            self.initialParameter['filename.cor'] = None


        elif extension in ("cor",):
            (_, data_theta,
                chi,
                data_x,
                data_y,
                dataintensity,
                _) = IOLT.readfile_cor(filepath)
            twicetheta = 2 * data_theta
            self.initialParameter['filename.cor'] = self.filename

        self.twicetheta = twicetheta
        self.chi = chi
        self.Data_I = dataintensity        

        self.data = (self.twicetheta, self.chi, self.Data_I, self.filename)
        # starting X,Y data to plot (2theta , chi)
        self.Data_index_expspot = np.arange(len(self.twicetheta))

        # pixel coordinates of experimental spots
        self.data_x, self.data_y = data_x, data_y

    def computeGnomonicExpData(self):
        # compute Gnomonic projection
        (twicetheta, chi, dataintensity) = self.data[:3]
        nbexpspots = len(twicetheta)

        originChi = 0

        if self.plotrangepanel.shiftChiOrigin.GetValue():
            originChi = float(self.plotrangepanel.meanchi.GetValue())

        dataselected = IOLT.createselecteddata(
                                            (twicetheta, chi + originChi, dataintensity),
                                            np.arange(nbexpspots),
                                            nbexpspots)[0]

        return IIM.ComputeGnomon_2(dataselected)

    def OnSaveCalib(self, _):
        """
        Save  calibration parameters in .det file
        """
        dlg = wx.TextEntryDialog(self,
            "Enter Calibration File name : \n Current Detector parameters are: \n %s\n Pixelsize and dimensions : %s"
            % (str(self.CCDParam), str([self.pixelsize, self.framedim[0], self.framedim[1]]),
            ), "Saving Calibration Parameters Entry")
        dlg.SetValue("*.det")
        self.filenameCalib = None
        if dlg.ShowModal() == wx.ID_OK:
            self.filenameCalib = str(dlg.GetValue())
            m11, m12, m13, m21, m22, m23, m31, m32, m33 = np.ravel(self.UBmatrix).round(
                decimals=7)

            dd, xcen, ycen, xbet, xgam = self.CCDParam

            outputfile = open(self.filenameCalib, "w")
            text = "%.3f, %.2f, %.2f, %.3f, %.3f, %.5f, %.0f, %.0f\n" % (
                                                                round(dd, 3),
                                                                round(xcen, 2),
                                                                round(ycen, 2),
                                                                round(xbet, 3),
                                                                round(xgam, 3),
                                                                self.pixelsize,
                                                                round(self.framedim[0], 0),
                                                                round(self.framedim[1], 0),
                                                            )
            text += "Sample-Detector distance(IM), xO, yO, angle1, angle2, pixelsize, dim1, dim2\n"
            text += "Calibration done with %s at %s with LaueToolsGUI.py\n" % (
                self.crystalparampanel.comboElem.GetValue(),
                time.asctime(),
            )
            text += "Experimental Data file: %s\n" % self.filename
            text += "Orientation Matrix:\n"
            text += "[[%.7f,%.7f,%.7f],[%.7f,%.7f,%.7f],[%.7f,%.7f,%.7f]]\n" % (
                                                    m11, m12, m13, m21, m22, m23, m31, m32, m33)
            #             CCD_CALIBRATION_PARAMETERS = ['dd', 'xcen', 'ycen', 'xbet', 'xgam',
            #                       'xpixelsize', 'ypixelsize', 'CCDLabel',
            #                       'framedim', 'detectordiameter', 'kf_direction']
            vals_list = [round(dd, 3), round(xcen, 2), round(ycen, 2),
                        round(xbet, 3), round(xgam, 3),
                        self.pixelsize, self.pixelsize, self.CCDLabel,
                        self.framedim, self.detectordiameter, self.kf_direction]

            key_material = str(self.crystalparampanel.comboElem.GetValue())

            text += "# %s : %s\n" % ("Material", key_material)
            for key, val in zip(DictLT.CCD_CALIBRATION_PARAMETERS, vals_list):
                text += "# %s : %s\n" % (key, val)

            outputfile.write(text[:-1])
            outputfile.close()

        dlg.Destroy()

        if self.filenameCalib is not None:
            fullname = os.path.join(os.getcwd(), self.filenameCalib)
            wx.MessageBox("Calibration file written in %s" % fullname, "INFO")

            #             # remove .cor file with old CCD geometry parameters
            #             os.remove(self.initialParameter['filename'])

            # update main GUI CCD geomtrical parameters
            # print("self.parent", self.parent)
            if self.parent:
                self.parent.defaultParam = self.CCDParam
                self.parent.pixelsize = self.pixelsize
                self.parent.kf_direction = self.kf_direction

    def OnStoreMatrix(self, _):
        """
        Store the current UBmatrix in the orientation UBmatrix dictionnary
        """

        tf = TextFrame(self, -1, self.getstringrep(self.crystalparampanel.UBmatrix),
                        self.storedmatrixindex)
        tf.Show(True)
        self.storedmatrixindex += 1
        return

    #         # current UBmatrix  : self.UBmatrix
    #
    #         # dialog for UBmatrix name
    #         dlg = wx.TextEntryDialog(self, 'Enter Matrix Name : \n Current Matrix is: \n %s' % \
    #                                  self.getstringrep(self.crystalparampanel.UBmatrix), 'Storing Matrix Name Entry')
    #         dlg.SetValue('')
    #         if dlg.ShowModal() == wx.ID_OK:
    #             matrix_name = str(dlg.GetValue())
    #
    #             self.crystalparampanel.UBmatrix = np.array(self.crystalparampanel.UBmatrix)
    #             DictLT.dict_Rot[matrix_name] = self.crystalparampanel.UBmatrix.tolist()
    #             self.crystalparampanel.comboMatrix.Append(matrix_name)
    #             dlg.Destroy()

    def getstringrep(self, matrix):
        if isinstance(matrix, np.ndarray):
            listmatrix = matrix.tolist()
        else:
            raise ValueError("matrix is not an array ?")
        strmat = "["
        for row in listmatrix:
            strmat += str(row) + ",\n"

        return strmat[:-2] + "]"

    def OnShowAndFilter(self, _):
        fields = ["#Spot Exp", "#Spot Theo", "h", "k", "l", "Intensity", "residues"]
        # self.linkedspots = dia.listofpairs
        # self.linkExpMiller = dia.linkExpMiller
        # self.linkIntensity = dia.linkIntensity

        indExp = self.linkedspots[:, 0]
        indTheo = self.linkedspots[:, 1]
        _h, _k, _l = np.transpose(np.array(self.linkExpMiller, dtype=np.int))[1:4]
        intens = self.linkIntensity
        if self.linkResidues is not None:
            residues = np.array(self.linkResidues)[:, 2]
        else:
            residues = -1 * np.ones(len(indExp))

        to_put_in_dict = indExp, indTheo, _h, _k, _l, intens, residues

        mySpotData = {}
        for k, ff in enumerate(fields):
            mySpotData[ff] = to_put_in_dict[k]
        dia = LSEditor.SpotsEditor(None, -1, "Spots Editor in Calibration Board",
                                    mySpotData,
                                    func_to_call=self.readdata_fromEditor_Filter,
                                    field_name_and_order=fields)

        dia.Show(True)

    def readdata_fromEditor_Filter(self, data):

        ArrayReturn = np.array(data)

        self.linkedspots = ArrayReturn[:, :2]
        self.linkExpMiller = np.take(ArrayReturn, [0, 2, 3, 4], axis=1)
        self.linkIntensity = ArrayReturn[:, 5]
        self.linkResidues = ArrayReturn[:, 6]

    def OnLinkSpotsAutomatic(self, _):
        """ create automatically links between currently close experimental
        and theoretical spots in 2theta chi representation

        .. todo::
            use getProximity() ??
        """
        veryclose_angletol = float(self.AngleMatchingTolerance.GetValue())  # in degrees

        # theoretical data
        twicetheta, chi, Miller_ind, posx, posy, _ = self.simulate_theo(removeharmonics=1)
        # experimental data (set exp. spots attributes)
        self.ReadExperimentData()

        print("theo. spots")
        print("k, x, y, 2theta, theta, chi hkl")
        for k in range(len(twicetheta)):
            print(k, posx[k], posy[k], twicetheta[k], twicetheta[k] / 2, chi[k], Miller_ind[k])

        Resi, ProxTable = matchingrate.getProximity(np.array([twicetheta, chi]),  # warning array(2theta, chi)
                                        self.twicetheta / 2.0,
                                        self.chi,  # warning theta, chi for exp
                                        proxtable=1,
                                        angtol=5.0,
                                        verbose=0,
                                        signchi=1)[:2]  # sign of chi is +1 when apparently SIGN_OF_GAMMA=1

        # len(Resi) = nb of theo spots
        # len(ProxTable) = nb of theo spots
        # ProxTable[index_theo]  = index_exp   closest link
        # print "Resi",Resi
        # print "ProxTable",ProxTable
        # print "Nb of theo spots", len(ProxTable)

        # array theo spot index
        very_close_ind = np.where(Resi < veryclose_angletol)[0]
        # print "In OnLinkSpotsAutomatic() very close indices",very_close_ind
        longueur_very_close = len(very_close_ind)

        List_Exp_spot_close = []
        Miller_Exp_spot = []

        # todisplay = ''
        if longueur_very_close > 0:
            for theospot_ind in very_close_ind:  # loop over theo spots index

                List_Exp_spot_close.append(ProxTable[theospot_ind])
                Miller_Exp_spot.append(Miller_ind[theospot_ind])

                # todisplay += "theo # %d   exp. # %d  Miller : %s \n"%(spot_ind, ProxTable[spot_ind],str(TwicethetaChi[0][spot_ind].Millers))
                # print "theo # %d   exp. # %d  Miller : %s"%(spot_ind, ProxTable[spot_ind],str(TwicethetaChi[0][spot_ind].Millers))
        # print "List_Exp_spot_close",List_Exp_spot_close
        # print "Miller_Exp_spot",Miller_Exp_spot

        # removing exp spot which appears many times(close to several simulated spots of one grain)--------------
        arrayLESC = np.array(List_Exp_spot_close, dtype=float)

        sorted_LESC = np.sort(arrayLESC)

        diff_index = sorted_LESC - np.array(list(sorted_LESC[1:]) + [sorted_LESC[0]])
        toremoveindex = np.where(diff_index == 0)[0]

        # print "List_Exp_spot_close", List_Exp_spot_close
        # print "sorted_LESC", sorted_LESC
        # print "toremoveindex", toremoveindex

        # print "number labelled exp spots", len(List_Exp_spot_close)
        # print "List_Exp_spot_close", List_Exp_spot_close
        # print "Miller_Exp_spot", Miller_Exp_spot

        if len(toremoveindex) > 0:
            # index of exp spot in arrayLESC that are duplicated
            ambiguous_exp_ind = GT.find_closest(
                np.array(sorted_LESC[toremoveindex], dtype=float), arrayLESC, 0.1
            )[1]
            # print "ambiguous_exp_ind", ambiguous_exp_ind

            # marking exp spots(belonging ambiguously to several simulated grains)
            for ind in ambiguous_exp_ind:
                Miller_Exp_spot[ind] = None

        # -----------------------------------------------------------------------------------------------------
        ProxTablecopy = copy.copy(ProxTable)
        # tag duplicates in ProxTable with negative sign ----------------------
        # ProxTable[index_theo]  = index_exp   closest link

        for theo_ind, exp_ind in enumerate(ProxTable):
            where_th_ind = np.where(ProxTablecopy == exp_ind)[0]
            # print "theo_ind, exp_ind ******** ",theo_ind, exp_ind
            if len(where_th_ind) > 1:
                # exp spot(exp_ind) is close to several theo spots
                # then tag the index with negative sign
                for indy in where_th_ind:
                    ProxTablecopy[indy] = -ProxTable[indy]
                # except that which corresponds to the closest
                closest = np.argmin(Resi[where_th_ind])
                # print "residues = Resi[where_th_ind]",Resi[where_th_ind]
                # print "closest",closest
                # print "where_exp_ind[closest]",where_th_ind[closest]
                # print "Resi[where_th_ind[closest]]", Resi[where_th_ind[closest]]
                ProxTablecopy[where_th_ind[closest]] = -ProxTablecopy[where_th_ind[closest]]

        # ------------------------------------------------------------------
        # print "ProxTable after duplicate removal tagging"
        # print ProxTablecopy

        # print "List_Exp_spot_close",List_Exp_spot_close
        # print "Results",[Miller_Exp_spot, List_Exp_spot_close]

        singleindices = []
        calib_indexed_spots = {}

        for k in range(len(List_Exp_spot_close)):

            exp_index = List_Exp_spot_close[k]
            if not singleindices.count(exp_index):
                # there is not exp_index in singleindices
                singleindices.append(exp_index)

                theo_index = np.where(ProxTablecopy == exp_index)[0]
                # print "theo_index", theo_index

                if len(theo_index) == 1:
                    # fill with expindex,[h,k,l]
                    calib_indexed_spots[exp_index] = [exp_index,
                                                    theo_index,
                                                    Miller_Exp_spot[k]]
                else:  # recent PATCH:
                    print("Resi[theo_index]", Resi[theo_index])
                    closest_theo_ind = np.argmin(Resi[theo_index])
                    # print theo_index[closest_theo_ind]
                    if Resi[theo_index][closest_theo_ind] < veryclose_angletol:
                        calib_indexed_spots[exp_index] = [exp_index,
                                                        theo_index[closest_theo_ind],
                                                        Miller_Exp_spot[k]]
            else:
                print("Experimental spot #%d may belong to several theo. spots!"
                    % exp_index)

        # find theo spot linked to exp spot ---------------------------------

        # calib_indexed_spots is a dictionnary:
        # key is experimental spot index and value is [experimental spot index,h,k,l]
        print("calib_indexed_spots", calib_indexed_spots)

        listofpairs = []
        linkExpMiller = []
        linkIntensity = []
        linkResidues = []
        # for val in list(calib_indexed_spots.values()):
        #     if val[2] is not None:
        #         listofpairs.append([val[0], val[1]])  # Exp, Theo,  where -1 for specifying that it came from automatic linking
        #         linkExpMiller.append([float(val[0])] + [float(elem) for elem in val[2]])  # float(val) for further handling as floats array
        #         linkIntensity.append(self.Data_I[val[0]])
        #         linkResidues.append([val[0], val[1], Resi[val[1]]])

        for val in list(calib_indexed_spots.values()):
            if val[2] is not None:
                if not isinstance(val[1], (list, np.ndarray)):
                    closetheoindex = val[1]
                else:
                    closetheoindex = val[1][0]

                listofpairs.append([val[0], closetheoindex])  # Exp, Theo,  where -1 for specifying that it came from automatic linking
                linkExpMiller.append([float(val[0])] + [float(elem) for elem in val[2]])  # float(val) for further handling as floats array
                linkIntensity.append(self.Data_I[val[0]])
                linkResidues.append([val[0], closetheoindex, Resi[closetheoindex]])


        self.linkedspots = np.array(listofpairs)
        self.linkExpMiller = linkExpMiller
        self.linkIntensity = linkIntensity
        self.linkResidues = linkResidues

        return calib_indexed_spots

    def OnLinkSpots(self, _):  # manual links
        """
        open an editor to link manually spots(exp, theo) for the next fitting procedure
        """
        print("self.linkExpMiller", self.linkExpMiller)

        dia = SLE.LinkEditor(None, -1, "Link between spots Editor", self.linkExpMiller,
                                                                    self.Miller_ind,
                                                                    intensitylist=self.Data_I)

        dia.Show(True)
        #         dia.Destroy()
        self.linkedspots = dia.listofpairs
        self.linkExpMiller = dia.linkExpMiller
        self.linkIntensity = dia.linkIntensity

    def OnUndoGoto(self, evt):
        self.cb_gotoresults.SetValue(False)

        # updating plot of theo. and exp. spots in calibFrame

        #         print "\n\nUndo Last go to refinement results detector\n"
        #         print "old ccd:", self.CCDParam
        #         print "old UBmatrix", self.UBmatrix

        self.CCDParam = copy.copy(self.previous_CCDParam)
        self.UBmatrix = self.previous_UBmatrix

        #         print "new ccd:", self.CCDParam
        #         print "new UBmatrix", self.UBmatrix
        #
        #         print '\n******\n\n'
        #
        #         if len(arr_indexvaryingparameters) > 1:
        #             for k, val in enumerate(arr_indexvaryingparameters):
        #                 if val < 5:  # only detector params
        #                     self.CCDParam[val] = results[k]
        #         elif len(arr_indexvaryingparameters) == 1:
        #             # only detector params [dd,xcen,ycen,alpha1,alpha2]
        #             if arr_indexvaryingparameters[0] < 5:
        #                 self.CCDParam[arr_indexvaryingparameters[0]] = results[0]
        #         print "New parameters", self.CCDParam
        #
        #         # update orient UBmatrix
        #         print "updating orientation parameters"
        #         # self.UBmatrix = np.dot(deltamat, self.UBmatrix)

        self.crystalparampanel.UBmatrix = self.UBmatrix
        self.deltamatrix = np.eye(3)  # identity
        #         # self.B0matrix is unchanged
        #
        # update exp and theo data
        self.update_data(evt)

    def StartFit(self, event):
        """
        StartFit in calib frame
        """
        if self.linkedspots == []:
            wx.MessageBox('You need to create first links between experimental and simulated spots '
                            'with the "link spots" button.',
                            "INFO")
            event.Skip()
            return

        print("\nStart fit")
        print("Pairs of spots used", self.linkedspots)
        arraycouples = np.array(self.linkedspots)

        exp_indices = np.array(arraycouples[:, 0], dtype=np.int)
        sim_indices = np.array(arraycouples[:, 1], dtype=np.int)

        nb_pairs = len(exp_indices)
        print("Nb of pairs: ", nb_pairs)
        print(exp_indices, sim_indices)

        # self.data_theo contains the current simulated spots: twicetheta, chi, Miller_ind, posx, posy
        # Data_Q = self.data_theo[2]  # all miller indices must be entered with sim_indices = arraycouples[:,1]

        print("self.linkExpMiller", self.linkExpMiller)
        Data_Q = np.array(self.linkExpMiller)[:, 1:]

        sim_indices = np.arange(nb_pairs)
        print("DataQ from self.linkExpMiller", Data_Q)

        # experimental spots selection from self.data_x, self.data_y(loaded when initialising calibFrame)
        pixX, pixY = (np.take(self.data_x, exp_indices),
                        np.take(self.data_y, exp_indices))  # pixel coordinates
        # twth, chi = np.take(self.twicetheta, exp_indices),np.take(self.chi, exp_indices)  # 2theta chi coordinates

        # initial parameters of calibration and misorientation from the current orientation UBmatrix
        print("detector parameters", self.CCDParam)

        allparameters = np.array(self.CCDParam + [0, 0, 0])  # 3 last params = 3 quaternion angles not used here

        # select the parameters that must be fitted
        boolctrl = [ctrl.GetValue() for ctrl in self.moveccdandxtal.listofparamfitctrl]
        varyingparameters = []
        init_values = []
        for k, val in enumerate(boolctrl):
            if val:
                varyingparameters.append(k)
                init_values.append(allparameters[k])

        if not bool(varyingparameters):
            wx.MessageBox("You need to select at least one parameter to fit!!", "INFO")
            return

        listparam = ["distance(mm)",
                    "Xcen(pixel)",
                    "Ycen(pixel)",
                    "Angle1(deg)",
                    "Angle2(deg)",  # detector parameter
                    "theta1(deg)",
                    "theta2(deg)",
                    "theta3(deg)"]  # misorientation with respect to initial UBmatrix(/ elementary axis rotation)

        # start fit
        initial_values = np.array(init_values)  # [dd, xcen, ycen, ang1, ang2, theta1, theta2, theta3]
        arr_indexvaryingparameters = np.array(varyingparameters)  # indices of position of parameters in [dd, xcen, ycen, ang1, ang2, theta1, theta2, theta3]

        self.UBmatrix = self.crystalparampanel.UBmatrix

        print("starting fit of :", [listparam[k] for k in arr_indexvaryingparameters])
        print("With initial values: ", initial_values)
        # print "miller selected ",np.take(self.data_theo[2],sim_indices, axis = 0) ????
        print("allparameters", allparameters)
        print("arr_indexvaryingparameters", arr_indexvaryingparameters)
        print("nb_pairs", nb_pairs)
        print("indices of simulated spots(selection in whole Data_Q list)", sim_indices)
        print("Experimental pixX, pixY", pixX, pixY)
        print("self.UBmatrix", self.UBmatrix)

        pureRotation = 0  # OR, was 1

        if self.use_weights.GetValue():
            weights = self.linkIntensity
        else:
            weights = None

        # fitting procedure for one or many parameters
        nb_fittingparams = len(arr_indexvaryingparameters)
        if nb_pairs < nb_fittingparams:
            wx.MessageBox("You need at least %d spots links to fit these %d parameters."
                            % (nb_fittingparams, nb_fittingparams),
                            "INFO")
            event.Skip()
            return

        print("Initial error--------------------------------------\n")
        residues, deltamat, newmatrix = FitO.error_function_on_demand_calibration(
                                            initial_values,
                                            Data_Q,
                                            allparameters,
                                            arr_indexvaryingparameters,
                                            sim_indices,
                                            pixX,
                                            pixY,
                                            initrot=self.UBmatrix,
                                            vecteurref=self.B0matrix,
                                            pureRotation=pureRotation,
                                            verbose=1,
                                            pixelsize=self.pixelsize,
                                            dim=self.framedim,
                                            weights=weights,
                                            kf_direction=self.kf_direction)
        print("Initial residues", residues)
        print("---------------------------------------------------\n")

        results = FitO.fit_on_demand_calibration(initial_values,
                                                Data_Q,
                                                allparameters,
                                                FitO.error_function_on_demand_calibration,
                                                arr_indexvaryingparameters,
                                                sim_indices,
                                                pixX,
                                                pixY,
                                                initrot=self.UBmatrix,
                                                vecteurref=self.B0matrix,
                                                pureRotation=pureRotation,
                                                pixelsize=self.pixelsize,
                                                dim=self.framedim,
                                                verbose=0,
                                                weights=weights,
                                                kf_direction=self.kf_direction)

        print("\n********************\n       Results of Fit        \n********************")
        print("results", results)
        allresults = allparameters

        if nb_fittingparams == 1:
            results = [results]

        print("weights = ", weights)

        residues, deltamat, newmatrix = FitO.error_function_on_demand_calibration(
                                        results,
                                        Data_Q,
                                        allparameters,
                                        arr_indexvaryingparameters,
                                        sim_indices,
                                        pixX,
                                        pixY,
                                        initrot=self.UBmatrix,
                                        vecteurref=self.B0matrix,
                                        pureRotation=pureRotation,
                                        verbose=1,
                                        pixelsize=self.pixelsize,
                                        dim=self.framedim,
                                        weights=weights,
                                        kf_direction=self.kf_direction)

        residues_nonweighted, _delta, _newmatrix, self.SpotsData = FitO.error_function_on_demand_calibration(results,
                                                Data_Q,
                                                allparameters,
                                                arr_indexvaryingparameters,
                                                sim_indices,
                                                pixX,
                                                pixY,
                                                initrot=self.UBmatrix,
                                                vecteurref=self.B0matrix,
                                                pureRotation=pureRotation,
                                                verbose=1,
                                                pixelsize=self.pixelsize,
                                                dim=self.framedim,
                                                weights=None,
                                                allspots_info=1,
                                                kf_direction=self.kf_direction)

        print("last pixdev table")
        print(residues_nonweighted)
        print("Mean pixdev no weights")
        print(np.mean(residues_nonweighted))
        print("Mean pixdev")
        print(np.mean(residues))
        print("initial UBmatrix")
        print(self.UBmatrix)
        print("New delta UBmatrix")
        print(deltamat)
        print("newmatrix")
        print(newmatrix)
        print(newmatrix.tolist())

        if len(arr_indexvaryingparameters) > 1:
            for k, val in enumerate(arr_indexvaryingparameters):
                allresults[val] = results[k]
        elif len(arr_indexvaryingparameters) == 1:
            allresults[arr_indexvaryingparameters[0]] = results[0]

        self.residues_fit = residues_nonweighted
        # display fit results
        dataresults = (allresults.tolist()
                    + [np.mean(self.residues_fit)]
                    + [len(self.residues_fit)])
        self.display_results(dataresults)

        # updating plot of theo. and exp. spots in calibFrame
        if self.cb_gotoresults.GetValue():
            print("Updating plot with new CCD parameters and crystal orientation detector")

            # saving previous results
            self.previous_CCDParam = copy.copy(self.CCDParam)
            self.previous_UBmatrix = copy.copy(self.UBmatrix)

            if len(arr_indexvaryingparameters) > 1:
                for k, val in enumerate(arr_indexvaryingparameters):
                    if val < 5:  # only detector params
                        self.CCDParam[val] = results[k]
            elif len(arr_indexvaryingparameters) == 1:
                # only detector params [dd,xcen,ycen,alpha1,alpha2]
                if arr_indexvaryingparameters[0] < 5:
                    self.CCDParam[arr_indexvaryingparameters[0]] = results[0]
            print("New parameters", self.CCDParam)

            # update orient UBmatrix
            #             print "updating orientation parameters"
            # self.UBmatrix = np.dot(deltamat, self.UBmatrix)
            self.UBmatrix = newmatrix
            self.crystalparampanel.UBmatrix = newmatrix
            self.deltamatrix = np.eye(3)  # identity
            # self.B0matrix is unchanged

            # OR
            UBB0 = np.dot(self.UBmatrix, self.B0matrix)

            Umat = CP.matstarlab_to_matstarlabOND(matstarlab=None, matLT3x3=self.UBmatrix)

            print("**********test U ****************************")
            print("U matrix = ")
            print(Umat.round(decimals=5))
            print("normes :")
            for i in range(3):
                print(i, GT.norme_vec(Umat[:, i]).round(decimals=5))
            print("produit scalaire")
            for i in range(3):
                j = np.mod(i + 1, 3)
                print(i, j, np.inner(Umat[:, i], Umat[:, j]).round(decimals=5))
            print("determinant")
            print(np.linalg.det(Umat).round(decimals=5))

            toto = Umat.transpose()
            Bmat_triang_up = np.dot(toto, self.UBmatrix)

            print(" Bmat_triang_up= ")
            print(Bmat_triang_up.round(decimals=5))

            self.Umat2 = Umat
            self.Bmat_tri = Bmat_triang_up

            list_HKL_names, HKL_xyz = CP.matrix_to_HKLs_along_xyz_sample_and_along_xyz_lab(
                matstarlab=None,  # OR
                UBmat=UBB0,  # LT , UBB0 ici
                omega=None,  # was MG.PAR.omega_sample_frame,
                mat_from_lab_to_sample_frame=None,
                results_in_OR_frames=0,
                results_in_LT_frames=1,
                sampletilt=40.0)
            self.HKLxyz_names = list_HKL_names
            self.HKLxyz = HKL_xyz

            # end OR

            # update exp and theo data
            self.update_data(event)

            print("self.linkedspots at the end of StartFit ", self.linkedspots)
            self.linkedspotsAfterFit = copy.copy(self.linkedspots)
            self.linkExpMillerAfterFit = copy.copy(self.linkExpMiller)
            self.linkIntensityAfterFit = copy.copy(self.linkIntensity)
            self.residues_fitAfterFit = copy.copy(self.residues_fit)

        # update .cor file  self.initialParameter["filename.cor"]
        print("self.defaultParam after refinement", self.CCDParam)
        fullpathfilename = os.path.join(self.initialParameter["dirname"],
                                        self.filename)
        print("fullpathfilename", fullpathfilename)

        (twicetheta, chi, dataintensity, data_x, data_y) = F2TC.Compute_data2thetachi(
                                                            fullpathfilename,
                                                            (0, 1, 3),
                                                            1,
                                                            sorting_intensity="yes",
                                                            param=self.CCDParam,
                                                            pixelsize=self.pixelsize,
                                                            kf_direction=self.kf_direction)

        filename = os.path.split(fullpathfilename)[1]
        #         print "dirname,filename",dirname,filename

        prefix = filename.split(".")[0]
        #         print 'prefix',prefix

        IOLT.writefile_cor(prefix,
                        twicetheta,
                        chi,
                        data_x,
                        data_y,
                        dataintensity,
                        sortedexit=0,
                        param=self.CCDParam + [self.pixelsize],
                        initialfilename=self.filename,
                        dirname_output=os.getcwd())  # check sortedexit = 0 or 1 to have decreasing intensity sorted data
        print("%s has been updated" % (prefix + ".cor"))
        self.initialParameter["filename.cor"] = prefix + ".cor"

    def OnWriteResults(self, _):
        """
        write a .fit file from refined orientation and detector calibration CCD geometry
        """
        print("self.linkedspots in OnWriteResults()", self.linkedspots)

        if self.SpotsData is None or self.linkedspotsAfterFit is None:
            wx.MessageBox("You must have run once a calibration refinement!", "INFO")
            return

        # spotsData = [Xtheo,Ytheo, Xexp, Yexp, Xdev, Ydev, theta_theo]
        spotsData = self.SpotsData

        print("Writing results in .fit file")
        suffix = ""
        if self.incrementfile.GetValue():
            self.savedindex += 1
            suffix = "_%d" % self.savedindex

        outputfilename = (self.filename.split(".")[0] + suffix + ".fit")

        indExp = np.array(self.linkedspotsAfterFit[:, 0], dtype=np.int)
        _h, _k, _l = np.transpose(np.array(self.linkExpMillerAfterFit, dtype=np.int))[1:4]
        intens = self.linkIntensityAfterFit
        residues_calibFit = self.residues_fitAfterFit

        # elem = self.crystalparampanel.comboElem.GetValue()

        # latticeparam = DictLT.dict_Materials[str(elem)][1][0] * 1.0
        Data_Q = np.array(self.linkExpMillerAfterFit)[:, 1:]

        dictCCD = {}
        dictCCD["CCDparam"] = self.CCDParam
        dictCCD["dim"] = self.framedim
        dictCCD["pixelsize"] = self.pixelsize
        dictCCD["kf_direction"] = self.kf_direction

        spotsProps = LAUE.calcSpots_fromHKLlist(self.UBmatrix, self.B0matrix, Data_Q, dictCCD)
        # H, K, L, Qx, Qy, Qz, Xtheo, Ytheo, twthe, chi, Energy = spotsProps
        Xtheo, Ytheo, twthe, chi, Energy = spotsProps[-5:]

        print('self.initialParameter["filename.cor"] in OnWriteResults',
                self.initialParameter["filename.cor"])
        
        initialdatfile = self.filename #self.initialParameter["filename.cor"]
        print('initialdatfile  :',initialdatfile)

        data_peak = IOLT.read_Peaklist(initialdatfile)

        selected_data_peak = np.take(data_peak, indExp, axis=0)

        if initialdatfile.endswith('.dat'):
            (Xexp, Yexp, _, peakAmplitude,
            peak_fwaxmaj, peak_fwaxmin, peak_inclination,
            Xdev_peakFit, Ydev_peakFit, peak_bkg, IntensityMax) = selected_data_peak.T

        elif initialdatfile.endswith('.cor'):
            (_, _, Xexp, Yexp, peakAmplitude) = selected_data_peak.T
            totalIntensity = peakAmplitude
            unknowns = np.zeros(len(Xexp))
            peak_fwaxmaj = unknowns
            peak_fwaxmin = unknowns
            peak_inclination = unknowns
            Xdev_peakFit = unknowns
            Ydev_peakFit, peak_bkg, IntensityMax = unknowns, unknowns, unknowns


        Xdev_calibFit, Ydev_calibFit = spotsData[4:6]

        # #spot index, peakamplitude, h,k,l, Xtheo, Ytheo, Xexp, Yexp, Xdev,
        # Xdev_calibFit, Ydev_calibFit, sqrt(Xdev_calibFit**2+Ydev_calibFit**2)
        # 2thetaTheo, chiTheo, EnergyTheo, peakamplitude, hottestintensity, localintensitybackground
        # peak_fullwidth_axisminor, peak_fullwidth_axismahor, peak elongation direction angle,
        # Xdev_peakfit, Ydev_peakfit (fit by gaussian 2D shape for example)
        Columns = [indExp, intens, _h, _k, _l, Xtheo, Ytheo, Xexp, Yexp,
                Xdev_calibFit, Ydev_calibFit, residues_calibFit,
                twthe, chi, Energy,
                peakAmplitude, IntensityMax, peak_bkg,
                peak_fwaxmaj, peak_fwaxmin, peak_inclination,
                Xdev_peakFit, Ydev_peakFit]

        datatooutput = np.transpose(np.array(Columns))
        datatooutput = np.round(datatooutput, decimals=5)

        # sort by decreasing intensity
        data = datatooutput[np.argsort(datatooutput[:, 1])[::-1]]

        dict_matrices = {}
        dict_matrices["Element"] = self.key_material

        dict_matrices["UBmat"] = self.UBmatrix
        dict_matrices["B0"] = self.B0matrix
        #         dict_matrices['UBB0'] = self.UBB0mat
        #         dict_matrices['devstrain'] = self.deviatoricstrain

        UBB0_v2 = np.dot(dict_matrices["UBmat"], dict_matrices["B0"])
        euler_angles = ORI.calc_Euler_angles(UBB0_v2).round(decimals=3)
        dict_matrices["euler_angles"] = euler_angles

        # Odile Robach's addition
        dict_matrices["UBB0"] = UBB0_v2
        dict_matrices["Umat2"] = self.Umat2
        dict_matrices["Bmat_tri"] = self.Bmat_tri
        dict_matrices["HKLxyz_names"] = self.HKLxyz_names
        dict_matrices["HKLxyz"] = self.HKLxyz
        dict_matrices["detectorparameters"] = list(np.array(self.CCDParam).round(decimals=3))
        dict_matrices["pixelsize"] = self.pixelsize
        dict_matrices["framedim"] = self.framedim
        dict_matrices["CCDLabel"] = self.CCDLabel

        columnsname = "spot_index Itot h k l Xtheo Ytheo Xexp Yexp XdevCalib YdevCalib pixDevCalib "
        columnsname += "2theta_theo chi_theo Energy PeakAmplitude Imax PeakBkg "
        columnsname += "PeakFwhm1 PeakFwhm2 PeakTilt XdevPeakFit YdevPeakFit\n"

        meanresidues = np.mean(residues_calibFit)

        IOLT.writefitfile(outputfilename,
                        data,
                        len(indExp),
                        dict_matrices=dict_matrices,
                        meanresidues=meanresidues,
                        PeakListFilename=initialdatfile,
                        columnsname=columnsname,
                        modulecaller="DetectorCalibration.py",
                        refinementtype="CCD Geometry")

        fullname = os.path.join(os.getcwd(), outputfilename)

        wx.MessageBox("Fit results saved in %s" % fullname, "INFO")

        if self.parent:
            # update main GUI CCD geometrical parameters
            self.parent.defaultParam = self.CCDParam
            self.parent.pixelsize = self.pixelsize
            self.parent.kf_direction = self.kf_direction

    def show_alltogglestate(self, flag):
        if flag:
            # print "self.pointButton.GetValue()",self.pointButton.GetValue()
            print("self.btn_label_theospot.GetValue()", self.btn_label_theospot.GetValue())
            print("self.btn_label_expspot.GetValue()", self.btn_label_expspot.GetValue())

    def ToggleLabelExp(self, _):
        self.show_alltogglestate(0)

        if self.p2S == 0:
            self.btn_label_theospot.SetBackgroundColour("Green")
            self.btn_label_expspot.SetBackgroundColour(self.defaultColor)
            self.btn_label_expspot.SetValue(False)

            #             print "Disable Rotation around axis"
            self.SelectedRotationAxis = None
            self.moveccdandxtal.rotatebtn.SetLabel(self.moveccdandxtal.EnableRotationLabel)
            self.RotationActivated = False

            self.p2S = 1
            self.p3S = 0
        else:
            self.btn_label_theospot.SetBackgroundColour(self.defaultColor)
            self.btn_label_theospot.SetValue(False)

            self.p2S = 0

    def ToggleLabelSimul(self, _):
        self.show_alltogglestate(0)
        if self.p3S == 0:
            self.btn_label_expspot.SetBackgroundColour("Green")
            self.btn_label_theospot.SetBackgroundColour(self.defaultColor)
            self.btn_label_theospot.SetValue(False)

            #             print "Disable Rotation around axis"
            self.SelectedRotationAxis = None
            self.moveccdandxtal.rotatebtn.SetLabel(self.moveccdandxtal.EnableRotationLabel)
            self.RotationActivated = False

            self.p3S = 1
            self.p2S = 0
        else:
            self.btn_label_expspot.SetBackgroundColour(self.defaultColor)
            self.btn_label_expspot.SetValue(False)

            self.p3S = 0

    def display_current(self):
        """display current CCD parameters in txtctrls
        """
        self.parametersdisplaypanel.act_distance.SetValue(str(self.CCDParam[0]))
        self.parametersdisplaypanel.act_Xcen.SetValue(str(self.CCDParam[1]))
        self.parametersdisplaypanel.act_Ycen.SetValue(str(self.CCDParam[2]))
        self.parametersdisplaypanel.act_Ang1.SetValue(str(self.CCDParam[3]))
        self.parametersdisplaypanel.act_Ang2.SetValue(str(self.CCDParam[4]))

    def display_results(self, dataresults):
        """display CCD parameters refinement results in txtctrls
        """
        self.parametersdisplaypanel.act_distance_r.SetValue(str(dataresults[0]))
        self.parametersdisplaypanel.act_Xcen_r.SetValue(str(dataresults[1]))
        self.parametersdisplaypanel.act_Ycen_r.SetValue(str(dataresults[2]))
        self.parametersdisplaypanel.act_Ang1_r.SetValue(str(dataresults[3]))
        self.parametersdisplaypanel.act_Ang2_r.SetValue(str(dataresults[4]))
        self.act_residues.SetValue(str(np.round(dataresults[8], decimals=2)))
        self.nbspots_in_fit.SetValue(str(dataresults[9]))

    def close(self, _):
        self.Close(True)

    def OnSetCCDParams(self, event):
        """
        called by goto current button according to CCD parameters value
        """
        try:
            self.CCDParam = [float(self.parametersdisplaypanel.act_distance.GetValue()),
                            float(self.parametersdisplaypanel.act_Xcen.GetValue()),
                            float(self.parametersdisplaypanel.act_Ycen.GetValue()),
                            float(self.parametersdisplaypanel.act_Ang1.GetValue()),
                            float(self.parametersdisplaypanel.act_Ang2.GetValue())]
            print("Actual detector parameters are now default parameters", self.CCDParam)
            self.initialParameter["CCDParam"] = self.CCDParam

            self.update_data(event)
        except ValueError:
            dlg = wx.MessageDialog(self, "Detector Parameters in entry field are not float values! ",
                                    "Incorr",
                                    wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        self._replot(event)

    def OnInputParam(self, event):
        """
        in calibration frame
        """
        self.initialParameter["CCDParam"] = self.CCDParam
        self.initialParameter["pixelsize"] = self.pixelsize
        self.initialParameter["framedim"] = self.framedim
        self.initialParameter["kf_direction"] = self.kf_direction
        self.initialParameter["detectordiameter"] = self.detectordiameter

        print("before\n\n", self.initialParameter)

        DPBoard = DP.DetectorParameters(self, -1, "Detector parameters Board", self.initialParameter)

        DPBoard.ShowModal()
        DPBoard.Destroy()

        print("new param", self.CCDParam + [self.pixelsize,
                                            self.framedim[0],
                                            self.framedim[1],
                                            self.detectordiameter,
                                            self.kf_direction])

        self.display_current()
        self.update_data(event)

    #     def OnInputMatrix(self, event):
    #
    #         helptstr = 'Enter Matrix elements : \n [[a11, a12, a13],[a21, a22, a23],[a31, a32, a33]]'
    #         helptstr += 'Or list of Matrices'
    #         dlg = wx.TextEntryDialog(self, helptstr, 'Calibration- Orientation Matrix elements Entry')
    #
    #         _param = '[[1,0,0],[0, 1,0],[0, 0,1]]'
    #         dlg.SetValue(_param)
    #         if dlg.ShowModal() == wx.ID_OK:
    #             paramraw = str(dlg.GetValue())
    #             if paramraw != '1':  # neutral value ?
    #                 try:
    #                     paramlist = paramraw.split(',')
    #                     a11 = float(paramlist[0][2:])
    #                     a12 = float(paramlist[1])
    #                     a13 = float(paramlist[2][:-1])
    #                     a21 = float(paramlist[3][1:])
    #                     a22 = float(paramlist[4])
    #                     a23 = float(paramlist[5][:-1])
    #                     a31 = float(paramlist[6][1:])
    #                     a32 = float(paramlist[7])
    #                     a33 = float(paramlist[8][:-2])
    #
    #                     self.inputmatrix = np.array([[a11, a12, a13], [a21, a22, a23], [a31, a32, a33]])
    #                     # may think about normalisation
    #
    #                     self.manualmatrixinput = 1
    #                     self.deltamatrix = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    #                     dlg.Destroy()
    #
    #                     self._replot(event)
    #                     self.display_current()
    #
    #                 except ValueError:
    #                     txt = "Unable to read the UBmatrix elements !!.\n"
    #                     txt += "There might be entered some strange characters in the entry field. Check it...\n"
    #                     wx.MessageBox(txt, 'INFO')
    #                     return

    def EnterMatrix(self, event):

        helptstr = "Enter Matrix elements : \n [[a11, a12, a13],[a21, a22, a23],[a31, a32, a33]]"
        helptstr += "Or list of Matrices"
        dlg = wx.TextEntryDialog(self, helptstr, "Calibration- Orientation Matrix elements Entry")

        _param = "[[1,0,0],[0, 1,0],[0, 0,1]]"
        dlg.SetValue(_param)
        if dlg.ShowModal() == wx.ID_OK:
            paramraw = str(dlg.GetValue())
            import re

            listval = re.split("[ ()\[\)\;\,\]\n\t\a\b\f\r\v]", paramraw)
            #             print "listval", listval
            listelem = []
            for elem in listval:
                try:
                    val = float(elem)
                    listelem.append(val)
                except ValueError:
                    continue

            nbval = len(listelem)
            #             print "nbval", nbval

            if (nbval % 9) != 0:
                txt = "Something wrong, I can't read matrix or matrices"
                print(txt)

                wx.MessageBox(txt, "INFO")
                return

            nbmatrices = nbval / 9
            ListMatrices = np.zeros((nbmatrices, 3, 3))
            ind_elem = 0
            for ind_matrix in range(nbmatrices):
                for i in range(3):
                    for j in range(3):
                        floatval = listelem[ind_elem]
                        ListMatrices[ind_matrix][i][j] = floatval
                        ind_elem += 1

            # save in list of orientation matrix
            # default name
            inputmatrixname = "InputMat_"

            initlength = len(DictLT.dict_Rot)
            for k, mat in enumerate(ListMatrices):
                mname = inputmatrixname + "%d" % k
                DictLT.dict_Rot[mname] = mat
                self.crystalparampanel.comboMatrix.Append(mname)
            print("len dict", len(DictLT.dict_Rot))

            # or combo.Clear  combo.Appenditems(dict.rot)
            #             listrot = DictLT.dict_Rot.keys()
            #             sorted(listrot)
            #             self.crystalparampanel.comboMatrix.choices = listrot
            self.crystalparampanel.comboMatrix.SetSelection(initlength)
            #             self.crystalparampanel.comboMatrix.SetValue(inputmatrixname + '0')

            # update with the first input matrix
            self.inputmatrix = ListMatrices[0]
            # may think about normalisation

            self.manualmatrixinput = 1
            self.deltamatrix = np.eye(3)

            dlg.Destroy()

            self._replot(event)
            self.display_current()

    def OnChangeBMatrix(self, event):
        """
        Bmatrix selected in list
        """
        self._replot(event)
        self.display_current()

    def OnChangeMatrix(self, event):
        """
        UBmatrix selected in list
        """
        self.deltamatrix = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        self.manualmatrixinput = 0
        self._replot(event)
        self.display_current()

    #     def OnChangeTransforms(self, event):
    #         """
    #         UBmatrix selected in list
    #         """
    #         self._replot(event)
    #         self.display_current()

    def OnChangeExtinc(self, event):
        self._replot(event)
        self.display_current()

    def OnChangeElement(self, event):
        key_material = self.crystalparampanel.comboElem.GetValue()
        self.sb.SetStatusText("Selected Material: %s" % str(DictLT.dict_Materials[key_material]))

        print("I change element to %s" % key_material)

        self.strainxtal.update_latticeparameters()
        # update extinctions rules
        extinc = DictLT.dict_Extinc_inv[DictLT.dict_Materials[key_material][2]]
        self.crystalparampanel.comboExtinctions.SetValue(extinc)
        self._replot(event)
        self.display_current()

    def update_data(self, event):
        """
        update experimental data according to CCD parameters
        and replot simulated data 
        with _replot
        """
        self.ReadExperimentData()

        # update theoretical data
        self._replot(event)
        self.display_current()

    # ---   --- Step Movements functions
    def OnDecreaseDistance(self, event):

        self.CCDParam[0] -= float(self.moveccdandxtal.stepdistance.GetValue())
        #         if self.CCDParam[0] < 20.:
        #             print "Distance seems too low..."
        #             self.CCDParam[0] = 20.
        self.update_data(event)

    def OnIncreaseDistance(self, event):

        self.CCDParam[0] += float(self.moveccdandxtal.stepdistance.GetValue())
        if self.CCDParam[0] > 200.0:
            print("Distance seems too high...")
            self.CCDParam[0] = 200.0
        self.update_data(event)

    def OnDecreaseXcen(self, event):

        self.CCDParam[1] -= float(self.moveccdandxtal.stepXcen.GetValue())
        if self.CCDParam[1] < -3000.0:
            print("Xcen seems too low...")
            self.CCDParam[1] = 3000
        self.update_data(event)

    def OnIncreaseXcen(self, event):

        self.CCDParam[1] += float(self.moveccdandxtal.stepXcen.GetValue())
        if self.CCDParam[1] > 6000.0:
            print("Xcen seems too high...")
            self.CCDParam[1] = 6000.0

        self.update_data(event)

    def OnDecreaseYcen(self, event):

        self.CCDParam[2] -= float(self.moveccdandxtal.stepYcen.GetValue())
        if self.CCDParam[2] < -3000.0:
            print("Ycen seems too low...")
            self.CCDParam[2] = -3000.0

        self.update_data(event)

    def OnIncreaseYcen(self, event):

        self.CCDParam[2] += float(self.moveccdandxtal.stepYcen.GetValue())
        if self.CCDParam[2] > 6000.0:
            print("Ycen seems too high...")
            self.CCDParam[2] = 6000.0

        self.update_data(event)

    def OnDecreaseang1(self, event):

        self.CCDParam[3] -= float(self.moveccdandxtal.stepang1.GetValue())
        #         if self.CCDParam[3] < -60.:
        #             print "Ang1 seems too low..."
        #             self.CCDParam[3] = -60.

        self.update_data(event)

    def OnIncreaseang1(self, event):

        self.CCDParam[3] += float(self.moveccdandxtal.stepang1.GetValue())
        #         if self.CCDParam[3] > 60.:
        #             print "Ang1 seems too high..."
        #             self.CCDParam[3] = 60.

        self.update_data(event)

    def OnDecreaseang2(self, event):

        self.CCDParam[4] -= float(self.moveccdandxtal.stepang2.GetValue())
        #         if self.CCDParam[4] < -60.:
        #             print "Ang2 seems too low..."
        #             self.CCDParam[4] = -60.

        self.update_data(event)

    def OnIncreaseang2(self, event):

        self.CCDParam[4] += float(self.moveccdandxtal.stepang2.GetValue())
        #         if self.CCDParam[4] > 60.:
        #             print "Ang2 seems too high..."
        #             self.CCDParam[4] = 60.

        self.update_data(event)

    # incrementing or decrementing orientation elementary angles
    def OnDecreaseAngle1(self, event):  # delta orientation angles around elementary axes
        # Xjsm =y Xmas  Yjsm = -Xxmas Zjsm = Zxmas
        a1 = float(self.moveccdandxtal.angle1.GetValue()) * DEG

        mat = np.array([[math.cos(a1), 0, -math.sin(a1)],
                        [0, 1, 0],
                        [math.sin(a1), 0, math.cos(a1)]])  # in XMAS and fitOrient
        self.deltamatrix = mat

        self._replot(event)
        self.display_current()

    def OnIncreaseAngle1(self, event):

        a1 = float(self.moveccdandxtal.angle1.GetValue()) * DEG
        mat = np.array([[math.cos(a1), 0, math.sin(a1)],
                        [0, 1, 0],
                        [-math.sin(a1), 0, math.cos(a1)]])  # in XMAS and fitOrient
        self.deltamatrix = mat

        self._replot(event)
        self.display_current()

    def OnDecreaseAngle2(self, event):

        a2 = float(self.moveccdandxtal.angle2.GetValue()) * DEG
        # mat = np.array([[math.cos(a2),0, math.sin(-a2)],[0, 1,0],[math.sin(a2),0, math.cos(a2)]])  #in LaueTools Frame
        mat = np.array([[1, 0, 0],
                        [0, math.cos(a2), -math.sin(a2)],
                        [0, math.sin(a2), math.cos(a2)]])  # in XMAS and fitOrient
        self.deltamatrix = mat

        self._replot(event)
        self.display_current()

    def OnIncreaseAngle2(self, event):

        a2 = float(self.moveccdandxtal.angle2.GetValue()) * DEG
        # mat = np.array([[math.cos(a2),0, math.sin(a2)],[0, 1,0],[-math.sin(a2),0, math.cos(a2)]]) in LaueTools Frame
        mat = np.array([[1, 0, 0],
                        [0, math.cos(a2), math.sin(a2)],
                        [0, math.sin(-a2), math.cos(a2)]])  # in XMAS and fitOrient
        self.deltamatrix = mat

        self._replot(event)
        self.display_current()

    def OnDecreaseAngle3(self, event):

        a3 = float(self.moveccdandxtal.angle3.GetValue()) * DEG
        mat = np.array([[math.cos(a3), math.sin(a3), 0],
                        [math.sin(-a3), math.cos(a3), 0],
                        [0.0, 0, 1]])  # XMAS and LaueTools are similar
        self.deltamatrix = mat

        self._replot(event)
        self.display_current()

    def OnIncreaseAngle3(self, event):

        a3 = float(self.moveccdandxtal.angle3.GetValue()) * DEG
        mat = np.array([[math.cos(a3), -math.sin(a3), 0],
                        [math.sin(a3), math.cos(a3), 0],
                        [0, 0, 1]])
        self.deltamatrix = mat

        self._replot(event)
        self.display_current()

    def OnSwitchPlot(self, event):
        self.tog += 1

        if self.tog % 3 == 0:
            self.datatype = "2thetachi"
        elif self.tog % 3 == 1:
            self.datatype = "gnomon"
        elif self.tog % 3 == 2:
            self.datatype = "pixels"

        self.init_plot = True
        self._replot(event)
        self.display_current()

    def OnCheckEmaxValue(self, _):
        # emax = float(self.crystalparampanel.emaxC.GetValue())
        pass

    #         if emax > 50:
    #             dlg = wx.MessageDialog(parent=self, message="This high energy limit emax=%s will be time-consumming!\nAre you sure?" % emax,
    #                                caption="Warning", style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
    #             if dlg.ShowModal() == wx.ID_NO:
    #                 self.crystalparampanel.emaxC.SetValue(25)
    #
    #             dlg.Destroy()

    def OnCheckEminValue(self, _):
        # emin = float(self.crystalparampanel.eminC.GetValue())
        pass

    #         if emin > 50:
    #             dlg = wx.MessageDialog(parent=self, message="This high energy limit emin=%s will be time-consumming!" % emin,
    #                                caption="Warning", style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
    #             if dlg.ShowModal() == wx.ID_NO:
    #                 self.crystalparampanel.eminC.SetValue(5)
    #             dlg.Destroy()

    def define_kf_direction(self):
        """
        define main region of Laue Pattern simulation
        """
        #         print "Define mean region of simulation in MainCalibrationFrame"
        Central2Theta = float(self.plotrangepanel.mean2theta.GetValue())
        CentralChi = float(self.plotrangepanel.meanchi.GetValue())

        # reflection (camera top)
        if (Central2Theta, CentralChi) == (90, 0):
            self.kf_direction = "Z>0"
        # transmission
        elif (Central2Theta, CentralChi) == (0, 0):
            self.kf_direction = "X>0"
        # back reflection
        elif (Central2Theta, CentralChi) == (180, 0):
            self.kf_direction = "X<0"
        # reflection (camera side plus)
        elif (Central2Theta, CentralChi) == (90, 90):
            self.kf_direction = "Y>0"
        # reflection (camera side plus)
        elif (Central2Theta, CentralChi) == (90, -90):
            self.kf_direction = "Y<0"
        else:
            self.kf_direction = [Central2Theta, CentralChi]

    #         print "kf_direction chosen:", self.kf_direction

    def onSetOrientMatrix_with_BMatrix(self, _):
        print("reset orientmatrix by integrating B matrix: OrientMatrix=OrientMatrix*B")
        self.crystalparampanel.UBmatrix = np.dot(self.crystalparampanel.UBmatrix, self.Bmatrix)

        self.crystalparampanel.comboBmatrix.SetValue("Identity")

    def simulate_theo(self, removeharmonics=0):
        """
        in MainCalibrationFrame

        Simulate theoretical Laue spots properties

        removeharmonics:  1  keep only lowest hkl (fondamental) for each harmonics spots family
                          0  consider all spots (fond. + harmonics)

        return:
        twicetheta, chi, self.Miller_ind, posx, posy, Energy
        """
        # print "self.UBmatrix",self.UBmatrix
        # print "misorientation UBmatrix",self.deltamatrix

        ResolutionAngstrom = None

        self.Extinctions = DictLT.dict_Extinc[
            self.crystalparampanel.comboExtinctions.GetValue()]

        # default
        # (deltamatrix can be updated step by step by buttons)
        if self.manualmatrixinput is None:
            self.crystalparampanel.UBmatrix = np.dot(
                self.deltamatrix, self.crystalparampanel.UBmatrix)
            # reset deltamatrix
            self.deltamatrix = np.eye(3)

        # from combobox of UBmatrix
        elif self.manualmatrixinput == 0:
            # self.UBmatrix = np.dot(self.deltamatrix, LaueToolsframe.dict_Rot[self.comboMatrix.GetValue()])
            self.crystalparampanel.UBmatrix = DictLT.dict_Rot[
                self.crystalparampanel.comboMatrix.GetValue()]
            # to keep self.UBmatrix unchanged at this step
            self.manualmatrixinput = None

        # from manual input
        elif self.manualmatrixinput == 1:
            self.crystalparampanel.UBmatrix = self.inputmatrix
            self.manualmatrixinput = None

        if 0:
            print("Beginning simulation of spots")
            print("self.UBmatrix", self.crystalparampanel.UBmatrix)
            print("misorientation UBmatrix", self.deltamatrix)

        pixelsize = self.pixelsize

        #         print "pixelsize in simulate_theo", pixelsize

        self.define_kf_direction()
        #        self.kf_direction = LaueToolsframe.kf_direction

        self.emin = self.crystalparampanel.eminC.GetValue()
        self.emax = self.crystalparampanel.emaxC.GetValue()

        self.key_material = self.crystalparampanel.comboElem.GetValue()

        Grain = CP.Prepare_Grain(self.key_material, self.crystalparampanel.UBmatrix,
                                                    dictmaterials=self.dict_Materials)

        self.B0matrix = Grain[0]

        Bmatrix_key = str(self.crystalparampanel.comboBmatrix.GetValue())
        self.Bmatrix = DictLT.dict_Transforms[Bmatrix_key]

        Grain[2] = np.dot(Grain[2], self.Bmatrix)

        if self.CCDLabel.startswith("sCMOS"):  # squared detector
            diameter_for_simulation = self.detectordiameter * 1.4 * 1.25
        else:
            diameter_for_simulation = self.detectordiameter

        SINGLEGRAIN = 1
        if SINGLEGRAIN:  # for single grain simulation
            if self.kf_direction in ("Z>0", "X>0") and removeharmonics == 0:
                # for single grain simulation (WITH HARMONICS   TROUBLE with TRansmission geometry)
                ResSimul = LAUE.SimulateLaue_full_np(Grain,
                                                    self.emin,
                                                    self.emax,
                                                    self.CCDParam[:5],
                                                    kf_direction=self.kf_direction,
                                                    ResolutionAngstrom=False,
                                                    removeharmonics=removeharmonics,
                                                    pixelsize=pixelsize,
                                                    dim=self.framedim,
                                                    detectordiameter=diameter_for_simulation * 1.25,
                                                    force_extinction=self.Extinctions,
                                                    dictmaterials=self.dict_Materials)
            else:
                ResSimul = LAUE.SimulateLaue(Grain,
                                            self.emin,
                                            self.emax,
                                            self.CCDParam[:5],
                                            kf_direction=self.kf_direction,
                                            ResolutionAngstrom=ResolutionAngstrom,
                                            removeharmonics=removeharmonics,
                                            pixelsize=pixelsize,
                                            dim=self.framedim,
                                            detectordiameter=diameter_for_simulation * 1.25,
                                            force_extinction=self.Extinctions,
                                            dictmaterials=self.dict_Materials)

            #             print "ResSimul", ResSimul[2]
            #             print 'len ResSimul[2]', len(ResSimul[2])
            if ResSimul is None:
                return None

            (twicetheta, chi, self.Miller_ind, posx, posy, Energy) = ResSimul

        #             print "nb of spots", len(twicetheta)

        else:
            # for twinned grains simulation
            print("---------------------------")
            print("Twins simulation mode")
            print("---------------------------")

            Grainparent = Grain
            twins_operators = [DictLT.dict_Transforms["twin010"]]
            #             twins_operators = [DictLT.dict_Transforms['sigma3_1']]

            #             axisrot = [np.cos((103.68 - 90) * DEG), 0, np.sin((103.68 - 90) * DEG)]
            #             rot180 = GT.matRot(axisrot, 180.)
            #             twins_operators = [rot180]

            (twicetheta,
                chi,
                self.Miller_ind,
                posx,
                posy,
                Energy) = LAUE.SimulateLaue_twins(Grainparent,
                                                twins_operators,
                                                self.emin,
                                                self.emax,
                                                self.CCDParam[:5],
                                                only_2thetachi=False,
                                                kf_direction=self.kf_direction,
                                                ResolutionAngstrom=False,
                                                removeharmonics=1,
                                                pixelsize=pixelsize,
                                                dim=self.framedim,
                                                detectordiameter=diameter_for_simulation * 1.25)

            print("nb of spots", len(twicetheta))

        return twicetheta, chi, self.Miller_ind, posx, posy, Energy

    def _replot(self, _):  # in MainCalibrationFrame
        """
        in MainCalibrationFrame
        Plot simulated spots only in 2theta, chi space
        """
        # simulate theo data
        ResSimul = self.simulate_theo()  # twicetheta, chi, self.Miller_ind, posx, posy
        if ResSimul is None:
            self.deltamatrix = np.eye(3)
            print("reset deltamatrix to identity")
            return

        self.data_theo = ResSimul

        if not self.init_plot:
            xlim = self.axes.get_xlim()
            ylim = self.axes.get_ylim()

        #             print "limits x", xlim
        #             print "limits y", ylim

        #         print "_replot MainCalibrationFrame"
        self.axes.clear()
        self.axes.set_autoscale_on(False)  # Otherwise, infinite loop
        #         self.axes.set_autoscale_on(True)

        # to have the data coordinates when pointing with the mouse
        def fromindex_to_pixelpos_x(index, pos):
            return index

        def fromindex_to_pixelpos_y(index, pos):
            return index

        self.axes.xaxis.set_major_formatter(FuncFormatter(fromindex_to_pixelpos_x))
        self.axes.yaxis.set_major_formatter(FuncFormatter(fromindex_to_pixelpos_y))

        # plot THEORETICAL SPOTS simulated data ------------------------------------------
        if self.data_theo is not None:  # only in 2theta, chi space
            # self.axes.scatter(self.data_theo[0], self.data_theo[1],s=50, marker='o',alpha=0, edgecolor='r',c='w')

            # laue spot model intensity 2
            Energy = self.data_theo[5]

            Polariz = (1 - (np.sin(self.data_theo[0] * DEG) * np.sin(self.data_theo[1] * DEG))** 2)
            #
            #             sizespot = 150 * np.exp(-Energy * 1. / 10.)  # * Polariz
            #             print "len(Polariz)", len(Polariz)
            #             print "Energy", Energy
            #             print "sizespot", sizespot
            #             print 'len(np.array(self.data_theo[2]))', len(np.array(self.data_theo[2]))
            Fsquare = 50.0 / np.sum(np.array(self.data_theo[2]) ** 2, axis=1)

            #             print "Fsquare", Fsquare[:5]

            sizespot = (100 * GT.CCDintensitymodel2(Energy) * Fsquare * Polariz
                * float(self.plotrangepanel.spotsizefactor.GetValue()))

            #             print "Polariz", Polariz
            #             print "Fsquare", Fsquare

            if self.datatype == "2thetachi":
                # dependent of matplotlib and OS see pickyframe...
                # self.axes.scatter(self.data_theo[0], self.data_theo[1],s=sizespot, marker='o',alpha=0, edgecolor='r',c='w')  # don't work with linux and matplotlib 0.99.1
                # self.axes.scatter(self.data_theo[0], self.data_theo[1],s = sizespot, marker='o',alpha=0, edgecolor='r',c='w')
                self.axes.scatter(self.data_theo[0],
                                    self.data_theo[1],
                                    s=sizespot,
                                    marker="o",
                                    edgecolor="r",
                                    facecolor="None")

            elif self.datatype == "gnomon":
                # compute Gnomonic projection
                nbofspots = len(self.data_theo[0])
                sim_dataselected = IOLT.createselecteddata(
                                        (self.data_theo[0], self.data_theo[1], np.ones(nbofspots)),
                                        np.arange(nbofspots), nbofspots)[0]
                self.sim_gnomonx, self.sim_gnomony = IIM.ComputeGnomon_2(sim_dataselected)
                self.axes.scatter(self.sim_gnomonx,
                                    self.sim_gnomony,
                                    s=sizespot,
                                    marker="o",
                                    edgecolor="r",
                                    facecolor="None")

            elif self.datatype == "pixels":
                # dependent of matplotlib and OS see pickyframe...
                # self.axes.scatter(self.data_theo[0], self.data_theo[1],s=sizespot, marker='o',alpha=0, edgecolor='r',c='w')  # don't work with linux and matplotlib 0.99.1
                # self.axes.scatter(self.data_theo[0], self.data_theo[1],s=sizespot, marker='o',alpha=0, edgecolor='r',c='w')
                self.axes.scatter(self.data_theo[3],
                                    self.data_theo[4],
                                    s=sizespot,
                                    marker="o",
                                    edgecolor="r",
                                    facecolor="None")

        # plot EXPERIMENTAL data ----------------------------------------
        if self.datatype == "2thetachi":
            originChi = 0

            if self.plotrangepanel.shiftChiOrigin.GetValue():
                originChi = float(self.plotrangepanel.meanchi.GetValue())

            self.axes.scatter(self.twicetheta,
                                self.chi + originChi,
                                s=self.Data_I / np.amax(self.Data_I) * 100.0,
                                c=self.Data_I / 50.0,
                                alpha=0.5)

            if self.init_plot:
                amp2theta = float(self.plotrangepanel.range2theta.GetValue())
                mean2theta = float(self.plotrangepanel.mean2theta.GetValue())

                ampchi = float(self.plotrangepanel.rangechi.GetValue())
                meanchi = float(self.plotrangepanel.meanchi.GetValue())

                min2theta = max(0, mean2theta - amp2theta)
                max2theta = min(180.0, mean2theta + amp2theta)

                minchi = max(-180, meanchi - ampchi)
                maxchi = min(180.0, meanchi + ampchi)

                mean2theta = 0.5 * (min2theta + max2theta)
                halfampli2theta = 0.5 * (max2theta - min2theta)

                meanchi = 0.5 * (maxchi + minchi)
                halfamplichi = 0.5 * (maxchi - minchi)

                xlim = (mean2theta - halfampli2theta, mean2theta + halfampli2theta)
                ylim = (meanchi - halfamplichi, meanchi + halfamplichi)

            self.axes.set_xlabel("2theta(deg.)")
            self.axes.set_ylabel("chi(deg)")

        elif self.datatype == "gnomon":

            self.data_gnomonx, self.data_gnomony = self.computeGnomonicExpData()

            self.axes.scatter(self.data_gnomonx,
                                self.data_gnomony,
                                s=self.Data_I / np.amax(self.Data_I) * 100.0,
                                c=self.Data_I / 50.0,
                                alpha=0.5)

            if self.init_plot:
                xmin = np.amin(self.data_gnomonx) - 0.1
                xmax = np.amax(self.data_gnomonx) + 0.1
                ymin = np.amin(self.data_gnomony) - 0.1
                ymax = np.amax(self.data_gnomony) + 0.1

                ylim = (ymin, ymax)
                xlim = (xmin, xmax)

            self.axes.set_xlabel("X gnomon")
            self.axes.set_ylabel("Y gnomon")

        elif self.datatype == "pixels":
            self.axes.scatter(self.data_x,
                            self.data_y,
                            s=self.Data_I / np.amax(self.Data_I) * 100.0,
                            c=self.Data_I / 50.0,
                            alpha=0.5)
            if self.init_plot:
                ylim = (-100, self.framedim[0] + 100)
                xlim = (-100, self.framedim[1] + 100)
            self.axes.set_xlabel("X CCD")
            self.axes.set_ylabel("Y CCD")

        self.axes.set_title("%s %d spots" % (os.path.split(self.filename)[-1], len(self.twicetheta)))
        self.axes.grid(True)

        # restore the zoom limits(unless they're for an empty plot)
        if xlim != (0.0, 1.0) or ylim != (0.0, 1.0):
            self.axes.set_xlim(xlim)
            self.axes.set_ylim(ylim)

        self.init_plot = False

        # redraw the display
        self.canvas.draw()

    def SelectOnePoint(self, event):
        """
        in MainCalibrationFrame
        """
        toreturn = []
        self.successfull = 0

        if self.nbsuccess == 0:
            self.EXPpoints = []

        xtol = 20
        ytol = 20.0
        """
        self.twicetheta, self.chi, self.Data_I, self.filename = self.data
        self.Data_index_expspot = np.arange(len(self.twicetheta))
        """
        xdata, ydata, annotes = (self.twicetheta, self.chi,
                                    list(zip(self.Data_index_expspot, self.Data_I)))

        _dataANNOTE_exp = list(zip(xdata, ydata, annotes))

        clickX = event.xdata
        clickY = event.ydata

        # print clickX, clickY

        annotes = []
        for x, y, a in _dataANNOTE_exp:
            if (clickX - xtol < x < clickX + xtol) and (clickY - ytol < y < clickY + ytol):
                annotes.append((GT.cartesiandistance(x, clickX, y, clickY), x, y, a))

        if annotes:
            annotes.sort()
            _distance, x, y, annote = annotes[0]
            # print "the nearest experimental point is at(%.2f,%.2f)"%(x, y)
            # print "with index %d and intensity %.1f"%(annote[0],annote[1])

            self.EXPpoints.append([annote[0], x, y])
            self.successfull = 1
            self.nbsuccess += 1
            print("# selected points", self.nbsuccess)
            # print "Coordinates(%.3f,%.3f)"%(x, y)

            toreturn = self.EXPpoints

        return toreturn

    def SelectThreePoints(self, event):
        """
        in MainCalibrationFrame
        """
        toreturn = []
        if self.nbclick_zone <= 3:
            if self.nbclick_zone == 1:
                self.threepoints = []
            xtol = 0.5
            ytol = 0.5
            """
            self.twicetheta, self.chi, self.Data_I, self.filename = self.data
            self.Data_index_expspot = np.arange(len(self.twicetheta))
            """
            xdata, ydata, annotes = (self.twicetheta, self.chi,
                                        list(zip(self.Data_index_expspot, self.Data_I)))

            _dataANNOTE_exp = list(zip(xdata, ydata, annotes))

            clickX = event.xdata
            clickY = event.ydata
            # print clickX, clickY
            annotes = []
            for x, y, a in _dataANNOTE_exp:
                if (clickX - xtol < x < clickX + xtol) and (clickY - ytol < y < clickY + ytol):
                    annotes.append((GT.cartesiandistance(x, clickX, y, clickY), x, y, a))

            if annotes:
                annotes.sort()
                _distance, x, y, annote = annotes[0]
                # print "the nearest experimental point is at(%.2f,%.2f)"%(x, y)
                # print "with index %d and intensity %.1f"%(annote[0],annote[1])

            self.threepoints.append([annote[0], x, y])
            print("# selected points", self.nbclick_zone)
            # print "Coordinates(%.3f,%.3f)"%(x, y)
            if len(self.threepoints) == 3:
                toreturn = self.threepoints
                self.nbclick_zone = 0
                print("final triplet", toreturn)

        self.nbclick_zone += 1
        self._replot(event)
        return toreturn

    def SelectSixPoints(self, event):
        """
        in MainCalibrationFrame
        """
        toreturn = []
        if self.nbclick_zone <= 6:
            if self.nbclick_zone == 1:
                self.sixpoints = []
            xtol = 2.0
            ytol = 2.0
            """
            self.twicetheta, self.chi, self.Data_I, self.filename = self.data
            self.Data_index_expspot = np.arange(len(self.twicetheta))
            """
            xdata, ydata, annotes = (self.twicetheta, self.chi,
                                                list(zip(self.Data_index_expspot, self.Data_I)))

            _dataANNOTE_exp = list(zip(xdata, ydata, annotes))

            clickX = event.xdata
            clickY = event.ydata

            # print clickX, clickY

            annotes = []
            for x, y, a in _dataANNOTE_exp:
                if (clickX - xtol < x < clickX + xtol) and (clickY - ytol < y < clickY + ytol):
                    annotes.append((GT.cartesiandistance(x, clickX, y, clickY), x, y, a))

            print("# selected points", self.nbclick_zone)
            if annotes:
                annotes.sort()
                _distance, x, y, annote = annotes[0]
                print("the nearest experimental point is at(%.2f,%.2f)" % (x, y))
                print("with index %d and intensity %.1f" % (annote[0], annote[1]))

            self.sixpoints.append([annote[0], x, y])

            if len(self.sixpoints) == 6:
                toreturn = self.sixpoints
                self.nbclick_zone = 0
                print("final six points", toreturn)

        self.nbclick_zone += 1
        self._replot(event)
        return toreturn

    def OnSelectZoneAxes(self, event):
        """
        in MainCalibrationFrame
        TODO: not implemented yet
        """
        pass

    def textentry(self):
        """
        in MainCalibrationFrame
        TODO: use better SetDetectorParam() of frame
        """
        dlg = wx.TextEntryDialog(self, "Enter Miller indices: [h, k,l]", "Miller indices entry")
        dlg.SetValue("[0, 0,1]")
        if dlg.ShowModal() == wx.ID_OK:
            miller = dlg.GetValue()
        dlg.Destroy()
        Miller = np.array(np.array(miller[1:-1].split(",")), dtype=int)
        return Miller

    def OnInputMiller(self, evt):
        """
        user selects TWO exp and gives corresponding miller indices
        comparison of theo and exp; distances.
        VERY usefull if the reference sample is well known
        """

        pts = self.SelectOnePoint(evt)

        if self.nbsuccess == 1:
            index1, X1, Y1 = pts[0]
            print("selected # exp.spot:", index1, " @(%.3f,%.3f)" % (X1, Y1))
            self.twopoints = [[X1, Y1]]

        if self.nbsuccess == 2:
            index1, X1, Y1 = pts[0]
            index2, X2, Y2 = pts[1]
            print("selected # exp.spot:", index2, " @(%.3f,%.3f)" % (X2, Y2))

            self.twopoints.append([X2, Y2])

            mil1 = self.textentry()
            print(mil1)
            mil2 = self.textentry()
            print(mil2)
            tdist = (np.arccos(np.dot(mil1, mil2) / np.sqrt(np.dot(mil1, mil1) * np.dot(mil2, mil2)))
                * 180.0 / np.pi)
            print("Theoretical distance", tdist)
            _dist = GT.distfrom2thetachi(np.array(self.twopoints[0]), np.array(self.twopoints[1]))
            print("Experimental distance: %.3f deg " % _dist)
            if _dist < 0.0000001:
                print("You may have selected the same theoretical spot ... So the distance is 0!")

            self.nbsuccess = 0

            wx.MessageBox("selected # exp.spot:%d @(%.3f ,%.3f)\nselected # exp.spot:%d @(%.3f ,%.3f)\nTheoretical distance %.3f\nExperimental distance %.3f"
                % (index1, X1, Y1, index2, X2, Y2, tdist, _dist), "Results")

    def allbuttons_off(self):
        """
        in MainCalibrationFrame
        """
        # self.pointButton.SetValue(False)
        self.btn_label_theospot.SetValue(False)
        self.btn_label_expspot.SetValue(False)

    def readlogicalbuttons(self):
        # return [self.pointButton.GetValue(),
        # self.btn_label_theospot.GetValue(),
        # self.btn_label_expspot.GetValue(),
        # self.pointButton3.GetValue()]

        return [self.btn_label_theospot.GetValue(), self.btn_label_expspot.GetValue()]

    def _on_point_choice(self, evt):
        """
        TODO: remove! obsolete
        in MainCalibrationFrame
        """
        if self.readlogicalbuttons() == [True, False]:
            self.allbuttons_off()
            self.btn_label_theospot.SetValue(True)
            self.Annotate_exp(evt)
        if self.readlogicalbuttons() == [False, True]:
            self.allbuttons_off()
            self.btn_label_expspot.SetValue(True)
            self.Annotate_theo(evt)

    def select_2pts(self, evt):  # pick distance
        """
        in MainCalibrationFrame
        """
        toreturn = []
        if self.nbclick_dist <= 2:
            if self.nbclick_dist == 1:
                self.twopoints = []

            self.twopoints.append([evt.xdata, evt.ydata])
            print("# selected points", self.nbclick_dist)
            print("Coordinates(%.3f,%.3f)" % (evt.xdata, evt.ydata))
            print("click", self.nbclick_dist)

            if len(self.twopoints) == 2:
                # compute angular distance:
                spot1 = self.twopoints[0]  # (X, Y) (e.g. 2theta, chi)
                spot2 = self.twopoints[1]
                if self.datatype == "2thetachi":
                    _dist = GT.distfrom2thetachi(np.array(spot1), np.array(spot2))
                    print("angular distance :  %.3f deg " % _dist)
                if self.datatype == "gnomon":
                    tw, ch = IIM.Fromgnomon_to_2thetachi(
                        [np.array([spot1[0], spot2[0]]),
                            np.array([spot1[1], spot2[1]])],
                        0,)[:2]
                    _dist = GT.distfrom2thetachi(np.array([tw[0], ch[0]]), np.array([tw[1], ch[1]]))
                    print("angular distance :  %.3f deg " % _dist)
                toreturn = self.twopoints
                self.nbclick_dist = 0
                # self.twopoints = []
                self.btn_label_theospot.SetValue(False)

        self.nbclick_dist += 1
        self._replot(evt)
        return toreturn

    def Reckon_2pts(self, evt):  # Recognise distance
        """
        in MainCalibrationFrame
        .. todo::
            May be useful to integrate back to the calibration board
        """
        twospots = self.select_2pts(evt)

        if twospots:
            print("twospots", twospots)
            spot1 = twospots[0]
            spot2 = twospots[1]
            print("---Selected points")

            if self.datatype == "2thetachi":
                _dist = GT.distfrom2thetachi(np.array(spot1), np.array(spot2))
                print("(2theta, chi) ")

            elif self.datatype == "gnomon":
                tw, ch = IIM.Fromgnomon_to_2thetachi(
                    [np.array([spot1[0], spot2[0]]), np.array([spot1[1], spot2[1]])], 0
                )[:2]
                _dist = GT.distfrom2thetachi(np.array([tw[0], ch[0]]), np.array([tw[1], ch[1]]))
                spot1 = [tw[0], ch[0]]
                spot2 = [tw[1], ch[1]]

            print("spot1 [%.3f,%.3f]" % (tuple(spot1)))
            print("spot2 [%.3f,%.3f]" % (tuple(spot2)))
            print("angular distance :  %.3f deg " % _dist)

            # distance recognition -------------------------
            ang_tol = 2.0
            # residues matching angle -------------------------
            ang_match = 5.0

            ind_sorted_LUT_MAIN_CUBIC = [np.argsort(elem) for elem in FindO.LUT_MAIN_CUBIC]
            sorted_table_angle = []
            for k in range(len(ind_sorted_LUT_MAIN_CUBIC)):
                # print len(LUT_MAIN_CUBIC[k])
                # print len(ind_sorted_LUT_MAIN_CUBIC[k])
                sorted_table_angle.append((FindO.LUT_MAIN_CUBIC[k])[ind_sorted_LUT_MAIN_CUBIC[k]])

            sol = INDEX.twospots_recognition([spot1[0] / 2.0, spot1[1]],
                                                [spot2[0] / 2.0, spot2[1]], ang_tol)
            print("sol = ", sol)

            print("\n")
            print("---Planes Recognition---")
            if type(sol) == type(np.array([1, 2])):
                print("planes found ------ for angle %.3f within %.2f deg"% (_dist, ang_tol))
                print("spot 1          spot 2           theo. value(deg)")
                for k in range(len(sol[0])):
                    theodist = (np.arccos(np.dot(sol[0][k], sol[1][k])
                            / np.sqrt(np.dot(sol[0][k], sol[0][k])* np.dot(sol[1][k], sol[1][k])
                            ))
                        * 180.0 / np.pi)
                    # print sol[0][k]
                    # print sol[1][k]
                    print(" %s          %s           %.3f" % (str(sol[0][k]), str(sol[1][k]), theodist))

                res = []
                self.mat_solution = [[] for k in range(len(sol[0]))]
                self.TwicethetaChi_solution = [[] for k in range(len(sol[0]))]

                print("datatype", self.datatype)

                for k in range(len(sol[0])):
                    mymat = FindO.givematorient(sol[0][k], spot1, sol[1][k], spot2, verbose=0)
                    self.mat_solution[k] = mymat
                    emax = 25
                    emin = 5
                    vecteurref = np.eye(3)  # means: a* // X, b* // Y, c* //Z
                    grain = [vecteurref, [1, 1, 1], mymat, "Cu"]

                    # PATCH: redefinition of grain to simulate any unit cell(not only cubic) ---
                    key_material = grain[3]
                    grain = CP.Prepare_Grain(key_material, grain[2],dictmaterials=self.dict_Materials)
                    # -----------------------------------------------------------------------------

                    # array(vec) and array(indices)(here with fastcompute = 0 array(indices) = 0) of spots exiting the crystal in 2pi steradian(Z>0)
                    spots2pi = LAUE.getLaueSpots(DictLT.CST_ENERGYKEV / emax,
                                                DictLT.CST_ENERGYKEV / emin,
                                                [grain],
                                                [[""]],
                                                fastcompute=1,
                                                fileOK=0,
                                                verbose=0,
                                                dictmaterials=self.dict_Materials)
                    # 2theta, chi of spot which are on camera(with harmonics)
                    TwicethetaChi = LAUE.filterLaueSpots(spots2pi, fileOK=0, fastcompute=1)
                    self.TwicethetaChi_solution[k] = TwicethetaChi

                    if self.datatype == "2thetachi":
                        tout = matchingrate.getProximity(TwicethetaChi,
                                                        np.array(self.data[0]) / 2.0,
                                                        np.array(self.data[1]),
                                                        angtol=ang_match)
                    elif self.datatype == "gnomon":
                        # print "self.data in reckon 2pts",self.data[0][:10]
                        TW, CH = IIM.Fromgnomon_to_2thetachi(self.data[:2], 0)[:2]
                        # print "TW in reckon 2pst",TW[:10]
                        # LaueToolsframe.control.SetValue(str(array(TW, dtype = '|S8'))+'\n'+str(array(CH, dtype = '|S8')))
                        tout = matchingrate.getProximity(TwicethetaChi,
                                                        np.array(TW) / 2.0,
                                                        np.array(CH),
                                                        angtol=ang_match)

                    # print "calcul residues",tout[2:]
                    # print mymat
                    # print "tout de tout",tout
                    res.append(tout[2:])

                # Display results
                if self.datatype == "gnomon":
                    self.data_fromGnomon = (TW, CH, self.Data_I, self.filename)
                    self.RecBox = RecognitionResultCheckBox(
                        self, -1, "Potential solutions", res, self.data_fromGnomon, emax=emax)
                    self.RecBox = str(self.crystalparampanel.comboElem.GetValue())
                    self.RecBox.TwicethetaChi_solution = self.TwicethetaChi_solution
                    self.RecBox.mat_solution = self.mat_solution
                else:  # default 2theta, chi
                    self.RecBox = RecognitionResultCheckBox(
                        self, -1, "Potential solutions", res, self.data, emax=emax)
                    self.RecBox = str(self.crystalparampanel.comboElem.GetValue())
                    self.RecBox.TwicethetaChi_solution = self.TwicethetaChi_solution
                    self.RecBox.mat_solution = self.mat_solution
                print("result", res)
                self.recognition_possible = False

            elif sol == []:
                print("Sorry! No planes found for this angle within angular tolerance %.2f"% ang_tol)
                print("Try to: increase the angular tolerance or be more accurate in clicking!")
                print("Try to extend the number of possible planes probed in recognition, ask the programmer!")
            # distance recognition -------------------------

            self._replot(evt)

    # ---  --- plot Annotations ------------
    def OnResetAnnotations(self, evt):
        self.drawnAnnotations_exp = {}
        self.drawnAnnotations_theo = {}
        self._replot(evt)

    def onKeyPressed(self, event):
        #        print dir(event)
        #        print event.x, event.y
        #        print event.xdata, event.ydata

        key = event.key
        #         print "key", key
        if key == "escape":
            ret = wx.MessageBox("Are you sure to quit?", "Question", wx.YES_NO | wx.NO_DEFAULT, self)

            if ret == wx.YES:
                self.Close()

        elif key in ("+", "-"):
            angle = float(self.moveccdandxtal.stepanglerot.GetValue())
            if key == "+":
                self.RotateAroundAxis(angle)
            if key == "-":
                self.RotateAroundAxis(-angle)

    def onClick(self, event):
        """ onclick or onPress with mouse
        """
        #        print 'clicked on mouse'
        if event.inaxes:
            #            print("inaxes", event)
            #             print("inaxes x,y", event.x, event.y)
            #             print("inaxes xdata, ydata", event.xdata, event.ydata)
            if event.button == 1:
                self.centerx, self.centery = event.xdata, event.ydata

            # rotation  around self.centerx, self.centery triggered by button
            if self.RotationActivated:
                # axis is already defined
                if self.SelectedRotationAxis is not None:
                    print("Rotation possible around : ", self.SelectedRotationAxis)
                    pass
                #                     self.RotateAroundAxis()
                # axis must be defined
                else:
                    self.SelectedRotationAxis = self.selectrotationaxis(event.xdata, event.ydata)

            elif self.toolbar.mode != "":
                print("You clicked on something, but toolbar is in mode %s."% str(self.toolbar.mode))

            elif self.btn_label_theospot.GetValue():
                self.Annotate_exp(event)

            elif self.btn_label_expspot.GetValue():
                self.Annotate_theo(event)
            #                 self.Annotate(event)

            elif self.toolbar.mode == "":  # dragging laue pattern
                self.press = event.xdata, event.ydata

    def onRelease(self, event):
        if self.press is None:
            return

        if event.button == 1:
            self.centerx, self.centery = self.press

            # define rotation axis from self.centerx, self.centery
            self.SelectedRotationAxis = self.selectrotationaxis(self.centerx, self.centery)
            self._replot(event)

        self.press = None

    def onMotion(self, event):
        if self.press is None:
            return
        if not event.inaxes:
            return

        xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress

        if dx == 0.0 and dy == 0.0:
            return

        # calculate new UBmat
        if self.datatype == "2thetachi":
            twth1, chi1 = self.press
            twth2, chi2 = event.xdata, event.ydata
            axis2theta, axischi = self.centerx, self.centery
        elif self.datatype == "pixels":
            X1, Y1 = self.press
            X2, Y2 = event.xdata, event.ydata

            #             print 'X1,Y1', X1, Y1
            #             print 'X2,Y2', X2, Y2
            twth1, chi1 = self.convertpixels2twotheta(X1, Y1)
            #             print 'twth1, chi1', twth1, chi1
            twth2, chi2 = self.convertpixels2twotheta(X2, Y2)
            #             print 'twth2, chi2', twth2, chi2
            axis2theta, axischi = self.convertpixels2twotheta(self.centerx, self.centery)
        else:
            return

        #         print "twth1, chi1", twth1, chi1
        #         print "twth2, chi2", twth2, chi2

        # left mouse button
        if event.button == 1:
            # drag a spot
            self.SelectedRotationAxis, angle = self.computeRotation(twth1, chi1, twth2, chi2)
        # right mouse button
        else:
            # rotate around a spot
            (self.SelectedRotationAxis,
                angle) = self.computeRotation_aroundaxis(axis2theta, axischi,
                                                        twth1, chi1, twth2, chi2)

        #         print "self.SelectedRotationAxis, angle", self.SelectedRotationAxis, angle
        self.RotateAroundAxis(angle)

        if self.datatype == "2thetachi":
            self.press = twth2, chi2
        elif self.datatype == "pixels":
            self.press = X2, Y2

    def convertpixels2twotheta(self, X, Y):

        tws, chs = F2TC.calc_uflab(np.array([X, X]),
                                    np.array([Y, Y]),
                                    self.CCDParam[:5],
                                    kf_direction=self.kf_direction)
        return tws[0], chs[0]

    def computeRotation(self, twth1, chi1, twth2, chi2):
        """
        compute rotation (axis, angle) from two points in 2theta chi coordinnates

        q = -2sintheta ( -sintheta,  costheta sin chi, costheta cos chi)
        rotation axis : q1unit^q2unit
        cos anglerot = q1unit.q2unit
        """
        q1 = np.array([-np.sin(twth1 / 2.0 * DEG),
                np.cos(twth1 / 2.0 * DEG) * np.sin(chi1 * DEG),
                np.cos(twth1 / 2.0 * DEG) * np.cos(chi1 * DEG)])
        q2 = np.array([-np.sin(twth2 / 2.0 * DEG),
                np.cos(twth2 / 2.0 * DEG) * np.sin(chi2 * DEG),
                np.cos(twth2 / 2.0 * DEG) * np.cos(chi2 * DEG)])

        qaxis = np.cross(q1, q2)
        angle = np.arccos(np.dot(q1, q2)) / DEG

        return qaxis, angle

    def computeRotation_aroundaxis(self, twthaxis, chiaxis, twth1, chi1, twth2, chi2):
        """
        compute rotation angle from two points in 2theta chi coordinnates around axis

        q = -2sintheta ( -sintheta,  costheta sin chi, costheta cos chi)
        rotation axis : q1unit^q2unit
        cos anglerot = q1unit.q2unit
        """
        # from self.centerx, self.centery
        qaxis = self.selectrotationaxis(twthaxis, chiaxis)

        qaxis = np.array(qaxis)

        q1 = qunit(twth1, chi1)
        q2 = qunit(twth2, chi2)

        beta = np.arccos(np.dot(q1, qaxis)) / DEG

        #         print "beta", beta
        #         print "qaxis", qaxis

        # q1 and q2 projection along qaxis and perpendicular to it
        q1_alongqaxis = np.dot(q1, qaxis)
        q1perp = q1 - q1_alongqaxis * qaxis

        q2_alongqaxis = np.dot(q2, qaxis)

        #         print 'q2_alongqaxis', q2_alongqaxis
        #         print 'q2', q2
        q2perp = q2 - (q2_alongqaxis * qaxis)

        # norms
        #         nq1perp = np.sqrt(np.dot(q1perp, q1perp))
        nq2perp = np.sqrt(np.dot(q2perp, q2perp))

        # q2_tilted coplanar with qaxis and q2, and same angle with qaxis than q1tilted
        #         q2_tilted = np.cos(beta * DEG) * qaxis + np.sin(beta * DEG) * q2perp / nq2perp
        #         q1_tilted = q1

        # q2tilted_perp and q1tilted_perp form a plane perpendicular to qaxis
        # angle between q2tilted_perp and q1tilted_perp is the rotation angle around qaxis
        #         q2tilted_perp = q2_tilted - (np.dot(q2_tilted, qaxis) * qaxis)
        q2tilted_perp = np.sin(beta * DEG) * q2perp / nq2perp
        # ie : np.sin(beta * DEG) * q2perp / nq2perp

        q1tilted_perp = q1perp

        # norm of qtilterperp  (must be equal)
        nq1tilted_perp = np.sqrt(np.dot(q1tilted_perp, q1tilted_perp))
        #         nq2tilted_perp = np.sqrt(np.dot(q2tilted_perp, q2tilted_perp))

        if nq1tilted_perp <= 0.0001:
            angle = 0
        else:
            angle = (1 / DEG * np.arcsin(np.dot( qaxis, np.cross(q1tilted_perp / nq1tilted_perp,
                                                    q2tilted_perp / nq1tilted_perp))))

        #         print 'angle', angle
        #         print "nq1tilted_perp", nq1tilted_perp

        return qaxis, angle

    def selectrotationaxis(self, twtheta, chi):
        """
        return 3D vector of rotation axis
        """
        #         print 'self.datatype', self.datatype

        if self.datatype == "gnomon":
            RES = IIM.Fromgnomon_to_2thetachi([np.array([twtheta, twtheta]),
                                                    np.array([chi, chi])], 0)[:2]
            twtheta = RES[0][0]
            chi = RES[1][0]
        #         elif self.datatype == 'pixels':
        #             twthetas, chis = F2TC.calc_uflab(np.array([twtheta, twtheta]),
        #                                          np.array([chi, chi]),
        #                                         self.CCDParam[:5],
        #                                         pixelsize=self.pixelsize,
        #                                         kf_direction=self.kf_direction)
        #             twtheta, chi = twthetas[0], chis[0]

        #         print "twtheta, chi", twtheta, chi
        theta = twtheta / 2.0

        sintheta = np.sin(theta * DEG)
        costheta = np.cos(theta * DEG)

        # q axis
        SelectedRotationAxis = [-sintheta,
                                costheta * np.sin(chi * DEG),
                                costheta * np.cos(chi * DEG)]

        return SelectedRotationAxis

    #         print "self.SelectedRotationAxis", self.SelectedRotationAxis

    def RotateAroundAxis(self, angle):
        #         print "now ready to rotate"

        self.deltamatrix = GT.matRot(self.SelectedRotationAxis, angle)

        self._replot(1)
        self.display_current()

    def drawAnnote_exp(self, axis, x, y, annote):
        """
        Draw the annotation on the plot here it s exp spot index

        in MainCalibrationFrame
        """
        if (x, y) in self.drawnAnnotations_exp:
            markers = self.drawnAnnotations_exp[(x, y)]
            # print markers
            for m in markers:
                m.set_visible(not m.get_visible())
            # self.axis.figure.canvas.draw()
            self.canvas.draw()
        else:
            # t = axis.text(x, y, "(%3.2f, %3.2f) - %s"%(x, y,annote), )  # par defaut
            if self.datatype == "2thetachi":
                t1 = axis.text(x + 1, y + 1, "%d" % (annote[0]), size=8)
                t2 = axis.text(x + 1, y - 1, "%.1f" % (annote[1]), size=8)
            elif self.datatype == "gnomon":
                t1 = axis.text(x + 0.02, y + 0.02, "%d" % (annote[0]), size=8)
                t2 = axis.text(x + 0.02, y - 0.02, "%.1f" % (annote[1]), size=8)
            elif self.datatype == "pixels":
                t1 = axis.text(x + 50, y + 50, "%d" % (annote[0]), size=8)
                t2 = axis.text(x + 50, y - 50, "%.1f" % (annote[1]), size=8)

            if matplotlibversion < "0.99.1":
                m = axis.scatter([x], [y], s=1, marker="d", c="r", zorder=100, faceted=False)
            else:
                m = axis.scatter([x], [y], s=1, marker="d", c="r", zorder=100, edgecolors="None")  # matplotlib 0.99.1.1

            self.drawnAnnotations_exp[(x, y)] = (t1, t2, m)
            # self.axis.figure.canvas.draw()
            self.canvas.draw()

    def drawSpecificAnnote_exp(self, annote):
        annotesToDraw = [(x, y, a) for x, y, a in self._dataANNOTE_exp if a == annote]
        for x, y, a in annotesToDraw:
            self.drawAnnote_exp(self.axes, x, y, a)

    def Annotate_exp(self, event):
        """
        in MainCalibrationFrame
        """
        if self.datatype == "2thetachi":
            xtol = 20
            ytol = 20
            xdata, ydata, annotes = (self.twicetheta,
                                        self.chi,
                                        list(zip(self.Data_index_expspot, self.Data_I)))

        elif self.datatype == "gnomon":
            xtol = 0.05
            ytol = 0.05
            xdata, ydata, annotes = (self.data_gnomonx,
                                    self.data_gnomony,
                                    list(zip(self.Data_index_expspot, self.Data_I)))

        elif self.datatype == "pixels":
            xtol = 100
            ytol = 100
            xdata, ydata, annotes = (self.data_x, self.data_y,
                                     list(zip(self.Data_index_expspot, self.Data_I)))

        self._dataANNOTE_exp = list(zip(xdata, ydata, annotes))

        clickX = event.xdata
        clickY = event.ydata

        print(clickX, clickY)

        annotes = []
        for x, y, a in self._dataANNOTE_exp:
            if (clickX - xtol < x < clickX + xtol) and (clickY - ytol < y < clickY + ytol):
                annotes.append((GT.cartesiandistance(x, clickX, y, clickY), x, y, a))

        if annotes:
            annotes.sort()
            _distance, x, y, annote = annotes[0]
            print("the nearest experimental point is at(%.2f,%.2f)" % (x, y))
            print("with index %d and intensity %.1f" % (annote[0], annote[1]))
            self.drawAnnote_exp(self.axes, x, y, annote)
            for l in self.links_exp:
                l.drawSpecificAnnote_exp(annote)

    def drawAnnote_theo(self, axis, x, y, annote):
        """
        Draw the annotation on the plot here it s exp spot index

        in MainCalibrationFrame
        """
        if (x, y) in self.drawnAnnotations_theo:
            markers = self.drawnAnnotations_theo[(x, y)]
            # print markers
            for m in markers:
                m.set_visible(not m.get_visible())
            # self.axis.figure.canvas.draw()
            self.canvas.draw()
        else:
            # t = axis.text(x, y, "(%3.2f, %3.2f) - %s"%(x, y,annote), )  # par defaut
            if self.datatype == "2thetachi":
                t1 = axis.text(x + 1, y + 1,
                    "#%d hkl=%s\nE=%.3f keV" % (annote[0], str(annote[1]), annote[2]),
                    size=8)
            elif self.datatype == "gnomon":
                t1 = axis.text(x + 0.02, y + 0.02,
                    "#%d hkl=%s\nE=%.3f keV" % (annote[0], str(annote[1]), annote[2]),
                    size=8)
            elif self.datatype == "pixels":
                t1 = axis.text(x + 50, y + 50,
                    "#%d hkl=%s\nE=%.3f keV" % (annote[0], str(annote[1]), annote[2]),
                    size=8)

            if matplotlibversion < "0.99.1":
                m = axis.scatter([x], [y], s=1, marker="d", c="r", zorder=100, faceted=False)
            else:
                m = axis.scatter([x], [y], s=1, marker="d", c="r", zorder=100, edgecolors="None")  # matplotlib 0.99.1.1

            self.drawnAnnotations_theo[(x, y)] = (t1, m)
            # self.axis.figure.canvas.draw()
            self.canvas.draw()

    def drawSpecificAnnote_theo(self, annote):
        annotesToDraw = [(x, y, a) for x, y, a in self._dataANNOTE_theo if a == annote]
        for x, y, a in annotesToDraw:
            self.drawAnnote_theo(self.axes, x, y, a)

    def Annotate_theo(self, event):
        """
        in MainCalibrationFrame
        """
        if self.datatype == "2thetachi":
            xtol = 20
            ytol = 20
            xdata, ydata, annotes = (self.data_theo[0], self.data_theo[1],
                list(zip(np.arange(len(self.data_theo[0])),
                        self.data_theo[2],
                        self.data_theo[-1])))

        elif self.datatype == "gnomon":
            xtol = 0.05
            ytol = 0.05
            xdata, ydata, annotes = (self.sim_gnomonx, self.sim_gnomony,
                list(zip(np.arange(len(self.data_theo[0])),
                        self.data_theo[2],
                        self.data_theo[-1])))

        elif self.datatype == "pixels":
            xtol = 100
            ytol = 100
            xdata, ydata, annotes = (self.data_theo[3], self.data_theo[4],
                list(zip(np.arange(len(self.data_theo[0])),
                        self.data_theo[2],
                        self.data_theo[-1])))

        self._dataANNOTE_theo = list(zip(xdata, ydata, annotes))

        clickX = event.xdata
        clickY = event.ydata

        # print clickX, clickY

        annotes = []
        for x, y, a in self._dataANNOTE_theo:
            if (clickX - xtol < x < clickX + xtol) and (clickY - ytol < y < clickY + ytol):
                annotes.append((GT.cartesiandistance(x, clickX, y, clickY), x, y, a))

        if annotes:
            annotes.sort()
            _distance, x, y, annote = annotes[0]
            print("the nearest theo. point is at (%.2f,%.2f)" % (x, y))
            print("with index %d and Miller indices %s " % (annote[0], str(annote[1])))
            print("with Energy (and multiples) (keV):")
            print(givesharmonics(annote[2], self.emin, self.emax))
            self.drawAnnote_theo(self.axes, x, y, annote)
            for l in self.links_theo:
                l.drawSpecificAnnote_theo(annote)


def qunit(twth, chi):
    th = 0.5 * twth * DEG
    chi = chi * DEG
    sinth = np.sin(th)
    costh = np.cos(th)
    sinchi = np.sin(chi)
    coschi = np.cos(chi)

    return np.array([-sinth, costh * sinchi, costh * coschi])


def givesharmonics(E, Emin, Emax):

    multiples_E = []
    n = 1
    Eh = E
    while Eh <= Emax:
        multiples_E.append(Eh)
        n += 1
        Eh = E * n
    return multiples_E


if __name__ == "__main__":

    initialParameter = {}
    initialParameter["CCDParam"] = [71, 1039.42, 1095, 0.0085, -0.981]
    initialParameter["detectordiameter"] = 165.0
    initialParameter["CCDLabel"] = "MARCCD165"
    initialParameter["filename"] = "Ge0001.dat"
    initialParameter["dirname"] = "/home/micha/LaueToolsPy3/LaueTools/Examples/Ge"
    initialParameter["dict_Materials"]=DictLT.dict_Materials

    filepathname = os.path.join(initialParameter["dirname"], initialParameter["filename"])
    #    initialParameter['imagefilename'] = 'SS_0171.mccd'
    #    initialParameter['dirname'] = '/home/micha/lauetools/trunk'

    CalibGUIApp = wx.App()
    CalibGUIFrame = MainCalibrationFrame(None,
                                            -1,
                                            "Detector Calibration Board",
                                            initialParameter,
                                            file_peaks=filepathname,
                                            starting_param=initialParameter["CCDParam"],
                                            pixelsize=165.0 / 2048,
                                            datatype="2thetachi",
                                            dim=(2048, 2048),
                                            fliprot="no",
                                            data_added=None)

    CalibGUIFrame.Show()

    CalibGUIApp.MainLoop()
