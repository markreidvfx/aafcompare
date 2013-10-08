import aaf
import xml.etree.cElementTree as ET

def aaf2xml(source, dest):

    f = aaf.open(source, 'r')
    f.save(dest)
    f.close()

def get_namespace(elem):
    if elem.tag[0] == "{":
        uri, ignore, tag = elem.tag[1:].partition("}")
    else:
        uri = None
        tag = elem.tag
    return uri

def strip_namespace(elem):
    namespace = get_namespace(elem)

    clean =  elem.tag.replace('{%s}' % namespace,'')

    return clean

class logger():
    
    def info(self,*args):
        pass
    def error(self,*args):
        
        strings = []
        for item in args:
            strings.append(str(item))
        print ' '.join(strings)
        
class AAF():

    def __init__(self,file_path):

        self.file_path = file_path

        self.logger = logger()


        self.Preface = None
        self.Extensions = None

        self.Packages = None

        #self.SourcePackages = []
        #self.MaterialPackages = []
        #self.CompositionPackage = []
        
        self.Sources = {}
        self.Materials = {}
        self.Compositions = {}

    def readFromFile(self):
        self.tree = ET.parse(self.file_path)

        self.root = self.tree.getroot()

        namespace = get_namespace(self.root)


        self.Preface =  self.root.find("{%s}Preface" % namespace)

        self.ContentStorageObject = self.Preface.find("{%s}ContentStorageObject" % namespace)
        self.ContentStorage = self.ContentStorageObject.find("{%s}ContentStorage" % namespace)

        self.Packages = self.ContentStorage.find("{%s}Packages" % namespace)
        
        
        for Package in self.Packages:
            
            name = strip_namespace(Package)            
            package_info = self.get_Package_info(Package)
            package_id = package_info['PackageID']
            #print name,package_id
            if name == 'SourcePackage':
                if self.Sources.has_key(package_id):
                    raise Exception()
                else:
                    self.Sources[package_id] = package_info
                    
            elif name == 'MaterialPackage':
                if self.Materials.has_key(package_id):
                    raise Exception()
                else:
                    self.Materials[package_id] = package_info
            elif name == 'CompositionPackage':
                
                if self.Compositions.has_key(package_id):
                    raise Exception()
                else:
                    self.Compositions[package_id] = package_info
                    
            else:
                print name
                raise Exception()
                
                
        self.sort_Main_Sequence()
        
        
        self.find_footage_in_seq()
        self.sort_Sources()
        
        self.sort_more()
    
        
        
    def sort_Main_Sequence(self):
        self.Sequences = []
        self.subClips = {}
        for item,value in self.Compositions.items():
            
            if value.has_key('PackageUsage'):
                PackageUsage = value['PackageUsage']
                
                #print value
                if PackageUsage == 'Usage_TopLevel':
                    self.Sequences.append(value)
                    
                elif PackageUsage == 'Usage_SubClip':
                    
                    self.subClips[value['PackageID']] = value
                    
                    #pprint(value)
                    #self.subClips[]
                    
                    pass
                    #print value['PackageName']
                    
                elif PackageUsage == 'Usage_LowerLevel':
                    pass
                    #print '**',value['PackageName']
                    
                else:
                    pass
                    #print PackageUsage
                    #print value['PackageUsage']
                    
        
        self.Main_Sequence = self.Sequences[0]
        
        timelines = []
        
        self.video_tracks = []
        self.audio_tracks = []
        
        video_timelines = []
        audio_timelines = []
        timecode_timelines = []
        other_timelines = []
        
        for PackageTrack in self.Main_Sequence['PackageTracks']:
            if PackageTrack['type'] == 'TimelineTrack':
                timelines.append(PackageTrack)
                
        for timeline in timelines:
            ComponentDataDefinition = timeline['TrackSegment']['ComponentDataDefinition']
            
            if ComponentDataDefinition in ['DataDef_LegacyTimecode','DataDef_Timecode']:
                #if timeline['type'] == 'Timecode':
                timecode_timelines.append(timeline)
                
            elif ComponentDataDefinition in ['DataDef_LegacySound','DataDef_Sound']:
                audio_timelines.append(timeline)
                
            elif ComponentDataDefinition in ['DataDef_Picture', 'DataDef_LegacyPicture']:
                video_timelines.append(timeline)
            else:
                other_timelines.append(timeline)
                
                
        self.Main_Sequence_StartTimecode = 0
                
        for timeline in timecode_timelines:
            
            if timeline.has_key('TrackSegment'):
                
                if timeline['TrackSegment']['type'] == 'Timecode':
                
                
                    FramesPerSecond = timeline['TrackSegment']['FramesPerSecond']
                    StartTimecode = timeline['TrackSegment']['StartTimecode']
                    
                    
                    if float(FramesPerSecond) == 24.0:
                        self.Main_Sequence_StartTimecode = int(StartTimecode)
                        
                        print 'Start TimeCode:', FramesPerSecond,StartTimecode
                        break
            
        #raise Exception()
                
        for timeline in video_timelines:
            #print timeline.keys()
            
            print '*',timeline['EditRate']
            
            #pprint(timeline)
            
            if timeline['TrackSegment'].has_key('NestedScopeTracks'):
            
                print len( timeline['TrackSegment']['NestedScopeTracks'])
                
                for track in timeline['TrackSegment']['NestedScopeTracks']:
                    track_type = track['type']
                    #print 'type =',track['type'],track.keys()
                    
                    if track_type == 'Sequence':
                       #print track['ComponentLength'],'objects =',len(track['ComponentObjects'])
                        
                        
                        #pprint(track['ComponentDataDefinition'])
                        self.video_tracks.append(track)
                    elif track_type == 'ScopeReference':
                        pass
                        pprint(track)
                    else:
                        pprint(track)
                        raise Exception()
                        
            else:
                track = timeline['TrackSegment']
                self.video_tracks.append(track)
                #pprint(track)
                
        print len(self.video_tracks),'video tracks'
                
        for i,track in enumerate(self.video_tracks):
            print 'track %04d' % i,len(track['ComponentObjects']), 'clips'
            for item in track['ComponentObjects']:
                pass
                #print '     ',item['type'], item
            
        
        #pprint(self.Main_Sequence)
        
    def sort_Sources(self):
        
        self.video_file_paths = []
        self.audio_file_paths = []
        
        self.video_materials = {}
        
        for item,value in self.Materials.items():
            
            for track in value['PackageTracks']:
                if track['TrackSegment']['ComponentDataDefinition'] in ['DataDef_LegacyPicture','DataDef_Picture']:
                    
                    if value['cuts']:
                        
                        value['StartTimecode'] = self.Main_Sequence_StartTimecode
                        self.video_materials[item] = value
                        #pprint(value)
                        break
        
        for item,value in self.subClips.items():
            
            for track in value['PackageTracks']:
                if track['TrackSegment']['ComponentDataDefinition'] in ['DataDef_LegacyPicture','DataDef_Picture']:
                    
                    if value['cuts']:
                        
                        value['StartTimecode'] = self.Main_Sequence_StartTimecode
                        self.video_materials[item] = value
                        #pprint(value)
                        break
            
                
            #pprint(value['PackageName'])
            
    def add_SourceClip_Cut(self,clip,track,In,Out,frameOffset=0):
        
        sourceID = clip['SourcePackageID']
        
        cut = {'In':In,'Out':Out,'start': clip['StartPosition'],
               'length' :clip['ComponentLength'],'track':track,'frameOffset':frameOffset}
                    
        if self.Materials.has_key(sourceID):
            #print '*Match'
            
            #pprint(clip)
            
            
            if cut not in self.Materials[sourceID]['cuts']:
                #pprint(self.Materials[sourceID])
                self.Materials[sourceID]['cuts'].append(cut)
                #pprint(self.Materials[sourceID])

            else:
                pass          
        else:


            if self.subClips.has_key(sourceID):
                
                if cut not in self.subClips[sourceID]['cuts']:
                    self.subClips[sourceID]['cuts'].append(cut)
                    
                else:
                    print 'cut alreday exists'
                    
                    #print 'in subclips'
                
            else:
                print 'No Materials Matching'
                
        
        
            
    def find_footage_in_seq(self):
        
        mobs = {}
        
        for i,track in enumerate(self.video_tracks):
           #print i,len(track['ComponentObjects']), 'clips'
            In = 0
            Out = 0
            masterLength = track['ComponentLength']
        
            for clip in track['ComponentObjects']:
                clip_type = clip['type']
                               
                length =  int(clip['ComponentLength'])
                
                
                
                Out +=  length
                
                #print clip_type,lenght,In,Out
                
                if clip_type == 'OperationGroup':
                    
                    #pprint(clip)
                    
                    for Segment in clip['InputSegments']:
                        
                        if Segment['type'] == 'SourceClip':
                            pass
                            #print 'OperationGroup adding cut'
                            self.add_SourceClip_Cut(Segment,i,In,Out,self.Main_Sequence_StartTimecode)
                            
                        elif Segment['type'] == 'Sequence':
                            
                            #print length,Segment['ComponentLength']
                            #print Segment['InputSegments']
                            #pprint(clip)
                        
                            pass
                        
                        else:
                            
                            pass
                            
                    #raise Exception()
                
                elif clip_type == 'ScopeReference':
                    #print i
                    
                    
                    pass
                    #pprint(clip)
                
                elif clip_type == 'Selector':
                    pass
                    
                elif clip_type == 'Transition':
                    pass
                    Out -= 2*length 
                
                elif clip_type == 'Filler':
                    pass
                elif clip_type == 'SourceClip':
                    #pprint(clip)
                    self.add_SourceClip_Cut(clip,i,In,Out,self.Main_Sequence_StartTimecode)
        
                else:
                    
                    print clip_type
                
                In = Out
                
            #print masterLength,'should Equal',Out
    
    
    def sort_more(self):
        
        pass
        #for item,value in self.Compositions.items():
            
            #print len(value['PackageTracks']),
# track in value['PackageTracks']:
                #print track['type'],
                
            #print ''
  
           
    def get_Package_info(self,package):

        package_info = {}
        
        package_type = strip_namespace(package)
        package_info['type'] = package_type
        
        if package_type == 'MaterialPackage':
            package_info['cuts'] = []
            
        elif package_type == 'CompositionPackage':
            package_info['cuts'] = []

        for data in package:
            name =  strip_namespace(data)

            self.logger.info( name)

            if name == 'AppCode':
                self.logger.info( ' ', data.text)
                package_info[name] = data.text
            elif name == 'ConvertFrameRate':
                self.logger.info( ' ', data.text)
                if data.text == 'true':
                    package_info[name] = True

                elif data.text == 'false':
                    package_info[name] = False
                else:
                    package_info[name] = data.text

            elif name == 'EssenceDescription':
                package_info[name] = self.get_EssenceDescription_info(data)


            elif name == 'MobAttributeList':
                package_info[name] = self.get_MobAttributeList_info(data)

            elif name == 'PackageUsage':
                self.logger.info( ' ', data.text)
                package_info[name] = data.text

            elif name == 'PackageTracks':
                package_info[name] = self.get_PackageTracks_info(data)


            elif name == 'PackageUserComments':
                #print ' ', name
                package_info[name] = self.get_PackageUserComments_info(data)

            elif name == 'PackageLastModified':
                self.logger.info( ' ', data.text)
                package_info[name] = data.text
            elif name == 'CreationTime':
                self.logger.info( ' ', data.text)
                package_info[name] = data.text
            elif name == 'PackageName':
                self.logger.info( ' ', data.text)
                package_info[name] = data.text

            elif name == 'PackageID':
                self.logger.info( ' ', data.text)
                package_info[name] = data.text
                
            elif name == 'SubclipFullLength1':
                
                #print name,data.text
                package_info[name] = data.text
                
            elif name == 'SubclipBegin':
                #print name,data.text
                package_info[name] = data.text
            
            else:
                
                print '**',name
                raise Exception()

        return package_info
    
    def get_PackageTracks_info(self,PackageTracks):
        
        PackageTracks_info = []
        
        #print len(PackageTracks)
        for data in PackageTracks:
            name = strip_namespace(data)
            #print name
            track_info = {'type':name}
            #print len(data)
            for item in data:
                item_name = strip_namespace(item)
                
                #print item_name
                
                if item_name in ['Origin','EditRate','TrackName','TrackID','EssenceTrackNumber',
                                 'MarkOut','MarkIn','EventTrackEditRate']:
                    track_info[item_name] = item.text

                elif item_name == 'TrackSegment':
                    
                    assert len(item) == 1
                    
                    track_info[item_name] = self.get_TrackSegment_info(item)[0]
                    
                #elif item_name == 'TaggedValue':
                    #fo
 
                else:
                    print item_name,item.text
                    #pprint(PackageTracks)
                    raise Exception()
                    
                
            
            
            PackageTracks_info.append(track_info)
            
            
            
        return PackageTracks_info
        

    def get_ComponentObjects_info(self,ComponentObjects):
        ComponentObjects_info = []
        
        
        for data in ComponentObjects:
            name = strip_namespace(data)
            
        
            component = {'type':name}
            
            for item in data:
                item_name = strip_namespace(item)
                   
                if item_name == 'ComponentLength':
                    
                    component[item_name] = item.text
                    
                elif item_name == 'ComponentDataDefinition':
                    component[item_name] = item.text
                    
                elif item_name == 'StartPosition':
                    component[item_name] = item.text
                    
                elif item_name == 'SourceTrackID':
                    component[item_name] = item.text
                    
                elif item_name == 'SourcePackageID':
                    component[item_name] = item.text  
                    
                elif item_name == 'DropFrame':
                    component[item_name] = item.text
                    
                elif item_name == 'FramesPerSecond':
                    component[item_name] = item.text 
                    
                elif item_name == 'StartTimecode':
                    component[item_name] = item.text
                    
                elif item_name == 'Operation':
                    component[item_name] = item.text
                
                elif item_name == 'CutPoint':
                    component[item_name] = item.text
                    
                elif item_name == 'TransitionOperation':
                    params = {}
                    
                    for param in item:
                        param_name  = strip_namespace(param)
                        
                        params[param_name] = param.text
                        
                    component[item_name] = params 
 
                elif item_name == 'Parameters':
                    
                    component[item_name] = self.get_Parameters_info(item) 
                
                elif item_name == 'InputSegments':
         
                    component[item_name] = self.get_InputSegments_info(item)
                    
                elif item_name == 'ComponentAttributeList':
                    
                    params = {}
                    
     
                    component[item_name] = self.get_PackageUserComments_info(item)
                    #component[item_name] = item
                    
                elif item_name == 'CommentMarkerTime':
                    component[item_name] = item.text
                elif item_name == 'CommentMarkerDate':
                    component[item_name] = item.text
                elif item_name == 'CommentMarkerUSer':
                    component[item_name] = item.text
                    
                elif item_name == 'CommentMarkerAnnotationList':
                    component[item_name] = item.text
                    
                elif item_name == 'EventComment':
                    component[item_name] = item.text
                    
                elif item_name == 'EventPosition':
                    component[item_name] = item.text
                    
                elif item_name == 'OpGroupMotionCtlOffsetMapAdjust':
                    component[item_name] = item.text
                elif item_name == 'RelativeTrack':
                    component[item_name] = item.text
                    
                elif item_name == 'RelativeScope':
                    component[item_name] = item.text
                    
                elif item_name == 'PhaseFrame':
                    component[item_name] = item.text
                    
                elif item_name == 'PulldownDirection':
                    component[item_name] = item.text
                    
                elif item_name == 'PulldownKind':
                    component[item_name] = item.text
                    
                elif item_name == 'Avid_Scope':
                    print item_name, item.text
                    
                    
 
                elif item.getchildren():
                    component[item_name] = str(item)
                    
                    
                else:
                    print item_name, item.text
                    raise Exception()
        

            ComponentObjects_info.append(component)
                
        return ComponentObjects_info
    
    def get_Parameters_info(self,Parameters):
        
        params = []
                    
        for param_group in Parameters:
            param_group_name  = strip_namespace(param_group)
            
            p = {'type':param_group_name}
            
            for param in param_group:
                param_name = strip_namespace(param)
                
                if param.getchildren():
                    p[param_name] = str(param)
                else:
                
                    p[param_name] = param.text
            
            params.append(p)
            
        return params
    
    def get_InputSegments_info(self,InputSegments):
        
        clips = []
                    
        for segment in InputSegments:
            segment_name  = strip_namespace(segment)
            
            segment_params = {'type':segment_name}
            
            for param in segment:
                param_name = strip_namespace(param)
                
                
                if param_name == 'ComponentAttributeList':
                    segment_params[param_name] = self.get_PackageUserComments_info(param)
                    
                elif param_name == 'Parameters':
                    segment_params[param_name]  = self.get_Parameters_info(param)
                    
                elif param_name == 'InputSegments':
                    segment_params[param_name] = self.get_InputSegments_info(param)
                    
                elif param_name == 'ComponentObjects':
                    segment_params[param_name] = self.get_ComponentObjects_info(param)
                    
                elif param.getchildren():
                    
                
                    segment_params[param_name] = str(param)
                    
                else:
                    segment_params[param_name] = param.text

            
            
            
            clips.append(segment_params)
        return clips
    
    def get_OperationGroup_info(self,OperationGroup):
        
      
        OperationGroup_info = {}
        
        
        for data in OperationGroup:
            name = strip_namespace(data)
            #print nam
            
            if name == 'InputSegments':
                OperationGroup_info[name] = self.get_InputSegments_info(data)
                
            elif name == 'Parameters':
                OperationGroup_info[name] = self.get_Parameters_info(data)
       
            elif name == 'ComponentAttributeList':
                OperationGroup_info[name] = self.get_PackageUserComments_info(data)
            elif data.getchildren():
                
                
                OperationGroup_info[name] =str(data)
                #OperationGroup_info[name] = None
            else:
                
                OperationGroup_info[name] = data.text
            
        
        #pprint(OperationGroup_info)
        
        return OperationGroup_info
    
    def get_Selector_info(self,Selector):
        Selector_info = {}
        
        
        for data in Selector:
            name = strip_namespace(data)
            #print nam
            
            if name == 'ComponentAttributeList':
                Selector_info[name] = self.get_PackageUserComments_info(data)
                
            elif name == 'AlternateSegments':
                Selector_info[name] = self.get_InputSegments_info(data)
                
            elif name == 'SelectedSegment':
                Selector_info[name] = self.get_InputSegments_info(data)

            elif data.getchildren():
                Selector_info[name] = str(data)
                #Selector_info[name] = None
            else:
                Selector_info[name] = data.text
                
        #pprint(Selector_info)
        
        return Selector_info
    
    
    def get_TrackSegment_info(self, TrackSegment):
        
        TrackSegment_info = []
        space = '      '
        for data in TrackSegment:
            
            name = strip_namespace(data)
            
            item_dict = {'type':name}
            
            for item in data:
                item_name = strip_namespace(item)
                if item_name == 'ComponentObjects':
                    self.logger.info( space,' ',item_name)
                    item_dict[item_name] = self.get_ComponentObjects_info(item)
                elif item_name == 'ComponentAttributeList':
                    item_dict[item_name] = self.get_PackageUserComments_info(item)
                elif item_name == 'InputSegment':
                    
                    item_dict[item_name] = self.get_InputSegments_info(item)
                    
                elif item_name == 'NestedScopeTracks':
                        
                    tracks = self.get_TrackSegment_info(item)
                    item_dict[item_name] = tracks
                
                elif item.getchildren():
                    item_dict[item_name] = str(item)
                    
                else:
                    self.logger.info( space,' ',item_name,item.text)
                    item_dict[item_name] = item.text
                    
            TrackSegment_info.append(item_dict)
            
            
        return TrackSegment_info
                

    def get_TimelineTrack_info(self,TimelineTrack):
        TimelineTrack_info = {}

        for data in TimelineTrack:
            name = strip_namespace(data)
            space =  '    '
            if name == 'TrackName':
                self.logger.info( space,name,data.text)

                TimelineTrack_info[name] = data.text

            elif name == 'MarkIn':
                self.logger.info( space,name,data.text)

                TimelineTrack_info[name] = data.text
            elif name == 'MarkOut':
                self.logger.info( space,name,data.text)
                TimelineTrack_info[name] = data.text

            elif name == 'Origin':
                self.logger.info( space,name,data.text)
                TimelineTrack_info[name] = data.text

            elif name == 'TrackID':
                self.logger.info( space,name,data.text)
                TimelineTrack_info[name] = data.text

            elif name == 'EditRate':
                self.logger.info( space,name,data.text)
                TimelineTrack_info[name] = data.text

            elif name == 'EssenceTrackNumber':
                self.logger.info( space,name,data.text)
                TimelineTrack_info[name] = data.text

            elif name == 'TrackSegment':
                self.logger.info( space,name)
                if TimelineTrack_info.has_key('TrackSegment'):
                    TimelineTrack_info[name].append(self.get_TrackSegment_info(data))
                else:
                    TimelineTrack_info[name] = [(self.get_TrackSegment_info(data))]

            else:
                self.logger.error( space,name, '**' ,data.text)


        return TimelineTrack_info


    def get_EventTrack_info(self,EventTrack):
        
        EventTrack_info = {}
        for data in EventTrack:
            name = strip_namespace(data)
            
            if name == 'TrackSegment':
                if EventTrack_info.has_key('TrackSegment'):
                    EventTrack_info[name].append(self.get_TrackSegment_info(data))
                else:
                    EventTrack_info[name] = [(self.get_TrackSegment_info(data))]
                
            
            elif data.getchildren():
                EventTrack_info[name] = str(data)
                
            else:
                EventTrack_info[name] = data.text
                
       #pprint(EventTrack_info)
        
        return EventTrack_info


    def get_PackageUserComments_info(self,PackageUserComments):

        comments = []

        for data in PackageUserComments:
            name =  strip_namespace(data)

            if name == 'TaggedValue':
                for value in data:
                    value_name = strip_namespace(value)

                    #if value_name == '
                    self.logger.info( '    ',value_name, ':',value.text)


                    comments.append({value_name:value.text})

        return comments


    def get_MobAttributeList_info(self,MobAttributeList):

        MobAttributeList_info = []
        for data in MobAttributeList:
            name =  strip_namespace(data)
            if name == 'TaggedValue':
                for value in data:
                    value_name = strip_namespace(value)
                    self.logger.info( '    ',value_name,':',value.text)

                    MobAttributeList_info.append({value_name:value.text})

            else:
                self.logger.error( '*****', name )
        return MobAttributeList_info
    
    def get_Locators_info(self,Locators):
        
        locators_info = []
        
        for data in Locators:
            
            name = strip_namespace(data)
            
            item_dict = {'type':name}
            #print name
            for item in data:
                item_name = strip_namespace(item)
                
                item_dict[item_name] = item.text
                
                #print item_name,item.text
            
            locators_info.append(item_dict)
            
            
        return locators_info


    def get_EssenceDescription_info(self,EssenceDescription):

        space = '   '
        EssenceDescription_info = {}

        for data in EssenceDescription:

            name = strip_namespace(data)

            EssenceDescription_info['type'] = name
                     
            for item in data:
                item_name = strip_namespace(item)
                if item_name == 'Locators':
                    EssenceDescription_info[item_name] = self.get_Locators_info(item)
                elif item.getchildren():
                    EssenceDescription_info[item_name] = str(item)
                    
                else:
                    
                    EssenceDescription_info[item_name] = item.text



        return EssenceDescription_info



def readXml(path):

    tree = ET.parse(path)

    #for elem in tree.getiterator():
        #print elem.tag,elem.attrib

    root = tree.getroot()

    namespace =  get_namespace(root)

    #print dir(root)
    #print root.attrib

    #extensions = root.getchildren()[0]
    Preface = root.find("{%s}Preface" % namespace)


    ContentStorageObject = Preface.find("{%s}ContentStorageObject" % namespace)
    ContentStorage = ContentStorageObject.find("{%s}ContentStorage" % namespace)

    Packages = ContentStorage.find("{%s}Packages" % namespace)
    CompositionPackage = Packages.findall("{%s}CompositionPackage" % namespace)
    MaterialPackages = Packages.findall("{%s}MaterialPackage" % namespace)

    SourcePackages = Preface.findall("{%s}SourcePackage" % namespace)

    #print SourcePackages

    for item in Packages:
        print strip_namespace(item)




    #for item in preface:


    #print dir(root)
    #for item in root:
        #print item
    #preface = root.find('{http://www.aafassociation.org/aafx/v1.1/20090617}Preface')

    #for item in preface:
        #print item
