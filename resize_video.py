import cv2


def resize_frame(input_frame, output_width, output_height):
    input_height, input_width = input_frame.shape[:2]
    input_aspect_ratio = input_width / input_height
    output_aspect_ratio = output_width / output_height

    if input_aspect_ratio > output_aspect_ratio:
        # Original video is wider than the target aspect ratio; crop width
        new_width = int(input_height * output_aspect_ratio)
        x_offset = (input_width - new_width) // 2
        cropped_frame = input_frame[:, x_offset:x_offset + new_width]
    else:
        # Original video is taller; crop height
        new_height = int(input_width / output_aspect_ratio)
        y_offset = (input_height - new_height) // 2
        cropped_frame = input_frame[y_offset:y_offset + new_height, :]

    resized_frame = cv2.resize(cropped_frame, (output_width, output_height))

    return resized_frame


def resize_video_to_fill(video_path, output_path, output_width, output_height):
    # Open the input video file
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (output_width, output_height))

    # Get the original video dimensions
    input_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    input_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    input_aspect_ratio = input_width / input_height
    output_aspect_ratio = output_width / output_height

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize with aspect ratio adjustment
        if input_aspect_ratio > output_aspect_ratio:
            # Original video is wider than the target aspect ratio; crop width
            new_width = int(input_height * output_aspect_ratio)
            x_offset = (input_width - new_width) // 2
            cropped_frame = frame[:, x_offset:x_offset+new_width]
        else:
            # Original video is taller; crop height
            new_height = int(input_width / output_aspect_ratio)
            y_offset = (input_height - new_height) // 2
            cropped_frame = frame[y_offset:y_offset+new_height, :]

        # Resize cropped frame to fit exactly the output size
        resized_frame = cv2.resize(cropped_frame, (output_width, output_height))

        # Write the resized frame to the output video
        out.write(resized_frame)

    # Release resources
    cap.release()
    out.release()
    print("Resized video saved to:", output_path)

# Example usage
if __name__ == "__main__":
    resize_video_to_fill(r'data\bee_orig.mp4', r'data\bee01.mp4', 1080, 960)
