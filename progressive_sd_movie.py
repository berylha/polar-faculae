################################################################################
# IMPORT STATEMENTS

import warnings
warnings.simplefilter('ignore', Warning)

import os
import sys
import numpy as np
from sunpy.map import Map
import astropy.units as u
import matplotlib.pyplot as plt
import imageio

################################################################################
# CHANGE THESE LINES

# Date in format 'YYYYMMDD'
date = '20130901'

# Folder to find intensity continuum data
folder_ic = 'path/to/intensity/continuum/data/'
# Folder to find magnetogram data
folder_M = 'path/to/magnetogram/data/'

################################################################################

# Northern Hemisphere in fall, Southern in spring
N = True if int(date[4:6])>6 else False

# define limits to crop image
x0 = 1350
x1 = 2745
y0 = 65 if N else 3530
y1 = 565 if N else 4030

################################################################################

def bytscl(arr, top, mn, mx):
    # Scales values between mn<x<mx to 0<x<top
    scarr = np.zeros(arr.shape)
    zz = (arr < mn)
    aa = (arr > mx)
    scarr[zz] = 0
    scarr[aa] = top
    scarr[(~aa)*(~zz)] = top * (arr[(~aa)*(~zz)] - mn) / (mx - mn)
    return scarr

################################################################################

# import colormap
cmap = plt.get_cmap('hmimag')

# access files from folders
filenames_ic = sorted([f for f in os.listdir(folder_ic) if f.endswith('.fits')])
filenames_M = sorted([f for f in os.listdir(folder_M) if f.endswith('.fits')])
if len(filenames_ic) != len(filenames_M):
     sys.exit(f'Number of files not equal: {len(filenames_ic)} intensity\
            continuum files and {len(filenames_M)} magnetogram files.')
os.mkdir(date)

# start with first file
n = 1
map_ic = Map(folder_ic + filenames_ic[0])
# initialize mean (xn), standard deviation (sn), full movie (mov) arrays
xn = np.fliplr(map_ic.data[y0:y1, x0:x1])
xn[np.isnan(xn)] = 0
sn = np.zeros((y1-y0, x1-x0))
mov = np.zeros((len(filenames_ic)-1, y1-y0, x1-x0, 4), dtype='uint8')

# loop through rest of images
for i, f_ic in enumerate(filenames_ic[1:]):
    n+=1
    if i%10 == 0:
        print(i)
    # open files, crop, and set nan values to 0
    map_ic = Map(folder_ic + f_ic)
    im_ic = np.fliplr(map_ic.data[y0:y1, x0:x1])
    im_ic[np.isnan(im_ic)] = 0
    map_M = Map(folder_M + filenames_M[i])
    im_M = np.fliplr(map_M.data[y0:y1, x0:x1])
    im_M[np.isnan(im_M)] = 0
    # update mean and standard deviation
    if i==0:
        sn = np.std([im_ic, xn], axis=0)
        xn = np.mean([im_ic, xn], axis=0)
    else:
        xn = ((n-1) * xn + im_ic) / n
        sn = np.sqrt(1/(n-1) * ((n-2) * sn**2 + n/(n-1) * (xn - im_ic)**2))
    # scale sn to [0, 255]
    sc_sd = bytscl(sn, 255, 0, 2500)
    # scale im_M to [0.0, 0.1] and apply cmap
    scz_M = bytscl(im_M, 1.0, -1500, 1500)
    cm_M = cmap(scz_M, bytes=True)
    # format sn from N*M to N*M*4 (where col4 is 255)
    cm_sd = np.dstack((sc_sd, sc_sd, sc_sd, np.ones(sc_sd.shape)*255))
    # overlay
    im_to_save = np.array(0.5*cm_M + 0.5*cm_sd, dtype='uint8')
    imageio.imwrite(f'{date}/{i}.png', im_to_save, format='png')
    mov[i] = im_to_save

# save mov using imageio.mimwrite
imageio.mimwrite(f'{date}.mp4', mov, format='mp4', fps=10)
