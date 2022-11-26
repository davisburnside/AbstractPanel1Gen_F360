#Author-Autodesk
#Description-Demonstrates the creation of a custom feature.

import adsk.core, adsk.fusion, traceback, random, math

_app: adsk.core.Application = None
_ui: adsk.core.UserInterface = None
_handlers = []

_customFeatureDef: adsk.fusion.CustomFeature = None

_directionSketchSelectInput: adsk.core.SelectionCommandInput = None
_boundarySketchSelectInput: adsk.core.SelectionCommandInput = None
_spawnBodyEdgeSelectInput: adsk.core.SelectionCommandInput = None
_cellHeightInput: adsk.core.ValueCommandInput = None
_cellChamferAngleInput: adsk.core.ValueCommandInput = None

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

            global _directionSketchSelectInput, _boundarySketchSelectInput, _cellChamferAngleInput, _cellHeightInput, _spawnBodyEdgeSelectInput, _lengthInput, _widthInput, _depthInput, _radiusInput

            # Define Command Inputs
            _boundarySketchSelectInput = inputs.addSelectionInput('selectBoundarySketch', 
                                                        'BoundarySketch', 
                                                        'desc desc')
            _boundarySketchSelectInput.addSelectionFilter('Sketches')
            _boundarySketchSelectInput.tooltip = 'desc'
            _boundarySketchSelectInput.setSelectionLimits(1, 1)

            _directionSketchSelectInput = inputs.addSelectionInput('selectDirectionSketch', 
                                                         'DirectionSketch', 
                                                         'desc desc')
            _directionSketchSelectInput.addSelectionFilter('Sketches')
            _directionSketchSelectInput.tooltip = 'desc'
            _directionSketchSelectInput.setSelectionLimits(1, 1)

            _spawnBodyEdgeSelectInput = inputs.addSelectionInput('selectSpawnBodyEdge', 
                                                         'SpawnBodyEdge', 
                                                         'desc desc')
            _spawnBodyEdgeSelectInput.addSelectionFilter('LinearEdges')
            _spawnBodyEdgeSelectInput.tooltip = 'desc'
            _spawnBodyEdgeSelectInput.setSelectionLimits(1, 1)

            default = adsk.core.ValueInput.createByReal(1)
            _cellHeightInput = inputs.addDistanceValueCommandInput('cellHeightInput', 'cellHeightInput', default)
            
            default = adsk.core.ValueInput.createByString("30 deg")
            _cellChamferAngleInput = inputs.addAngleValueCommandInput('cellChamferAngleInput', 'cellChamferAngleInput', default)

             
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

            showMessage(f"ComputeCustomFeature(adsk.fusion.CustomFeatureEventHandler)")

            # directionLineMidpointsCol, copiedBodiesCol = spawnBodyCopies(args)


            # showMessage(f"hit 3b")

        except:
            showMessage('CustomFeatureCompute: {}\n'.format(traceback.format_exc()))

def spawnBodyCopies(args):

    showMessage(f"HIT 1")

    eventArgs = adsk.core.CommandEventArgs.cast(args)        

    # Get the settings from the inputs.
    sketch: adsk.fusion.SketchPoint = _directionSketchSelectInput.selection(0).entity
    
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

    # For each direction line, spawn a body at it's center & align body to line
    # This has only been tested in the XY plane
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
            angle = 90 + math.degrees(math.atan2(deltaY, deltaX))

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

            # Create a Matrix for movement & rotation of body
            matrix: adsk.core.Matrix3D = adsk.core.Matrix3D.create()
            rotationVector = vector = adsk.core.Vector3D.create(0, 0, 1)
            matrix.setToRotation(math.radians(angle), rotationVector, midpoint_spawnEdge)
            transformMatrix = adsk.core.Matrix3D.create()
            transformMatrix.translation = midpoint_spawnEdge.vectorTo(midpoint_sketchPoint)
            matrix.transformBy(transformMatrix)

            # Create Copy / Paste Feature for Body
            newCopyFeature = spawnBodyComp.features.copyPasteBodies.add(spawnBody)
            baseBodyCopy = spawnBodyComp.bRepBodies.item(index + 1)
            baseBodyCopy.name = f"CopiedBody_{index}"
            if not firstFeature:
                firstFeature = newCopyFeature

            # # Create Movement Feature
            moveFeatures = spawnBodyComp.features.moveFeatures
            inputEnts = adsk.core.ObjectCollection.create()
            inputEnts.add(baseBodyCopy)
            moveInput = moveFeatures.createInput(inputEnts, matrix)
            moveFeature = moveFeatures.add(moveInput)
            lastFeature = moveFeature

            directionLineMidpointsCol.add(midpoint_sketchPoint)
            copiedBodiesCol.add(baseBodyCopy)

    showMessage(f"HIT 2")




Why don't I just get the profile underneath the current point?
I don't need to cycle through every one













    boundarySketch: adsk.fusion.Profile = _boundarySketchSelectInput.selection(0).entity
    for profile in boundarySketch.profiles:
        # if profile != boundaryProfile:


            profileBoundingBoxContainsDirectionLine = True
            boundBox = profile.boundingBox
            showMessage(f"\n\n max: {boundBox.maxPoint.getData()}\nmin: {boundBox.minPoint.getData()}")
            for index, point in enumerate(directionLineMidpointsCol):
                showMessage(f" point: {point.getData()}")
                showMessage(f"Contains? {boundBox.contains(point)}\n")

            if profileBoundingBoxContainsDirectionLine:

            
                # Create Extrusion Feature and get new Body
                extrudes = spawnBodyComp.features.extrudeFeatures
                # showMessage(f"{_cellHeightInput} {_cellHeightInput.expression} ")
                distance = adsk.core.ValueInput.createByString(_cellHeightInput.expression)
                # showMessage(f"{distance},   {distance.stringValue}")
                newExtrude = extrudes.addSimple(profile, distance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                extrudedProfileBody: adsk.fusion.BRepBody = newExtrude.bodies.item(0)
                
                # Check if the new body contains/touches any direction line midpoints
                # If so, make an Intersect Feature between the extruded body & copied Body
                # If not, delete the new body
                bodyHasAPoint = False
                pointIndex = -1
                for index, point in enumerate(directionLineMidpointsCol):
                    pc: adsk.fusion.PointContainment = extrudedProfileBody.pointContainment(point)
                    if (pc == adsk.fusion.PointContainment.PointInsidePointContainment 
                        or pc == adsk.fusion.PointContainment.PointOnPointContainment):    
                        bodyHasAPoint = True
                        pointIndex = index
                        break

                # If there is a direction line present in a sketch profile's boundary    
                if bodyHasAPoint:

                    # identidy edges of top (+Z facing) face
                    edgeCollection = adsk.core.ObjectCollection.create()
                    vecZ = adsk.core.Vector3D.create(0,0,1)
                    faces = [f for f in extrudedProfileBody.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType]
                    for face in faces:
                        if vecZ.angleTo(face.geometry.normal) == 0:
                            [edgeCollection.add(edge) for edge in face.edges]
                            break

                    # Create the ChamferInput object.
                    chamferFeatureInput = spawnBodyComp.features.chamferFeatures.createInput2() 
                    chamferOffset = adsk.core.ValueInput.createByReal(0.3)
                    chamferAngle = adsk.core.ValueInput.createByString(_cellChamferAngleInput.expression)
                    chamferOffset = adsk.core.ValueInput.createByString(_cellHeightInput.expression)
                    chamferFeatureInput.chamferEdgeSets.addDistanceAndAngleChamferEdgeSet(edgeCollection, chamferOffset, chamferAngle, True, True)
                    chamferFeature = spawnBodyComp.features.chamferFeatures.add(chamferFeatureInput) 
                    lastFeature = chamferFeature

                    # Intersect with Copied Body
                    copiedBodyToIntersect = copiedBodiesCol.item(pointIndex)
                    bodyCollection = adsk.core.ObjectCollection.create()
                    bodyCollection.add(copiedBodyToIntersect)
                    combineFeatureInput = features.combineFeatures.createInput(extrudedProfileBody, bodyCollection)
                    combineFeatureInput.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
                    combineFeatureInput.isKeepToolBodies = False
                    newCombineFeature = features.combineFeatures.add(combineFeatureInput)
                    lastFeature = newCombineFeature

                # If not, delete the extruded body (No direction line associated with the Sketch Profile)
                else: 
                    didDelete = extrudedProfileBody.deleteMe()

                showMessage(f"HIT 3")

    # Roll all new features above into a Custom feature
    custFeatInput = spawnBodyComp.features.customFeatures.createInput(_customFeatureDef)
    custFeatInput.addDependency('Sketch', sketch)
    custFeatInput.addDependency('SpawnBodyEdge', spawnEdge)
    custFeatInput.setStartAndEndFeatures(firstFeature, lastFeature)
    spawnBodyComp.features.customFeatures.add(custFeatInput)

    showMessage(f"HIT 4")

    return directionLineMidpointsCol, copiedBodiesCol

def showMessage(message, error = False):
    textPalette: adsk.core.TextCommandPalette = _ui.palettes.itemById('TextCommands')
    textPalette.writeText(message)

    if error:
        _ui.messageBox(message)