from moviepy.editor import TextClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx.all import fadein, fadeout
#import sys
import os
import asyncio
import psutil
from proglog import ProgressBarLogger
from PySide6.QtCore import Signal, QObject


#from NBAHighlightsMaker.players.getplayers import read_event_ids

class MyProgressBarLogger(QObject, ProgressBarLogger):
    progress_bar_values = Signal(int, str)
    def __init__(self):
        super().__init__()
        self.min_time_interval = 1.0
        #self.update_progress_bar = update_progress_bar
        self.cancelled = False

    def bars_callback(self, bar, attr, value, old_value=None):
        print("Bars called back:")
        try:
            if self.cancelled:
                print("Bars callback raised exception for cancelling print.")
                raise IOError("Bars callback raise exception for cancelling.")
            if bar == 't' and attr == 'index':
                total = self.bars[bar]['total']
                percent = int((value / total) * 100)
                # value and total are in frames, so convert to seconds
                self.progress_bar_values.emit(percent, f"Editing - {percent}% : {(value / 60):.1f}s / {(total / 60):.1f}s")
        except IOError as e:
            print(f"IOError caught in bars_callback: {e}")
            self.cancelled = False

    def cancel(self):
        self.cancelled = True
        print("Logger cancellation triggered.")
        
#organize files in video created date
class VideoMaker():
    def __init__(self, update_progress_bar):
        self.data_dir = os.path.join(os.getcwd(), 'data', 'vids')
        self.logger = MyProgressBarLogger()
        self.logger.progress_bar_values.connect(update_progress_bar)

    def get_clip_order(self):
        #get all files in data directory
        clips_paths = [f for f in os.listdir(self.data_dir) if f.endswith('.mp4')]
        sorted_clips_paths = sorted(clips_paths, key=lambda x: int(x.split('.')[0]))
        return sorted_clips_paths
    
    def cancel_editing(self):
        # cancel the editing process
        self.logger.cancel()
        print("Editing cancelled by user (cancel_editing called).")

    # given a videoFileClip from moviepy, make a text overlay and return it
    def create_overlay(self, string):
        txt_clip = TextClip(font= './resources/Boldonse-Regular.ttf',
                                    text = string, 
                                    font_size = 20, 
                                    color = 'white', 
                                    text_align = 'center',
                                    duration = 3,
        )
        #txt_clip = txt_clip.with_position(('bottom', 'right'))
        return txt_clip

    def create_video_clip(self, clip_path):
        clip = VideoFileClip(clip_path, target_resolution = (720, 1280))
        clip = fadein(clip, duration=1)
        clip = clip.fadeout(duration=1)
        return clip

    async def create_video_clips(self, clip_paths):
        new_clips = []

        for clip_path in clip_paths:
            clip = self.create_video_clip(clip_path)
            new_clips.append(clip)
        
        return new_clips

    # make each clip into a videoFileClip, and call create overlay to get the text clip
    # then make a composite videoFileClip
    def create_composite_clips(self, event_ids, clips_paths, data_dir):
        #get pd dataframe of the descriptions for each clip
        composite_clips = []
        #for each clip path
        for clip_path in clips_paths:
            event_num = int(clip_path.split('.')[0])
            full_clip_path = os.path.join(data_dir, clip_path)
            desc = event_ids.loc[event_ids['EVENTNUM'] == event_num, 'DESCRIPTION'].values[0]
            #make into videoClip
            clip = self.create_video_clip(full_clip_path)
            #make text overlay
            txt_clip = self.create_overlay(desc)
            #make it a composite video
            composite_clip = CompositeVideoClip([clip, txt_clip])
            composite_clips.append(composite_clip)
        
        return composite_clips

    def terminate_ffmpeg_processes(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'ffmpeg-win-x86_64-v7.1.exe':
                print(f"Terminating FFmpeg process: {proc.info['pid']} : {proc.info['name']}")
                proc.terminate()
    
    # concatenate all composite clips
    async def make_final_vid(self, clip_paths):
        clips = None
        final_vid = None
        
        try:
            clips = await self.create_video_clips(clip_paths)
            self.total_duration = sum([clip.duration for clip in clips])
            final_vid = concatenate_videoclips(clips, method="chain")
            path = os.path.join(self.data_dir, "final_vid.mp4")
            await asyncio.to_thread(final_vid.write_videofile, path, codec='libx264', temp_audiofile='temp-audio.mp3', fps=60, logger=self.logger)
        except asyncio.CancelledError:
            print("Caught asyncio.CancelledError in make_final_vid.")
            raise  
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
        finally:
            # clean up everything
            print("Cleaning up moviepy...")
            if clips:
                for clip in clips:
                    clip.close()
            if final_vid:
                final_vid.close()
            self.terminate_ffmpeg_processes()
            # await asyncio.sleep(1)
            self.logger.cancelled = False
            #return final_vid
            

# def main():
#     # print(sys.path)
#     data_dir = os.path.join(os.getcwd(), 'data', 'vids')
#     # pass this order in in the real program
#     clip_paths = get_clip_order(data_dir)
#     clips = create_video_clips(clip_paths, data_dir)
#     #composite_clips = create_composite_clips(clip_paths, data_dir)
#     #print(clips)
#     final_vid = make_final_vid(data_dir, clips)
#     # print(clip_order)
#     # test = create_overlay("test")


# if __name__ == '__main__':
#     main()