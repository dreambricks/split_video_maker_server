import os
import cv2
import subprocess
from resize_video import resize_frame

def stack_videos_vertically_with_loop(video1_path, video2_path, output_video_path, output_width=1080, output_height=1920):

    video1_path_no_ext, t_ext = os.path.splitext(video1_path)
    temp_audio_path = video1_path_no_ext + "_temp_audio.aac"
    temp_video_path = video1_path_no_ext + "_temp_video.mp4"

    # Open the video files
    cap1 = cv2.VideoCapture(video1_path)
    cap2 = cv2.VideoCapture(video2_path)

    # Get properties of the first video
    width1 = int(cap1.get(cv2.CAP_PROP_FRAME_WIDTH))
    height1 = int(cap1.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps1 = cap1.get(cv2.CAP_PROP_FPS)
    change1 = width1 != output_width or height1 != output_height / 2

    # Get properties of the second video
    width2 = int(cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
    height2 = int(cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps2 = cap2.get(cv2.CAP_PROP_FPS)
    change2 = width2 != output_width or height2 != output_height / 2

    # Use the minimum fps between the two videos to prevent errors
    fps = min(fps1, fps2)

    # Ensure videos have the same width; resize if necessary
    #if width1 != width2:
    #    raise ValueError("The videos have different widths. Please resize them to match.")

    # Define the codec and create VideoWriter for the output video
    #output_height = height1 + height2
    output_size = (output_width, output_height)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, output_size)

    # Read and stack frames
    while True:
        ret1, frame1 = cap1.read()

        # If the first video ends, stop
        if not ret1:
            break

        # Read the second video's frame, reset to the start if it finishes
        ret2, frame2 = cap2.read()
        if not ret2:  # Loop second video
            cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret2, frame2 = cap2.read()

        if change1:
            frame1 = resize_frame(frame1, output_width, output_height // 2)

        if change2:
            frame2 = resize_frame(frame2, output_width, output_height // 2)

        # Stack frames vertically
        stacked_frame = cv2.vconcat([frame1, frame2])

        # Write the stacked frame to the output video
        out.write(stacked_frame)

    # Release everything
    cap1.release()
    cap2.release()
    out.release()

    print('Finished merging files')
    try:
        print('Creating audio file')
        # extract audio from the first video using FFmpeg
        subprocess.run(['ffmpeg', '-i', video1_path, '-q:a', '0', '-map', 'a', temp_audio_path], check=True)
    except:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        print('Error when creating audio file')

    print('Final step')
    if os.path.exists(temp_audio_path):
        print('Merging audio into final video')
        # combine the output video with the extracted audio
        subprocess.run(
            ['ffmpeg', '-i', temp_video_path, '-i', temp_audio_path, '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0',
             '-map', '1:a:0', output_video_path], check=True)

        # clean up
        os.remove(temp_audio_path)
        os.remove(temp_video_path)
    else:
        print('No audio file')
        os.rename(temp_video_path, output_video_path)

    print("Video stacking with looping complete. Output saved to:", output_video_path)


if __name__ == "__main__":
    # Example usage
    stack_videos_vertically_with_loop(r'examples\bee_orig.mp4', r'examples\particles_orig.mp4', r'examples\out03.mp4')
    # stack_videos_vertically_with_loop(r'examples\IMG_0944.mov', r'examples\IMG_3102.MOV', r'examples\IMG_0944_IMG_3102.mp4')
    # stack_videos_vertically_with_loop(r'examples\IMG_09702.mov', r'examples\IMG_3102.MOV', r'examples\IMG_09702_IMG_3102.mp4')
    # stack_videos_vertically_with_loop(r'examples\IMG_0970.mov', r'examples\IMG_3102.MOV', r'examples\IMG_0970_IMG_3102.mp4')
    # stack_videos_vertically_with_loop(r'examples\IMG_0976.mov', r'examples\IMG_3102.MOV', r'examples\IMG_0976_IMG_3102.mp4')
    # stack_videos_vertically_with_loop(r'examples\IMG_0988.mov', r'examples\IMG_3102.MOV', r'examples\IMG_0988_IMG_3102.mp4')
