import adsk.core, adsk.fusion, math, time, json, builtins

def run(_context: str):
    with open(r'D:\Code Projects\GridfinityWorkshop\experiments\loft-cell\original-profiles.json',encoding='utf-8') as profile_file:
        data=json.load(profile_file)
    app=adsk.core.Application.get()
    doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name='Gridfinity 1x1 - captured profile loft'
    d=adsk.fusion.Design.cast(app.activeProduct)
    d.designType=adsk.fusion.DesignTypes.ParametricDesignType
    c=d.rootComponent
    builtins.gf_captured_design=d
    start=time.perf_counter()
    sketches={}
    def p(arr):
        return adsk.core.Point3D.create(arr[0]/10,arr[1]/10,0)
    for section in data['profiles']:
        z=section['zFromBottomMM']
        plane=c.xYConstructionPlane
        if z!=0:
            i=c.constructionPlanes.createInput()
            i.setByOffset(plane,adsk.core.ValueInput.createByString(str(z)+' mm'))
            plane=c.constructionPlanes.add(i)
            plane.name=section['name']+' plane'
            plane.isLightBulbOn=False
        s=c.sketches.add(plane)
        s.name=section['name']
        for q in section['curves']:
            if q['type']=='Line3D':
                ent=s.sketchCurves.sketchLines.addByTwoPoints(p(q['startPointMM']),p(q['endPointMM']))
            elif q['type']=='Circle3D':
                ent=s.sketchCurves.sketchCircles.addByCenterRadius(p(q['centerMM']),q['radius']/10)
            elif q['type']=='Arc3D':
                sweep=(q['endAngle']-q['startAngle'])*q['normal'][2]
                ent=s.sketchCurves.sketchArcs.addByCenterStartSweep(p(q['centerMM']),p(q['startPointMM']),sweep)
            else:
                raise RuntimeError('Unexpected geometry '+q['type'])
            ent.isFixed=True
        s.isVisible=False
        sketches[section['name']]=s
    ops=adsk.fusion.FeatureOperations
    def loft(name,a,b,operation):
        i=c.features.loftFeatures.createInput(operation)
        i.loftSections.add(sketches[a].profiles.item(0))
        i.loftSections.add(sketches[b].profiles.item(0))
        if operation==ops.CutFeatureOperation:
            i.participantBodies=[c.bRepBodies.item(0)]
        f=c.features.loftFeatures.add(i)
        f.name=name
    loft('Bottom bevel','Outside bottom','Outside shoulder',ops.NewBodyFeatureOperation)
    loft('Vertical envelope','Outside shoulder','Outside top',ops.JoinFeatureOperation)
    loft('Lower socket taper','Socket floor','Socket lower shoulder',ops.CutFeatureOperation)
    loft('Straight socket band','Socket lower shoulder','Socket upper shoulder',ops.CutFeatureOperation)
    loft('Upper socket taper','Socket upper shoulder','Socket mouth',ops.CutFeatureOperation)
    def cut(name,s,depth):
        profiles=adsk.core.ObjectCollection.create()
        for q in s.profiles:
            profiles.add(q)
        i=c.features.extrudeFeatures.createInput(profiles,ops.CutFeatureOperation)
        i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(depth)),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        i.participantBodies=[c.bRepBodies.item(0)]
        f=c.features.extrudeFeatures.add(i)
        f.name=name
    cut('Skeleton opening',sketches['Skeleton opening'],'3.4 mm')
    cut('Four magnet pockets',sketches['Magnet pockets'],'2.4 mm')
    d.computeAll()
    b=c.bRepBodies.item(0)
    b.name='Gridfinity 1x1 captured loft cell'
    builtins.gf_captured_build_seconds=time.perf_counter()-start
    app.activeViewport.fit()
    print(json.dumps({'buildSeconds':builtins.gf_captured_build_seconds,'volumeMM3':b.volume*1000,'faces':b.faces.count,'timeline':d.timeline.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'health':[{'name':t.name,'state':int(t.healthState),'message':t.errorOrWarningMessage} for t in d.timeline if int(t.healthState)!=0]}))

