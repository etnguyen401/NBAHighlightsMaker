"""Concatenates video clips together to create a final output video.

This module defines the MyProgressBarLogger class for logging the progress of the video editing
on the UI, and the VideoMaker class for combining video clips into a final video.
"""

import os
import asyncio
from proglog import ProgressBarLogger
from PySide6.QtCore import Signal, QObject

class MyProgressBarLogger(QObject, ProgressBarLogger):
    """Custom progress bar logger for MoviePy updating progress in the UI and handling potential cancel from user.

    This class extends QObject to emit a signal to update the UI and ProgressBarLogger as it is used by MoviePy to log progress.

    Attributes:
        progress_bar_values (Signal): Signal emitting progress percentage and description.
        min_time_interval (float): Minimum time interval between progress updates.
    """
    progress_bar_values = Signal(int, str)
    def __init__(self):
        super().__init__()
        self.min_time_interval = 1.0

    def bars_callback(self, bar, attr, value, old_value=None):
        """Callback to update progress bars in the UI.

        Emits a signal with progress percentage and a description every "min_time_interval" seconds. This signal
        is used by the VideoMaker class to update the progress bar in the UI.

        Args:
            bar (str): The type of the progress bar (i.e chunk, or t).
            attr (str): The attribute being updated (i.e index: the current number elapsed of "bar").
            value (int): The current value of the attr.
            old_value (int, optional): The previous value of the attr.

        """
        if bar == 't' and attr == 'index':
            total = self.bars[bar]['total']
            percent = int((value / total) * 100)
            # value and total are in frames, so convert to seconds
            self.progress_bar_values.emit(percent, f"Editing - {percent}% : {(value / 60):.1f}s / {(total / 60):.1f}s")
        
#organize files in video created date
class VideoMaker():
    """
    Concatenates video clips and saves the final edited video.

    Args:
        update_progress_bar (Callable): Function to update the progress bar in the UI.
        data_dir (str): Directory where video clips are stored.

    Attributes:
        data_dir (str): Directory where video clips are stored.
        logger (MyProgressBarLogger): Custom logger to update the progress bar UI and allow for cancelling the video editing.
    """
    def __init__(self, update_progress_bar, data_dir):
        self.data_dir = os.path.join(data_dir, 'vids')
        self.logger = MyProgressBarLogger()
        self.logger.progress_bar_values.connect(update_progress_bar)

    def get_clip_order(self):
        #get all files in data directory
        clips_paths = [f for f in os.listdir(self.data_dir) if f.endswith('.mp4')]
        sorted_clips_paths = sorted(clips_paths, key=lambda x: int(x.split('.')[0]))
        return sorted_clips_paths
    
    async def create_video_clips(self, clip_paths):
        """Creates VideoFileClip objects from file paths with fade-in and fade-out effects.
        
        Args:
            clip_paths (list): List of video clip file paths.

        Returns:
            list: List of VideoFileClip objects.
        """
        new_clips = []
        # lazy loading
        from moviepy.video.fx.all import fadein, fadeout
        from moviepy.editor import VideoFileClip
        for clip_path in clip_paths:
            clip = VideoFileClip(clip_path, target_resolution = (720, 1280))
            clip = fadein(clip, duration=1)
            clip = fadeout(clip, duration=1) 
            new_clips.append(clip)
        
        return new_clips

    # concatenate all composite clips
    async def make_final_vid(self, clip_paths):
        """
        Concatenates video clips and writes the final video file.

        From a list of video clip paths, this function creates the video clip objects for each clip,
        concatenates them into a single video, and writes the file to disk.

        Args:
            clip_paths (list): List of video clip file paths, usually from the event_ids dataframe.

        Raises:
            Exception: For unexpected errors during video creation.    
        """
        clips = None
        final_vid = None
        from moviepy.editor import concatenate_videoclips
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
            await asyncio.sleep(1.0)
            if os.path.exists(os.path.join("temp-audio.mp3")):
                os.remove(os.path.join("temp-audio.mp3"))
                print("Deleted the temp audio file")
            