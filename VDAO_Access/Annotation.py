import os 
import utils
import sys

class Annotation:
    """
	This class represents a .txt file containing the labels and bounding
    boxes of objects in a given video.

        Developed by: Rafael Padilla
        SMT - Signal Multimedia and Telecommunications Lab
        COPPE - Universidade Federal do Rio de Janeiro
        Last modification: March 9th 2018
    """
    
    def __init__(self, annotationFilePath = None, totalFrames=None):
        self.totalFrames = totalFrames
        self.annotationFilePath = annotationFilePath
        self.listAnnotation = []
        self.parsed = False
        self.error = False
    
    # Returns True if parse was successfully done, otherwise returns False
    def _parseFile(self):
        if self.annotationFilePath == None or os.path.exists(self.annotationFilePath) == False:
            return False

        # (*) Annotation objects (not the file) will always start counting from 1
        # it means that if there are 8632 frames, listAnnotation will have
        # length of 8633, the first position (annot[0]) will always be discarded
        # Annotation file has its first frame count as 0

        # create array from 0 to totalFrames+1
        items = self.totalFrames+1
        self.listAnnotation.clear()
        [self.listAnnotation.append([]) for i in range(items)]

        f = open(self.annotationFilePath,"r")
        for line in f:
            params = line.split(' ')
            readFrame = int(params[1])+1 #(*)
            # Sometimes VDAO annotation file has annotated more frames than the video has.
            # Ex: annotation file 'obj-mult-ext-part02-video01.avi' has line: 'greenBox0 29039 0 0 0 0 3', but this file contains only 29034 frames
            if readFrame < items:
                # class, (x,y,r,b), subObj, 'class (subobj)', frame
                self.listAnnotation[readFrame].append((params[0], (int(params[2]),int(params[3]),int(params[4]),int(params[5])), int(params[6]), ('%s (%s)' % (params[0], params[6].replace('\n',''))), int(params[1])))
        f.close()
        self.parsed = True
        self.error = False
        return True
        
    # Return True if Annotation file is valid, otherwise return False
    def IsValid(self):
        if self.parsed == False:
            return self._parseFile()
        else:
            return self.error

    def GetClassesObjects(self):
        if self.parsed == False:
            self._parseFile()
        listObjects = []
        [[listObjects.append(bb[0][0:len(bb[0])-1]) for bb in annotation] for annotation in self.listAnnotation]
        return set(listObjects)
    
    # Ex: [0] = ('shoe0', (a,b,c,d), ..., 1) -> Frame 1 has 'shoe0' in bb (a,b,c,d)
    #     [1] = ('backpack1', (e,f,g,h), ...,3) -> Frame 3 has 'backpack1' in bb (e,f,g,h)
    #     [2] = ('backpack1', (e,f,g,h), ...,4) ('bottle1', (i,j,k,l), 4) -> Frame 4 has 'backpack1' in bb (e,f,g,h) and 'bottle1' in bb (i,j,k,l)
    def GetNonEmptyFrames(self):
        if self.parsed == False:
            self._parseFile()
        return  list(filter(lambda annot: annot != [], (annot for annot in self.listAnnotation)))
    
    def GetNumberOfAnnotatedFrames(self):
        if self.parsed == False:
            self._parseFile()
        nonEmptyFrames = self.GetNonEmptyFrames()
        minObj = (sys.maxsize,-1,-1,-1,-1,-1) # (area,frame,x,y,r,b)
        maxObj = (-1,-1,-1,-1,-1,-1) # (area,frame,x,y,r,b)
        counted=[]
        for nef in nonEmptyFrames:
            for f in nef:
                counted.append(f[4])
                area = (f[1][0]-f[1][2])*(f[1][1]-f[1][3]) #(x2-x1)*(y2-y1)
                if area < minObj[0]:
                    minObj = (area,f[4],f[1])
                if area > maxObj[0]:
                    maxObj = (area,f[4],f[1])
        return [len(set(counted)), min(counted), max(counted), minObj, maxObj]

    @staticmethod
    def FilterOnlySpecificObjects(refAnnotation, labels):
        if refAnnotation.parsed == False:
            refAnnotation._parseFile()
        # Create a new annotation object the with the same annotations as the reference one
        annot = Annotation()
        items = len(refAnnotation.listAnnotation)
        [annot.listAnnotation.append([]) for i in range(items)]

        frameNumber = 0
        for annotation in refAnnotation.listAnnotation:
            if annotation != []:
                for label in labels:    
                    for a in annotation:
                        if a[0].lower().startswith(label.lower()):
                            annot.listAnnotation[frameNumber].append(a)
            frameNumber = frameNumber + 1
        # sort by frame position
        return annot

    @staticmethod
    def FilterOnlyNonOverlappingObjects(refAnnotation):
        if refAnnotation.parsed == False:
            refAnnotation._parseFile()

        # Create a new annotation object the with the same annotations as the reference one
        annot = Annotation()
        items = len(refAnnotation.listAnnotation)
        [annot.listAnnotation.append([]) for i in range(items)]

        # go through each annotation (bounding box)
        boxes = []
        for frameId in range(len(refAnnotation.listAnnotation)):
            boxes.clear()
            for a in range(len(refAnnotation.listAnnotation[frameId])):
                box = refAnnotation.listAnnotation[frameId][a][1]
                boxes.append(box)
            nonOverlappedBoxes, idx = utils.getNonOverlappedBoxes(boxes)

            for b in range(len(nonOverlappedBoxes)):
                annot.listAnnotation[frameId].append(refAnnotation.listAnnotation[frameId][idx[b]])
        return annot

            