import av,sys,json,numpy as np,h5py,math,os,torch,time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def getFramesFromVideo(videoPath, startFrame, endFrame, scaleWidth, scaleHeight):
    print(f"Extracting frames from {startFrame} to {endFrame}...")
    container = av.open(videoPath)
    frames = []

    stream = container.streams.video[0]
    frameIndex = 0

    for packet in container.demux(stream):
        for frame in packet.decode():
            if startFrame <= frameIndex < endFrame:
                frameImage = frame.to_image().resize((scaleWidth, scaleHeight))
                frames.append(np.array(frameImage))
            frameIndex += 1
            if frameIndex >= endFrame:
                return np.array(frames)
    
    return np.array(frames)

def calculateLuminanceBatch(frames):
    if frames is None or frames.size == 0:
        raise ValueError("No frames provided for luminance calculation.")
    
    framesTensor = torch.tensor(frames, dtype=torch.float32, device=device)
    framesTensor /= 255.0
    luminance = 0.299 * framesTensor[:, :, :, 2] + 0.587 * framesTensor[:, :, :, 1] + 0.114 * framesTensor[:, :, :, 0]
    luminance = luminance * 255.0
    return luminance.cpu().numpy().astype(np.uint8)

def getMetadata(videoPath):
    print("Gathering Metadata...")
    container = av.open(videoPath)
    stream = container.streams.video[0]

    width = stream.width
    height = stream.height
    totalFrames = sum(1 for _ in container.demux(stream))
    fps = float(stream.average_rate)
    
    duration = totalFrames / fps if fps > 0 else 0
    
    print(f"Width: {width}, Height: {height}, Frames: {totalFrames}, FPS: {fps}, Duration: {duration}")

    return width, height, totalFrames, duration

if __name__ == "__main__":
    args = sys.argv[1:]
    videoPath = args[0]
    print(f"Video path: {videoPath}")

    print("Loading Settings...")
    with open('./conf/settings.json', 'r') as settingsJson:
        settings = json.load(settingsJson)

    fontWidth = settings['capture']['fontWidth']
    fontHeight = settings['capture']['fontHeight']
    
    width, height, totalFrames, duration = getMetadata(videoPath)

    scaleWidth = int((settings['capture']['scaledWidth'] if settings['capture']['scaledWidth'] != -1 else width*2) / fontWidth)
    scaleHeight = int((settings['capture']['scaledHeight'] if settings['capture']['scaledHeight'] != -1 else height*2) / fontHeight)
    
    bufferSize = 512
    hdf5File = f'./saved/{os.path.basename(videoPath)}.ascii'

    totalFramesProcessed = 0
    totalProcessingTime = 0.0

    print("Creating Ascii File...")
    with h5py.File(hdf5File, 'w') as h5f:
        chunks = (min(bufferSize, totalFrames), scaleHeight, scaleWidth)
        
        luminanceDataset = h5f.create_dataset(
            "luminanceData",
            (totalFrames, scaleHeight, scaleWidth),
            dtype=np.uint8,
            compression="gzip",
            compression_opts=9,
            chunks=chunks
        )

        buffer = []
        printInterval = max(1, totalFrames // 100)

        print("Starting Main Loop...")

        for startFrame in range(0, totalFrames, bufferSize):
            endFrame = min(startFrame + bufferSize, totalFrames)
            
            startTime = time.time()
            
            frames = getFramesFromVideo(videoPath, startFrame, endFrame, scaleWidth, scaleHeight)
            if frames is None or frames.size == 0:
                print(f"Warning: No frames extracted for range {startFrame}-{endFrame}.")
                continue

            luminanceBatch = calculateLuminanceBatch(frames)
            
            buffer.extend(luminanceBatch)
            if len(buffer) >= bufferSize:
                startIdx = startFrame
                endIdx = min(startFrame + bufferSize, totalFrames)
                luminanceDataset[startIdx:endIdx, :, :] = buffer[:bufferSize]
                buffer = buffer[bufferSize:]
            
            elapsedTime = time.time() - startTime
            totalProcessingTime += elapsedTime
            totalFramesProcessed += len(frames)

            currentFrame = endFrame - 1
            percentage = (currentFrame / totalFrames) * 100
            fps = len(frames) / elapsedTime if elapsedTime > 0 else 0
            print(f"{percentage:.2f}% | Frame: {currentFrame}/{totalFrames} | FPS: {fps:.2f} | Buffer Size: {len(buffer)}")

        if buffer:
            startIdx = totalFrames - len(buffer)
            luminanceDataset[startIdx:totalFrames, :, :] = buffer

    fpsAvg = totalFramesProcessed / totalProcessingTime if totalProcessingTime > 0 else 0
    print(f"FPS AVG: {fpsAvg:.2f}")