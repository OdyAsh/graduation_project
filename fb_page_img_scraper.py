# Useless file: it was initially used to run parallel helium chrome browsers, 
# but the shared list doesn't work, 
# so I just used this function in a synchronous fashion in data_scraper.ipynb 
from helium import *
import regex as re
import html
import pickle
import time
import threading
import multiprocessing
from multiprocessing import Process

dataDir = '/dataset'
listAndDicLock = threading.Lock()
allEmemesLinks = []
prevObtainedPages = {}

def pklSave(contentToBeSaved, fullPath):
    with open(fullPath, 'wb') as f:
        pickle.dump(contentToBeSaved, f)

def pklLoad(fullPath):
    with open(fullPath, 'rb') as f:
        contentToBeLoaded = pickle.load(f)
    return contentToBeLoaded

def scrollTillEnd(heliumBrowser):
    heliumBrowser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    lenOfPage = heliumBrowser.execute_script("var lenOfPage=document.body.scrollHeight; return lenOfPage;")
    match=False
    while(match==False):
        lastCount = lenOfPage
        time.sleep(2)
        heliumBrowser.execute_script("window.scrollTo(0, document.body.scrollHeight); window.scrollBy(0,-200);")
        lenOfPage = heliumBrowser.execute_script("var lenOfPage=document.body.scrollHeight; return lenOfPage;")
        if lastCount==lenOfPage:
            match=True
        break

def fbPageName(htmlText):
    headerOfPageTitle = re.search('<h[12] .+?(?=/h[12]>)', htmlText)
    if (headerOfPageTitle is None):
        return ""
    headerOfPageTitle = headerOfPageTitle.group() #group() to get the entired matched string out of the regex "match" object
    spanText = re.search('<span>(.*)</span>', headerOfPageTitle)
    if (spanText is not None):
        pageName = spanText.group(1).strip() # group(1) to return what is between parentheses
    else:
        pageName = re.search('>(.*)<', headerOfPageTitle).group(1).strip()
    return pageName

def fbExtractImgsLinks(htmlText):
    try:
        htmlStartingFromAllPhotos = re.findall(r'>(?:All )?[pP]hotos.*', htmlText)[0] # Regex to get pages starting from "All photos" or "photos", but it has to be preceded by ">", in order not to match "photos" in random URLs
    except Exception as e:
        print(e)
        return []
    imgLinks = re.findall(r'https://scontent[^"]+', htmlStartingFromAllPhotos)
    imgLinks = [html.unescape(link) for link in imgLinks][1:] #avoiding first image, as it might be the page's logo
    return imgLinks

def fbExtractImgsLinksOld(heliumBrowser): # didn't use this, as regex is faster than selenium methods 
    imgTags = heliumBrowser.find_elements_by_tag_name('img')
    imgLinks = []
    for link in imgTags:
        if link.get_attribute('src') is not None:
            imgLinks.append(link.get_attribute('src'))
    imgLinks = [html.unescape(link) for link in imgLinks][1:] #avoiding first image, as it might be the page's logo
    return imgLinks

def fbPageImgScraper(pagesLinks, startIdx, endIdx):
    heliumBrowser = start_chrome(headless=False)
    for i in range(startIdx, len(pagesLinks)):
        if i == endIdx:
            break
        heliumBrowser.get(pagesLinks[i])
        pageName = fbPageName(heliumBrowser.page_source)
        if pageName == "":
            print("page not found...")
            continue
        if (pageName in prevObtainedPages):
            print("This page has already been scraped")
            continue
        time.sleep(1)
        press(PAGE_DOWN)
        press(PAGE_DOWN)
        time.sleep(1)
        try:
            click('Close')
        except Exception as e:
            print("pop-up didn't  show, moving on...")
        print("Scrolling page:", pageName)
        scrollTillEnd(heliumBrowser)
        imgLinks = fbExtractImgsLinks(heliumBrowser.page_source)[:5]
        with listAndDicLock:
            allEmemesLinks.extend(imgLinks) #extend() expands the elements of an iterable
            pklSave(imgLinks, f"{dataDir}ememesLinksfbPage{i}.pickle")
            prevObtainedPages[pageName] = (i, pagesLinks[i])
        if i == endIdx-1 or i == len(pagesLinks)-1:
            print("Finished scraping!", end='\n\n')
        else:
            print("Finished, scraping next link...", end='\n\n')
    print(len(imgLinks))

def getAsyncPagesFunctions(fbPagesLinks, interval):
    fns = []
    i = 0
    while i < len(fbPagesLinks):
        fns.append((fbPageImgScraper, (fbPagesLinks, i, i+interval)))
        i += interval
    return fns

def runInParallel(fns):
  proc = []
  for fn in fns:
    p = Process(target=fn[0], args=(fn[1]))
    p.start()
    proc.append(p)
  for p in proc:
    p.join()

if __name__ == "__main__":
    fbLinks = [
        "https://www.facebook.com/%D9%85%D9%8A%D9%85%D8%B2-%D9%84%D8%A7-%D9%81%D8%A7%D8%A6%D8%AF%D8%A9-%D9%85%D9%86%D9%87%D8%A7-%D9%85%D8%AB%D9%84-%D8%AD%D9%8A%D8%A7%D8%AA%D9%83-290489111460684/photos",
        "https://www.facebook.com/MemesYard/photos/?ref=page_internal",
        "https://www.facebook.com/memes.Stolen.1.0/photos/?ref=page_internal",

        "https://www.facebook.com/%D8%A8%D9%86%D8%B3%D8%B1%D9%82-%D9%85%D9%8A%D9%85%D8%B2-%D9%88%D9%83%D9%88%D9%85%D9%8A%D9%83-%D8%B9%D8%B4%D8%A7%D9%86-%D9%85%D8%B4-%D8%A8%D9%86%D8%B9%D8%B1%D9%81-%D9%86%D8%B9%D9%85%D9%84-1735677470065180/photos/?ref=page_internal",
        "https://www.facebook.com/profile.php?id=100064850389099&sk=photos",
        "https://www.facebook.com/%D9%85%D9%8A%D9%85%D8%B2-%D9%84%D9%88%D8%B1%D8%AF-%D9%82%D9%85%D8%AF-100182408618014/photos/?ref=page_internal",
        
        "https://www.facebook.com/%D9%85%D9%8A%D9%85%D8%B2-%D9%85%D8%B5%D8%B1%D9%8A%D9%87-101966151287716/photos/?ref=page_internal",
        "https://www.facebook.com/%D9%85%D9%8A%D9%85%D8%B2-%D9%85%D8%B4-%D9%87%D9%8A%D9%81%D9%87%D9%85%D9%87%D8%A7-%D8%A7%D9%84%D9%86%D9%88%D8%B1%D9%85%D9%8A%D8%B2-%D8%B9%D8%B4%D8%A7%D9%86-%D9%86%D9%88%D8%B1%D9%85%D9%8A%D8%B2-833501407023909/photos/?ref=page_internal",
        "https://www.facebook.com/arabicclassicalartmemes/photos/?ref=page_internal",
        
        "https://web.facebook.com/True.Memes.Comics/photos/?ref=page_internal",
        "https://web.facebook.com/societyforsarcasm/photos/?ref=page_internal",
        "https://web.facebook.com/memes.officil/photos",
    ]
    fns = getAsyncPagesFunctions(fbLinks, len(fbLinks)//3)
    runInParallel(fns)

    pklSave(allEmemesLinks, f"{dataDir}allFbPagesEmemes.pickle")
    pklSave(prevObtainedPages, f"{dataDir}fbPagesUsed.pickle")