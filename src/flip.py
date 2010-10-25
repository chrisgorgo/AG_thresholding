'''
Created on 23 Oct 2010

@author: filo
'''
import nipype.externals.pynifti as nb
import numpy as np

image_filename2 = "/media/sdb2/laura_study/DATA_4_chis/func/AG_1247/LH_clench/fmask.nii"

nii2 = nb.load(image_filename2)

affine = nii2.get_affine()
print affine
flip_matrix = np.eye(4)
#flip_matrix[0,0] = -1
affine = np.dot(flip_matrix,affine)

data = nii2.get_data()

nb.save(nb.Nifti1Image(data, affine, nii2.get_header()), "new_mask.nii")