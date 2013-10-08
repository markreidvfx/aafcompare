import os
import aaf2xml

import traceback

import operator
from pprint import pprint

import time
import datetime
import copy

import cPickle as pickle


def read_aaf(aaf_path):
    print aaf_path
    basename = os.path.basename(aaf_path)
    
    dirname = os.path.dirname(aaf_path)
    
    name,ext = os.path.splitext(basename)
    
    
    xml_path = os.path.join(dirname,name + '.xml')
    
    if os.path.exists(xml_path):
        print 'xml file already exists skipping convert'
        
    else:
        print 'converting aaf to xml'
        aaf2xml.aaf2xml(aaf_path,xml_path)
    
    reload(aaf2xml)
    
    aaf = aaf2xml.AAF(xml_path)
    aaf.readFromFile()
    
    return aaf


def frames_to_timecode(frames,frameOffset=86400,fps=24):
    
    seconds = (float(frames + frameOffset) / float(fps))
            
    timecode = time.strftime("%H:%M:%S",time.gmtime(seconds))
    
    f = int(frames)
    while True:
        if f < 24:
            break
        else:
            f -= 24
         
    timecode += ':%02d' % f
 
    return timecode

def get_clip_length(clip):
    
    length = 0
    
    for timeline in clip['PackageTracks']:
        
        timeline_type = timeline['type']
        
        if timeline_type == 'TimelineTrack':
            try:
                ComponentLength = int(timeline['TrackSegment']['ComponentLength'])
                if ComponentLength > length:
                    length = ComponentLength
                    
            except:
                print timeline
        
        
    return length


def summarize_materials(data):
    
    summarry = []
    
    for item,value in data.items():
        clip = {}
        clip_name = value['PackageName']
        
        #StartTimecode =value['StartTimecode']
        #frameOffset = value['frameOffset']
        clip_id = value['PackageID']
        
        clip['name'] = clip_name
        clip['id'] = clip_id
        
        clip['children'] = []
        
        clip_length = get_clip_length(value)
        
        clip['frames'] = clip_length
        
        #print value.keys()
        
        if value['cuts']:
            
            cuts = []
            
            
            for i,cut in enumerate(value['cuts']):
                clip_cut = {}
                #pprint(cut)
                
                
                start = int(cut['start'])
                length = int(cut['length'])
                track = cut['track'] + 1
                
                frameOffset = cut['frameOffset']
                
                tail =  clip_length - (start + length)
                
                In = cut['In']
                Out = cut['Out']
                clip_cut =  {'cut':'%s' % (clip_name),
                             'In':frames_to_timecode(In,frameOffset=frameOffset),
                             'Out':frames_to_timecode(Out,frameOffset=frameOffset),
                             'FrameIn':In + frameOffset -86400,
                             'FrameOut':Out + frameOffset - 86400,
                             
                             'head':start,
                             'tail':tail,
                             #'in':frames_to_timecode(start),
                             #'out':frames_to_timecode(start+length),
                             'frame_in':start,
                             'frames':length,
                             'track':track}
                
                
                
                cuts.append(clip_cut)
                
            
            sorted_cuts = sorted(cuts,key=lambda k: k['FrameIn'])
            
            for i,item in enumerate(sorted_cuts):
                cut_name = item['cut']
                item['cut'] = '%s:%04d' % (cut_name,i+1)
                
            clip['children'] = sorted_cuts
            #keys = cuts.keys()
            #keys.sort()
            
            #for key in keys:
                #clip['children'].append(cuts[key])
                
                
                
        summarry.append(clip)
            
    sorted_summarry = sorted(summarry,key=lambda k: k['name'])
    
    
    
    return sorted_summarry



def compared_modified(old_children,new_children):
    
    #old_children = old_clip['children']
    #old_children = new_clip['children']
    
    #print len(old_children),len(new_children)
    
    if len(old_children) == len(new_children):
        for i,child in enumerate(old_children):
            
            new_child = new_children[i]
            
            if new_child['frames'] == child['frames']:
                pass
            else:
                
                return 'Modified'
            
        return 'Shifted'
    
    else:
    
    
        return 'Modified'


def compare_summaries(old,new):
    
    old_dict = {}
    
    new_dict = {}
    
    summarry = []
    
    for item in old:
        item_id = item['id']
        
        if old_dict.has_key(item_id):
            raise Exception()
        
        old_dict[item_id] = item
        
    for item in new:
        item_id =  item['id']
        
        if new_dict.has_key(item_id):
            raise Exception()
        
        new_dict[item_id] = item
        
        
    for item,value in old_dict.items():
        
        if new_dict.has_key(item):
            
            new_clip = new_dict[item]
            
            changed = False
            
            new_children = []
            for child in new_clip['children']:
                if child in value['children']:
                    unchanged_child_index = value['children'].index(child)
                    unchanged_child = value['children'][unchanged_child_index]
                    
                    unchanged_child['status'] = 'Original'
                else:
                    changed = True
                    child['status'] = 'New'
                    new_children.append(child)
                    
                    #value['children'].append(child)
                    
            for child in value['children']:
                
                if child.has_key('status'):
                    pass
                else:
                    child['status'] = 'Old'
                    changed = True
                    
            if changed:
                value['status'] = compared_modified(value['children'],new_children)
                value['children'].extend(new_children)
                                                    
            else:
                value['status'] = 'Original'
                
            
        else:
            value['status'] = 'Missing'
            for child in value['children']:
                child['status'] = 'Missing'
                
        
                
            
        summarry.append(value)
        
    for item,value in new_dict.items():
        
        if old_dict.has_key(item):
            pass
                
        else:
            value['status'] = 'New'
            for child in value['children']:
                child['status'] = 'New'
            
            summarry.append(value)
            
    for clip in summarry:
        
        
        
        sorted_children = sorted(clip['children'],key=lambda k: k['FrameIn'])
        
        clip['children'] = sorted_children
        
        
        
    return summarry


def get_other_info(summarry):
    
    vfx_shots = []
    
    vfx_labels = 0
    
    unlabel_vfx_shots = []
    
    sequences = {}
    
    
    other_data = ''
    
    for item in summarry:
        
        name = item['name']
        
        
        
        
        if name.count('VFX'):
            vfx_labels += len(item['children'])
            print 'VFX =',vfx_labels
            
            unlabel_vfx_shots.append(item)
        
        try:
            
            seq,num1,num2 = name.split('_')
            
            
            i = 0
            for item in num2:
                
                if item.isdigit():
                    i += 1
                    
                else:
                    break
                
            assert len(seq) == 2
                
            num2 = int(num2[:i])
            num1 = int(num1)
            
            shotname = '%s_%03d_%03d' % (seq,num1,num2)
            
            
            
            
            if not shotname in vfx_shots:
                print 'shot =',shotname
                vfx_shots.append(shotname)
                
                if sequences.has_key(seq):
                    sequences[seq].append(shotname)
                else:
                    sequences[seq] = [shotname]
                    
            
            
        except:
            pass
        
        
    #print len(vfx_shots),'labeled vfx_shots'
    #print vfx_labels, 'unlabeled vfx_shots'
    
    other_data += '%i vfx shots\n\n' % (len(vfx_shots) + vfx_labels)
    
    other_data += '%i labeled vfx shots\n' % len(vfx_shots)
    other_data += '%i unlabeled vfx shots\n\n' % vfx_labels
    
    for key in sequences.keys():
        #print '  ', key,'shots:',len(sequences[key])
        
        other_data += '   %s shots: %i\n' % (key,len(sequences[key]))
        
        
    other_data += '\n\n\nUnlabeled VFX Shots:\n\n'
    
    for item in unlabel_vfx_shots:
        
        other_data += 'Name: "%s"\n' % item['name']
        
        for cut in item['children']:
            other_data += '    in: %s out: %s track: %s\n' % (cut['In'],cut['Out'],cut['track'])
        
    #other_data += ""    
    #other_data += str(unlabel_vfx_shots)
    
    print other_data
    
    
        
        
    
    return other_data

def get_vfx_counts(summary):
    
    vfx_counts ={}
    
    for item in summary:
        name = item['name']
        
        keys = {}
        try:
            for key_value in name.split(','):
                
                key,value = key_value.split('-')
                
                key = key.strip().upper()
                
                value = int(value)
                
                keys[key] = value
                
                
        except:
            pass
            #print 'skipping',name
        if keys:
            count = len(item['children'])
            print name,keys,count
            
            for key,value in keys.items():
                
                if vfx_counts.has_key(key):
                    
                    vfx_counts[key] += value * count
                else:
                    vfx_counts[key] = value * count
    
    string = ""        
    
    total = 0
    for key,value in sorted(vfx_counts.items()):
        print 'total', key,value 
        string += "%s: %i\n" % (key,value)
        
        total += value
        
    string += '\nTotal: %i' % total
    #raise Exception()
    
    return string

class Simple_AFF(object):
    
    def __init__(self,video_materials):
        self.video_materials = video_materials
        
        


class AAF_Compare():
    
    def __init__(self,old_paths,new_paths):
       
        self.old_paths = old_paths
        self.new_paths = new_paths
        
        self.base_dir = None
        
        self.old_aaf = None
        self.new_aad = None
        
        self.old_basename = None
        self.new_basename = None
        
        self.only_quicktimes =True
        
    def read_aaf(self,aaf_path):
        print aaf_path
        
        aaf_base_dir = os.path.join(self.base_dir,'AAF')
        xml_base_dir = os.path.join(self.base_dir,'XML')        
        
        basename = os.path.basename(aaf_path)
        
        dirname = os.path.dirname(aaf_path)
        
        name,ext = os.path.splitext(basename)
        
        xml_dest_dir = dirname.replace(aaf_base_dir,xml_base_dir)
        
        xml_path = os.path.join(xml_dest_dir,name + '.xml')
        
        pickle_path = os.path.join(xml_dest_dir,name + '.pkl')
        
        print xml_dest_dir
        print xml_path
        
        
        if os.path.exists(pickle_path):
            pkl_file = open(pickle_path,'rb')
            
            
            video_materials = pickle.load(pkl_file)
            aaf = Simple_AFF(video_materials)
            
            return aaf
            
        
            
        
        elif os.path.exists(xml_path):
            print 'xml file already exists skipping convert'
            
        else:
            print 'converting aaf to xml'
            
            self.progress_message('converting aaf to xml')
            if not os.path.exists(xml_dest_dir):
                os.makedirs(xml_dest_dir)
            aaf2xml.aaf2xml(aaf_path,xml_path)
        
        reload(aaf2xml)
        
        self.progress_message('reading xml')
        aaf = aaf2xml.AAF(xml_path)
        aaf.readFromFile()
        
        
        #s_aaf = Simple_AFF(aaf.video_materials)
        
        print 'saving pickle file'
        pkl_file = open(pickle_path,'wb')
        
        
        #video_materials = {}
        
        #for item,value in aaf.video_materials.items():
            
        
        
        pickle.dump(aaf.video_materials,pkl_file,-1)
        pkl_file.close()
        
        
        return aaf
        
    
    #def 
        
        
        
    def progress(self,value,max_value):
        pass
    def progress_message(self,message):
        pass
    
    def merge_aafs(self,aaf_list):
        
        video_materials = {}
        
        
        for item in aaf_list:
            
            for key,value in item.video_materials.items():
                
                if video_materials.has_key(key):
                    
                    
                    cuts = value['cuts']
                    
                    for cut in cuts:
                        if cut in video_materials[key]['cuts']:
                            print 'cut already exists',cut
                            pass
                        else:
                            video_materials[key]['cuts'].append(cut)

                    pass
                else:
                    video_materials[key] = value
                    
                    
        return Simple_AFF(video_materials)
                    
                    
    def read_aafs(self):
        self.progress(10,100)
        self.progress_message('reading old aafs')
        old_aafs = []
        new_aafs = []
        
        progress = 10
        
        step = 30.0/len(self.old_paths)
        
        for path in self.old_paths:
            self.progress(progress,100)
            aaf = self.read_aaf(path)
        
            old_aafs.append(aaf)
            
            progress += step
            
        self.progress_message('reading new aafs')
        
        step = 30.0/len(self.old_paths)
        
        for path in self.new_paths:
            self.progress(progress,100)
            aaf = self.read_aaf(path)
            
            new_aafs.append(aaf)
            progress += step
        
        
        self.old_aaf = self.merge_aafs(old_aafs)
        self.new_aaf = self.merge_aafs(new_aafs)
        
            
        self.new_basename = os.path.basename(self.new_paths[0])
        self.old_basename = os.path.basename(self.old_paths[0])
        
    def get_summarry(self):
        summarry = []
        
        header = {'headers':self.get_headers()}
        
        #summarry.append(header)
        
        summarry_old = summarize_materials(self.old_aaf.video_materials)
        summarry_new = summarize_materials(self.new_aaf.video_materials)
        
        
        self.summarry_old = copy.deepcopy(summarry_old)
        self.summarry_new = copy.deepcopy(summarry_new)
        
        
        if self.only_quicktimes:
            clean_old = self.clean_garbage(summarry_old)
            clean_new = self.clean_garbage(summarry_new)
            
        else:
            clean_old = summarry_old
            clean_new = summarry_new
            
            
        
        clean_summary = clean_old
        
        compared_summarry = compare_summaries(clean_old,clean_new)
        
        header['totals'] = self.get_totals(compared_summarry)
        
        
        
        compared_summarry.insert(0,header)

            
        return compared_summarry
    
    def get_totals(self,summarry):
        
        totals = []
        
        clips = 0
        
        
        unchanged_clips = 0
        missing_clips = 0
        
        modified_clips = 0
        
        shifted_clips = 0
        
        new_clips = 0
        
        cuts = 0
        original_cuts = 0
        old_cuts = 0
        new_cuts = 0
        
        for clip in summarry:
            
            
            clips += 1
            
            clip_status  = clip['status']
            
            if clip_status == 'Original':
                unchanged_clips += 1
            elif clip_status == 'Missing':
                missing_clips += 1
                
            elif clip_status == 'New':
                new_clips += 1
                
            elif clip_status == 'Modified':
                modified_clips += 1
                
            elif clip_status == 'Shifted':
                shifted_clips += 1
            
            for cut in clip['children']:
                cuts += 1
                
                cut_status = cut['status']
                
                if cut_status == 'Original':
                    original_cuts += 1
                elif cut_status == 'New':
                    new_cuts += 1 
                elif cut_status == 'Old':
                    old_cuts += 1
                
                
        return [['Clips',clips],             
                ['Missing Clips',missing_clips],
                ['New Clips',new_clips],
                ['Modified Clips',modified_clips],
                ['Shifted Clips',shifted_clips],
                ['Original Clips',unchanged_clips],
                ['Cuts',cuts],
                ['Old Cuts',old_cuts],
                ['New Cuts',new_cuts],
                ['Original Cuts',original_cuts]]
            
            
    
    def get_headers(self):
        headers = ['name','cut','status','In','Out','FrameIn','FrameOut','head','frames','tail','track','id']
        
        return headers
    
    def clean_garbage(self,summary):
        
        clean_summary = []
        
        
        for item in summary:
            item_name = item['name']
            
            name,ext = os.path.splitext(item_name)
            
            if ext in ['.mov']:
                clean_summary.append(item)
                
        return clean_summary
    
    def split_track(self,data,track=15):
        
        data = copy.deepcopy(data)
        
        header = data[0]
        
        track_data =  []
        
        
        for item in data[1:]:
            
            new_cuts = []
            
            for cut in item['children']:
                
                if cut['track'] == track:
                    new_cuts.append(cut)
                    
            if new_cuts:
                item['children'] = new_cuts
                track_data.append(item)
                    
                    
        header['totals'] = self.get_totals(track_data)
                
        track_data.insert(0,header)
        
        
        return track_data
    
    
    def split_catagories(self,data):
        missing = []
        new = []
        modified = []
        original = []
        shifted = []
        
        header = copy.deepcopy(data[0])
        
        
        for item in data[1:]:
            item_status = item['status'] 
            
            if item_status == 'Missing':
                missing.append(item)
                
            elif item_status == 'New':
                new.append(item)
                
            elif item_status == 'Shifted':
                shifted.append(item)
                
            elif item_status == 'Modified':
                modified.append(item)
                
            elif item_status == 'Original':
                original.append(item)
        
        for item in [missing,new,shifted,modified,original]:
            
            totals = self.get_totals(item)
            
            header['totals'] = totals
            
            item.insert(0,copy.deepcopy(header))
        
        return missing,new,shifted,modified,original
        
    
    def get_data(self):
        data = {}
        self.read_aafs()
        
        self.progress_message('Sorting Data')
        
        self.progress(80,100)
        summarry = self.get_summarry()
        
        data['summary'] = summarry
        
        missing,new,shifted,modified,original = self.split_catagories(summarry)
        
        data['missing'] = missing
        data['new'] = new
        data['shifted'] = shifted
        data['modified'] = modified
        data['original'] = original
        
        data['shifted'] = shifted
        
        data['Editorial'] = self.split_track(summarry, 15)
        data['DS Online'] = self.split_track(summarry, 16)
        
        self.progress(90,100)
        
        
        #data['other'] = get_other_info(summarry)
        
        data['old_shot_totals'] = get_other_info(self.summarry_old)
        data['new_shot_totals'] = get_other_info(self.summarry_new)
        
        data['old_vfx_counts'] = get_vfx_counts(self.summarry_old)
        data['new_vfx_counts'] = get_vfx_counts(self.summarry_new)
        
        data['aaf_names'] = [self.old_basename,self.new_basename]
        self.progress(98,100)
        
        
        return data
    
    


def aaf_compare(aaf_path,compare_aaf_path):
    
    aaf = read_aaf(aaf_path)
    aaf_compare = None
    
    #aaf_compare = read_aaf(compare_aaf_path)
    
    
    return {'AAF':[aaf,aaf_compare]}