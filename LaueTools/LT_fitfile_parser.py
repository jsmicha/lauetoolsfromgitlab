#!/usr/bin/python3
#-*- coding: utf-8 -*-
# LaueTools fit files parser
# rev. : 2016-08-03
# Sam Tardif (samuel.tardif@gmail.com)

import numpy as np

class Peak:
    def __init__(self,p, peak_attributes):
        for iii in np.arange(len(peak_attributes)):
            setattr(self,peak_attributes[iii],float(p[iii]))


        # if len(p) == 18:
        #     self.spot_index    = float(p[ 0])
        #     self.Intensity     = float(p[ 1])
        #     self.h             = int(float(p[ 2]))
        #     self.k             = int(float(p[ 3]))
        #     self.l             = int(float(p[ 4]))
        #     self.pixDev        = float(p[ 5])
        #     self.energy        = float(p[ 6])
        #     self.Xexp          = float(p[ 7])
        #     self.Yexp          = float(p[ 8])
        #     self.twotheta_exp  = float(p[ 9])
        #     self.chi_exp       = float(p[10])
        #     self.Xtheo         = float(p[11])
        #     self.Ytheo         = float(p[12])
        #     self.twotheta_theo = float(p[13])
        #     self.chi_theo      = float(p[14])
        #     self.Qx            = float(p[15])
        #     self.Qy            = float(p[16])
        #     self.Qz            = float(p[17])
        # elif len(p) == 12:
        #     self.spot_index    = float(p[ 0])
        #     self.Intensity     = float(p[ 1])
        #     self.h             = int(float(p[ 2]))
        #     self.k             = int(float(p[ 3]))
        #     self.l             = int(float(p[ 4]))
        #     self.twotheta_exp  = float(p[ 5])
        #     self.chi_exp       = float(p[ 6])
        #     self.Xexp          = float(p[ 7])
        #     self.Yexp          = float(p[ 8])
        #     self.energy        = float(p[ 9])
        #     self.GrainIndex    = float(p[10])
        #     self.pixDev        = float(p[11]) 


class LT_fitfile:
    """
    Parse the .fit file in a LT_fitfile object
    """

    # dictionary definitions for handling the LaueTools .fit files lines
    def __param__(self):
        return  { '#UB matrix in q= (UB) B0 G* ' : self.__UB__,
                  '#B0 matrix in q= UB (B0) G*' : self.__B0__,
                  '#UBB0 matrix in q= (UB B0) G* i.e. recip. basis vectors are columns in LT frame: astar = UBB0[0,:], bstar = UBB0[1,:], cstar = UBB0[2,:]. (abcstar as lines on xyzlab1, xlab1 = ui, ui = unit vector along incident beam)' : self.__UBB0__,
                  '#UBB0 matrix in q= (UB B0) G* , abcstar as lines on xyzlab1, xlab1 = ui, ui = unit vector along incident beam : astar = UBB0[0,:], bstar = UBB0[1,:], cstar = UBB0[2,:]' : self.__UBB0__,
                  '#deviatoric strain in crystal frame (10-3 unit)' : self.__devCrystal__,
                  '#deviatoric strain in direct crystal frame (10-3 unit)' : self.__devCrystal__,
                  '#deviatoric strain in sample2 frame (10-3 unit)' : self.__devSample__,
                  '#DetectorParameters' : self.__DetectorParameters__,
                  '#pixelsize' : self.__PixelSize__,
                  '#Frame dimensions' : self.__FrameDimension__,
                  '#CCDLabel' : self.__CCDLabel__,
                  '#Element' : self.__Element__,
                  '#grainIndex' : self.__GrainIndex__,
                  '#spot_index intensity h k l 2theta Chi Xexp Yexp Energy GrainIndex PixDev' : self.__Peaks__,
                  '##spot_index intensity h k l 2theta Chi Xexp Yexp Energy GrainIndex PixDev' : self.__Peaks__,
                  '#spot_index Intensity h k l pixDev energy(keV) Xexp Yexp 2theta_exp chi_exp Xtheo Ytheo 2theta_theo chi_theo Qx Qy Qz' : self.__Peaks__,
                  '##spot_index Intensity h k l pixDev energy(keV) Xexp Yexp 2theta_exp chi_exp Xtheo Ytheo 2theta_theo chi_theo Qx Qy Qz' : self.__Peaks__,
                  '# Number of indexed spots' : self.__NumberIndexedSpots__,
                  '# Mean Deviation(pixel)' : self.__MeanDev__,
                  '#Strain and Orientation Refinement from experimental file' : self.__ExperimentalFile__,
                  '#File created at' : self.__FileCreationDate__,
                  '#Number of indexed spots' : self.__NumberIndexedSpots__,
                  '#Mean Deviation(pixel)' : self.__MeanDev__,
                  '##spot_index Intensity h k l pixDev energy(keV) Xexp Yexp 2theta_exp chi_exp Xtheo Ytheo 2theta_theo chi_theo Qx Qy Qz' : self.__Peaks__,
                  '#(B-I)*1000 ' : self.__BminusItimes1000__,
                  '#HKL coord. of lab and sample frame axes :' : self.__HKLcoords__,
                  '#Euler angles phi theta psi (deg)' : self.__Euler__,
                  '#new lattice parameters' : self.__NewLatticeParameters__,
                  '#Umatrix in q_lab= (UB) B0 G* ' : self.__U__,
                  '#Bmatrix in q_lab= (UB) B0 G* ' : self.__B__,
                  '#' : self.__EmptyLine__,
                  }


    def __NotImplementYet__(self, f, l):
        print('Reading {:s} is not implemented yet, following KeyErrors may be expected'.format(l))


    def __EmptyLine__(self, f, l):
        pass

    def __HKLcoords__(self, f, l):
        print('Reading {:s} is not implemented yet'.format(l))
        l = f.readline()
        l = f.readline()
        l = f.readline()
        l = f.readline()
        l = f.readline()
        l = f.readline()


    def __ExperimentalFile__(self, f, l):
        self.ExperimentalFile = l


    def __FileCreationDate__(self, f, l):  
        self.FileCreationDate = l


    def __Euler__(self, f, l):  
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        self.Euler1, self.Euler2, self.Euler3 = float(l[0]),float(l[1]),float(l[2])


    def __NewLatticeParameters__(self, f, l):  
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        self.new_a, self.new_b, self.new_c, self.new_alpha = float(l[0]),float(l[1]),float(l[2]),float(l[3])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        self.new_beta, self.new_gamma = float(l[0]),float(l[1])


    def __UB__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ub11,ub12,ub13 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ub21,ub22,ub23 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ub31,ub32,ub33 = float(l[0]),float(l[1]),float(l[2])
        self.UB = np.array([[ub11,ub12,ub13],[ub21,ub22,ub23],[ub31,ub32,ub33]])


    def __U__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        u11,u12,u13 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        u21,u22,u23 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        u31,u32,u33 = float(l[0]),float(l[1]),float(l[2])
        self.UB = np.array([[u11,u12,u13],[u21,u22,u23],[u31,u32,u33]])


    def __B__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        b11,b12,b13 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        b21,b22,b23 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        b31,b32,b33 = float(l[0]),float(l[1]),float(l[2])
        self.B = np.array([[b11,b12,b13],[b21,b22,b23],[b31,b32,b33]])


    def __B0__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        b011,b012,b013 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        b021,b022,b023 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        b031,b032,b033 = float(l[0]),float(l[1]),float(l[2])
        self.B0 = np.array([[b011,b012,b013],[b021,b022,b023],[b031,b032,b033]])


    def __UBB0__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ubb011,ubb012,ubb013 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ubb021,ubb022,ubb023 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ubb031,ubb032,ubb033 = float(l[0]),float(l[1]),float(l[2])
        self.UBB0 = np.array([[ubb011,ubb012,ubb013],[ubb021,ubb022,ubb023],[ubb031,ubb032,ubb033]])


    def __BminusItimes1000__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        BmIt1000_11,BmIt1000_12,BmIt1000_13 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()        
        BmIt1000_21,BmIt1000_22,BmIt1000_23 = float(l[0]),float(l[1]),float(l[2])
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()        
        BmIt1000_31,BmIt1000_32,BmIt1000_33 = float(l[0]),float(l[1]),float(l[2])
        self.BmIt1000 = np.array([[BmIt1000_11,BmIt1000_12,BmIt1000_13],
                                  [BmIt1000_21,BmIt1000_22,BmIt1000_23],
                                  [BmIt1000_31,BmIt1000_32,BmIt1000_33]])


    def __devCrystal__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ep11,ep12,ep13 = float(l[0])*1E-3,float(l[1])*1E-3,float(l[2])*1E-3
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ep22,ep23 = float(l[1])*1E-3,float(l[2])*1E-3
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ep33 = float(l[2])*1E-3
        self.deviatoric = np.array([[ep11,ep12,ep13],[ep12,ep22,ep23],[ep13,ep23,ep33]])


    def __devSample__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ep_sample11,ep_sample12,ep_sample13 = float(l[0])*1E-3,float(l[1])*1E-3,float(l[2])*1E-3
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ep_sample22,ep_sample23 = float(l[1])*1E-3,float(l[2])*1E-3
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').split()
        ep_sample33 = float(l[2])*1E-3
        self.dev_sample = np.array([[ep_sample11,ep_sample12,ep_sample13],[ep_sample12,ep_sample22,ep_sample23],[ep_sample13,ep_sample23,ep_sample33]])


    def __DetectorParameters__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').replace(' ','').split(',')
        self.dd   = float(l[0])
        self.xcen = float(l[1])
        self.ycen = float(l[2])
        self.xbet = float(l[3])
        self.xgam = float(l[4])
        self.DetectorParameters = [self.dd,self.xcen,self.ycen,self.xbet,self.xgam]


    def __PixelSize__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').replace(' ','').split(',')
        self.PixelSize = float(l[0])


    def __FrameDimension__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('(','').replace(')','').replace(',',' ').replace('\n','').split()
        self.FrameDimension = [float(l[0]),float(l[1])]


    def __CCDLabel__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').replace(' ','').split(',')
        self.CCDLabel = l[0]


    def __Element__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').replace(' ','').split(',')
        self.Element = l[0]


    def __GrainIndex__(self, f, l):
        l = f.readline().replace('#','').replace('[','').replace(']','').replace('\n','').replace(' ','').split(',')
        self.GrainIndex = l[0]


    def __Peaks__(self, f, l):
        self.peak_attributes = l.replace('#','').split()
        self.peak={}
        for _ in np.arange(self.NumberOfIndexedSpots):
          l = f.readline().split()
          self.peak['{:d} {:d} {:d}'.format(int(float(l[2])),int(float(l[3])),int(float(l[4])))] = Peak(l,self.peak_attributes)


    def __NumberIndexedSpots__(self, f, l):
        self.NumberOfIndexedSpots = int(l.split(' ')[-1])


    def __MeanDev__(self, f, l):
        self.MeanDevPixel = float(l.split(' ')[-1])  


    def __init__(self,filename,verbose=False):
        try:
            with open(filename,'rU') as f:
                self.filename = filename

                l = f.readline()
                self.corfile = l.split(' ')[-1]

                l = f.readline()
                self.timestamp, self.software = l.lstrip('# File created at ').split(' with ')

                l = f.readline().replace('\n','')
                while l != '\n' and l != '':
                    try:  # first try to use the full line as the key 
                        self.__param__()[l](f,l)
                        if verbose: print('read ', l)
                        l = f.readline().replace('\n','')

                    except KeyError: # if it does not work, split it at ':' as it it may be a single line (key + value)
                        try:
                            #print l.split(':')[0]
                            self.__param__()[l.split(':')[0]](f,l)
                            l = f.readline().replace('\n','')

                        except KeyError: # if it still does not find how to read it, give up 
                            print("could not read line {}".format(l))
                            l = f.readline().replace('\n','')



                # some extra calculations to get the direct and reciprocal lattice basis vector 
                # NOTE: the scale of the lattice basis vector is UNKNOWN !!! 
                #       they are given here with a arbitrary scale factor
                if not hasattr(self, 'UBB0'):
                    self.UBB0 = np.dot(self.UB,self.B0)
                    
                try:
                    self.astar_prime = self.UBB0[:,0]
                    self.bstar_prime = self.UBB0[:,1]
                    self.cstar_prime = self.UBB0[:,2]
                    
                    self.a_prime = np.cross(self.bstar_prime,self.cstar_prime)/np.dot(self.astar_prime,np.cross(self.bstar_prime,self.cstar_prime))
                    self.b_prime = np.cross(self.cstar_prime,self.astar_prime)/np.dot(self.bstar_prime,np.cross(self.cstar_prime,self.astar_prime))
                    self.c_prime = np.cross(self.astar_prime,self.bstar_prime)/np.dot(self.cstar_prime,np.cross(self.astar_prime,self.bstar_prime))
                    
                    self.boa = np.linalg.linalg.norm(self.b_prime)/np.linalg.linalg.norm(self.a_prime)
                    self.coa = np.linalg.linalg.norm(self.c_prime)/np.linalg.linalg.norm(self.a_prime)
                    
                    self.alpha = np.arccos(np.dot(self.b_prime,self.c_prime)/np.linalg.linalg.norm(self.b_prime)/np.linalg.linalg.norm(self.c_prime))*180./np.pi
                    self.beta  = np.arccos(np.dot(self.c_prime,self.a_prime)/np.linalg.linalg.norm(self.c_prime)/np.linalg.linalg.norm(self.a_prime))*180./np.pi
                    self.gamma = np.arccos(np.dot(self.a_prime,self.b_prime)/np.linalg.linalg.norm(self.a_prime)/np.linalg.linalg.norm(self.b_prime))*180./np.pi
                    
                except ValueError:
                  print("could not compute the reciprocal space from the UBB0")
               
        except IOError:
            print("file {} not found!".format(filename))
            pass



