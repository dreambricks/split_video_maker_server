import cProfile
import pstats
from video_stacker import stack_videos_vertically_with_loop


def profile_code():
    input_video1 = r'examples\4k_30fps_15s.mov'
    input_video2 = r'examples\4k_60fps_133s.mov'
    output_video = r'examples\out06.mp4'
    stack_videos_vertically_with_loop(input_video1, input_video2, output_video)


if __name__ == "__main__":
    cProfile.run('profile_code()', 'profile_output')

    # Analyze the profiling results
    with open('profile_results.txt', 'w') as f:
        p = pstats.Stats('profile_output', stream=f)
        p.sort_stats('cumulative').print_stats()
