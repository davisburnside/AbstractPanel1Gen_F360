#Author-Autodesk
#Description-Demonstrates the creation of a custom feature.

import adsk.core, adsk.fusion, traceback, random, math

_app: adsk.core.Application = None
_ui: adsk.core.UserInterface = None
_handlers = []

_customFeatureDef: adsk.fusion.CustomFeature = None

_directionSketchSelectInput: adsk.core.SelectionCommandInput = None
_boundarySketchSelectInput: adsk.core.SelectionCommandInput = None
_spawnBodySelectInput: adsk.core.SelectionCommandInput = None
_destPlaneInput: adsk.core.SelectionCommandInput = None
_cellHeightInput: adsk.core.ValueCommandInput = None
_cellChamferAngleInput: adsk.core.ValueCommandInput = None

_editedCustomFeature: adsk.fusion.CustomFeature = None
_restoreTimelineObject: adsk.fusion.TimelineObject = None
_isRolledForEdit = False

def getPreciseBoundingBox3D(
    profile :adsk.fusion.Profile
    ) -> adsk.core.BoundingBox3D:

    # get sketch
    skt :adsk.fusion.Sketch = profile.parentSketch
    sktMat :adsk.core.Matrix3D = skt.transform

    # get WireBody
    loop :adsk.fusion.ProfileLoop = profile.profileLoops[0]
    crvs = [pc.geometry for pc in loop.profileCurves]
    if not sktMat.isEqualTo(adsk.core.Matrix3D.create()):
        for crv in crvs:
            crv.transformBy(sktMat)

    tmpMgr = adsk.fusion.TemporaryBRepManager.get()
    wireBody, _ = tmpMgr.createWireFromCurves(crvs)

    # get OrientedBoundingBox3D
    vecX :adsk.core.Vector3D = skt.xDirection
    vecY :adsk.core.Vector3D = skt.yDirection

    app = adsk.core.Application.get()
    measureMgr :adsk.core.MeasureManager = app.measureManager
    orientedBox :adsk.core.OrientedBoundingBox3D = measureMgr.getOrientedBoundingBox(
        wireBody, vecY, vecX)

    halfX = orientedBox.width * 0.5
    halfY = orientedBox.length * 0.5
    halfZ = orientedBox.height * 0.5

    vec3D = adsk.core.Vector3D
    maxPnt :adsk.core.Point3D = orientedBox.centerPoint.copy()
    maxPnt.translateBy(vec3D.create(halfX, halfY, halfZ))

    minPnt :adsk.core.Point3D = orientedBox.centerPoint.copy()
    minPnt.translateBy(vec3D.create(-halfX, -halfY, -halfZ))

    return minPnt, maxPnt

    # return adsk.core.BoundingBox3D.create(minPnt, maxPnt)

# Mainly for fast prototyping, to avoid repetitively selecting things in the UI
def getSketchByName(name):

    app = adsk.core.Application.get()
    activeSelection = adsk.fusion.Design.cast(app.activeProduct)
    sketch = activeSelection.rootComponent.sketches.itemByName(name)
    return sketch

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

            global _directionSketchSelectInput
            global _boundarySketchSelectInput 
            global _cellChamferAngleInput 
            global _cellHeightInput
            global _spawnBodySelectInput 
            global _destPlaneInput
            # _lengthInput
            # _widthInput
            # depthInput
            # _radiusInput

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

            _destPlaneInput = inputs.addSelectionInput('selectDestPlane', 
                                                'DestPlane', 
                                                'desc desc')
            _destPlaneInput.addSelectionFilter('Profiles')
            _destPlaneInput.tooltip = 'desc'
            _destPlaneInput.setSelectionLimits(1, 1)

            _spawnBodySelectInput = inputs.addSelectionInput('selectSpawnBody', 
                                                'SpawnBody', 
                                                'desc desc')
            _spawnBodySelectInput.addSelectionFilter('Bodies')
            _spawnBodySelectInput.tooltip = 'desc'
            _spawnBodySelectInput.setSelectionLimits(1, 1)

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
            directionLineMidpointsCol, copiedBodiesCol = spawnBodyCopies(args)

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

def getBodyBottomFace(bRepBody):

    vecNegZ = adsk.core.Vector3D.create(0,0,-1)
    faces = [f for f in bRepBody.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType]
    for face in faces:

        eva: adsk.core.SurfaceEvaluator = face.evaluator

        normal: adsk.core.Vector3D
        _, normal = eva.getNormalAtPoint(face.pointOnFace)
        normal.normalize()
        


        # showMessage(f"{face.geometry.normal.x}, {face.geometry.normal.y}, {face.geometry.normal.z}")
        if vecNegZ.angleTo(normal) == 0:
            showMessage(f"{normal.x}, {normal.y}, {normal.z}")
            return face

def spawnBodyCopies(args):

    showMessage("HIT 1")

    app = adsk.core.Application.get() 
    design = adsk.fusion.Design.cast(app.activeProduct) 
    root = design.rootComponent
    eventArgs = adsk.core.CommandEventArgs.cast(args)        

    # Get the settings from the inputs.
    sketch: adsk.fusion.SketchPoint = _directionSketchSelectInput.selection(0).entity
    
    spawnBody = _spawnBodySelectInput.selection(0).entity
    # spawnBody = spawnEdge.body

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
    angleIndexes = []

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

            # Get midpoint of bottom face of Bounding Box for Body
            boundBox = spawnBody.boundingBox
            negZVector = adsk.core.Vector3D.create(0, 0, -1)

            zVal = boundBox.minPoint.z
            yVal = (boundBox.minPoint.y + boundBox.maxPoint.y ) / 2
            xVal = (boundBox.minPoint.x + boundBox.maxPoint.x ) / 2
            midpoint_spawnBodyBottom = adsk.core.Point3D.create(xVal, yVal, zVal)

            # Create a Matrix for movement & rotation of body
            matrix: adsk.core.Matrix3D = adsk.core.Matrix3D.create()
            rotationVector = vector = adsk.core.Vector3D.create(0, 0, 1)
            matrix.setToRotation(math.radians(angle), rotationVector, midpoint_spawnBodyBottom)
            transformMatrix = adsk.core.Matrix3D.create()
            transformMatrix.translation = midpoint_spawnBodyBottom.vectorTo(midpoint_sketchPoint)
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
            angleIndexes.append(angle)

    # Next, iterate through all Sketch profile in the "Cell Boundaries" Sketch
    allNewBodies = adsk.core.ObjectCollection.create()
    boundarySketch: adsk.fusion.Profile = _boundarySketchSelectInput.selection(0).entity
    for profile in boundarySketch.profiles:

        # Get Profile's BoundingBox X & Y
        # If that box does contains a direction Line's Midpoint, do not extrude it
        # This step acts to prevent too many extrusions from being created for complicated cell patterns
        profileBoundingBoxContainsDirectionLine = False
        profileBoundBoxMinPnt, profileBoundBoxMaxPnt = getPreciseBoundingBox3D(profile)
        for index, point in enumerate(directionLineMidpointsCol):
            _, pointX, pointY, pointZ = point.getData()
            if (pointX >= profileBoundBoxMinPnt.x and pointX <= profileBoundBoxMaxPnt.x
                and pointY >= profileBoundBoxMinPnt.y and pointY <= profileBoundBoxMaxPnt.y):

                profileBoundingBoxContainsDirectionLine = True
                showMessage(f" point: [{pointX},{pointY}] is inside box with min&max bounds of [{profileBoundBoxMinPnt.x},{profileBoundBoxMinPnt.y}] & [{profileBoundBoxMaxPnt.x},{profileBoundBoxMaxPnt.y}]")
                break

        if profileBoundingBoxContainsDirectionLine:

            # Create Extrusion Feature with new Body
            extrudes = spawnBodyComp.features.extrudeFeatures
            distance = adsk.core.ValueInput.createByString(_cellHeightInput.expression)
            newExtrude: adsk.fusion.ExtrudeFeature = extrudes.addSimple(profile, distance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrudedProfileBody: adsk.fusion.BRepBody = newExtrude.bodies.item(0)
            
            # Check if the new body contains/touches any direction line midpoints
            # If so, make an Intersect Feature between the extruded body & copied Body
            # If not, delete the new body
            bodyHasAPoint = False
            pointIndex = -1
            for index, point in enumerate(directionLineMidpointsCol):
                pc: adsk.fusion.PointContainment = extrudedProfileBody.pointContainment(point)
                # showMessage(f"{pc},      {point.getData()},  {extrudedProfileBody.boundingBox.minPoint.getData()}, {extrudedProfileBody.boundingBox.maxPoint.getData()} ")
                if (pc == adsk.fusion.PointContainment.PointInsidePointContainment 
                    or pc == adsk.fusion.PointContainment.PointOnPointContainment):    
                    bodyHasAPoint = True
                    pointIndex = index
                    break

            # If there is a direction line midpoint present in a sketch profile's boundary    
            if bodyHasAPoint:

                # identify edges of top (+Z facing) face
                edgeCollection = adsk.core.ObjectCollection.create()
                # vecZ = adsk.core.Vector3D.create(0,0,1)
                # faces = [f for f in extrudedProfileBody.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType]
                # for face in faces:
                #     if vecZ.angleTo(face.geometry.normal) == 0:
                #         [edgeCollection.add(edge) for edge in face.edges]
                #         break
                endFace = newExtrude.endFaces.item(0)
                [edgeCollection.add(edge) for edge in endFace.edges]

                newExtrude.endFaces.item(0).attributes.add('CellArtGen1', 'extrusionEndFace', "1")
                newExtrude.startFaces.item(0).attributes.add('CellArtGen1', 'extrusionStartFace', "1")

                # Create the ChamferInput object.
                chamferFeatureInput = spawnBodyComp.features.chamferFeatures.createInput2() 
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
                newCombineFeature: adsk.fusion.CombineFeature = features.combineFeatures.add(combineFeatureInput)
                lastFeature = newCombineFeature

                # add new body to Collection, for use after current loop finishes
                newBody = newCombineFeature.bodies.item(0)
                angle = angleIndexes[pointIndex]
                newBody.attributes.add('AbstractCellGen1', 'BodyAngle', str(angle))
                allNewBodies.add(newBody)
                showMessage(f"{pointIndex}, {angleIndexes[pointIndex]}, {newCombineFeature.bodies.item(0).name}")

            # If not, delete the extruded body (No direction line associated with the Sketch Profile)
            elif extrudedProfileBody: 
                didDelete = extrudedProfileBody.deleteMe()

    # Move all new Bodies to a new Collection & record the move as a Feature
    allCompNames = [design.allComponents.item(i).name for i in range(design.allComponents.count)]
    nameIndex = 1
    newCompName = f"Copied Bodies {nameIndex}"
    while f"Copied Bodies {nameIndex}" in allCompNames:
        nameIndex += 1
        newCompName = f"Copied Bodies {nameIndex}"
    newParentComponent = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()) 
    newParentComponent.component.name = newCompName
    toNewComponentFeature = newParentComponent.component.features.copyPasteBodies.add(allNewBodies)
    lastFeature = toNewComponentFeature

    # Create Component to store realigned & repositioned pieces
    camReadyBodiesCompNeame = "CAM-Ready Bodies"
    camReadyCompOcc: adsk.fusion.Occurrence = None
    if camReadyBodiesCompNeame not in allCompNames:
        camReadyCompOcc = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()) 
        camReadyCompOcc.component.name = camReadyBodiesCompNeame
        toNewComponentFeature = camReadyCompOcc.component.features.cutPasteBodies.add(allNewBodies)
        lastFeature = toNewComponentFeature
    else:
        camReadyCompOcc = design.allComponents.itemByName(camReadyBodiesCompNeame)
    
    # Rotate Bodies to align all their "Tracks"
    for body in camReadyCompOcc.bRepBodies:
        try:
            # Get Angle attribute from Body
            allAttrs = design.findAttributes('AbstractCellGen1', 'BodyAngle')
            angleStr = [x.value for x in allAttrs if x.parent and x.parent.name == body.name][0]
            angle = -float(angleStr)
            matrix: adsk.core.Matrix3D = adsk.core.Matrix3D.create()
            rotationVector = vector = adsk.core.Vector3D.create(0, 0, 1)
            
            # Create Rotation matrix and Feature
            # Rotation point of matrix is irrelevant, so we can use an out-of-date Point3D
            # It's Irrelevant because the body will be repositioned when the Joint is created 
            matrix.setToRotation(math.radians(angle), rotationVector, midpoint_spawnBodyBottom)
            moveFeatures = camReadyCompOcc.component.features.moveFeatures
            inputEnts = adsk.core.ObjectCollection.create()
            inputEnts.add(body)
            moveInput = moveFeatures.createInput(inputEnts, matrix)
            moveFeature = moveFeatures.add(moveInput)
            lastFeature = moveFeature
        except Exception as e:
            showMessage(f"{e}")

    # Next, convert all bodies in "CAM-Ready Bodies" into SubComponents
    # This is needed to allow them to move individually when Joints are applied
    objCollection = adsk.core.ObjectCollection.create()
    for body in camReadyCompOcc.bRepBodies:
        newCompBody: adsk.fusion.Component = body.createComponent()
        if objCollection.count == 0:
            objCollection.add(newCompBody)

    # Create Planar Joints for all bodies in "CAM-ready Bodies"
    # This allows the user to easily position them
    for childOcc in camReadyCompOcc.childOccurrences:
        body = childOcc.bRepBodies.item(0)
        body.isSelectable = False
        bottomFace = getBodyBottomFace(body)
        geo0 = adsk.fusion.JointGeometry.createByPlanarFace(bottomFace, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        sketchProfile = _destPlaneInput.selection(0).entity
        geo1 = adsk.fusion.JointGeometry.createByProfile(sketchProfile, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        joints: adsk.fusion.Joints = newParentComponent.component.joints
        jointInput = joints.createInput(geo0, geo1)
        jointInput.setAsPlanarJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        jointInput.isFlipped = True
        joint = joints.add(jointInput)

    # Make 2 MoveFeatures that cancel out
    # This is to allow the Joints created above to be rolled up into the singular CustomFeature 
    objCollection = adsk.core.ObjectCollection.create()
    [objCollection.add(body) for body in spawnBodyComp.bRepBodies]
    transform = adsk.core.Matrix3D.create()   
    moveFeats = spawnBodyComp.features.moveFeatures
    transform.translation = adsk.core.Vector3D.create(0.0, 0, 1) 
    moveFeatureInput = moveFeats.createInput(objCollection, transform)
    moveFeature = moveFeats.add(moveFeatureInput)
    transform.translation = adsk.core.Vector3D.create(0.0, 0, -1) 
    moveFeatureInput = moveFeats.createInput(objCollection, transform)
    moveFeature = moveFeats.add(moveFeatureInput)
    lastFeature = moveFeature

    # Roll all new features above into a Custom feature
    custFeatInput = rootComp.features.customFeatures.createInput(_customFeatureDef)
    custFeatInput.setStartAndEndFeatures(firstFeature, lastFeature)
    rootComp.features.customFeatures.add(custFeatInput)

    return directionLineMidpointsCol, copiedBodiesCol

def showMessage(message, error = False):
    textPalette: adsk.core.TextCommandPalette = _ui.palettes.itemById('TextCommands')
    textPalette.writeText(message)

    if error:
        _ui.messageBox(message)