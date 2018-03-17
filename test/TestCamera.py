import picamera

camera = picamera.PiCamera()
camera.resolution = '1080p'
camera.framerate = 30
camera.vflip = True
camera.annotate_frame_num = True

camera.start_preview(fullscreen=False, window = (960, 0, 960, 540))

video_file='/home/camera/vte/data/my_video.h264'
picam_quality=25

camera.start_recording(video_file, quality=picam_quality, level='4.2', format='h264')
camera.wait_recording(300)
camera.stop_recording()
camera.stop_preview()
