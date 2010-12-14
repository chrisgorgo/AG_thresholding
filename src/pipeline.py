import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm          # spm
import nipype.algorithms.misc as misc
import nodes
from nipype.interfaces.dcm2nii import Dcm2nii
from nipype.interfaces import fsl

data_dir = os.path.abspath('/media/sdb2/laura_study/DATA_4_chis/')

task_dict = {'AG_1240':17.5 #}
             , 'AG_1241':13.1,'AG_1247':10,'AG_1251':6,'AG_1255':10.3,'AG_1256':10,
                'AG_1257':9,'AG_1260':9, 'AG_1261':5.7,'AG_1262':10, 
                'AG_1264':7}

info = dict(t_map=[['subject_id', 'spmT_0003.img']],
            spm_mat_file=[['subject_id', 'SPM.mat']],
            mask=[['subject_id', 'mask.img']],
            expert_thresholded_map=[['subject_id', 'threshold']],
            struct=[['subject_id']],
            tumour_mask=[['subject_id']] )

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")
infosource.iterables = ('subject_id', task_dict.keys())

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'threshold'],
                                               outfields=info.keys()),
                     name = 'datasource')
datasource.inputs.base_directory = data_dir
datasource.inputs.template = 'func/%s/*/%s'
datasource.inputs.field_template = dict(expert_thresholded_map='func/%s/*/AG*%s.img',
                                        struct='SPGRs/%s/*.img',
                                        tumour_mask='SPGRs/%s/tumour.nii')
datasource.inputs.template_args = info

struct_analyze2nii = pe.Node(interface = spm.Analyze2nii(), name="struct_analyze2nii")

#expert_distance = pe.Node(interface=misc.Distance(), name="expert_distance")
#expert_distance.iterables = ('method', ["eucl_min", "eucl_cog", "eucl_mean", "eucl_wmean"])
#
#expert_fdr_ggmm_disssimilarity = pe.Node(interface=misc.disssimilarity(), name="expert_fdr_ggmm_disssimilarity")


analyze2nii = pe.Node(interface = Dcm2nii(), name="analyze2nii")
fix_affine = pe.Node(interface=misc.ModifyAffine(), name="fix_affine")
#reslice = pe.Node(interface=spm.Coregister(jobtype="write"), name="reslice")

convert_pipeline = pe.Workflow(name="analyze2nifti")
convert_pipeline.connect([(analyze2nii, fix_affine, [('converted_files', 'volumes')]),
#                          (fix_affine, reslice, [('transformed_volumes', 'source')])
                          ])

convert_manual = convert_pipeline.clone("convert_manual")
convert_mask = convert_pipeline.clone("convert_mask")
convert_t_map = convert_pipeline.clone("convert_t_map")

threshold_stat = pe.Node(interface=spm.model.ThresholdStatistics(), name="threshold_stat")
threshold_stat.inputs.contrast_index = 3
threshold_stat.inputs.extent_threshold = 10

def get_th(subjec_id):
    num_th = task_dict[subjec_id]
    return str(num_th).replace('.','d')

def get_th_f(subjec_id):
    return task_dict[subjec_id]

compare_pipeline = pe.Workflow(name="compare_pipeline")
compare_pipeline.base_dir = os.path.abspath("workdir")
compare_pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id'),
                                                    (('subject_id', get_th), 'threshold')]),
                                                                              
                          (datasource, struct_analyze2nii, [('struct', 'analyze_file')]),
                          
                          (datasource, convert_manual, [('expert_thresholded_map', 'analyze2nii.source_names')]),
#                          (struct_analyze2nii, convert_manual, [('nifti_file', 'reslice.target')]),
                          
                          (datasource, convert_mask, [('mask', 'analyze2nii.source_names')]),
 #                         (struct_analyze2nii, convert_mask, [('nifti_file', 'reslice.target')]),
                          
                          (datasource, convert_t_map, [('t_map', 'analyze2nii.source_names')]),
 #                         (struct_analyze2nii, convert_t_map, [('nifti_file', 'reslice.target')]),
 
                          (infosource, threshold_stat, [(('subject_id', get_th_f), 'height_threshold')]),
                          (datasource, threshold_stat,[('spm_mat_file','spm_mat_file')]),
                          (convert_t_map, threshold_stat, [('fix_affine.transformed_volumes','stat_image')]),
                          
#                          
#                          
#                          
#                          (convert_t_map, thresholdGGMM,[('fix_affine.transformed_volumes', 'stat_image')]),
#                          (convert_mask, thresholdGGMM,[('fix_affine.transformed_volumes', 'mask_file')]),
#                          
#                          (datasource, threshold_l2,[('spm_mat_file','spm_mat_file')]),
#                          (convert_t_map, threshold_l2, [('fix_affine.transformed_volumes','stat_image')]),
#                          (thresholdGGMM, threshold_l2,[('threshold','height_threshold')]),
#                          
#                          (datasource, expert_distance, [('tumour_mask','volume1')]),
#                          (convert_manual, expert_distance, [('fix_affine.transformed_volumes','volume2')]),
#                          
#                          (convert_manual, expert_fdr_ggmm_disssimilarity, [('fix_affine.transformed_volumes', 'volume1')]),
#                          (threshold_l2, expert_fdr_ggmm_disssimilarity,[('thresholded_map','volume2')])               
                          ])

expert_dissimilarity = pe.Node(interface=misc.Dissimilarity(), name="expert_dissimilarity")
tumour_overlap = pe.Node(interface=misc.Dissimilarity(), name="tumour_overlap")

tumour_distance = pe.Node(interface=misc.Distance(), name="tumour_distance")
tumour_distance.iterables = ('method', ["eucl_min", "eucl_cog", "eucl_mean", "eucl_wmean"])

reslice = pe.Node(interface=spm.Coregister(jobtype="write"), name="reslice")

inputnode = pe.Node(interface=util.IdentityInterface(fields=['map_to_evaluate',
                                                             'expert_map',
                                                                 'tumour_mask']), name="inputnode")
evaluation_worflow = pe.Workflow(name="evaluation_worflow")

evaluation_worflow.connect([(inputnode, expert_dissimilarity,[('expert_map','volume1')]),
                            (inputnode, expert_dissimilarity,[('map_to_evaluate','volume2')]),
                                                 
                              (inputnode, tumour_distance, [('tumour_mask','volume1')]),
                              (inputnode, tumour_distance, [('map_to_evaluate','volume2')]),
                              
                              (inputnode, reslice, [('tumour_mask','target')]),
                              (inputnode, reslice, [('map_to_evaluate','source')]),
                              (inputnode, tumour_overlap, [('tumour_mask', 'volume1')]),
                              (reslice, tumour_overlap, [('coregistered_source','volume2')])
                              ])



topo_fdr_with_fwe = pe.Node(interface = spm.Threshold(), name="topo_fdr_with_fwe")
topo_fdr_with_fwe.inputs.contrast_index = 3
topo_fdr_with_fwe.iterables = ('extent_threshold', [0,   10])

topo_fdr_with_fwe_ev = evaluation_worflow.clone(name="topo_fdr_with_fwe_ev")

compare_pipeline.connect([(datasource, topo_fdr_with_fwe,[('spm_mat_file','spm_mat_file')]),
                          (convert_t_map, topo_fdr_with_fwe, [('fix_affine.transformed_volumes','stat_image')]),
                                                
                          (topo_fdr_with_fwe, topo_fdr_with_fwe_ev, [('thresholded_map','inputnode.map_to_evaluate')]),            
                          (convert_manual, topo_fdr_with_fwe_ev, [('fix_affine.transformed_volumes', 'inputnode.expert_map')]),                 
                          (datasource, topo_fdr_with_fwe_ev, [('tumour_mask','inputnode.tumour_mask')])
                          ])

topo_fdr_with_fwe_ui_0_0001 = pe.Node(interface = spm.Threshold(), name="topo_fdr_with_fwe_ui_0_0001")
topo_fdr_with_fwe_ui_0_0001.inputs.contrast_index = 3
topo_fdr_with_fwe_ui_0_0001.inputs.extent_threshold = 10
topo_fdr_with_fwe_ui_0_0001.inputs.height_threshold = 0.0001

topo_fdr_with_fwe_ui_0_0001_ev = evaluation_worflow.clone(name="topo_fdr_with_fwe_ui_0_0001_ev")

compare_pipeline.connect([(datasource, topo_fdr_with_fwe_ui_0_0001,[('spm_mat_file','spm_mat_file')]),
                          (convert_t_map, topo_fdr_with_fwe_ui_0_0001, [('fix_affine.transformed_volumes','stat_image')]),
                                                
                          (topo_fdr_with_fwe_ui_0_0001, topo_fdr_with_fwe_ui_0_0001_ev, [('thresholded_map','inputnode.map_to_evaluate')]),            
                          (convert_manual, topo_fdr_with_fwe_ui_0_0001_ev, [('fix_affine.transformed_volumes', 'inputnode.expert_map')]),                 
                          (datasource, topo_fdr_with_fwe_ui_0_0001_ev, [('tumour_mask','inputnode.tumour_mask')])
                          ])

topo_fdr_with_fwe_ui_5uncorr = pe.Node(interface = spm.Threshold(), name="topo_fdr_with_fwe_ui_5uncorr")
topo_fdr_with_fwe_ui_5uncorr.inputs.contrast_index = 3
topo_fdr_with_fwe_ui_5uncorr.inputs.extent_threshold = 10
topo_fdr_with_fwe_ui_5uncorr.inputs.height_threshold = 5
topo_fdr_with_fwe_ui_5uncorr.inputs.use_fwe_correction = False

topo_fdr_with_fwe_ui_5uncorr_ev = evaluation_worflow.clone(name="topo_fdr_with_fwe_ui_5uncorr_ev")

compare_pipeline.connect([(datasource, topo_fdr_with_fwe_ui_5uncorr,[('spm_mat_file','spm_mat_file')]),
                          (convert_t_map, topo_fdr_with_fwe_ui_5uncorr, [('fix_affine.transformed_volumes','stat_image')]),
                                                
                          (topo_fdr_with_fwe_ui_5uncorr, topo_fdr_with_fwe_ui_5uncorr_ev, [('thresholded_map','inputnode.map_to_evaluate')]),            
                          (convert_manual, topo_fdr_with_fwe_ui_5uncorr_ev, [('fix_affine.transformed_volumes', 'inputnode.expert_map')]),                 
                          (datasource, topo_fdr_with_fwe_ui_5uncorr_ev, [('tumour_mask','inputnode.tumour_mask')])
                          ])

topo_fdr_with_fwe_ui_laura = pe.Node(interface = spm.Threshold(), name="topo_fdr_with_fwe_ui_laura")
topo_fdr_with_fwe_ui_laura.inputs.contrast_index = 3
topo_fdr_with_fwe_ui_laura.inputs.extent_threshold = 10
topo_fdr_with_fwe_ui_laura.inputs.use_fwe_correction = False
topo_fdr_with_fwe_ui_laura.inputs.use_topo_fdr = False

topo_fdr_with_fwe_ui_laura_ev = evaluation_worflow.clone(name="topo_fdr_with_fwe_ui_laura_ev")

compare_pipeline.connect([(datasource, topo_fdr_with_fwe_ui_laura,[('spm_mat_file','spm_mat_file')]),
                          (convert_t_map, topo_fdr_with_fwe_ui_laura, [('fix_affine.transformed_volumes','stat_image')]),
                          (infosource, topo_fdr_with_fwe_ui_laura, [(('subject_id', get_th_f), 'height_threshold')]),
                                                
                          (topo_fdr_with_fwe_ui_laura, topo_fdr_with_fwe_ui_laura_ev, [('thresholded_map','inputnode.map_to_evaluate')]),            
                          (convert_manual, topo_fdr_with_fwe_ui_laura_ev, [('fix_affine.transformed_volumes', 'inputnode.expert_map')]),                 
                          (datasource, topo_fdr_with_fwe_ui_laura_ev, [('tumour_mask','inputnode.tumour_mask')])
                          ])


ggmm = pe.Node(interface=nodes.ThresholdGGMM(no_deactivation_class=False), name="ggmm")

topo_fdr_with_ggmm = pe.Node(interface = spm.Threshold(), name="topo_fdr_with_ggmm")
topo_fdr_with_ggmm.inputs.contrast_index = 3
topo_fdr_with_ggmm.inputs.use_fwe_correction = False
topo_fdr_with_ggmm.iterables = ('extent_threshold', [0,   10])

topo_fdr_with_ggmm_ev = evaluation_worflow.clone(name="topo_fdr_with_ggmm_ev")

compare_pipeline.connect([(convert_mask, ggmm, [('fix_affine.transformed_volumes','mask_file')]),
                          (convert_t_map, ggmm, [('fix_affine.transformed_volumes','stat_image')]),
                          (ggmm, topo_fdr_with_ggmm,[('threshold','height_threshold')]),
                          (datasource, topo_fdr_with_ggmm,[('spm_mat_file','spm_mat_file')]),
                          (convert_t_map, topo_fdr_with_ggmm, [('fix_affine.transformed_volumes','stat_image')]),                  
                          
                          (topo_fdr_with_ggmm, topo_fdr_with_ggmm_ev, [('thresholded_map','inputnode.map_to_evaluate')]),                 
                          (convert_manual, topo_fdr_with_ggmm_ev, [('fix_affine.transformed_volumes', 'inputnode.expert_map')]),                   
                          (datasource, topo_fdr_with_ggmm_ev, [('tumour_mask','inputnode.tumour_mask')])
                          ])

smm = pe.Node(interface=fsl.SMM(), name="smm")
threshold_smm = pe.Node(interface=misc.SimpleThreshold(threshold=0.5), name="threshold_smm")

smm_ev = evaluation_worflow.clone(name="smm_ev")

compare_pipeline.connect([(convert_t_map, smm, [('fix_affine.transformed_volumes','spatial_data_file')]),
                          (convert_mask, smm, [('fix_affine.transformed_volumes','mask')]),
                          (smm,threshold_smm,[('activation_p_map', 'volumes')]),
                          
                          (threshold_smm, smm_ev, [('thresholded_volumes','inputnode.map_to_evaluate')]),            
                          (convert_manual, smm_ev, [('fix_affine.transformed_volumes', 'inputnode.expert_map')]),      
                          (datasource, smm_ev, [('tumour_mask','inputnode.tumour_mask')])
                          ])

expert_ev = evaluation_worflow.clone(name="expert_ev")

compare_pipeline.connect([                         
                          (convert_manual, expert_ev, [('fix_affine.transformed_volumes', 'inputnode.map_to_evaluate'),
                                                       ('fix_affine.transformed_volumes', 'inputnode.expert_map')]),
                          (datasource, expert_ev, [('tumour_mask','inputnode.tumour_mask')])
                          ])


compare_pipeline.run()
#compare_pipeline.write_graph()