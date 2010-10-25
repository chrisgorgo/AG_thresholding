'''
Created on 22 Oct 2010

@author: filo
'''
import nipype.externals.pynifti as nb
import numpy as np
from scipy.ndimage.morphology import binary_erosion
from scipy.spatial.distance import cdist, euclidean

image_filename1 = '/media/sdb2/laura_study/workdir/compare_pipeline/_subject_id_AG_1247/reslice_tumour/rtumour.nii'
#image_filename2 = '/media/sdb2/laura_study/workdir/compare_pipeline/_subject_id_AG_1247/expert_flip/rAG_1247_LHclench_t10_out.nii'
image_filename2 = "/media/sdb2/laura_study/workdir/compare_pipeline/_subject_id_AG_1247/expert_fix_affine/fAG_1247_LHclench_t10_transformed.nii"

def findBorder(data):
    eroded = binary_erosion(data)
    border = np.logical_and(data, np.logical_not(eroded))
    return border

def getCoordinates(data, affine):
    if len(data.shape) == 4:
        data = data[:,:,:,0]
    indices = np.vstack(np.nonzero(data))
    indices = np.vstack((indices, np.ones(indices.shape[1])))
    coordinates = np.dot(affine,indices)
    return coordinates[:3,:]

nii1 = nb.load(image_filename1)
origdata1 = nii1.get_data().astype(np.bool)
border1 = findBorder(origdata1)
print np.sum(border1)

nb.save(nb.Nifti1Image(border1, nii1.get_affine(), nii1.get_header()), "border1.nii")

nii2 = nb.load(image_filename2)
origdata2 = nii2.get_data().astype(np.bool)
border2 = findBorder(origdata2)
print np.sum(border2)
nb.save(nb.Nifti1Image(border2, nii2.get_affine(), nii2.get_header()), "border2.nii")

set1_coordinates = getCoordinates(border1, nii1.get_affine())
print set1_coordinates.T.shape

set2_coordinates = getCoordinates(border2, nii2.get_affine())
print set2_coordinates.T.shape

dist_matrix = cdist(set1_coordinates.T, set2_coordinates.T)
(point1, point2) = np.unravel_index(np.argmin(dist_matrix), dist_matrix.shape)
print set1_coordinates.T[point1,:]
print set2_coordinates.T[point2,:]
print euclidean(set1_coordinates.T[point1,:], set2_coordinates.T[point2,:])
print np.max(dist_matrix)


#count = 0
#for point in set1_indices:
#    for point in set1_indices:
#        count+=1
#        print count