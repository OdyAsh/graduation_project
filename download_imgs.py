import requests
import os

def downloadImgs(imgType, imgsUrls, startIdx = 0, endIdx = -1, offset = 0):
    path = os.path.join('dataset/', imgType)
    for i in range(startIdx, len(imgsUrls)):
        try:
            if i == endIdx:
                return
            img = requests.get(imgsUrls[i]).content
            fileName = f"{imgType[imgType.find('.')+2:]}{format(i+offset, '07d')}.jpg"
            filePath = os.path.join(path, fileName)
            with open(filePath, 'wb') as f:
                f.write(img)
        except Exception as e:
            print(e)