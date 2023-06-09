# filename = 'C:\\Users\\user\\Desktop\\skull_strip_230131.py'
# exec(compile(open(filename).read(), filename, 'exec'))

import os
import vtk
import slicer
import MRMLCorePython
from vtk.util import numpy_support

path = r'E:\vv' #main folder containing the CT Scans
dicom_folders = sorted(os.listdir(path), key = lambda x: int(x.split('_')[0]))
print(dicom_folders)

folder_count = 0 #0 if none are done, change to number of total of done, not the folder name

for folder in dicom_folders:
    dicomDataDir = os.path.join(path, folder)
    print(f"starting on images: {folder}")

    
    #import DICOM into scene
    
    loadedNodeIDs = []  # this list will contain the list of all loaded node IDs

    from DICOMLib import DICOMUtils
    with DICOMUtils.TemporaryDICOMDatabase() as db:
      DICOMUtils.importDicom(dicomDataDir, db)
      patientUIDs = db.patients()
      for patientUID in patientUIDs:
        loadedNodeIDs.extend(DICOMUtils.loadPatientByUID(patientUID))


    # Load CT into the scene and run this script to automatically segment endocranium
    masterVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")

    # Create segmentation
    slicer.app.processEvents()
    segmentationNode = slicer.vtkMRMLSegmentationNode()
    slicer.mrmlScene.AddNode(segmentationNode)
    segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)

    # Create segment editor to get access to effects
    slicer.app.processEvents()
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    if not segmentEditorWidget.effectByName("Wrap Solidify"):
        slicer.util.errorDisplay("Please install 'SurfaceWrapSolidify' extension using Extension Manager.")

    segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
    slicer.mrmlScene.AddNode(segmentEditorNode)
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode)
    segmentEditorWidget.setSourceVolumeNode(masterVolumeNode)

    # Create bone segment by thresholding
    slicer.app.processEvents()
    boneSegmentID = segmentationNode.GetSegmentation().AddEmptySegment("bone")
    segmentEditorNode.SetSelectedSegmentID(boneSegmentID)
    segmentEditorWidget.setActiveEffectByName("Threshold")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("MinimumThreshold",300)
    effect.setParameter("MaximumThreshold",3071)
    effect.self().onApply()

##    # Isolate Largest Vol
##    slicer.app.processEvents()
##    segmentEditorWidget.setActiveEffectByName("Islands")
##    effect = segmentEditorWidget.activeEffect()
##    effect.setParameterDefault("Operation", "KEEP_LARGEST_ISLAND")
##    effect.self().onApply()

    # Cavity Wrap to create ICV
    slicer.app.processEvents()
    segmentEditorWidget.setActiveEffectByName("Wrap Solidify")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("region", "largestCavity")
    effect.setParameter("splitCavities", True)
    effect.setParameter("splitCavitiesDiameter", 30)
    effect.setParameter("outputType", "newSegment")
    effect.setParameter("smoothingFactor", 0.2)
    effect.setParameter("remeshOversampling", 1.50)
    effect.setParameter("shrinkwrapIterations", 6)
    effect.self().onApply()

##    # Create Soft Tissues by thresholding
##    slicer.app.processEvents()
##    boneSegmentID = segmentationNode.GetSegmentation().AddEmptySegment("Soft Tissue")
##    segmentEditorNode.SetSelectedSegmentID(boneSegmentID)
##    segmentEditorWidget.setActiveEffectByName("Threshold")
##    effect = segmentEditorWidget.activeEffect()
##    effect.setParameter("MinimumThreshold",300)
##    effect.setParameter("MaximumThreshold",3071)
##    effect.self().onApply()

##    # Isolate Largest Vol
##    slicer.app.processEvents()
##    segmentEditorWidget.setActiveEffectByName("Islands")
##    effect = segmentEditorWidget.activeEffect()
##    effect.setParameterDefault("Operation", "KEEP_LARGEST_ISLAND")
##    effect.self().onApply()

    # export to all segments to STL
    slicer.vtkSlicerSegmentationsModuleLogic.ExportSegmentsClosedSurfaceRepresentationToFiles(dicomDataDir, segmentationNode, None, 'STL', True, 1.0, False)

    # clean up - empty the scene
    slicer.mrmlScene.RemoveNode(segmentEditorNode)
    slicer.mrmlScene.Clear(0)

    print(f"Finished {folder}")

    folder_count += 1
    print(f"{folder_count} of {len(dicom_folders)} ICVs calculated")
    print("-----\n")

    
