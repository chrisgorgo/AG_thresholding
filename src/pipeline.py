import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.freesurfer as fs 
import nodes

data_dir = os.path.abspath('/media/sdb2/laura_study/DATA_4_chis/')

task_dict = {
#             'AG_1240':17.5, 'AG_1241':13.1,'AG_1247':10,'AG_1251':6,'AG_1255':3,'AG_1256':10,
#                'AG_1257':9,'AG_1260':9, 'AG_1261':5.7,'AG_1262':10, 
                'AG_1264':7}

info = dict(t_map=[['subject_id', 'spmT_0003.img']],
            spm_mat_file=[['subject_id', 'SPM.mat']],
            mask=[['subject_id', 'mask.img']],
            expert_thresholded_map=[['subject_id', 'threshold']],
            struct=[['subject_id']])

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")
infosource.iterables = ('subject_id', task_dict.keys())

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'threshold'],
                                               outfields=['t_map', 'spm_mat_file', 'mask', 'expert_thresholded_map', 'struct']),
                     name = 'datasource')
datasource.inputs.base_directory = data_dir
datasource.inputs.template = 'func/%s/*/%s'
datasource.inputs.field_template = dict(expert_thresholded_map='func/%s/*/AG*%s.img',
                                        struct='SPGRs/%s/*.img')
datasource.inputs.template_args = info




map_analyze2nii = pe.Node(interface = spm.Analyze2nii(), name="map_analyze2nii")

mask_analyze2nii = pe.Node(interface = spm.Analyze2nii(), name="mask_analyze2nii")

map_flip = pe.Node(interface = fs.MRIConvert(), name="map_flip")
map_flip.inputs.in_i_dir = (-1, 0, 0)
map_flip.inputs.out_type = 'nii'

mask_flip = pe.Node(interface = fs.MRIConvert(), name="mask_flip")
mask_flip.inputs.in_i_dir = (-1, 0, 0)
map_flip.inputs.out_type = 'nii'

expert_th_analyze2nii = pe.Node(interface = spm.Analyze2nii(), name="expert_th_analyze2nii")

expert_flip = pe.Node(interface = fs.MRIConvert(), name="expert_flip")
expert_flip.inputs.in_i_dir = (-1, 0, 0)
map_flip.inputs.out_type = 'nii'

struct_analyze2nii = pe.Node(interface = spm.Analyze2nii(), name="struct_analyze2nii")

threshold = pe.Node(interface = spm.Threshold(), name="threshold_topo_fdr_with_fwe")
threshold.inputs.contrast_index = 3
threshold.iterables = ('extent_threshold', [0,   10])

thresholdGGMM = pe.Node(interface=nodes.ThresholdGGMM(no_deactivation_class=True),name="ThresholdGGMM")

threshold_l2 = pe.Node(interface = spm.Threshold(), name="threshold_topo_fdr_with_ggmm")
threshold_l2.inputs.contrast_index = 3
threshold_l2.inputs.use_fwe_correction = False
threshold_l2.iterables = ('extent_threshold', [0,   10])

reslice = pe.Node(interface=spm.Coregister(), name="reslice")
reslice.inputs.jobtype = 'write'
reslice.inputs.write_interp = 0


def get_th(subjec_id):
    num_th = task_dict[subjec_id]
    return str(num_th).replace('.','d')

compare_pipeline = pe.Workflow(name="compare_pipeline")
compare_pipeline.base_dir = os.path.abspath("workdir")
compare_pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id'),
                                                    (('subject_id', get_th), 'threshold')]),
                          
                          (datasource, map_analyze2nii, [('t_map', 'analyze_file')]),
                          (map_analyze2nii, map_flip, [('nifti_file', 'in_file')]),
                          
                          (datasource, mask_analyze2nii, [('mask', 'analyze_file')]),
                          (mask_analyze2nii, mask_flip, [('nifti_file', 'in_file')]),
                          
                          (datasource, expert_th_analyze2nii, [('expert_thresholded_map', 'analyze_file')]),
                          (expert_th_analyze2nii, expert_flip, [('nifti_file', 'in_file')]),
                          
                          (datasource, struct_analyze2nii, [('struct', 'analyze_file')]),
                          
                          (datasource, threshold,[('spm_mat_file','spm_mat_file'),
#                                                  ('t_map','stat_image')
]),
                          (map_flip, threshold,[('out_file', 'stat_image')]),
                          
                          (datasource, thresholdGGMM,[('t_map', 'stat_image'),
#                                                           ('mask', 'mask_file')
]),
                          (mask_flip, thresholdGGMM, [('out_file', 'mask_file')]),
                          
                          (datasource, threshold_l2,[('spm_mat_file','spm_mat_file'),
#                                                     ('t_map','stat_image')
]),
                          (map_flip, threshold_l2,[('out_file', 'stat_image')]),
                          (thresholdGGMM, threshold_l2,[('threshold','height_threshold')]),
                          
                          (threshold_l2, reslice, [('thresholded_map', 'source')]),
                          (struct_analyze2nii, reslice, [('nifti_file', 'target')])                        
                          ])
compare_pipeline.run()