from moviepy import *
import os
from NBAHighlightsMaker.players.getplayers import read_event_ids

#organize files in video created date
#MIGHT CHANGE TO ORGANIZE BY COMBINATION OF REAL LIFE TIME AND PERIOD TIME 
#REMAINING
#OR WHEN CLIP IS DOWNLOADED, COMBINE PATH AND DATA DIRECTORY, ADD TO ROW

def get_clip_order(data_dir):
    #get all files in data directory
    clips_paths = [f for f in os.listdir(data_dir) if f.endswith('.mp4')]
    sorted_clips_paths = sorted(clips_paths, key=lambda x: int(x.split('.')[0]))
    return sorted_clips_paths

# given a videoFileClip from moviepy, make a text overlay and return it
def create_overlay(string):
    txt_clip = TextClip(font= './resources/Boldonse-Regular.ttf',
                                text = string, 
                                font_size = 20, 
                                color = 'white', 
                                text_align = 'center',
                                duration = 3,
    )
    #txt_clip = txt_clip.with_position(('bottom', 'right'))
    return txt_clip

def create_video_clip(clip_path):
    clip = VideoFileClip(clip_path, target_resolution= (1280, 720))
    return clip

# make each clip into a videoFileClip, and call create overlay to get the text clip
# then make a composite videoFileClip
def create_composite_clips(clips_paths, data_dir):
    #get pd dataframe of the descriptions for each clip
    event_ids = read_event_ids()
    composite_clips = []
    #for each clip path
    for clip_path in clips_paths:
        event_num = int(clip_path.split('.')[0])
        full_clip_path = os.path.join(data_dir, clip_path)
        desc = event_ids.loc[event_ids['EVENTNUM'] == event_num, 'DESCRIPTION'].values[0]
        #make into videoClip
        clip = create_video_clip(full_clip_path)
        #make text overlay
        txt_clip = create_overlay(desc)
        #make it a composite video
        composite_clip = CompositeVideoClip([clip, txt_clip])
        composite_clips.append(composite_clip)
    
    return composite_clips

# concatenate all composite clips
def make_final_vid(data_dir, composite_clips):
    final_vid = concatenate_videoclips(composite_clips)
    path = os.path.join(data_dir, "final_vid.mp4")
    final_vid.write_videofile(path, codec = 'libx264', fps = 24)
    return final_vid

def main():
    data_dir = os.path.join(os.getcwd(), 'data', 'vids')
    clip_paths = get_clip_order(data_dir)
    composite_clips = create_composite_clips(clip_paths, data_dir)
    final_vid = make_final_vid(data_dir, composite_clips)
    # print(clip_order)
    # test = create_overlay("test")


if __name__ == '__main__':
    main()