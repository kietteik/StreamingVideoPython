class VideoStream:
    def __init__(self, filename):
        self.frameDict = {}
        self.currFrame = 0
        self.filename = filename
        try:
            self.file = open(filename, 'rb')
        except:
            raise IOError
        self.frameNum = 0

    def nextFrame(self):
        """Get next frame."""
        data = self.file.read(5)  # Get the framelength from the first 5 bits
        if data:
            framelength = int(data)

            # Read the current frame
            data = self.file.read(framelength)
            self.frameNum += 1
        return data

    def frameNbr(self):
        """Get frame number."""
        return self.frameNum

    def totalFrame(self):
        with open(self.filename, 'rb') as file:
            frameCount = 0
            length = file.read(5)
            while length:
                data = file.read(int(length))
                frameCount += 1
                length = file.read(5)
                self.frameDict[frameCount] = data
        return frameCount
