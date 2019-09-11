#!/usr/bin/python3

#MIT License

#Copyright (c) 2019 Blume

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import sys, getopt, requests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import eyed3

url = "http://music.163.com/song/media/outer/url?id="
songURLPage = "https://music.163.com/#/song?id="
albumURLPage = "https://music.163.com/#/album?id="
playlistURLPage = "https://music.163.com/#/playlist?id="

fake_headers = {
    "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
}
#不然它不会重定向

gDriver = None

downloadCovers = False

def bootupDriver():
    global gDriver
    if not gDriver:
        print("Starting Chrome driver...")
        try:
            options = Options()
            options.add_argument("--headless")
            gDriver = webdriver.Chrome(options=options)
            print("Done")
            return True
        except:
            print("Failed to start Chrome driver.")
            sys.exit()
            return False
    else:
        return True

class songInfo():
    def __init__(self, pid = 0, pname = "\0"):
        self.id = pid
        self.artist = "\0"
        self.name = pname
        self.album = "\0"
        self.coverlnk = "\0"
    def get(self):   
        if bootupDriver():
            print("Getting song's info...")

            try:
                gDriver.get(songURLPage + str(self.id))
                gDriver.switch_to.frame(gDriver.find_element_by_name("contentFrame"))
                soup = BeautifulSoup(gDriver.page_source, 'html.parser')

                self.name = soup.find("meta", property="og:title")["content"]
                self.artist = soup.find("meta", property="og:music:artist")["content"]
                self.album = soup.find("meta", property="og:music:album")["content"]
                if downloadCovers:
                    self.coverlnk = soup.find("img", class_="j-img")["data-src"] #原图封面
                else:
                    self.coverlnk = soup.find("img", class_="j-img")["src"]

                return True
            except:
                print("Failed to get song info of %d."%(int(self.id)))
                return False

def getSongID(value):
    try:
        int(value)
        return value
    except:
        position = value.find("song?id=")
        if position != -1:
            value = value[position+8:]
            return int(value)
        else:
            return -1

class albumInfo():
    def __init__(self, aid = 0):
        self.id = aid
        self.name = "\0"
        self.artist = "\0"
        self.description = "\0"
        self.release_date = "\0"
        self.songs = []
    def get(self):
        if bootupDriver():
            print("Getting album's info...")
            try:
                gDriver.get(albumURLPage + str(self.id))
                gDriver.switch_to.frame(gDriver.find_element_by_name("contentFrame"))
                soup = BeautifulSoup(gDriver.page_source, 'html.parser')

                self.name = soup.find("meta", property="og:title")['content']
                self.description = soup.find( attrs={"name":"description"} )['content']
                self.release_date = soup.find("meta", property="music:release_date")['content']

                lst = soup.find_all("meta", property="og:music:album:song")
                for i in range(len(lst)):
                    temp = lst[i]['content']
                    pos = temp.find(";url=")
                    sid = getSongID(temp[pos + 4 + (len(songURLPage) - 1): ])
                    #4 is len(";url=")
                    if sid != -1:
                        self.songs.append(songInfo(sid, temp[6: pos]))

                return True
            except:
                print("Failed to get album info of %d."%(int(self.id)))
                return False
    def save(self, where):
        with open(where, 'a') as f:
            f.write("#-------------------\n#%s\n" % (tmp.description))
            for i in range(len(tmp.songs)):
                f.write("%d #%s\n" % (int(tmp.songs[i].id), tmp.songs[i].name))
            f.write("#-------------------\n\n")
        print("\033[92mSaved all songs to: %s\033[0m"%(where))

def getAlbumID(value):
    try:
        int(value)
        return value
    except:
        position = value.find("album?id=")
        if position != -1:
            value = value[position+9:]
            return int(value)
        else:
            return -1

class playlistInfo():
    def __init__(self, plid = 0):
        self.id = plid
        self.name = "\0"
        self.songs = []
    def get(self):
        if bootupDriver():
            print("Getting playlist's info...")
            try:
                gDriver.get(playlistURLPage + str(self.id))
                gDriver.switch_to.frame(gDriver.find_element_by_name("contentFrame"))
                soup = BeautifulSoup(gDriver.page_source, 'html.parser')

                self.name = soup.find("meta", property="og:title")['content']
                
                if self.name == "网易云音乐": #正常情况下，标题不可能是这个
                    print("The playlist %d is nonexistent! (or maybe it's private playlist?)"%(self.id))
                    return False

                #我不知道为什么在这里获取的内容和在浏览器获取的不一样
                #还有它可能很慢
                lst = soup.find_all("span", class_ = "txt")
                
                for i in range(len(lst)):
                    songID = getSongID(lst[i].find('a')['href'])
                    if songID != -1:
                        self.songs.append(songInfo(songID, lst[i].find('b')['title']))

                return True
            except:
                print("Failed to get playlist info of %d."%(int(self.id)))
                return False
    def save(self, where):
        with open(where, 'a') as f:
            f.write("#-------------------\n#%s\n" % (tmp.name))
            for i in range(len(tmp.songs)):
                f.write("%d #%s\n" % (int(tmp.songs[i].id), tmp.songs[i].name))
            f.write("#-------------------\n\n")
        print("\033[92mSaved all songs to: %s\033[0m"%(where))

def getPlaylistID(value):
    try:
        int(value)
        return value
    except:
        position = value.find("playlist?id=")
        if position != -1:
            value = value[position+12:]
            return int(value)
        else:
            return -1

def download(info = songInfo(), file = None):
    try:
        if downloadCovers:
            #抱歉同样的代码
            result = requests.get(info.coverlnk, headers=fake_headers, stream = True)
            total_size = int(result.headers['Content-length']) / 1024
            save = ((info.name + " - " + info.artist) if not file else file) + ".jpg"
            save = save.replace('/', ", ") #去掉"/" 否则路径会错误
            with open(save, 'wb') as f:
                for data in tqdm(iterable = result.iter_content(chunk_size = 1024), total = total_size, unit = 'KB'):
                    f.write(data)
            print("\033[92mSaved: %s\033[0m"%(save))
        else:
            result = requests.get(url + str(info.id) + ".mp3", headers=fake_headers, stream = True)
            if result.url[len(result.url)-4:] != ".mp3":
                print("Cannot found this song(ID:%d)."%(int(info.id)))
                result.close() ##终止##
            else:

                print("Downloading \"%s\" ..."%(info.name))

                total_size = int(result.headers['Content-length']) / 1024

                ####一行搞定
                save = ((info.name + " - " + info.artist) if not file else file) + ".mp3"
                save = save.replace('/', ", ") #去掉"/" 否则路径会错误

                with open(save, 'wb') as f:
                    for data in tqdm(iterable = result.iter_content(chunk_size = 1024), total = total_size, unit = 'KB'):
                        f.write(data)

                result.close()

                #下载封面，添加信息
                print("Configuring infos...")
                result = requests.get(info.coverlnk, headers=fake_headers, stream = False)

                mp3 = eyed3.load(save)
                mp3.tag.artist = mp3.tag.album_artist = info.artist
                mp3.tag.title = info.name
                mp3.tag.album = info.album
                mp3.tag.images.set(3, result.content, 'image/jpg')
                mp3.tag.save()

                print("\033[92mSaved: %s\033[0m"%(save))

    except requests.ConnectionError:
        print("Failed to download from server.")

def showHelps():
    print("""\033[91m
    ███╗   ██╗ ██████╗███╗   ███╗    ██████╗ ██╗     
    ████╗  ██║██╔════╝████╗ ████║    ██╔══██╗██║     
    ██╔██╗ ██║██║     ██╔████╔██║    ██║  ██║██║     
    ██║╚██╗██║██║     ██║╚██╔╝██║    ██║  ██║██║     
    ██║ ╚████║╚██████╗██║ ╚═╝ ██║    ██████╔╝███████╗
    ╚═╝  ╚═══╝ ╚═════╝╚═╝     ╚═╝    ╚═════╝ ╚══════╝
\033[0m""")
    print("""Parameters:
    -h Show helps
    -v Show version
    -t Target a song by its ID (Also can be link)
    -d Once download
    -f Output filename
    -l Download songs from a file (IDs list)
    -i Get a song's info
    -c Downloading only for covers(SRC)
    -a Save all songs from an album to a list
    -p Save all songs from a playlist to a list
    
Examples:
    ./nd.py -t 29460504 -d --- Download the song of ID 29460504
    ./nd.py -t https://music.163.com/#/song?id=29460504 -d --- Download the song of its page
    ./nd.py -t 29460504 -f MySong -d --- Download song of ID 2946050 and save as \"MySong.mp3\"
    ./nd.py -l list.txt --- Download all songs from \"list.txt\"
    ./nd.py -a https://music.163.com/#/album?id=3076168 -f list.txt --- Save all songs from album 3076168 to \"list.txt\"
    ./nd.py -p https://music.163.com/#/playlist?id=116090875 -f list.txt --- Save all songs from playlist 116090875 to \"list.txt\"""")

####################################

try:
    opts, args = getopt.getopt(sys.argv[1:], "ht:f:dl:ica:p:v",
    ["help","target=","filename=","download","list=","info","cover","album=","playlist=","version"])

except getopt.GetoptError as err:
    print(str(err))  # will print something like "option -a not recognized"
    sys.exit()
    
if not opts:
    showHelps()
    sys.exit()

songID = albumID = playlistID = -1
filename = "\0"
downloadSong = False
getInfo = False

for opt_name,opt_value in opts:
    if opt_name == '-c': #应该在所有选项之前
        downloadCovers = True
    if opt_name == '-h':
        showHelps()
        sys.exit() #end
    if opt_name == '-t':
        songID = getSongID(opt_value)
        if songID == -1:
            print("Invaild song ID.")
            sys.exit()
       
    if opt_name == '-f':
        filename = opt_value

    if opt_name == '-d':
        downloadSong = True

    if opt_name == '-l':
        success = False
        try:
            songList = open(opt_value, 'r')
            lines = songList.read().splitlines() #没有 \n
            for i in range(len(lines)):
                lines[i] = lines[i].replace(" ", "")
                intera = getSongID(lines[i].split('#')[0]) #注释
                if intera != -1:
                    tmp = songInfo(intera)
                    if tmp.get():
                        download(tmp)
            success = True
        except:
            print("Cannot open \"%s\"" % (opt_value))  
        finally:
            if success: #如果打开成功
                songList.close()
    
    if opt_name == '-i':
        getInfo = True

    if opt_name == '-a':
        albumID = getAlbumID(opt_value)
        if albumID == -1:
            print("Invaild album ID.")
            sys.exit()

    if opt_name == '-p':
        playlistID = getPlaylistID(opt_value)
        if playlistID == -1:
            print("Invaild playlistID ID.")
            sys.exit()

    if opt_name == "-v":
        print("Current version: Beta ZERO");

if songID != -1:
    if getInfo:
        tmp = songInfo(songID)
        if tmp.get():
            print("Name: %s\nArtist: %s\nAlbum: %s"%(tmp.name, tmp.artist, tmp.album))
    if downloadSong:
        tmp = songInfo(songID)
        if tmp.get():
            if filename[0] != '\0':
                download(tmp, filename)
            else:
                download(tmp)

if albumID != -1:
    tmp = albumInfo(albumID)
    if tmp.get():
        listFile = "\0"
        if filename[0] != '\0':
            listFile = filename
        else:
            listFile = tmp.name

        tmp.save(listFile + ".txt")

if playlistID != -1:
    tmp = playlistInfo(playlistID)
    if tmp.get():
        listFile = "\0"
        if filename[0] != '\0':
            listFile = filename
        else:
            listFile = tmp.name

        tmp.save(listFile + ".txt")

if gDriver:
    gDriver.close()
    #记住！