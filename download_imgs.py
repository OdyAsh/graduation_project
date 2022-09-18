import requests
import os

def downloadImgs(imgType, imgsUrls, startIdx = 0, endIdx = -1, offset = 0):
    path = os.path.join('dataset/', imgType)
    for i in range(startIdx, len(imgsUrls)):
        try:
            if i == endIdx:
                return
            img = requests.get(imgsUrls[i], timeout=(10, 30)).content # remove the timeout parameter if you'll leave your computer over night and worry about connection loss (note that you'll probably interrupt the .ipynb because the requests.get() will probably not reuturn at one of the requests, so p.join() in runInParallel() will not finish)
            fileName = f"{imgType[imgType.find('.')+2:]}{format(i+offset, '07d')}.jpg"
            filePath = os.path.join(path, fileName)
            with open(filePath, 'wb') as f:
                f.write(img)
        except Exception as e:
            print(e)