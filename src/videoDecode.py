import h5py,numpy as np,time,sys,json,tempfile,multiprocessing
from collections import deque
from pydub import AudioSegment
from pydub.playback import play

def playAudio(audio_file):
    audio = AudioSegment.from_mp3(audio_file)
    play(audio)

def luminanceToChar(luminance):
    indices = np.searchsorted(charThreshold, luminance, side='right') - 1
    return chars[indices]

def readFrame(path, frameIndex):
    with h5py.File(path, 'r') as h5f:
        lumData = h5f['luminanceData']
        if frameIndex < 0 or frameIndex >= lumData.shape[0]:
            raise IndexError(f"Frame index {frameIndex} is out of bounds for dataset with {lumData.shape[0]} frames.")
        frame = lumData[frameIndex, :, :]
    return frame

def displayFrames(filePath, fps):
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    
    frameIndex = 0
    frameBuffer = deque(maxlen=2)
    prevFrameArray = None
    prevCharArray = None
    luminanceThreshold = 0.5
    
    frameInterval = 1 / fps
    next_frame_time = time.time()
    
    try:
        while True:
            if len(frameBuffer) < 2:
                frameArray = readFrame(filePath, frameIndex)
                charArray = luminanceToChar(frameArray)
                frameBuffer.append((frameArray, charArray))
                frameIndex += 1
            
            if frameBuffer:
                current_time = time.time()
                if current_time < next_frame_time:
                    time.sleep(next_frame_time - current_time)
                
                sys.stdout.write("\033[H")  
                frameArray, charArray = frameBuffer.popleft()
                
                if prevFrameArray is not None:
                    mask = np.abs(frameArray - prevFrameArray) > luminanceThreshold
                    charArray = np.where(mask, charArray, prevCharArray)
                
                screenBuffer = ''.join([''.join(row) + '\n' for row in charArray])
                sys.stdout.write(screenBuffer)
                sys.stdout.flush()
                
                prevFrameArray = frameArray
                prevCharArray = charArray
                
                next_frame_time += frameInterval
    
    except IndexError:
        pass

    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        
if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        chars = np.array([' ', '`', '.', '-', "'", ':', '_', ',', '^', '=', ';', '>', '<', '+', '!', 'r', 'c', '*', '/', 'z', '?', 's', 'L', 'T', 'v', ')', 'J', '7', '(', '|', 'F', 'i', '{', 'C', '}', 'f', 'I', '3', '1', 't', 'l', 'u', '[', 'n', 'e', 'o', 'Z', '5', 'Y', 'x', 'j', 'y', 'a', ']', '2', 'E', 'S', 'w', 'q', 'k', 'P', '6', 'h', '9', 'd', '4', 'V', 'p', 'O', 'G', 'b', 'U', 'A', 'K', 'X', 'H', 'm', '8', 'R', 'D', '#', '$', 'B', 'g', '0', 'M', 'N', 'W', 'Q', '%', '&', '@'])
        charThreshold = np.array([-np.inf, 19.1, 21.1, 21.6, 31.2, 35.7, 39.7, 47.1, 55.6, 61.6, 65.5, 72.7, 74.0, 74.4, 79.0, 81.3, 82.4, 83.9, 86.2, 92.0, 92.2, 93.5, 95.2, 95.5, 97.8, 99.9, 100.9, 101.5, 101.8, 103.9, 104.3, 104.5, 107.1, 107.8, 108.2, 108.9, 109.4, 110.3, 111.7, 111.8, 112.7, 114.0, 114.1, 114.8, 116.3, 116.7, 117.5, 118.2, 119.0, 119.4, 119.6, 119.9, 123.2, 124.4, 126.0, 126.3, 127.2, 140.4, 141.9, 142.0, 142.5, 142.8, 142.8, 144.0, 147.2, 147.3, 148.3, 149.6, 152.2, 152.9, 154.0, 154.2, 155.3, 155.5, 164.8, 167.3, 168.1, 169.0, 171.2, 172.3, 173.6, 173.8, 176.5, 179.4, 180.6, 184.4, 186.2, 186.9, 193.8, 199.7, 204.9, 250.9])

        with open('./conf/settings.json', 'r') as settingsJson:
            settings = json.load(settingsJson)
        
        try:
            tmp=tempfile.gettempdir()
            audioFile = f'{tmp}\\{str(args)[:-11].rsplit("/", 1)[-1]}mp3'

            audioSegment = AudioSegment.from_mp3(audioFile)

            audio = multiprocessing.Process(target=playAudio, args=(audioFile,))

            audio.start()
        except:
            print("Failed to load audio. Does this video have audio?")

        asciiFile = args[0]
        print(f"Ascii file path: {asciiFile}")

        time.sleep(1)

        displayFrames(asciiFile, fps=settings['playback']['framerate'])

    else:
        print("No file path provided.")
    