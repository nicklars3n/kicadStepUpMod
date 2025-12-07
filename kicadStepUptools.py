import FreeCAD,FreeCADGui,Part,Mesh


def Load_models(pcbThickness,modules):
    global off_x, off_y, volume_minimum, height_minimum, bbox_all, bbox_list
    global whitelisted_model_elements
    global models3D_prefix, models3D_prefix2, models3D_prefix3, models3D_prefix4
    global last_pcb_path, full_placement, whitelisted_3Dmodels
    global allow_compound, compound_found, bklist, force_transparency, warning_nbr, use_AppPart
    global conv_offs, use_Links, links_imp_mode, use_pypro, use_LinkGroups, fname_sfx
    
    #say (modules)
    missing_models = ''
    compound_found=False
    loaded_models = []
    loaded_model_objs = []
    loaded_models_skipped = []
    createScaledObjs=False #box and cyl from wrl scale params
    virtual_nbr=0
    virtualTop_nbr=0
    virtualBot_nbr=0
    modelTop_nbr=0
    modelBot_nbr=0
    mod_cnt=0
    top_name='Top'+fname_sfx
    bot_name='Bot'+fname_sfx
    topV_name='TopV'+fname_sfx
    botV_name='BotV'+fname_sfx
    stepM_name='Step_Models'+fname_sfx
    stepV_name='Step_Virtual_Models'+fname_sfx
    board_name='Board'+fname_sfx
    
    my_hide_list=""

    for i in range(len(modules)):
        step_module=modules[i][0]
        module_container = step_module
        #print(type(step_module))  #maui test py3
        #sayw('added '+str(i)+' model(s)')
        # say(' modelname= '+modules[i][0]+' '+str(i));
        # say(' modelLayer= '+modules[i][4]+' '+str(i));
        # say(' modelparams '+str(modules[i])+' '+str(i));
        #FreeCAD.Console.PrintMessage('step-module '+step_module)
        encoded=0
        sayw(step_module) # utf-8 test
        if step_module == 'no3Dmodel' or modules[i][4] == 'noLayer':
            say('virtual skipped')
        elif (step_module.startswith(':')) or (step_module.startswith('":')):  #alias 3D path
            step_module_t=step_module.split(':', 1)[-1]
            step_module=step_module_t.split(':', 1)[-1]
            #step_module=step_module.decode("utf-8").replace(u'"', u'')  # name with spaces
            step_module=step_module.replace(u'"', u'')  # name with spaces
            if (step_module.startswith('/')) or  (step_module.startswith('\\')):
                step_module=step_module[1:]
            encoded=1
            #say(step_module)
            #step_module=step_module_t[1]
            #say(step_module.split(':')[1:])
            say('adjusting Alias Path')
            say('step-module-replaced '+step_module)
        elif (step_module.find('${HOME}')!=-1):  #local 3D path
            #step_module=step_module.replace('${KIPRJMOD}', '.')
            home = expanduser("~")
            #step_module=step_module.decode("utf-8").replace(u'${HOME}', home.decode("utf-8"))
            step_module=step_module.replace(u'${HOME}', home)
            step_module=step_module.replace(u'"', u'')  # name with spaces
            encoded=1
            say('adjusting Local Path')
            say('step-module-replaced '+step_module)
        elif (step_module.find('${KIPRJMOD}')!=-1):  #local 3D path
            step_module = re.sub("\\\\", "/", step_module)
            #if isinstance(step_module, str):
            #    step_module = step_module.decode('unicode_escape')
            last_pcb_path = re.sub("\\\\", "/", last_pcb_path)
            #if isinstance(last_pcb_path, str):
            #    last_pcb_path = last_pcb_path.decode('unicode_escape')
            step_module=step_module.replace(u'${KIPRJMOD}', last_pcb_path)
            #sm=step_module
            #step_module=re.sub(r"^\$\{KIPRJMOD\}.*$",last_pcb_path, sm)
            #step_module=re.sub('\${.KIPRJMOD}/', '', step_module)
            step_module=step_module.replace(u'"', u'')  # name with spaces
            encoded=1
            say('adjusting Relative Path')
            say('step-module-replaced '+step_module)
        elif (step_module.startswith('.')) or (step_module.startswith('".')):  #relative path
            #step_module=last_pcb_path+"/"+step_module
            step_module=last_pcb_path+os.sep+step_module
            step_module=step_module.replace(u'"', u'')  # name with spaces
            #step_module=last_pcb_path+step_module[14:]
            encoded=1
            sayw('adjusting Relative Path')
            say('step-module-replaced '+step_module)
            #stop
        elif (step_module.find('${KISYS3DMOD}/')!=-1):  #local ${KISYS3DMOD} 3D path
            #step_module=step_module.replace('${KIPRJMOD}', '.')
            #step_module=step_module.decode("utf-8").replace(u'${KISYS3DMOD}/', u'')
            step_module=step_module.replace(u'${KISYS3DMOD}/', u'')
            step_module=step_module.replace(u'"', u'')  # name with spaces
            #step_module=last_pcb_path+step_module[14:]
            encoded=1
            say('adjusting Local Path')
            say('step-module-replaced '+step_module)
        elif (step_module.find('${')!=-1) and encoded==0:  #extra local ${ENV} 3D path
            step_module= re.sub('\${.*?}/', '', step_module)
            #step_module=step_module.decode("utf-8").replace(u'${}/', u'')
            step_module=step_module.replace(u'${}/', u'')
            step_module=step_module.replace(u'"', u'')  # name with spaces
            encoded=1
            say('adjusting 2nd Local Path')
            say('step-module-replaced '+step_module)      
        elif (step_module.find('$(')!=-1) and encoded==0:  #extra local $(ENV) 3D path
            step_module= re.sub('\$(.*?)/', '', step_module)
            #step_module=step_module.decode("utf-8").replace(u'${}/', u'')
            step_module=step_module.replace(u'$()/', u'')
            step_module=step_module.replace(u'"', u'')  # name with spaces
            encoded=1
            say('adjusting 2nd Local Path')
            say('step-module-replaced '+step_module)      
        if (encoded == 0) and step_module != 'no3Dmodel' and modules[i][4] != 'noLayer':  #test local 3D path without the use of KIPRJMOD or ENV
            step_module_local = re.sub("\\\\", "/", step_module)     #subst '\\' with '/'
            # step_module_local = step_module_local.replace("\\", "/") #subst '\'  with '/'
            last_pcb_path_local = re.sub("\\\\", "/", last_pcb_path)
            # print(step_module)
            # print(step_module_local)
            step_module_local=step_module_local.replace(u'"', u'')  # name with spaces
            #print(step_module_local)
            utf_path_local=os.path.join(make_unicode(last_pcb_path_local),make_unicode(step_module_local))
            #print(utf_path_local)
            pos=utf_path_local.rfind('.')
            #sayw(pos)
            rel_pos=len(utf_path_local)-pos
            local_path=utf_path_local[:-rel_pos+1]
            #print(local_path)
            #stop
            if os.path.exists(local_path+u'stpZ'):
                step_module = local_path+u'stpZ'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            elif os.path.exists(local_path+u'stpz'):
                step_module = local_path+u'stpz'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            elif os.path.exists(local_path+u'STPZ'):
                step_module = local_path+u'STPZ'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            elif os.path.exists(local_path+u'step'):
                step_module = local_path+u'step'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            elif os.path.exists(local_path+u'STEP'):
                step_module = local_path+u'STEP'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            elif os.path.exists(local_path+u'stp'):
                step_module = local_path+u'stp'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            elif os.path.exists(local_path+u'STP'):
                step_module = local_path+u'STP'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            
            elif os.path.exists(local_path+u'iges'):
                step_module = local_path+u'iges'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            elif os.path.exists(local_path+u'IGES'):
                step_module = local_path+u'IGES'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            elif os.path.exists(local_path+u'igs'):
                step_module = local_path+u'igs'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
            elif os.path.exists(local_path+u'IGS'):
                step_module = local_path+u'IGS'
                encoded=1
                say('adjusting Relative Path to pcb file')
                say('step-module-replaced '+step_module)
        # print(modules[i][4],i,step_module)
        # print(modules[i][4] == 'noLayer')
        if step_module != 'no3Dmodel' and modules[i][4] != 'noLayer':
            #model_type = step_module.split('.')[1]
            #if encoded!=1:
            step_module = re.sub("\\\\", "/", step_module)      #subst '\\' with '/'
            # step_module =  step_module.replace("\\", "/") #subst '\'  with '/'
            
            wrl_model = ''
            if step_module.lower().endswith('wrl') or step_module.lower().endswith('wrz'):
                wrl_model = step_module
            #step_transparency = check_wrl_transparency
            step_module=step_module.replace(u'"', u'')  # name with spaces
            pos=step_module.rfind('.')
            #sayw(pos)
            rel_pos=len(step_module)-pos
            #sayw(rel_pos)
            #stop
            step_module=step_module[:-rel_pos+1]+u'stpZ'
            step_module_lw=step_module[:-4]+u'stpz'
            step_module_up=step_module[:-4]+u'STPZ'
            #step_module=step_module[:-3]+'step'
            step_module2=step_module[:-4]+u'step'
            step_module2_up=step_module[:-4]+u'STEP'
            step_module3=step_module[:-4]+u'stp'
            step_module3_up=step_module[:-4]+u'stp'
            step_module4=step_module[:-4]+u'iges'
            step_module4_up=step_module[:-4]+u'IGES'
            step_module5=step_module[:-4]+u'igs'
            step_module5_up=step_module[:-4]+u'IGS'
            # step_module=step_module[:-rel_pos+1]+u'step'
            # #step_module=step_module[:-3]+'step'
            # step_module2=step_module[:-4]+u'stp'
            # step_module3=step_module[:-4]+u'iges'
            # step_module4=step_module[:-4]+u'igs'
            # step_module5=step_module[:-4]+u'stpz'
            #if encoded!=1:
            #    #step_module=step_module.decode("utf-8").replace(u'"', u'')  # name with spaces
            #    step_module=step_module.replace(u'"', u'')  # name with spaces
            model_name=step_module[:-5]
            last_slash_pos1=model_name.rfind('/')
            last_slash_pos2=model_name.rfind('\\')
            last_slash_pos=max(last_slash_pos1,last_slash_pos2)
            model_name=model_name[last_slash_pos+1:]
            #say('model name '+model_name+'.'+model_type)
            say('model name '+model_name)
        else:
            model_name='no3Dmodel'
        blacklisted=0
        if blacklisted_model_elements != '':
            if blacklisted_model_elements.find(model_name) != -1:
                if model_name not in whitelisted_3Dmodels:
                    blacklisted=1
        ###

        if (blacklisted==0):
            # print(modules[i][4],i,step_module)
            # print(modules[i][4] == 'noLayer')
            if step_module != 'no3Dmodel' and modules[i][4] != 'noLayer':
                createScaledObjs=False
                if model_name=="box_mcad" or model_name=="cylV_mcad" or model_name=="cylH_mcad":
                    createScaledObjs=True
                if not createScaledObjs:
                    path_list = [models3D_prefix,models3D_prefix2,models3D_prefix3,models3D_prefix4]
                    model_type = [step_module,step_module_lw,step_module_up,step_module2,step_module2_up,step_module3,step_module3_up,step_module4,step_module4_up,step_module5,step_module5_up]
                    module_path = findModelPath(model_type, path_list)     # Find module in all paths and types specified
                else:
                    scale_vrml=modules[i][8]
                    #sayw(scale_vrml)
                    #scale_val=scale_vrml.split(" ")
                    scale_val=scale_vrml
                    #sayw(scale_val)
                    createScaledBBox(model_name,scale_val)
                    module_path='internal shape'
                if module_path!='not-found' and module_path!='internal shape':
                    #FreeCADGui.Selection.removeSelection(FreeCAD.activeDocument().ActiveObject)  mauitemp volume diff
                    say("opening "+ module_path)
                    mod_cnt+=1
                    doc1=FreeCAD.ActiveDocument
                    counterObj=0;counter=0
                    prevObjs = doc1.Objects
                    for ObJ in doc1.Objects:
                        counterObj+=1
                    say(model_name)
                    Links_available = False
                    if 'LinkView' in dir(FreeCADGui):
                        Links_available = True
                    if model_name not in loaded_models:
                        loaded_models.append(model_name)
                        #sayw(module_path)
                        #make_unicode(module_path)
                        #module_path_n = re.sub("/", "\\\\", module_path)
                        #sayerr(module_path_n)
                        #ImportGui.insert(module_path_n,FreeCAD.ActiveDocument.Name)
                        try: #tobefixed HERE
                            # support for stpZ files
                            if module_path.lower().endswith('stpz'):
                                import stepZ
                                stepZ.insert(module_path,FreeCAD.ActiveDocument.Name)
                            elif module_path.lower().endswith('iges') or module_path.lower().endswith('igs'):
                                sayerr("bug for ImportGui *.iges ... using Part.insert")
                                Part.insert(module_path,FreeCAD.ActiveDocument.Name)
                            else:
                                ImportGui.insert(module_path,FreeCAD.ActiveDocument.Name)
                                # on FC0.20+ there is an issue in inserting a 'compound'
                                # FreeCAD.ActiveDocument.ActiveObject.recompute(True)
                                # say('model imported w ImportGui')
                            #FreeCADGui.Selection.clearSelection()
                            imported_obj_list = []
                            counterTmp=0
                            for ObJ in doc1.Objects:
                                counterTmp+=1#stop
                            mp_found=False
                            if counterTmp!=counterObj+1:
                                #multipart loaded
                                #print ('allow_compound ',allow_compound)
                                FreeCADGui.Selection.clearSelection()
                                mp_found=True
                                #if allow_compound != 'False' and allow_compound != 'Hierarchy':
                                if allow_compound != 'False' and (allow_compound != 'Hierarchy' or not Links_available):
                                    create_compound(counterObj,model_name)
                                    myStep = FreeCAD.ActiveDocument.ActiveObject
                                    impLabel = myStep.Label
                                elif allow_compound == 'Hierarchy' and Links_available:
                                    imported_obj_list = doc1.Objects[counterObj+1:]
                                    compound_found=True
                                    #say(str(doc1.Objects)+' HERE')
                                    #sayw(str(imported_obj_list)+' HERE')
                                    newStep = find_top_container(imported_obj_list)
                                    if newStep is not None:
                                        impLabel = make_string(newStep.Label)
                                    else: #old format import multi objs without a Part container
                                        actObjs = doc1.Objects
                                        actObjNum = len (actObjs)
                                        newStep = doc1.addObject('App::Part',model_name)
                                        impLabel = make_string(newStep.Label)
                                        for o in actObjs[counterObj:]:
                                            doc1.getObject(newStep.Name).addObject(doc1.getObject(o.Name))
                                            #print(o.Label)
                            #myStep = FreeCAD.ActiveDocument.ActiveObject
                            #print(myStep.Label)
                            #impLabel = myStep.Label
                            if (allow_compound != 'Hierarchy' or not Links_available) or not mp_found :
                                newStep=reset_prop_shapes(FreeCAD.ActiveDocument.ActiveObject,FreeCAD.ActiveDocument, FreeCAD,FreeCADGui,True)
                                myStep=newStep
                                if wrl_model != '':
                                    wrl_module_path = module_path[:module_path.rfind(u'.')]+wrl_model[-4:]
                                    step_transparency = check_wrl_transparency(wrl_module_path)
                                    if step_transparency != 0: #keeping transparency if found in step file
                                        FreeCADGui.ActiveDocument.getObject(myStep.Name).Transparency = step_transparency
                                impLabel = make_string(myStep.Label)
                            #use_pypro=False
                            if use_pypro:  #use python property for timestamp
                                myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","model3D")
                                myObj.ViewObject.Proxy = 0 # this is mandatory unless we code the ViewProvider too
                                myObj.Shape = newStep.Shape
                                newStep.Label = 'old'
                                #myObj.Label = impLabel
                                #print(modules[i][10]);print(modules[i][11])
                                myObj.addProperty("App::PropertyString","TimeStamp")
                                myObj.TimeStamp=str(modules[i][10])
                                myObj.addProperty("App::PropertyString","Reference")
                                myObj.Reference=str(modules[i][11])
                                if '*' not in myObj.Reference:
                                    myObj.Label = myObj.Reference + '_'+ impLabel
                                else:
                                    myObj.Label = 'REF_'+impLabel + '_'
                                FreeCADGui.ActiveDocument.ActiveObject.ShapeColor=FreeCADGui.ActiveDocument.getObject(newStep.Name).ShapeColor
                                FreeCADGui.ActiveDocument.ActiveObject.LineColor=FreeCADGui.ActiveDocument.getObject(newStep.Name).LineColor
                                FreeCADGui.ActiveDocument.ActiveObject.PointColor=FreeCADGui.ActiveDocument.getObject(newStep.Name).PointColor
                                FreeCADGui.ActiveDocument.ActiveObject.DiffuseColor=FreeCADGui.ActiveDocument.getObject(newStep.Name).DiffuseColor
                                FreeCADGui.ActiveDocument.ActiveObject.Transparency=FreeCADGui.ActiveDocument.getObject(newStep.Name).Transparency
                                FreeCAD.ActiveDocument.removeObject(newStep.Name)
                            else: #use Label for timestamp
                                myReference=str(modules[i][11]).rstrip('"').lstrip('"')
                                myValue=str(modules[i][14]).rstrip('"').lstrip('"')
                                myDescr=str(modules[i][15]).rstrip('"').lstrip('"')
                                myTimeStamp=str(modules[i][10]).rstrip('"').lstrip('"')
                                if len(myTimeStamp)> 8:
                                    myTimeStamp=myTimeStamp[-12:]
                                myModelNbr=(modules[i][12])
                                #print (myModelNbr)#;stop
                                if myModelNbr == 1:
                                    myModelNbr = ''
                                else:
                                    myModelNbr = '['+str(myModelNbr)+']'
                                if '*' not in myReference:
                                    newStep.Label = myReference + myTimeStamp + myModelNbr
                                    newStep.Label2 = myDescr
                                else:
                                    newStep.Label = 'REF_'+impLabel + '_'  + myTimeStamp + myModelNbr
                                #stop
                            #sayerr('loading first time!!!')
                            counterTmp=0
                            for ObJ in doc1.Objects:
                                counterTmp+=1#stop
                            #sayw(str(counterObj)+":"+str(counterTmp))
                            #stop
                            if counterTmp==counterObj:
                                #bug in ImportGui.insert iges file
                                sayerr("bug for ImportGui *.iges ... using Part.insert")
                                Part.insert(module_path,FreeCAD.ActiveDocument.Name)
                            # s = Part.Shape()
                            # s.read(module_path)       # incoming file igs, stp, stl, brep NO colors!
                            # Part.show(s)
                            #Part.Shape.read(module_path)
                            #Part.insert(module_path,FreeCAD.ActiveDocument.Name)
                        except: #tobefixed
                            sayerr('3D STEP model '+model_name+' is WRONG')
                            msg="""3D STEP model <b><font color=red>"""
                            msg+=model_name+"</font> is WRONG</b><br>or are not allowed Multi Part objects...<br>"
                            msg+="@ "+module_path+" <br>...stopping execution! <br>Please <b>fix</b> the model or change your settings."
                            QtGui.QApplication.restoreOverrideCursor()
                            reply = QtGui.QMessageBox.information(None,"Info ...",msg)
                            stop   
                        if allow_compound != 'False' and (allow_compound != 'Hierarchy' or not Links_available):
                            create_compound(counterObj,model_name)
                            newobj = FreeCAD.ActiveDocument.ActiveObject
                            if not use_pypro:
                                if '*' not in myReference:
                                    newobj.Label = myReference + '_' + myTimeStamp + myModelNbr
                                    newobj.Label2 = myDescr
                                else:
                                    newobj.Label = 'REF_'+impLabel + '_'  + myTimeStamp + myModelNbr
                        ##addProperty mod
                        #newobj=reset_prop_shapes(FreeCAD.ActiveDocument.ActiveObject,FreeCAD.ActiveDocument, FreeCAD,FreeCADGui)
                        elif allow_compound == 'Hierarchy' and mp_found:
                            newobj = newStep
                            #tobefixed
                            if not use_pypro:
                                if '*' not in myReference:
                                    newobj.Label = myReference + '_' + myTimeStamp + myModelNbr
                                else:
                                    newobj.Label = 'REF_'+impLabel + '_'  + myTimeStamp + myModelNbr
                        else:
                            newobj = FreeCAD.ActiveDocument.ActiveObject                        ##addProperty mod
                        #newobj=reset_prop_shapes(FreeCAD.ActiveDocument.ActiveObject,FreeCAD.ActiveDocument, FreeCAD,FreeCADGui)
                        #newobj = FreeCAD.ActiveDocument.ActiveObject
                        #stop
                        ##newobj.Label=newobj.Label+"_"
                        # not adding '_' at the end of the name
                        if (bbox_all==1) or (bbox_list==1):
                            if whitelisted_model_elements.find(model_name) == -1:
                                bboxLabel=newobj.Label=newobj.Label
                                newobj=createSolidBBox3(newobj)
                        skip_status="not"
                        #tobefixed volume for App::Part
                        if model_name not in whitelisted_3Dmodels:
                            if volume_minimum != 0 or height_minimum != 0: #if checking volume or height
                                if newobj.Shape.Volume>volume_minimum:  #mauitemp min vol
                                    if abs(newobj.Shape.BoundBox.ZLength)>height_minimum:  #mauitemp min height
                                        if (height_minimum!=0):
                                            say("height > Min height "+ str(newobj.Shape.BoundBox.ZLength) + " "+newobj.Label)
                                        if (volume_minimum!=0):
                                            say("Volume > Min Volume "+ str(newobj.Shape.Volume) + " "+newobj.Label)
                                    else:
                                        skip_status="skip"
                                        say("height <= Min height "+ str(newobj.Shape.BoundBox.ZLength) + " "+newobj.Label)
                                else:
                                    skip_status="skip"
                                    say("Volume <= Min Volume "+ str(newobj.Shape.BoundBox.ZLength) + " "+newobj.Label)
                        loaded_models_skipped.append(skip_status)
                        use_cache=0
                        #say("NO use_cache")
                        FreeCADGui.Selection.clearSelection()
                        for ObJ in doc1.Objects:
                            counter+=1
                        if counterObj+1 != counter and (allow_compound != 'Hierarchy' or not Links_available):
                            msg="""3D STEP model <b><font color=red>"""
                            msg+=model_name+"</font> is NOT fused ('union') in a single part</b> ...<br>"
                            msg+="@ "+module_path+" <br>...stopping execution! <br>Please <b>fix</b> the model."
                            QtGui.QApplication.restoreOverrideCursor()
                            reply = QtGui.QMessageBox.information(None,"Info ...",msg)
                            stop
                        if skip_status!="skip":
                            loaded_model_objs.append(newobj)
                        else:
                            loaded_model_objs.append(None)
                            FreeCAD.activeDocument().removeObject(newobj.Name)
                    else:
                        use_cache=1
                        #sayw("using cache!!!")
                    #say(loaded_models);say(" models")
                    #say(str(len(loaded_model_objs))+" nbr loaded objs")
                    if use_cache:
                        counterObj=counterObj-2
                    pos_x=modules[i][1]-off_x
                    pos_y=modules[i][2]-off_y
                    rot=modules[i][3]
                    step_layer=modules[i][4]
                    #wrl_off_x=modules[i][6]
                    #rotz_vrml_norm=modules[i][7][0].replace("(xyz ","")
                    #rotz_vrml_norm=modules[i][7].replace("(xyz ","")
                    #say("rotz_vrml_norm ");sayw(rotz_vrml_norm)
                    wrl_rot=modules[i][7]
                    #sayerr(wrl_rot);sayw(float(wrl_rot[0]));stop
                    pos_vrml=modules[i][6]
                    wrl_pos=pos_vrml
                    #sayerr(wrl_pos);sayw(float(wrl_pos[0]));stop
                    isVirtual=modules[i][9]
                    isHidden=modules[i][13]
                    if (isHidden):
                        md_hide=True
                    else:
                        md_hide=False
                    
                    #if show_debug:
                    #    sayw(wrl_rot)
                    #    sayerr(modules[i])
                    #wrl_pos=pos_vrml[0].split(" ")
                    #wrl_pos=pos_vrml.split(" ")
                    #say(rotz_vrml_norm)
                    #sayw("wrl rot ");sayw(wrl_rot)
                    #say("wrl pos ");sayw(wrl_pos)                   
                    #say (str(rot))
                    for j in range(len(loaded_models)):
                        if loaded_models[j]==model_name:
                            #say (str(i)+" i")
                            idxO=j
                    if loaded_models_skipped[idxO]!="skip":
                        if use_cache:
                            #mod_cnt+=1
                            sayw('copying from cache')
                            ##impPart=copy_objs(loaded_model_objs[idxO],FreeCAD.ActiveDocument, FreeCAD,FreeCADGui)
                            ### FreeCAD.ActiveDocument.addObject('Part::Feature',loaded_model_objs[idxO].Label).Shape=loaded_model_objs[idxO].Shape
                            ### #FreeCAD.ActiveDocument.ActiveObject.Label=obj.Label
                            ### FreeCADGui.ActiveDocument.ActiveObject.ShapeColor=Gui.ActiveDocument.getObject(loaded_model_objs[idxO].Name).ShapeColor
                            ### FreeCADGui.ActiveDocument.ActiveObject.LineColor=Gui.ActiveDocument.getObject(loaded_model_objs[idxO].Name).LineColor
                            ### FreeCADGui.ActiveDocument.ActiveObject.PointColor=Gui.ActiveDocument.getObject(loaded_model_objs[idxO].Name).PointColor
                            ### FreeCADGui.ActiveDocument.ActiveObject.DiffuseColor=Gui.ActiveDocument.getObject(loaded_model_objs[idxO].Name).DiffuseColor
                            ### FreeCAD.ActiveDocument.recompute()
                            try: # Links ATM don't support added proprierties
                                if use_Links and links_imp_mode == 'links_allowed':
                                    o = loaded_model_objs[idxO]
                                    # FreeCAD.ActiveDocument.addObject('App::Link',o.Label+'_ln_').setLink(o)
                                    if use_pypro:
                                        FreeCAD.ActiveDocument.addObject('App::LinkPython',o.Label).setLink(o)
                                        FreeCAD.ActiveDocument.ActiveObject.addProperty("App::PropertyString","TimeStamp")
                                        #FreeCAD.ActiveDocument.ActiveObject.TimeStamp=str(modules[i][10])
                                        FreeCAD.ActiveDocument.ActiveObject.addProperty("App::PropertyString","Reference")
                                        #FreeCAD.ActiveDocument.ActiveObject.Reference=str(modules[i][11])
                                        FreeCAD.ActiveDocument.ActiveObject.ViewObject.Proxy = 0
                                    else:
                                        FreeCAD.ActiveDocument.addObject('App::Link',o.Label+'_ln_').setLink(o)
                                else:
                                    FreeCAD.ActiveDocument.copyObject(loaded_model_objs[idxO], True)
                                #allow_compound != 'Hierarchy':
                                impPart=FreeCAD.ActiveDocument.ActiveObject
                                if use_pypro:
                                    impPart.TimeStamp=str(modules[i][10])
                                    impPart.Reference=str(modules[i][11])
                                    if '*' not in impPart.Reference:
                                        impPart.Label = loaded_model_objs[idxO].Label[loaded_model_objs[idxO].Label.find('_')+1:]
                                        impPart.Label = impPart.Reference + '_' + impPart.Label # loaded_model_objs[idxO].Label
                                        #impPart.Label = impPart.Reference + '_'+ impLabel
                                    #say("FC 0.15 copy method for preserving color in fusion")
                                    else:
                                        impPart.Label = 'REF_'+loaded_model_objs[idxO].Label + '_' + myTimeStamp
                                else:
                                    myTimeStamp=str(modules[i][10]).rstrip('"').lstrip('"')
                                    if len(myTimeStamp)> 8:
                                        myTimeStamp=myTimeStamp[-12:]
                                    myReference=str(modules[i][11]).rstrip('"').lstrip('"')
                                    myValue=str(modules[i][14]).rstrip('"').lstrip('"')
                                    myDescr=str(modules[i][15]).rstrip('"').lstrip('"')
                                    myModelNbr=(modules[i][12])
                                    #print (myModelNbr);stop
                                    if myModelNbr == 1:
                                        myModelNbr = ''
                                    else:
                                        myModelNbr = '['+str(myModelNbr)+']'
                                    if '*' not in myReference:
                                        impPart.Label = myReference + '_' + myTimeStamp + myModelNbr
                                        impPart.Label2 = myDescr
                                        # loaded_model_objs[idxO].Label
                                    else:
                                        impPart.Label = 'REF_'+loaded_model_objs[idxO].Label[:loaded_model_objs[idxO].Label.rfind('_')] + '_'  + myTimeStamp + myModelNbr
                            except:
                                #impPart=copy_objs(loaded_model_objs[idxO],FreeCAD.ActiveDocument, FreeCAD,FreeCADGui)
                                impPart=copy_objs(loaded_model_objs[idxO],FreeCAD.ActiveDocument)
                                sayw("fusion color problem in FC earlier than 0.15\n")
                                pass
                            ##
                            #impPart=reset_prop_shapes2(impPart,FreeCAD.ActiveDocument, FreeCAD,FreeCADGui)
                            ##resetting placement properties
                            impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x,pos_y,-pcbThickness),FreeCAD.Rotation(FreeCAD.Vector(0,1,0),180))
                            #obj.Placement = impPart.Placement
                            if use_Links and links_imp_mode == 'links_allowed':
                                shape=Part.getShape(o)
                            else:
                                shape=impPart.Shape.copy()
                            shape.Placement=impPart.Placement;
                            shape.rotate((pos_x,pos_y,0),(0,0,1),rot)
                            impPart.Placement=shape.Placement
                            #impPart.Label = impPart.Label + '_ch_'
                            #sayerr('caching')
                        else:
                            impPart=loaded_model_objs[idxO]
                            #impPart.Label = impPart.Label + '_nc_'
                        ## say(loaded_model_objs)
                        say("module "+step_module)
                        #say("selection 3D model "+ impPart.Label)
                        #to verify!!!! next row
                        ##impPart=reset_prop_shapes(impPart,FreeCAD.ActiveDocument, FreeCAD,FreeCADGui)                        
                        model3D=impPart.Name
                        #say("impPart "+ impPart.Name)
                        obj = FreeCAD.ActiveDocument.getObject(model3D)
                        FreeCADGui.Selection.addSelection(obj)
                        obj=FreeCAD.ActiveDocument.ActiveObject
                        #volume_minimum=1
                        myPart=FreeCAD.ActiveDocument.getObject(obj.Name)   #mauitemp min vol
                        if md_hide:
                            myPart.ViewObject.Visibility=False
                            # myPart.ViewObject.Transparency=70
                            sayerr('hiding '+myPart.Label)
                            my_hide_list+=myPart.Label+'\r\n'
                        #else:
                        #    myPart.ViewObject.Transparency=0
                            # sayerr('hiding '+myPart.Label)
                        #sayw(obj.Label)
                        #sayw(step_layer);
                        #sayw(str(myPart.Shape.Volume))
                        #sayw(str(myPart.Shape.BoundBox.ZLength))
                        myReference=str(modules[i][11]).rstrip('"').lstrip('"')
                        if step_layer == 'Top':
                            if full_placement:
                                ## new placement wip
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0]),pos_y+float(wrl_pos[1]),0+float(wrl_pos[2])),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),rot))
                                #                                                                                                                                                         (yaw z, pitch y, roll x) 
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,0+float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2]),-float(wrl_rot[1]),-float(wrl_rot[0])))
                                ##impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,0+float(wrl_pos[2])*25.4),FreeCAD.Rotation(rot,-float(wrl_rot[1]),-float(wrl_rot[0]))) #rot is already rot fp -rot wrl
                                #say("rot z top ");sayw(wrl_rot);sayw(rot)
                                impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,0+float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2]),-float(wrl_rot[1]),-float(wrl_rot[0]))) #rot is already rot fp -rot wrl
                                if impPart.TypeId=='App::Link' or impPart.TypeId=='App::LinkPython':
                                    shape=Part.getShape(o)
                                elif impPart.TypeId=='App::Part': #tobefixed
                                    shape=Part.getShape(impPart)
                                else:
                                    shape=impPart.Shape.copy()
                                shape.Placement=impPart.Placement;
                                shape.rotate((pos_x,pos_y,0),(0,0,1),rot+float(wrl_rot[2]))
                                impPart.Placement=shape.Placement;
                                ##TBChecked
                                if force_transparency:
                                    FreeCADGui.ActiveDocument.ActiveObject.Transparency=70
                                ##TBChecked
                            else:
                                impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x,pos_y,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),rot))
                            FreeCADGui.Selection.addSelection(impPart)
                            ## to evaluate to add App::Part hierarchy
                            # App.activeDocument().Tip = App.activeDocument().addObject('App::Part','Part')
                            # App.activeDocument().Part.Label = 'Part'
                            # Gui.activeView().setActiveObject('part', App.activeDocument().Part)
                            # App.ActiveDocument.recompute()
                            if isVirtual == 0:
                                if use_AppPart and not use_LinkGroups: #layer Top    
                                    if impPart.TypeId != 'App::Part':
                                        part = FreeCAD.ActiveDocument.addObject('App::Part','Part')
                                        part.Label = myReference
                                        part.Label2 = impPart.Label2
                                        part.addObject(impPart)
                                        FreeCAD.ActiveDocument.getObject(board_name).addObject(part)
                                    else:
                                        impPart.Label = myReference
                                        FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                                    modelTop_nbr+=1
                                elif use_LinkGroups:
                                    #FreeCAD.ActiveDocument.getObject(impPart.Name).adjustRelativeLinks(FreeCAD.ActiveDocument.getObject('Top'))
                                    FreeCAD.ActiveDocument.getObject(board_name).ViewObject.dropObject(FreeCAD.ActiveDocument.getObject(impPart.Name),FreeCAD.ActiveDocument.getObject(impPart.Name),'',[])
                                    modelTop_nbr+=1
                                else:
                                    FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                            else:  #virtual
                                if use_AppPart and not use_LinkGroups: #layer Top                                  
                                    #print(topV_name)
                                    FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                                    virtualTop_nbr+=1
                                elif use_LinkGroups:
                                    #FreeCAD.ActiveDocument.getObject(impPart.Name).adjustRelativeLinks(FreeCAD.ActiveDocument.getObject('TopV'))
                                    FreeCAD.ActiveDocument.getObject(board_name).ViewObject.dropObject(FreeCAD.ActiveDocument.getObject(impPart.Name),FreeCAD.ActiveDocument.getObject(impPart.Name),'',[])
                                    virtualTop_nbr+=1
                                else:
                                    FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                                virtual_nbr+=1
                        ###
                        else:
                        #Bottom
                        #Bottom
                            #impPart=reset_prop_shapes2(impPart,FreeCAD.ActiveDocument, FreeCAD,FreeCADGui)
                            if full_placement:
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x,pos_y,-pcbThickness),FreeCAD.Rotation(FreeCAD.Vector(0,1,0),180))
                                ## new placement wip
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[1])*25.4,pos_y+float(wrl_pos[0])*25.4,-pcbThickness-float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2])-rot+180,-float(wrl_rot[1])+180,-float(wrl_rot[0])))
                                ##impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[1])*25.4,pos_y+float(wrl_pos[0])*25.4,-pcbThickness-float(wrl_pos[2])*25.4),FreeCAD.Rotation(-rot+180,-float(wrl_rot[1])+180,-float(wrl_rot[0])))  #rot is already rot fp -rot wrl
                                impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,+pcbThickness+float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2]),-float(wrl_rot[1]),-float(wrl_rot[0]))) #rot is already rot fp -rot wrl
                                if impPart.TypeId=='App::Link' or impPart.TypeId=='App::LinkPython':
                                    shape=Part.getShape(o)
                                else:
                                    shape=impPart.Shape.copy()
                                shape.Placement=impPart.Placement;
                                shape.rotate((pos_x,pos_y,0),(0,0,1),180+rot+float(wrl_rot[2]))
                                impPart.Placement=shape.Placement;
                                if impPart.TypeId=='App::Link' or impPart.TypeId=='App::LinkPython':
                                    shape=Part.getShape(o)
                                else:
                                    shape=impPart.Shape.copy()
                                shape.Placement=impPart.Placement;
                                shape.rotate((pos_x,pos_y,0),(0,1,0),180)
                                impPart.Placement=shape.Placement;
                                if force_transparency:
                                    FreeCADGui.ActiveDocument.ActiveObject.Transparency=60
                                #say("rot z bot ");sayw(wrl_rot);sayw(rot)
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,-pcbThickness+float(wrl_pos[2])*25.4),FreeCAD.Rotation(FreeCAD.Vector(0,1,0),180))
                            else:
                                impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x,pos_y,-pcbThickness),FreeCAD.Rotation(FreeCAD.Vector(0,1,0),180))
                            #obj.Placement = impPart.Placement
                                if impPart.TypeId=='App::Link' or impPart.TypeId=='App::LinkPython':
                                    shape=Part.getShape(o)
                                else:
                                    shape=impPart.Shape.copy()
                                shape.Placement=impPart.Placement;
                            #if not full_placement:
                                #shape.rotate((pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,-pcbThickness+float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2]),-float(wrl_rot[1])+180,-float(wrl_rot[0])))
                            #else:
                                shape.rotate((pos_x,pos_y,-pcbThickness),(0,0,1),-rot+180)
                                impPart.Placement=shape.Placement
                            FreeCADGui.Selection.addSelection(impPart)
                            FreeCAD.ActiveDocument.getObject(impPart.Name)
                            if isVirtual == 0:
                                if use_AppPart and not use_LinkGroups: #layer Top                                  
                                    if impPart.TypeId != 'App::Part':
                                        part = FreeCAD.ActiveDocument.addObject('App::Part','Part')
                                        part.Label = myReference
                                        part.Label2 = impPart.Label2
                                        part.addObject(impPart)
                                        FreeCAD.ActiveDocument.getObject(board_name).addObject(part)
                                    else:
                                        impPart.Label = myReference
                                        FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                                    modelBot_nbr+=1
                                elif use_LinkGroups:
                                    #FreeCAD.ActiveDocument.getObject(impPart.Name).adjustRelativeLinks(FreeCAD.ActiveDocument.getObject('Bot'))
                                    FreeCAD.ActiveDocument.getObject(board_name).ViewObject.dropObject(FreeCAD.ActiveDocument.getObject(impPart.Name),FreeCAD.ActiveDocument.getObject(impPart.Name),'',[])
                                    modelBot_nbr+=1
                                else:
                                    FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                            else:  #virtual
                                if use_AppPart and not use_LinkGroups: #layer Top
                                    FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                                    virtualBot_nbr+=1
                                elif use_LinkGroups:
                                    #FreeCAD.ActiveDocument.getObject(impPart.Name).adjustRelativeLinks(FreeCAD.ActiveDocument.getObject('BotV'))
                                    FreeCAD.ActiveDocument.getObject(board_name).ViewObject.dropObject(FreeCAD.ActiveDocument.getObject(impPart.Name),FreeCAD.ActiveDocument.getObject(impPart.Name),'',[])
                                    virtualBot_nbr+=1
                                else:
                                    FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                                virtual_nbr+=1
                ###
                elif module_path=='internal shape':
                    impPart=FreeCAD.ActiveDocument.ActiveObject
                    scale_vrml=modules[i][8]
                    #sayw(scale_vrml)
                    #scale_val=scale_vrml.split(" ")
                    scale_val=scale_vrml
                    #sayw(scale_val)
                    pos_x=modules[i][1]-off_x
                    pos_y=modules[i][2]-off_y
                    rot=modules[i][3]
                    wrl_rot=modules[i][7]
                    step_layer=modules[i][4]
                    #wrl_off_x=modules[i][6]
                    #rotz_vrml_norm=modules[i][7][0].replace("(xyz ","")
                    #rotz_vrml_norm=modules[i][7].replace("(xyz ","")
                    #say("rotz_vrml_norm ");sayw(rotz_vrml_norm)
                    #wrl_rot=rotz_vrml_norm.split(" ")
                    pos_vrml=modules[i][6]
                    wrl_pos=pos_vrml
                    #wrl_pos=pos_vrml[0].split(" ")
                    #wrl_pos=pos_vrml.split(" ")
                    #say(rotz_vrml_norm)
                    #sayw("wrl rot ");sayw(wrl_rot)
                    #say("wrl pos ");sayw(wrl_pos)
                    shape_vol=abs(float(scale_val[0])*float(scale_val[1])*float(scale_val[2]))
                    skip_status="not"
                    if shape_vol>volume_minimum:  #mauitemp min vol
                        if abs(float(scale_val[2]))>height_minimum:  #mauitemp min height
                            if (height_minimum!=0):
                                say("height > Min height "+ str(scale_val[2]) + " "+impPart.Label)
                            if (volume_minimum!=0):
                                say("Volume > Min Volume "+ str(shape_vol) + " "+impPart.Label)
                        else:
                            skip_status="skip"
                            say("height <= Min height "+ str(scale_val[2]) + " "+impPart.Label)
                    else:
                        skip_status="skip"
                        say("Volume <= Min Volume "+ str(shape_vol) + " "+impPart.Label)
                    if skip_status=="not":
                        if step_layer == 'Top':
                            if full_placement:
                                ## new placement wip
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0]),pos_y+float(wrl_pos[1]),0+float(wrl_pos[2])),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),rot))
                                #                                                                                                                                                         (yaw z, pitch y, roll x) 
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,0+float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2]),-float(wrl_rot[1]),-float(wrl_rot[0])))
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,0+float(wrl_pos[2])*25.4),FreeCAD.Rotation(rot,-float(wrl_rot[1]),-float(wrl_rot[0]))) #rot is already rot fp -rot wrl
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,0+float(wrl_pos[2])*25.4),FreeCAD.Rotation(rot,-float(wrl_rot[1]),-float(wrl_rot[0]))) #rot is already rot fp -rot wrl
                                impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,0+float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2]),-float(wrl_rot[1]),-float(wrl_rot[0]))) #rot is already rot fp -rot wrl
                                shape=impPart.Shape.copy()
                                shape.Placement=impPart.Placement;
                                shape.rotate((pos_x,pos_y,0),(0,0,1),rot+float(wrl_rot[2]))
                                impPart.Placement=shape.Placement;
                                if force_transparency:
                                    FreeCADGui.ActiveDocument.ActiveObject.Transparency=100
                                ##TBChecked shapes
                                #say("rot z top ");sayw(wrl_rot);sayw(rot)
                            else:
                                impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x,pos_y,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),rot))
                            FreeCADGui.Selection.addSelection(impPart)
                            if use_AppPart: #Top
                                FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                                modelTop_nbr+=1
                            else:
                                FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                        else:
                        #Bottom
                        #Bottom
                            #impPart=reset_prop_shapes2(impPart,FreeCAD.ActiveDocument, FreeCAD,FreeCADGui)
                            if full_placement:
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x,pos_y,-pcbThickness),FreeCAD.Rotation(FreeCAD.Vector(0,1,0),180))
                                ## new placement wip
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[1])*25.4,pos_y+float(wrl_pos[0])*25.4,-pcbThickness-float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2])-rot+180,-float(wrl_rot[1])+180,-float(wrl_rot[0])))
                                # impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[1])*25.4,pos_y+float(wrl_pos[0])*25.4,-pcbThickness),FreeCAD.Rotation(-float(wrl_rot[2])+180,-float(wrl_rot[1])+180,-float(wrl_rot[0])))  #rot is already rot fp -rot wrl
                                # #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[1])*25.4,pos_y+float(wrl_pos[0])*25.4,-pcbThickness-float(wrl_pos[2])*25.4),FreeCAD.Rotation(float(wrl_rot[2]),-float(wrl_rot[1]),-float(wrl_rot[0]))) #rot is already rot fp -rot wrl
                                # shape=impPart.Shape.copy()
                                # shape.Placement=impPart.Placement;
                                # shape.rotate((pos_x+float(wrl_pos[1])*25.4,pos_y+float(wrl_pos[0])*25.4,-pcbThickness-float(wrl_pos[2])*25.4),(0,0,1),-180+rot-float(wrl_rot[2]))
                                # impPart.Placement=shape.Placement;
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[1])*25.4,pos_y+float(wrl_pos[0])*25.4,-pcbThickness-float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2])-rot+180,-float(wrl_rot[1])+180,-float(wrl_rot[0])))
                                impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,+pcbThickness+float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2]),-float(wrl_rot[1]),-float(wrl_rot[0]))) #rot is already rot fp -rot wrl
                                shape=impPart.Shape.copy()
                                shape.Placement=impPart.Placement;
                                shape.rotate((pos_x,pos_y,0),(0,0,1),180+rot+float(wrl_rot[2]))
                                impPart.Placement=shape.Placement;
                                shape=impPart.Shape.copy()
                                shape.Placement=impPart.Placement;
                                shape.rotate((pos_x,pos_y,0),(0,1,0),180)
                                impPart.Placement=shape.Placement;
                                if force_transparency:
                                    FreeCADGui.ActiveDocument.ActiveObject.Transparency=60
                                ##TBChecked shapes
                                #say("rot z bot ");sayw(wrl_rot);sayw(rot)
                                #impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,-pcbThickness+float(wrl_pos[2])*25.4),FreeCAD.Rotation(FreeCAD.Vector(0,1,0),180))
                            else:
                                impPart.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_x,pos_y,-pcbThickness),FreeCAD.Rotation(FreeCAD.Vector(0,1,0),180))
                            #obj.Placement = impPart.Placement
                                shape=impPart.Shape.copy()
                                shape.Placement=impPart.Placement;
                            #if not full_placement:
                                #shape.rotate((pos_x+float(wrl_pos[0])*25.4,pos_y+float(wrl_pos[1])*25.4,-pcbThickness+float(wrl_pos[2])*25.4),FreeCAD.Rotation(-float(wrl_rot[2]),-float(wrl_rot[1])+180,-float(wrl_rot[0])))
                            #else:
                                shape.rotate((pos_x,pos_y,-pcbThickness),(0,0,1),-rot+180)
                                impPart.Placement=shape.Placement
                            FreeCADGui.Selection.addSelection(impPart)
                            FreeCAD.ActiveDocument.getObject(impPart.Name)
                            if use_AppPart: #Bot
                                FreeCAD.ActiveDocument.getObject("Bot").addObject(impPart)
                                modelBot_nbr+=1
                            else:
                                FreeCAD.ActiveDocument.getObject(board_name).addObject(impPart)
                    else:                        
                        FreeCAD.ActiveDocument.removeObject(impPart.Name)
                else:
                    #say("error missing "+ make_string(models3D_prefix)+make_string(step_module))
                    say("error missing "+ make_string(module_container))
                    #test = missing_models.find(make_string(step_module))
                    test = missing_models.find(make_string(module_container))
                    if test == -1:
                        #missing_models += make_string(models3D_prefix)+make_string(step_module)+'\r\n' #matched        
                        # missing_models += make_string(step_module)+'\r\n' #matched  
                        missing_models += make_string(module_container)+' (.stp or .step)\r\n' #matched 
            ###
        gui_refresh=20
        if int(PySide.QtCore.qVersion().split('.')[0]) > 4 or use_Links:  # Qt5 or Links refresh
            if mod_cnt%gui_refresh == 0: # (one on 'gui_refresh' times)
                #FreeCADGui.updateGui()
                QtGui.QApplication.processEvents()
        ###
        sayw('added '+str(mod_cnt)+' model(s)')
        ###
    ###
    #say(loaded_models);
    #sleep
    if virtual_nbr==0:
        #FreeCAD.ActiveDocument.getObject("Step_Virtual_Models").removeObjectsFromDocument()
        # FreeCAD.ActiveDocument.removeObject(stepV_name)
        if use_AppPart:
            pass
            # FreeCAD.ActiveDocument.removeObject(botV_name)
            # FreeCAD.ActiveDocument.removeObject(topV_name)
    else:
        if use_AppPart:
            if virtualTop_nbr==0:
                pass
                #FreeCAD.ActiveDocument.getObject("TopV").removeObjectsFromDocument()
                # FreeCAD.ActiveDocument.removeObject(topV_name)
                #FreeCAD.ActiveDocument.recompute()
            if virtualBot_nbr==0:
                pass
                #FreeCAD.ActiveDocument.getObject("BotV").removeObjectsFromDocument()
                # FreeCAD.ActiveDocument.removeObject(botV_name)
                #FreeCAD.ActiveDocument.recompute()  
    if use_AppPart:
        if modelTop_nbr==0:
            pass
            #FreeCAD.ActiveDocument.getObject("Top").removeObjectsFromDocument()
            # FreeCAD.ActiveDocument.removeObject(top_name)    
        if modelBot_nbr==0:
            pass
            #FreeCAD.ActiveDocument.getObject("Bot").removeObjectsFromDocument()
            # FreeCAD.ActiveDocument.removeObject(bot_name)    
    
    FreeCAD.ActiveDocument.recompute()
    say_time()
    FreeCADGui.Selection.clearSelection()
    if 0: #try
        print('TreeView Test collapsing')
        FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Board)
        import kicadStepUpCMD
        FreeCADGui.runCommand('ksuToolsToggleTreeView',0)
        s=FreeCADGui.Selection.getSelection()[0]
        print(s.Label)
        FreeCADGui.runCommand('ksuToolsToggleTreeView',0)
        #kicadStepUpCMD.ksuToolsToggleTreeView.Activated(s)
        #FreeCADGui.Selection.clearSelection()
        #FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Board)
        #s=FreeCADGui.Selection.getSelection()[0]
        #print(s.Label)
        #kicadStepUpCMD.ksuToolsToggleTreeView.Activated(s)
        FreeCADGui.Selection.clearSelection()
    elif 0: #except:
        import expTree; 
        print('TreeView Test collapsing 2')
        #import importlib; importlib.reload(expTree);
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Board)
        expTree.collS_Tree()
        FreeCADGui.Selection.clearSelection()
        print('TreeView Test collapsing 2 step 2')
    else:
        pass
    #print (my_hide_list)
    if my_hide_list != "":
        n_rpt_max=10
        sayw(str(len(my_hide_list.split('\r\n'))-1)+" model[s] hidden")
        sayw(str(my_hide_list.split('\r\n')[:-1]))
        my_hide_res = []
        my_hide_res = my_hide_list.split('\r\n')
        wmsg="""... model[s] hidden<br>"""
        for i in range(min(len (my_hide_res),n_rpt_max)):
            wmsg=wmsg+my_hide_res[i]+'<br>'
        QtGui.QApplication.restoreOverrideCursor()
        reply = QtGui.QMessageBox.information(None,"Warning ...",wmsg+'<b><font color=blue>. . . '+str(len(my_hide_res)-1)+' model[s] hidden</font></b>' )
        
    if missing_models != '':
        last_pcb_path_local = re.sub("\\\\", "/", last_pcb_path)
        last_pcb_path_local_U = make_unicode(last_pcb_path_local)
        say("missing models");say (missing_models)
        say("searching path")
        for mpath in path_list:
            say(mpath)
        #say(models3D_prefix_U);say (models3D_prefix2_U)
        say(last_pcb_path_local_U)
        missings=[]
        missings=missing_models.split('\r\n')
        n_rpt_max=10
        #if len (missings) > n_rpt_max: #warning_nbr =-1 for skipping the test
        wmsg="""... missing module(s)<br>"""
        wmsg+="""... searching path:<br>"""
        for mpath in path_list:
            wmsg+=mpath+"""<br>"""
        #wmsg+=models3D_prefix_U+"""<br>"""
        #wmsg+=models3D_prefix2_U+"""<br>"""
        wmsg+=last_pcb_path_local_U+"""<br>"""
        wmsg+="""... missing module(s) '.step' or '.stp' or .iges' or '.igs'<br>"""
        for i in range(min(len (missings),n_rpt_max)):
            wmsg=wmsg+missings[i]+'<br>'
        QtGui.QApplication.restoreOverrideCursor()
        reply = QtGui.QMessageBox.information(None,"Error ...",wmsg+'<br><b>. . . missing '+str(len(missings)-1)+' model(s)</b>' )
        if len (missings) > warning_nbr and warning_nbr != -1: #warning_nbr =-1 for skipping the test
            QtGui.QApplication.restoreOverrideCursor()
            wmsg="""<font color=red>"""
            wmsg+="too many missing modules <b>["
            wmsg+=str(len (missings))+"]<br></b></font><font color=blue><b>Have you configured your KISYS3DMOD path<br>or 3d model prefix path?</font></b>"
            wmsg+="<br>StepUp configuration options are located in the preferences system of FreeCAD."
            wmsg+="<br></b></font><font color=blue><b>Are you on FC Snap or Flatpack?</b></font><br><i>You may need to \'bind mount\' your 3d models folder</i>"
            reply = QtGui.QMessageBox.information(None,"Error ...",wmsg)
    #if blacklisted_model_elements != '':
    #    FreeCAD.Console.PrintMessage("black-listed module "+ '\n'.join(map(str, blacklisted_models)))
    #    reply = QtGui.QMessageBox.information(None,"Info ...","... black-listed module(s)\n"+ '\n'.join(map(str, blacklisted_models)))
    #    #FreeCAD.Console.PrintMessage("black-listed module "+ '\n'.join(map(str, blacklisted_models)))
    return blacklisted_model_elements
###

def onLoadBoard(file_name=None,load_models=None,insert=None):
    #name=QtGui.QFileDialog.getOpenFileName(this,tr("Open Image"), "/home/jana", tr("Image Files (*.png *.jpg *.bmp)"))[0]
    #global module_3D_dir
    global test_flag, last_pcb_path, configParser, configFilePath, start_time
    global aux_orig, base_orig, base_point, idf_to_origin, off_x, off_y, export_board_2step
    global real_board_pos_x, real_board_pos_y, board_base_point_x, board_base_point_y
    global models3D_prefix, models3D_prefix2, models3D_prefix3, models3D_prefix4
    global blacklisted_model_elements, col, colr, colg, colb, whitelisted_3Dmodels
    global bbox, volume_minimum, height_minimum, idf_to_origin, aux_orig
    global base_orig, base_point, bbox_all, bbox_list, whitelisted_model_elements
    global fusion, addVirtual, blacklisted_models, exportFusing, min_drill_size
    global last_fp_path, last_pcb_path, plcmnt, xp, yp, exportFusing
    global ignore_utf8, ignore_utf8_incfg, pcb_path, disable_VBO, use_AppPart, force_oldGroups, use_Links, use_LinkGroups
    global original_filename, edge_width, load_sketch, grid_orig, warning_nbr, running_time, addConstraints
    global conv_offs, zfit, fname_sfx, missingHeight, restore_specular_cls, preset_light

    import fcad_parser
    from fcad_parser import KicadPCB,SexpList
    import kicad_parser
    objs_toberemoved = []
    ImportMode_status=0
    import_drawings = False
    objs_pre=[]
    doc=FreeCAD.ActiveDocument
    if doc is not None:
        objs_pre=doc.Objects
    
    if preset_light:
        check_lightDir(set_default=True)

    pull_sketch = False
    override_pcb = None
    keep_pcb_sketch = None
    SketchLayer = 'Edge.Cuts' #None
    if load_models is None:
        load_models = True
    if load_models == False:
        # layer_list = ['Edge.Cuts','Dwgs.User','Cmts.User','Eco1.User','Eco2.User','Margin']
        # layer_list = ['Edge.Cuts','Dwgs.User','Cmts.User','Eco1.User','Eco2.User','Margin', 'F.FillZone', 'F.KeepOutZone', 'F.MaskZone','B.FillZone', 'B.KeepOutZone', 'B.MaskZone',]
        layer_list = ['Edge.Cuts','Dwgs.User','Cmts.User','Eco1.User','Eco2.User','User.1','User.2','User.3','User.4','User.5','User.6','User.7','User.8','User.9','Margin', 'F.FillZone', 'F.KeepOutZone', 'F.MaskZone','B.FillZone', 'B.KeepOutZone', 'B.MaskZone',]
        LayerSelectionDlg = QtGui.QDialog()
        ui = Ui_LayerSelection()
        ui.setupUi(LayerSelectionDlg)
        ui.comboBoxLayerSel.addItems(layer_list)
        if 0:
            ui.comboBoxLayerSel.setEditable(True)
        ui.label.setText("Select the layer to pull into the Sketch\nDefault: \'Edge.Cuts\'")
        reply=LayerSelectionDlg.exec_()
        if reply==1: # ok
            SketchLayer=str(ui.comboBoxLayerSel.currentText())
            print(SketchLayer)
            if SketchLayer == 'Edge.Cuts':
                #override_pcb = ui.checkBox_replace.isChecked()
                if ui.radioBtn_replace_pcb.isChecked():
                    override_pcb = True
                elif ui.radioBtn_keep_sketch.isChecked(): #enabling keep sketch only if override is True 
                    override_pcb = True
                    keep_pcb_sketch = True
            else:
                if ui.radioBtn_replace_pcb.isChecked():
                    import_drawings = True
            pull_sketch = True
        else:
            print('Cancel')
    if pull_sketch or load_models:
        default_value='/'
        clear_console()
        #lastPcb_dir='C:/Cad/Progetti_K/ksu-test'
        #say(lastPcb_dir+' last Pcb dir')
        #print(make_string(last_pcb_path))
        #print (make_unicode(last_pcb_path))
        if not os.path.isdir(make_unicode(last_pcb_path)):
            last_pcb_path=u"./"
        #say(last_pcb_path)
        if file_name is not None:
            #export_board_2step=True #for cmd line force exporting to STEP
            name=file_name
        elif test_flag==False:
            Filter=""
            #minimize main window
            #self.setWindowState(QtCore.Qt.WindowMinimized)
            #infoDialog('ciao')
            #reply = QtGui.QInputDialog.getText(None, "Hello","Enter your thoughts for the day:")
            #if reply[1]:
            #        # user clicked OK
            #        replyText = reply[0]
            #else:
            #        # user clicked Cancel
            #        replyText = reply[0] # which will be "" if they clicked Cancel
            #restore main window
            #self.setWindowState(QtCore.Qt.WindowActive)
            prefs_ = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
            if not(prefs_.GetBool('not_native_dlg')):
                name, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open kicad PCB File...",
                    make_unicode(last_pcb_path), "*.kicad_pcb")
            else:
                name, Filter = PySide.QtGui.QFileDialog.getOpenFileName(None, "Open kicad PCB File...",
                    make_unicode(last_pcb_path), "*.kicad_pcb",options=QtWidgets.QFileDialog.DontUseNativeDialog)
        else:
            name="C:/Cad/Progetti_K/ksu-test/multidrill.kicad_pcb"
        if len(name) > 0:
            if os.path.isfile(name):
                original_filename=name
                say('opening '+name)
                path, fname = os.path.split(name)
                fname=os.path.splitext(fname)[0]
                fname_sfx=crc_gen(make_unicode(fname))
                top_name='Top'+fname_sfx
                bot_name='Bot'+fname_sfx
                topV_name='TopV'+fname_sfx
                botV_name='BotV'+fname_sfx
                stepM_name='Step_Models'+fname_sfx
                stepV_name='Step_Virtual_Models'+fname_sfx
                pcb_name='Pcb'+fname_sfx
                sketch_name_sfx = 'PCB_Sketch'+fname_sfx
                board_name='Board'+fname_sfx
                boardG_name='Board_Geoms'+fname_sfx
                LCS_name = 'Local_CS'+fname_sfx
                #say(fname_sfx)
                #fpth = os.path.dirname(os.path.abspath(__file__))
                fpth = os.path.dirname(os.path.abspath(name))
                #filePath = os.path.split(os.path.realpath(__file__))[0]
                say ('my file path '+fpth)
                if fpth == "":
                    fpth = u"."
                last_pcb_path = fpth
                #last_pcb_path=path
                pcb_path=fpth
                # update existing value
                #say(default_ksu_msg)
                #stop
                last_pcb_path = re.sub("\\\\", "/", last_pcb_path)
                #    configParser.write(configfile)
                ##stop utf-8 test
                ini_vars[10] = last_pcb_path
                #cfg_update_all()
                test_import = False
                if override_pcb == True:
                    insert=True
                if insert == True:
                    test_import = True
                if test_import:
                    doc=FreeCAD.ActiveDocument
                    if doc is None:
                        doc=FreeCAD.newDocument(fname)
                        override_pcb = False
                        try:
                            doc.removeObject(LCS_name)
                        except:
                            pass
                    elif override_pcb == True:
                        if doc.getObject(boardG_name) in doc.Objects: #if 1: #try:
                            if keep_pcb_sketch==True:
                                #doc.getObject(boardG_name).removeObject(doc.getObject(sketch_name_sfx)) #keep sketck & constrains
                                doc.getObject(boardG_name).ViewObject.dragObject(doc.getObject(sketch_name_sfx))
                                #objs_toberemoved.append([doc.getObject(sketch_name_sfx)])
                            removesubtree([doc.getObject(boardG_name)])
                            #objs_toberemoved.append([doc.getObject(boardG_name)])
                            #doc.recompute()
                            try:
                                doc.removeObject(LCS_name)
                            except:
                                pass
                            sayw('old Pcb removed')
                            #stop
                        else: #except:
                            override_pcb = False
                            say('Pcb not present')
                else:
                    if import_drawings and FreeCAD.ActiveDocument is not None:
                        doc=FreeCAD.ActiveDocument
                    else:
                        doc=FreeCAD.newDocument(fname)
                # doc.commitTransaction()
                doc.openTransaction('opening_kicad')
                say('opening Transaction \'opening_kicad\'')
                pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUp")
                pg.SetString("last_pcb_path", make_string(last_pcb_path)) # py3 .decode("utf-8")
                #pg.SetString("last_pcb_path", last_pcb_path.decode("utf-8"))
                modules=[]
                start_time=current_milli_time()
                #filename="C:/Cad/Progetti_K/D-can-term/can-term-test-fcad.kicad_pcb"
                #filename="c:\\Temp\\backpanel3.kicad_pcb"
                mypcb = KicadPCB.load(name) #test parser
                off_x=0; off_y=0  #offset of the board & modules
                grid_orig_warn=False
                aux_orig_warn=False
                if (grid_orig==1):
                    #xp=getAuxAxisOrigin()[0]; yp=-getAuxAxisOrigin()[1]  #offset of the board & modules
                    if hasattr(mypcb, 'setup'):
                        if hasattr(mypcb.setup, 'grid_origin'):
                            #say('aux_axis_origin' + str(mypcb.setup.aux_axis_origin))
                            xp=-mypcb.setup.grid_origin[0]; yp=mypcb.setup.grid_origin[1]
                            sayw('grid origin found @ ('+str(xp)+', '+str(yp)+')') 
                        else:
                            say('grid origin not set\nusing default top left corner')
                            xp=0;yp=0
                            grid_orig_warn=True
                    else:
                        say('grid origin not set\nusing default top left corner')
                        xp=0;yp=0
                        grid_orig_warn=True
                    ##off_x=-xp+xmin+(xMax-xmin)/2; off_y=-yp-(ymin+(yMax-ymin)/2)  #offset of the board & modules
                    #off_x=-xp+center_x;off_y=-yp+center_y
                    off_x=-xp;off_y=-yp
                if (aux_orig==1):
                    #xp=getAuxAxisOrigin()[0]; yp=-getAuxAxisOrigin()[1]  #offset of the board & modules
                    if hasattr(mypcb, 'setup'):
                        if hasattr(mypcb.setup, 'aux_axis_origin'):
                            #say('aux_axis_origin' + str(mypcb.setup.aux_axis_origin))
                            sayw('aux origin found @: '+str(mypcb.setup.aux_axis_origin)) 
                            xp=-mypcb.setup.aux_axis_origin[0]; yp=mypcb.setup.aux_axis_origin[1]
                        else:
                            aux_orig_warn=True
                            say('aux origin not set') 
                            xp=-148.5;yp=98.5
                    else:
                        aux_orig_warn=True
                        say('aux origin not set') 
                        xp=-148.5;yp=98.5
                    ##off_x=-xp+xmin+(xMax-xmin)/2; off_y=-yp-(ymin+(yMax-ymin)/2)  #offset of the board & modules
                    #off_x=-xp+center_x;off_y=-yp+center_y
                    off_x=-xp;off_y=-yp
                #if (aux_orig==1):
                #    #xp=getAuxAxisOrigin()[0]; yp=-getAuxAxisOrigin()[1]  #offset of the board & modules
                #    if hasattr(mypcb.setup, 'aux_axis_origin'):
                #        #say('aux_axis_origin' + str(mypcb.setup.aux_axis_origin))
                #        xp=mypcb.setup.aux_axis_origin[0]; yp=-mypcb.setup.aux_axis_origin[1]
                #    else:
                #        say('aux origin not used') 
                #    ##off_x=-xp+xmin+(xMax-xmin)/2; off_y=-yp-(ymin+(yMax-ymin)/2)  #offset of the board & modules
                #    off_x=-xp+center_x;off_y=-yp+center_y
                #    #off_x=-xp;off_y=-yp
                modules,nsk = DrawPCB(mypcb,SketchLayer,override_pcb,keep_pcb_sketch)
                if override_pcb == True:
                    if use_AppPart and not force_oldGroups and not use_LinkGroups:
                        doc.getObject(board_name).addObject(doc.getObject(boardG_name))
                    elif use_LinkGroups:
                        doc.getObject(board_name).ViewObject.dropObject(doc.getObject(boardG_name),doc.getObject(boardG_name),'',[])
                if SketchLayer == 'Edge.Cuts':
                    FreeCAD.ActiveDocument.getObject(board_name).Label = fname
                if hasattr(mypcb, 'general'):
                    pcbThickness=float(mypcb.general.thickness)
                else:
                    pcbThickness=1.6
                ## stop  #test parser
                check_requirements()
                #stop
                #pcbThickness,modules,board_elab,mod_lines,mod_arcs,mod_circles=LoadKicadBoard(name)
                #say(modules)
                #routineDrawPCB(pcbThickness,board_elab,mod_lines,mod_arcs,mod_circles)
                doc.commitTransaction()
                say('closing Transaction \'opening_kicad\'')
            else:
                say(name+' missing\r')
                stop
            ##Placing board at configured position
            # pos objs x,-y
            # pos board xm+(xM-xm)/2
            # pos board -(ym+(yM-ym)/2)        
            if SketchLayer == 'Edge.Cuts':
                #center_x, center_y, bb_x, bb_y = findPcbCenter("Pcb")
                center_x, center_y, bb_x, bb_y = findPcbCenter(u"Pcb"+fname_sfx)
            else:
                draw=FreeCAD.ActiveDocument.PCB_Sketch_draft
                center_x, center_y, bb_x, bb_y = findPcbCenter(draw.Name)
            ## using PcbCenter
            xMax=center_x+bb_x/2
            xmin=center_x-bb_x/2
            yMax=center_y+bb_y/2
            ymin=center_y-bb_y/2
            #off_x=0; off_y=0  #offset of the board & modules
            if hasattr(mypcb, 'setup'):
                if hasattr(mypcb.setup, 'edge_width'): #maui edge width
                    edge_width=mypcb.setup.edge_width
                elif hasattr(mypcb.setup, 'edge_cuts_line_width'): #maui edge cuts new width k 5.99
                    edge_width=mypcb.setup.edge_cuts_line_width
            #if (grid_orig==1):
            #    #xp=getAuxAxisOrigin()[0]; yp=-getAuxAxisOrigin()[1]  #offset of the board & modules
            #    if hasattr(mypcb.setup, 'grid_origin'):
            #        #say('aux_axis_origin' + str(mypcb.setup.aux_axis_origin))
            #        xp=-mypcb.setup.grid_origin[0]; yp=mypcb.setup.grid_origin[1]
            #    else:
            #        say('grid origin not found\nplacing at center of an A4')
            #        xp=-148.5;yp=98.5
            #    ##off_x=-xp+xmin+(xMax-xmin)/2; off_y=-yp-(ymin+(yMax-ymin)/2)  #offset of the board & modules
            #    #off_x=-xp+center_x;off_y=-yp+center_y
            #    off_x=-xp;off_y=-yp
            if (base_orig==1):
                ##off_x=xmin+(xMax-xmin)/2; off_y=-(ymin+(yMax-ymin)/2)  #offset of the board & modules
                off_x=center_x;off_y=center_y
            #sayw(base_point);sayw(" base point")
            if (base_point==1):
                ##off_x=-xp+xmin+(xMax-xmin)/2; off_y=-yp-(ymin+(yMax-ymin)/2)  #offset of the board & modules
                #off_x=-xp+center_x;off_y=-yp+center_y
                off_x=-xp+center_x;off_y=-yp+center_y
                #sayw(off_x)
            ## test maui board_base_point_x=(xMax-xmin)/2-off_x
            ## test maui board_base_point_y=-((yMax-ymin)/2)-off_y
            #real_board_pos_x=xmin+(xMax-xmin)/2
            #real_board_pos_y=-(ymin+(yMax-ymin)/2)
            ## using PcbCenter
            real_board_pos_x=center_x
            real_board_pos_y=center_y
            # doc = FreeCAD.ActiveDocument
            if idf_to_origin == True:
                board_base_point_x=-off_x
                board_base_point_y=-off_y
            else:
            ## using PcbCenter
                say ('using PcbCenter')
                #board_base_point_x=xmin+(xMax-xmin)/2-off_x
                #board_base_point_y=-(ymin+(yMax-ymin)/2)-off_y
                board_base_point_x=center_x-off_x
                board_base_point_y=center_y-off_y
            sayw('placing board @ '+str(board_base_point_x)+','+str(board_base_point_y))
            if SketchLayer == 'Edge.Cuts':
                #FreeCAD.ActiveDocument.getObject("Pcb").Placement = FreeCAD.Placement(FreeCAD.Vector(board_base_point_x,board_base_point_y,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
                FreeCAD.ActiveDocument.getObject(pcb_name).Placement = FreeCAD.Placement(FreeCAD.Vector(board_base_point_x,board_base_point_y,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
            #else:
            #    draw.Placement = FreeCAD.Placement(FreeCAD.Vector(board_base_point_x,board_base_point_y,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
            newname="PCB_Sketch"+fname_sfx
            if load_sketch:
                if SketchLayer != 'Edge.Cuts' and SketchLayer is not None:
                    newname = SketchLayer.split('.')[0]+'_Sketch'
                say_inline('building up pcb time')
                get_time()
                say(str(running_time))
                t1=(running_time)
                #add_constraints("PCB_Sketch_draft")
                #FreeCAD.ActiveDocument.recompute()
                if aux_orig==1 or grid_orig ==1:
                    s_name=cpy_sketch("PCB_Sketch_draft",newname)
                    FreeCAD.ActiveDocument.recompute()
                    #add_constraints(s_name)
                    #say_time()
                #stop
                elif (base_point==1):
                    s_name=shift_sketch("PCB_Sketch_draft", [-center_x,center_y],newname)
                    #stop
                    #add_constraints(s_name)
                    FreeCAD.ActiveDocument.getObject(s_name).Placement = FreeCAD.Placement(FreeCAD.Vector(xp,yp,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
                    #say_time()            
                elif (base_orig==1):
                    s_name=shift_sketch("PCB_Sketch_draft", [-center_x,center_y],newname)
                    #stop
                    #add_constraints(s_name)
                    FreeCAD.ActiveDocument.getObject(s_name).Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
                    #say_time()            
                else:
                    s_name=shift_sketch("PCB_Sketch_draft", [-center_x,center_y],newname)
                    #stop
                    #add_constraints(s_name)
                    #sayerr('usebasepoint')
                    #sayerr('usedefault')
                    FreeCAD.ActiveDocument.getObject(s_name).Placement = FreeCAD.Placement(FreeCAD.Vector(center_x,center_y,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
                    #stop
                    #say_time()
                # FreeCAD.ActiveDocument.removeObject("PCB_Sketch_draft")
                objs_toberemoved.append([FreeCAD.ActiveDocument.getObject("PCB_Sketch_draft")])
                if (zfit):
                    FreeCADGui.SendMsgToActiveView("ViewFit")
                if 0: # test_face # addConstraints!='none': 
                    say('start adding constraints to pcb sketch')
                    add_constraints(s_name)
                    get_time()
                    #say('adding constraints time ' +str(running_time-t1))
                    say('adding constraints time ' + "{0:.3f}".format(running_time-t1))
    
                ##FreeCAD.ActiveDocument.recompute()
                pcb_sk=FreeCAD.ActiveDocument.getObject(newname)
                gi = 0
                for g in pcb_sk.Geometry:
                    if 'BSplineCurve object' in str(g):
                        # say(str(g))
                        FreeCAD.ActiveDocument.getObject(newname).exposeInternalGeometry(gi)
                    gi+=1
                if use_LinkGroups and SketchLayer == 'Edge.Cuts':
                    FreeCAD.ActiveDocument.getObject(boardG_name).ViewObject.dropObject(FreeCAD.ActiveDocument.getObject(newname),FreeCAD.ActiveDocument.getObject(newname),'',[])
                    FreeCADGui.Selection.clearSelection()
                    sl = FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.getObject(newname))
                    #FreeCADGui.runCommand('Std_HideSelection',0)
                    FreeCADGui.runCommand('Std_ToggleVisibility',0)
                    FreeCADGui.Selection.clearSelection()
                    #FreeCADGui.ActiveDocument.PCB_Sketch.Visibility = False
                    #FreeCAD.ActiveDocument.getObject('PCB_Sketch').adjustRelativeLinks(FreeCAD.ActiveDocument.getObject('Board_Geoms'))
                elif SketchLayer == 'Edge.Cuts':
                    FreeCAD.ActiveDocument.getObject(boardG_name).addObject(pcb_sk)
                
            #updating pcb_sketch
            if SketchLayer != 'Edge.Cuts' and SketchLayer is not None:
                pcb_sk.Label = SketchLayer
                if nsk > 1:
                    pcb_sk.Label+="s"
                    pcb_sk.ViewObject.Visibility=False
            #FreeCAD.ActiveDocument.getObject("PCB_Sketch").Placement = FreeCAD.Placement(FreeCAD.Vector(board_base_point_x,board_base_point_y,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
            #FreeCAD.ActiveDocument.getObject("PCB_SketchN").Placement = FreeCAD.Placement(FreeCAD.Vector(board_base_point_x,board_base_point_y,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
            ## FreeCAD.ActiveDocument.getObject("Pcb").Placement = FreeCAD.Placement(FreeCAD.Vector(-off_x,-off_y,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
            if (zfit):
                FreeCADGui.SendMsgToActiveView("ViewFit")
            #ImportGui.insert(u"./c0603.step","demo_5D_vrml_from_step")
            if (not pt_lnx): # and (not pt_osx): issue on AppImages hanging on loading 
                FreeCADGui.SendMsgToActiveView("ViewFit")
            else:
                zf= Timer (0.1,ZoomFitThread)
                zf.start()
            if keep_pcb_sketch == True:
                #sayw(sketch_name_sfx+'001')
                if doc.getObject(sketch_name_sfx+'001') in doc.Objects: #if 1: #try:
                    doc.removeObject(sketch_name_sfx+'001') #keep sketck & constrains
                    #objs_toberemoved.append([doc.getObject(sketch_name_sfx+'001')])
                    docG = FreeCADGui.ActiveDocument
                    docG.getObject(sketch_name_sfx).Visibility=True
            elif override_pcb == True:
                if doc.getObject(sketch_name_sfx) in doc.Objects: #if 1: #try:
                    docG = FreeCADGui.ActiveDocument
                    docG.getObject(sketch_name_sfx).Visibility=True
            if not pull_sketch or load_models:
                if use_AppPart and not force_oldGroups and not use_LinkGroups:
                    #sayw("creating hierarchy")
                    ## to evaluate to add App::Part hierarchy
                    # doc.Tip = doc.addObject('App::Part',stepM_name)
                    # stepM = doc.ActiveObject
                    # stepM.Label = stepM_name
                    # doc.Tip = doc.addObject('App::Part',top_name)
                    # topG = doc.ActiveObject
                    # topG.Label = top_name
                    # doc.Tip = doc.addObject('App::Part',bot_name)
                    # botG = doc.ActiveObject
                    # botG.Label = bot_name
                    # doc.getObject(stepM_name).addObject(doc.getObject(top_name))
                    # doc.getObject(stepM_name).addObject(doc.getObject(bot_name))            
                    try:
                        pass
                        # doc.Step_Models.License = ''
                        # doc.Step_Models.LicenseURL = ''
                    except:
                        pass
                    #FreeCADGui.activeView().setActiveObject('Step_Models', doc.Step_Models)
                    # doc.getObject(board_name).addObject(doc.getObject(stepM_name))
                    # doc.Tip = doc.addObject('App::Part',stepV_name)
                    # stepV = doc.ActiveObject
                    # stepV.Label = stepV_name
                    # doc.Tip = doc.addObject('App::Part',topV_name)
                    # topV = doc.ActiveObject
                    # topV.Label = topV_name
                    # doc.Tip = doc.addObject('App::Part',botV_name)
                    # botV = doc.ActiveObject
                    # botV.Label = botV_name
                    # doc.getObject(stepV_name).addObject(doc.getObject(topV_name))
                    # doc.getObject(stepV_name).addObject(doc.getObject(botV_name))
                    try:
                        pass
                        # stepV.License = ''
                        # stepV.LicenseURL = ''
                    except:
                        pass
                    # FreeCADGui.activeView().setActiveObject(stepV_name, stepV)
                    # doc.getObject(board_name).addObject(doc.getObject(stepV_name))
                    doc.getObject(board_name).Label=fname
                    doc.getObject(boardG_name).Label = fname.replace('pcba', 'pcb')
                    doc.getObject(boardG_name).Label2 = 'PCB ' + doc.getObject(boardG_name).Label
                    try:
                        doc.getObject(board_name).License=''
                        doc.getObject(board_name).LicenseURL=''
                    except:
                        pass
                    ## end hierarchy
                elif use_LinkGroups:
                    # doc.Tip = doc.addObject('App::LinkGroup',stepM_name)
                    # stepM=doc.ActiveObject
                    # stepM.Label = stepM_name
                    # doc.Tip = doc.addObject('App::LinkGroup',stepV_name)
                    # stepV=doc.ActiveObject
                    # stepV.Label = stepV_name
                    # doc.addObject('App::LinkGroup',top_name)
                    # topG=doc.ActiveObject
                    # topG.Label = top_name
                    # doc.addObject('App::LinkGroup',bot_name)
                    # botG=doc.ActiveObject
                    # botG.Label = bot_name
                    # doc.addObject('App::LinkGroup',topV_name)
                    # topVG=doc.ActiveObject
                    # topVG.Label = topV_name
                    # doc.addObject('App::LinkGroup',botV_name)
                    # botVG=doc.ActiveObject
                    # botVG.Label = botV_name
                    #doc.getObject('Top').adjustRelativeLinks(doc.getObject('Step_Models'))
                    # doc.getObject(stepM_name).ViewObject.dropObject(doc.getObject(top_name),doc.getObject(top_name),'',[])
                    #doc.getObject('TopV').adjustRelativeLinks(doc.getObject('Step_Virtual_Models'))
                    # doc.getObject(stepV_name).ViewObject.dropObject(doc.getObject(topV_name),doc.getObject(topV_name),'',[])
                    #doc.getObject('Bot').adjustRelativeLinks(doc.getObject('Step_Models'))
                    # doc.getObject(stepM_name).ViewObject.dropObject(doc.getObject(bot_name),doc.getObject(bot_name),'',[])
                    #doc.getObject('BotV').adjustRelativeLinks(doc.getObject('Step_Virtual_Models'))
                    # doc.getObject(stepV_name).ViewObject.dropObject(doc.getObject(botV_name),doc.getObject(botV_name),'',[])
                    #doc.getObject('Step_Models').adjustRelativeLinks(doc.getObject('Board'))
                    # doc.getObject(board_name).ViewObject.dropObject(doc.getObject(stepM_name),doc.getObject(stepM_name),'',[])
                    #doc.getObject('Step_Virtual_Models').adjustRelativeLinks(doc.getObject('Board'))
                    # doc.getObject(board_name).ViewObject.dropObject(doc.getObject(stepV_name),doc.getObject(stepV_name),'',[])
                    FreeCADGui.Selection.clearSelection()
                else:
                    pass
                    #sayerr("creating flat groups")
                    # doc.addObject("App::DocumentObjectGroup", stepM_name)
                    # doc.addObject("App::DocumentObjectGroup", stepV_name)
                doc.recompute()
                say_time()
                if disable_VBO:
                    paramGetV = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View")
                    VBO_status=paramGetV.GetBool("UseVBO")
                    #sayerr("checking VBO")
                    say("VBO status "+str(VBO_status))
                    if VBO_status:
                        paramGetV.SetBool("UseVBO",False)
                        sayw("disabling VBO")
                    #stop
                #stop   
                if disable_PoM_Observer:
                    #paramGetPoM = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/PartOMagic")
                    #PoMObs_status=paramGetPoM.GetBool("EnableObserver")
                    PoMObs_status = False
                    if Observer.isRunning():
                        PoMObs_status=True
                    #if PoMObs_status:
                        Observer.stop()
                #    paramGetPoM.SetBool("EnableObserver",False)
                        sayw("disabling PoM Observer")
        
                prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import")
                ImportMode_status = 0
                if hasattr(prefs, 'GetInts'):
                    if len(prefs.GetInts()) > 0:
                        if prefs.GetInt('ImportMode') != 0:
                            ImportMode_status = prefs.GetInt('ImportMode')
                            prefs.SetInt('ImportMode', 0)
                            sayerr('STEP ImportMode NOT as \'Single document\''+'\n')
                ##ReadShapeCompoundMode
                paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
                ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
                #sayerr("checking ReadShapeCompoundMode")
                sayw("ReadShapeCompoundMode status "+str(ReadShapeCompoundMode_status))
                #FreeCAD.Console.PrintLog("ReadShapeCompoundMode status "+str(ReadShapeCompoundMode_status)+"\n")
                #stop
                enable_ReadShapeCompoundMode=False
                if ReadShapeCompoundMode_status and allow_compound=='True' \
                   or ReadShapeCompoundMode_status and allow_compound=='Hierarchy':
                    paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
                    paramGetVS.SetBool("ReadShapeCompoundMode",False)
                    sayw("disabling ReadShapeCompoundMode")
                    enable_ReadShapeCompoundMode=True
                elif not ReadShapeCompoundMode_status and allow_compound=='Simplified':
                    paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
                    paramGetVS.SetBool("ReadShapeCompoundMode",True)
                    sayw("enabling ReadShapeCompoundMode -> Simplified Mode")
                    enable_ReadShapeCompoundMode=True
                #paramGetVS.SetBool("ReadShapeCompoundMode",False)
                if load_sketch:
                    FreeCADGui.ActiveDocument.getObject(newname).Visibility=False # hidden Sketch
                ##Load 3D models
                #Load_models(pcbThickness,modules)
                if (zfit):
                    FreeCADGui.SendMsgToActiveView("ViewFit")
                #else:        
                Load_models(pcbThickness,modules)
        
                #enable_ReadShapeCompoundMode=False
                if enable_ReadShapeCompoundMode:
                    paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
                    paramGetVS.SetBool("ReadShapeCompoundMode",ReadShapeCompoundMode_status)
                    sayw("enabling ReadShapeCompoundMode")
                if disable_VBO:
                    if VBO_status:
                        paramGetV.SetBool("UseVBO",True)
                        sayw("enabling VBO")
                if disable_PoM_Observer:
                    if PoMObs_status:
                        Observer.start()
                #    paramGetPoM.SetBool("EnableObserver",True)
                        sayw("enabling PoM Observer")
                
                def find_nth(haystack, needle, n):
                    start = haystack.find(needle)
                    while start >= 0 and n > 1:
                        start = haystack.find(needle, start+len(needle))
                        n -= 1
                    return start
                
                msg=""
                n_rpt=0
                for mod3d in modules:
                    #say(mod3d)
                    #for e in mod3d:
                    #    print e #.decode("utf-8")
                    #if mod3d[5] is not None:
                    if mod3d[5] != "":
                        say(mod3d[0]);sayw(" error: reset"+mod3d[5])
                        #stop 
                        #msg+=""+mod3d[0].decode("utf-8")+" error: "+mod3d[5]+"<br>"
                        msg+=""+mod3d[0]+"<br>error: "+mod3d[5]+"<br>"
                        n_rpt=n_rpt+1
                n_rpt_max=10
                zf= Timer (0.3,ZoomFitThread)
                zf.start()
                if (show_messages==True) and msg!="":
                    msg="""<b>error in model(s)</b><br>"""+msg
                    QtGui.QApplication.restoreOverrideCursor()
                    #print n_rpt,'-',p_rpt
                    if n_rpt >  n_rpt_max:
                        p_rpt=find_nth(msg, '<br>', n_rpt_max)
                        #print n_rpt,'-',p_rpt
                        reply = QtGui.QMessageBox.information(None,"Info ...",msg[:p_rpt]+'<br><b> . . .</b>')
                    else:
                        reply = QtGui.QMessageBox.information(None,"Info ...",msg)
                
                #if 'LinkView' in dir(FreeCADGui):
                #    FreeCADGui.Selection.clearSelection()
                #    o=FreeCAD.ActiveDocument.getObject('Board')
                #    #FreeCADGui.Selection.addSelection('Board')
                #    FreeCADGui.Selection.addSelection(doc.Name,o.Name)
                #    #import expTree; #import importlib;importlib.reload(expTree)
                #    #print('collapsing selection')
                #    #expTree.collS_Tree() #toggle_Tree()
                #    clps = Timer (3,collaps_Tree)
                #    clps.start()
                if export_board_2step:
                    #say('aliveTrue')
                    Export2MCAD(blacklisted_model_elements)
                else:
                    #say('aliveFalse')
                    Display_info(blacklisted_model_elements)
                if (zfit):
                    FreeCADGui.SendMsgToActiveView("ViewFit")
            if restore_specular_cls:
                restore_specular(objs_pre)

            msg="running time: "+str(round(running_time,3))+"sec"    
            say(msg)
            zf= Timer (0.3,ZoomFitThread)
            zf.start()
            zf.cancel()
            if SketchLayer != 'Edge.Cuts' and SketchLayer is not None:
                FreeCADGui.ActiveDocument.ActiveView.viewTop()
            if grid_orig_warn: #adding a warning message because GridOrigin is set in FC Preferences but not set in KiCAD pcbnew file
                msg = 'GridOrigin is set in FC Preferences but not set in KiCAD pcbnew file'
                sayw(msg)
                QtGui.QApplication.restoreOverrideCursor()
                msg="""<b><font color='red'>GridOrigin is set in FreeCAD Preferences<br>but not set in KiCAD pcbnew file</font></b>"""
                msg+="""<br><br>Please assign Grid Origin to your KiCAD pcbnew board file"""
                msg+="""<br>for a better Mechanical integration"""
                reply = QtGui.QMessageBox.information(None,"Warning ...",msg)
            elif aux_orig_warn: #adding a warning message because AuxOrigin is set in FC Preferences but not set in KiCAD pcbnew file
                msg = 'AuxOrigin is set in FC Preferences but not set in KiCAD pcbnew file'
                sayw(msg)
                QtGui.QApplication.restoreOverrideCursor()
                msg="""<b><font color='red'>AuxOrigin is set in FreeCAD Preferences<br>but not set in KiCAD pcbnew file</font></b>"""
                msg+="""<br><br>Please assign Aux Origin to your KiCAD pcbnew board file"""
                msg+="""<br>for a better Mechanical integration"""
                reply = QtGui.QMessageBox.information(None,"Warning ...",msg)
            prefsKSU = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/kicadStepUpGui")
            prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import")
            paramGetVS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Import/hSTEP")
            ReadShapeCompoundMode_status=paramGetVS.GetBool("ReadShapeCompoundMode")
            if ImportMode_status != 0:
                prefs.SetInt('ImportMode',ImportMode_status)
            FCV_date = ''
            STEP_UseAppPart_available = False
            if len (FreeCAD.Version()) >= 5:
                FCV_date = str(FreeCAD.Version()[-3])
                FCV_date = FCV_date[0:FCV_date.find(' ')]
                say('FreeCAD version: '+FreeCAD.Version()[0]+'.'+FreeCAD.Version()[1])
                say('FreeCAD build date: '+FCV_date)
                if FCV_date >= '2020/06/27':
                    STEP_UseAppPart_available = True #new STEP import export mode available
                    say('STEP UseAppPart available')
            if hasattr(prefs, 'GetBools'):
                if (('UseAppPart' in prefs.GetBools() or 'UseLinkGroup' in prefs.GetBools()) and STEP_UseAppPart_available) or len (prefs.GetBools()) == 0:
                    if (not prefs.GetBool('UseAppPart') and not ('UseLinkGroup' in prefs.GetBools()))  or prefs.GetBool('UseLegacyImporter') or not prefs.GetBool('UseBaseName')\
                        or prefs.GetBool('ExportLegacy') or ReadShapeCompoundMode_status or prefs.GetBool('UseLinkGroup'): #  or ImportMode_status != 0:
                        msg = "Please set your preferences for STEP Import Export as in the displayed image\n"
                        msg += "(you can disable this warning on StepUp preferences)\n"
                        if 'help_warning_enabled' in prefsKSU.GetBools():
                            if prefsKSU.GetBool('help_warning_enabled'):
                                StepPrefsDlg = QtGui.QDialog()
                                ui = Ui_STEP_Preferences()
                                ui.setupUi(StepPrefsDlg)
                                reply=StepPrefsDlg.exec_()
                                sayw(msg)
                                #QtGui.QApplication.restoreOverrideCursor()
                                #reply = QtGui.QMessageBox.information(None,"Info ...",msg)
                        else: #first time new settings parameter
                            StepPrefsDlg = QtGui.QDialog()
                            ui = Ui_STEP_Preferences()
                            ui.setupUi(StepPrefsDlg)
                            reply=StepPrefsDlg.exec_()
                            sayw(msg)
            # TB reviewed
            #if 'LinkView' in dir(FreeCADGui):
            #    FreeCADGui.Selection.clearSelection()
            #    o=FreeCAD.ActiveDocument.getObject('Board')
            #    #FreeCADGui.Selection.addSelection('Board')
            #    FreeCADGui.Selection.addSelection(doc.Name,o.Name)
            #    #import expTree; #import importlib;importlib.reload(expTree)
            #    #print('collapsing selection')
            #    #expTree.collS_Tree() #toggle_Tree()
            #    clps = Timer (3,collaps_Tree)
            #    FreeCADGui.Selection.clearSelection()
            #    o=FreeCAD.ActiveDocument.getObject('Board')
            #    #FreeCADGui.Selection.addSelection('Board')
            #    FreeCADGui.Selection.addSelection(doc.Name,o.Name)
            #    #collaps_Tree()
            #    clps.start()
            
            #say_time()
            #stop
    def removing_kobjs():
        ''' removing objects after delay ''' 
        from kicadStepUptools import removesubtree
        doc=FreeCAD.ActiveDocument
        if doc is not None:
            doc.openTransaction('rmv_objs_kicad')
            for tbr in objs_toberemoved:
                removesubtree(tbr)
            doc.commitTransaction()
        # doc.undo()
        # doc.undo()
        # adding a timer to allow double transactions during the python code
    QtCore.QTimer.singleShot(0.2,removing_kobjs)
    if (zfit):
        FreeCADGui.SendMsgToActiveView("ViewFit")
    #ImportGui.insert(u"./c0603.step","demo_5D_vrml_from_step")
    if (not pt_lnx): # and (not pt_osx): issue on AppImages hanging on loading 
        FreeCADGui.SendMsgToActiveView("ViewFit")
    else:
        zf= Timer (0.25,ZoomFitThread)
        zf.start()

    """ mypcb = KicadPCB.load(file_pcb) """
    ## NB use always float() to guarantee number not string!!!
    import fcad_parser
    from fcad_parser import KicadPCB,SexpList
    import kicad_parser
    
    warn=""
    PCB_Models = []
    Edge_Cuts_lvl=44
    Top_lvl=0
    conv_offs=25.4
    if hasattr(mypcb, 'host'):
        print(mypcb.host)
    if hasattr(mypcb, 'version'):
        version = float(mypcb.version)
        if version <= 3:
            QtGui.QApplication.restoreOverrideCursor()
            reply = QtGui.QMessageBox.information(None,"Error ...","... KICAD pcb version "+ str(version)+" not supported \r\n"+"\r\nplease open and save your board with the latest kicad version")
            stop
        if version>=4:
            Edge_Cuts_lvl=44
            Top_lvl=0
        conv_offs=1.0
        if version >= 20171114:
            conv_offs=25.4
    
    for lynbr in mypcb.layers: #getting layers name
        if float(lynbr) == Top_lvl:
            LvlTopName=(mypcb.layers['{0}'.format(str(lynbr))][0])
        if float(lynbr) == Edge_Cuts_lvl:
            LvlEdgeName=(mypcb.layers['{0}'.format(str(lynbr))][0])

    for m in mypcb.module:  #parsing modules  #check top/bottom for placing 3D models
        #print(m.tstamp);print(m.fp_text[0][1])
        #stop
        if len(m.at)==2:
            m_angle=0
        else:
            m_angle=m.at[2]
        m_at=[m.at[0],-m.at[1]] #y reversed
        virtual=0
        if hasattr(m, 'attr'):
            if 'virtual' in m.attr:
                #say('virtual module')
                virtual=1
        else:
            virtual=0
        m_x = float(m.at[0])
        m_y = float(m.at[1]) * (-1)
        m_rot = float(m_angle)
        #sayw(m.layer);sayerr(LvlTopName)
        if m.layer == LvlTopName:  # top
            side = "Top"
            #sayw('top ' + m.layer)
        else:
            side = "Bottom"
            m_rot *= -1 ##bottom 3d model rotation
            #sayw('bot ' + m.layer)
        n_md=1
        for md in m.model:
            #say (md[0]) #model name
            #say(md.at.xyz)
            #say(md.scale.xyz)
            #say(md.rotate.xyz)
            error_scale_module=False
            #say('scale ');sayw(scale_vrml)#;
            #error_scale_module=False
            xsc_vrml_val=md.scale.xyz[0]
            ysc_vrml_val=md.scale.xyz[1]
            zsc_vrml_val=md.scale.xyz[2]        
            # if scale_vrml!='1 1 1':
            if float(xsc_vrml_val)!=1 or float(ysc_vrml_val)!=1 or float(zsc_vrml_val)!=1:
                if "box_mcad" not in md[0] and "cylV_mcad" not in md[0] and "cylH_mcad" not in md[0]:
                    sayw('wrong scale!!! set scale to (1 1 1)')
                error_scale_module=True
            #model_list.append(mdl_name[0])
            #model=model_list[j]+'.wrl'
            #if py2:
            if sys.version_info[0] == 2: #py2
                model=md[0].decode("utf-8")
                #stop
            else: #py3
                model=md[0] # py3 .decode("utf-8")
            #print (model, ' MODEL', type(model)) #maui test py3
            if (virtual==1 and addVirtual==0):
                model_name='no3Dmodel'
                side='noLayer'
                if model:
                    sayw("virtual model "+model+" skipped") #virtual found warning
            else:
                if model:
                    model_name=model
                    #sayw(model_name)
                    warn=""
                    if "box_mcad" not in model_name and "cylV_mcad" not in model_name and "cylH_mcad" not in model_name:
                        if error_scale_module:
                            sayw('wrong scale!!! for '+model_name+' Set scale to (1 1 1)')
                            msg="""<b>Error in '.kicad_pcb' model footprint</b><br>"""
                            msg+="<br>reset values of<br><b>"+model_name+"</b><br> to:<br>"
                            msg+="(scale (xyz 1 1 1))<br>"
                            #warn+=("reset values of scale to (xyz 1 1 1)")
                            warn=("reset values of scale to (xyz 1 1 1)")
                            ##reply = QtGui.QMessageBox.information(None,"info", msg)
                            #stop
                    #model_name=model_name[1:]
                    #say(model_name)
                    #sayw("here")
                else:
                    model_name='no3Dmodel'  #to do how to manage no3Dmodel
                    side='noLayer'
                    sayerr('no3Dmodel')
                mdl_name=model_name # re.findall(r'(.+?)\.wrl',params)
                #if virtual == 1:
                #    sayerr("virtual model(s)");sayw(mdl_name)
                # sayw(mdl_name)
                # sayerr(params)
                if len(mdl_name) > 0:
                    # model_name, rot_comb, warn, pos_vrml, rotz_vrml, scale_vrml = get3DParams(mdl_name,params, rot, virtual)
                    #sayerr(md.at.xyz)
                    if conv_offs != 1: #pcb version >= 20171114 (offset wrl in mm)
                        if hasattr(md,'at'):
                            ofs=[md.at.xyz[0]/conv_offs,md.at.xyz[1]/conv_offs,md.at.xyz[2]/conv_offs]
                        if hasattr(md,'offset'):
                            ofs=[md.offset.xyz[0]/conv_offs,md.offset.xyz[1]/conv_offs,md.offset.xyz[2]/conv_offs]
                    else:
                        ofs=md.at.xyz
                    line = []
                    line.append(model_name)
                    line.append(m_x)
                    line.append(m_y)
                    line.append(m_rot-md.rotate.xyz[2])
                    line.append(side)
                    line.append(warn)
                    line.append(ofs) #(md.at.xyz) #pos_vrml)
                    line.append(md.rotate.xyz) #rotz_vrml)
                    #sayerr(rotz_vrml)
                    line.append(md.scale.xyz) #scale_vrml)
                    line.append(virtual)
                    if hasattr(m,'tstamp'):
                        line.append(m.tstamp) # fp tstamp
                    elif hasattr(m,'uuid'):
                        line.append(m.uuid) # fp tstamp
                    else:
                        sayw('missing \'TimeStamp\'')
                        line.append('null')
                    try:
                        line.append(m.fp_text[0][1]) #fp reference
                    except:
                        line.append(m.property[0][1]) #fp reference kv8
                    line.append(n_md) #number of models in module
                    PCB_Models.append(line)
                    n_md+=1
    return PCB_Models

    # first call include '(gr_line' in line or '(gr_curve' in line or '(gr_arc' in line or '(gr_circle' in line or '(gr_rect' in line or '(gr_poly' in line:
    # offset,add_line = search_content(content,id,ssklayer)
    # check if the lines are inside a footprint... then they have to be skipped because they mixed fp_ and gr_ prefixes https://gitlab.com/kicad/code/kicad/-/issues/16660
    # kv8 Check if given Parentheses expression is balanced
    add_ln=True
    l=len(cnt)
    line = cnt[i]
    closed=False
    j=i
    found_tag=False
    open_p=0
    close_p=0
    ## if '(layer' in line and '))' in line: #kv5
    ##     if layer in line: #kv5
    ##         add_ln = False
    ##         i =j+1
    ##         closed=True
    ##     else:
    ##         add_ln = True
    ##         i =j+1
    ##         closed=True
    ##     return add_ln, i
    ## # here if not kv5
    while j < l and closed==False:  # kv6-kv8 Check if given Parentheses expression is balanced
        line_next=cnt[j]
        if '(gr_line' in line_next or '(gr_curve' in line_next or '(gr_arc' in line_next or '(gr_circle' in line_next or '(gr_rect' in line_next or '(gr_poly' in line_next:
            #starting group
            found_tag=True
            open_p+=line_next.count('(')
            close_p+=line_next.count(')')
            if '(layer' in line_next and layer in line_next:
                add_ln = False
            if open_p == close_p:
                #print (line_next + ' closed fp')
                return add_ln, j+1
            j+=1
        elif found_tag==True and closed==False:
            #line_next=cnt(j)
            open_p+=line_next.count('(')
            close_p+=line_next.count(')')
            if '(layer' in line_next and layer in line_next:
                add_ln = False
            if open_p == close_p:
                #print (line_next + ' closed fp')
                return add_ln, j+1
                #return j+1
            j+=1
    stop #we shouldn't arrive here
    # return j, add_ln