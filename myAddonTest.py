#Author-Autodesk
#Description-Demonstrates the creation of a custom feature.

import adsk.core, adsk.fusion, traceback, random, math

_app: adsk.core.Application = None
_ui: adsk.core.UserInterface = None
_handlers = []

_customFeatureDef: adsk.fusion.CustomFeature = None

_sketchSelectInput: adsk.core.SelectionCommandInput = None
_cuttingBodySelectInput: adsk.core.SelectionCommandInput = None
_spawnBodySelectInput: adsk.core.SelectionCommandInput = None
_spawnBodyEdgeSelectInput: adsk.core.SelectionCommandInput = None
_lengthInput: adsk.core.ValueCommandInput = None
_widthInput: adsk.core.ValueCommandInput = None
_depthInput: adsk.core.ValueCommandInput = None
_radiusInput: adsk.core.ValueCommandInput = None

_editedCustomFeature: adsk.fusion.CustomFeature = None
_restoreTimelineObject: adsk.fusion.TimelineObject = None
_isRolledForEdit = False


def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface

        # Create the command definition for the creation command.
        createCmdDef = _ui.commandDefinitions.addButtonDefinition('adskCustomPocketCreate', 
                                                                    'Custom Pocket', 
                                                                    'Adds a pocket at a point.', 
                                                                    'Resources/myAddonTest')        

        # Add the create button after the Emboss command in the CREATE panel of the SOLID tab.
        solidWS = _ui.workspaces.itemById('FusionSolidEnvironment')
        panel = solidWS.toolbarPanels.itemById('SolidCreatePanel')
        panel.controls.addCommand(createCmdDef, 'EmbossCmd', False)        

        # Create the command definition for the edit command.
        editCmdDef = _ui.commandDefinitions.addButtonDefinition('adskCustomPocketEdit', 
                                                                'Edit myAddonTest', 
                                                                'Edit myAddonTest.', '')        

        # Connect to the command created event for the create command.
        createCommandCreated = CreatePocketCommandCreatedHandler()
        createCmdDef.commandCreated.add(createCommandCreated)
        _handlers.append(createCommandCreated)

        # Create the custom feature definition.
        global _customFeatureDef
        _customFeatureDef = adsk.fusion.CustomFeatureDefinition.create('adskCustomPocket', 
                                                                        'myAddonTest', 
                                                                        'Resources/myAddonTest')
        _customFeatureDef.editCommandId = 'adskCustomPocketEdit'

        # Connect to the compute event for the custom feature.
        computeCustomFeature = ComputeCustomFeature()
        _customFeatureDef.customFeatureCompute.add(computeCustomFeature)
        _handlers.append(computeCustomFeature)
    except:
        showMessage('Run Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        # Remove all UI elements.
        solidWS = _ui.workspaces.itemById('FusionSolidEnvironment')
        panel = solidWS.toolbarPanels.itemById('SolidCreatePanel')
        cntrl = panel.controls.itemById('adskCustomPocketCreate')
        if cntrl:
            cntrl.deleteMe()
            
        cmdDef = _ui.commandDefinitions.itemById('adskCustomPocketCreate')
        if cmdDef:
            cmdDef.deleteMe()

        cmdDef = _ui.commandDefinitions.itemById('adskCustomPocketEdit')
        if cmdDef:
            cmdDef.deleteMe()
    except:
        showMessage('Stop Failed:\n{}'.format(traceback.format_exc()))


# Define the command inputs needed to get the input from the user for the
# creation of the feauture and connect to the command related events.
class CreatePocketCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs
            des: adsk.fusion.Design = _app.activeProduct

            global _sketchSelectInput, _cuttingBodySelectInput, _spawnBodySelectInput, _spawnBodyEdgeSelectInput, _lengthInput, _widthInput, _depthInput, _radiusInput

            # Create the selection input to select the body(s).
            inputs.addSelectionInput
            _sketchSelectInput = inputs.addSelectionInput('selectSketch', 
                                                         'Sketch', 
                                                         'desc desc')
            _sketchSelectInput.addSelectionFilter('Sketches')
            _sketchSelectInput.tooltip = 'desc'
            _sketchSelectInput.setSelectionLimits(1, 1)

            _spawnBodyEdgeSelectInput = inputs.addSelectionInput('selectSpawnBodyEdge', 
                                                         'SpawnBodyEdge', 
                                                         'desc desc')
            _spawnBodyEdgeSelectInput.addSelectionFilter('LinearEdges')
            _spawnBodyEdgeSelectInput.tooltip = 'desc'
            _spawnBodyEdgeSelectInput.setSelectionLimits(1, 1)
             
            # Connect to the needed command related events.
            # onExecutePreview = ExecutePreviewHandler()
            # cmd.executePreview.add(onExecutePreview)
            # _handlers.append(onExecutePreview)

            onExecute = CreateExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)  

        except:
            showMessage('CommandCreated failed: {}\n'.format(traceback.format_exc()))


        
# Event handler for the execute event of the create command.
class CreateExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs: adsk.fusion.CustomFeatureEventArgs = args

            showMessage(f"hit 1")

            directionLineMidpointsCol, copiedBodiesCol = spawnBodyCopies(args)
            showMessage(f"hit 1.0")
            showMessage(f"{directionLineMidpointsCol}, {copiedBodiesCol}")
            showMessage(f"hit 1.1")
            intersectBodiesWithSketchProfiles(args, directionLineMidpointsCol, copiedBodiesCol)

            showMessage(f"hit 3")

        except:
            eventArgs.executeFailed = True
            showMessage('Execute: {}\n'.format(traceback.format_exc()))


# Event handler for the executePreview event.
class ExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            
            spawnBodyCopies(args)

        except:
            showMessage('ExecutePreview: {}\n'.format(traceback.format_exc()))       

# Event handler to handle the compute of the custom feature.
class ComputeCustomFeature(adsk.fusion.CustomFeatureEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs: adsk.fusion.CustomFeatureEventArgs = args

            # showMessage(f"hit 1b")

            # directionLineMidpointsCol, copiedBodiesCol = spawnBodyCopies(args)

            # intersectBodiesWithSketchProfiles(args, directionLineMidpointsCol, copiedBodiesCol)

            # showMessage(f"hit 3b")

        except:
            showMessage('CustomFeatureCompute: {}\n'.format(traceback.format_exc()))

def spawnBodyCopies(args):

    eventArgs = adsk.core.CommandEventArgs.cast(args)        

    # Get the settings from the inputs.
    sketch: adsk.fusion.SketchPoint = _sketchSelectInput.selection(0).entity
    # cuttingBody: adsk.fusion.SketchPoint = _cuttingBodySelectInput.selection(0).entity
    
    spawnEdge = _spawnBodyEdgeSelectInput.selection(0).entity
    spawnBody = spawnEdge.body

    design: adsk.fusion.Design = _app.activeProduct
    rootComp = design.rootComponent
    spawnBodyComp = spawnBody.parentComponent
    features = rootComp.features

    firstFeature = None
    lastFeature = None

    # These two collections link to each other by index. 
    # Points and Bodies are linked 1-1
    directionLineMidpointsCol = adsk.core.ObjectCollection.create()
    copiedBodiesCol = adsk.core.ObjectCollection.create()

    sketchCurves = sketch.sketchCurves
    lines = sketchCurves.sketchLines
    index = -1
    for line in lines:
        if line.isConstruction:

            index += 1

            # Get angle between points
            skPtStartData = line.startSketchPoint.geometry.getData()
            skPtEndData = line.endSketchPoint.geometry.getData()
            deltaX = -skPtStartData[1] + skPtEndData[1]
            deltaY = -skPtStartData[2] + skPtEndData[2]
            angle = math.degrees(math.atan2(deltaY, deltaX))

            # showMessage(f"{skPtStartData}, {skPtEndData}")
            # showMessage(f"{angle}, {deltaX}, {deltaY}")
            
            # Get world midpoint of sketch points
            skPtStartWorldData = line.startSketchPoint.worldGeometry.getData()
            skPtEndWorldData = line.endSketchPoint.worldGeometry.getData()
            midpoint_sketchPoint = adsk.core.Point3D.create(
                (skPtStartWorldData[1] + skPtEndWorldData[1]) / 2, 
                (skPtStartWorldData[2] + skPtEndWorldData[2]) / 2, 
                (skPtStartWorldData[3] + skPtEndWorldData[3]) / 2
                )

            # Get midpoint of body edge points
            spawnEdgeStartVert = spawnEdge.startVertex.geometry.getData()
            spawnEdgeEndVert = spawnEdge.endVertex.geometry.getData()
            midpoint_spawnEdge = adsk.core.Point3D.create(
                (spawnEdgeStartVert[1] + spawnEdgeEndVert[1]) / 2, 
                (spawnEdgeStartVert[2] + spawnEdgeEndVert[2]) / 2, 
                (spawnEdgeStartVert[3] + spawnEdgeEndVert[3]) / 2
                )

            # Create a matrix that defines the translation from point 1 to point 2.
            trans: adsk.core.Matrix3D = adsk.core.Matrix3D.create()
            rotationVector = vector = adsk.core.Vector3D.create(0, 1, 0)

            # Get Matrix for movement & rotation of body
            trans.setToRotation(math.radians(angle), rotationVector, midpoint_spawnEdge)
            newTransform = adsk.core.Matrix3D.create()
            newTransform.translation = midpoint_spawnEdge.vectorTo(midpoint_sketchPoint)
            trans.transformBy(newTransform)

            # Create Copy / Paste Feature
            newCopyFeature = spawnBodyComp.features.copyPasteBodies.add(spawnBody)
            baseBodyCopy = spawnBodyComp.bRepBodies.item(index + 1)
            baseBodyCopy.name = f"CopiedBody_{index}"
            if not firstFeature:
                firstFeature = newCopyFeature

            # Create Movement Feature
            moveFeatures = spawnBodyComp.features.moveFeatures
            inputEnts = adsk.core.ObjectCollection.create()
            inputEnts.add(baseBodyCopy)
            moveInput = moveFeatures.createInput(inputEnts, trans)
            moveFeature = moveFeatures.add(moveInput)
            lastFeature = moveFeature

            directionLineMidpointsCol.add(midpoint_sketchPoint)
            copiedBodiesCol.add(baseBodyCopy)

            # newOcc = rootComp.occurrences.addExistingComponent (spawnBodyComp, trans)
            # newBody = newOcc.bRepBodies.item(0)

    custFeatInput = spawnBodyComp.features.customFeatures.createInput(_customFeatureDef)
    custFeatInput.addDependency('Sketch', sketch)
    custFeatInput.addDependency('SpawnBodyEdge', spawnEdge)
    custFeatInput.setStartAndEndFeatures(firstFeature, lastFeature)
    spawnBodyComp.features.customFeatures.add(custFeatInput)

    return directionLineMidpointsCol, copiedBodiesCol

def intersectBodiesWithSketchProfiles(args, directionLineMidpointsCol, copiedBodiesCol):

    showMessage(f"hit 2")

    showMessage(f"{directionLineMidpointsCol}, {copiedBodiesCol}")

    # Things to consider:
    #   I can't check if a point lies inside a profile, but I can check if it lies inside a bRedBody
    #       BRepBody.pointContainment s

    # Make a map associating each direction line midpoint with a new copied body
    # Extrude all sketch profiles except boundary
    # For each direction line midpoint, determine which new body it lies inside.
    # Use that body to intersect with the copied body associated with direction line 

def showMessage(message, error = False):
    textPalette: adsk.core.TextCommandPalette = _ui.palettes.itemById('TextCommands')
    textPalette.writeText(message)

    if error:
        _ui.messageBox(message)