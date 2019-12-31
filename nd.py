#!/usr/bin/python3

import sys, getopt, requests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import eyed3

DirectSongURL = "http://music.163.com/song/media/outer/url?id=" #歌曲直链
SongURLPage = "https://music.163.com/song?id=" #歌曲页面
AlbumURLPage = "https://music.163.com/album?id=" #专辑页面
PlaylistURLPage = "https://music.163.com/playlist?id=" #歌单页面

fake_headers = {
    "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
}

gDriver = None #驱动
CoverOnly = False #只下载封面

def BootupDriver():
    global gDriver
    if not gDriver:
        print("Starting Chrome driver...")
        try:
            options = Options()
            options.add_argument("--headless")
            gDriver = webdriver.Chrome(options=options, executable_path='chromedriver')
            print("Done")
            return True
        except:
            print("Failed to start Chrome driver.")
            sys.exit()
            return False
    else:
        return True

class CSong():
    def __init__(self, pid = 0):
        self.id = pid #歌曲的ID
        self.artist = "\0" #歌手
        self.name = "\0" #名称
        self.album = "\0" #所属专辑
        self.coverlnk = "\0" #封面链接

    def get(self):
        if BootupDriver():
            print("Scraping infomation of song(%d)..." %(self.id))
            try:
                gDriver.get(SongURLPage + str(self.id))
                gDriver.switch_to.frame(gDriver.find_element_by_name("contentFrame"))
                soup = BeautifulSoup(gDriver.page_source, 'html.parser')

                self.name = soup.find("meta", property="og:title")["content"]
                self.artist = soup.find("meta", property="og:music:artist")["content"]
                self.album = soup.find("meta", property="og:music:album")["content"]
                if CoverOnly:
                    self.coverlnk = soup.find("img", class_="j-img")["data-src"] #原图封面
                else:
                    self.coverlnk = soup.find("img", class_="j-img")["src"] #缩小后的

                return True
            except:
                print("Failed to get song infomation of %d."%(self.id))
                return False

    def download(self, file = None): #在这里，file指特定的输出文件名
        if not CoverOnly:

            result = requests.get(DirectSongURL + str(self.id) + ".mp3", stream = True, headers=fake_headers) #请求音乐直链
            # DirectSongURL + ID + .mp3

            if result.url[len(result.url)-4:] != ".mp3":
                print("Cannot found this song(ID:%d)."%(id))
                result.close() ##终止##
            else:
                print("Downloading \"%s\" ..."%(self.name))
                total_size = int(result.headers['Content-length']) / 1024

                ####一行搞定
                save = ((self.name + " - " + self.artist) if not file else file) + ".mp3"
                save = save.replace('/', ", ") #去掉"/" 否则路径会错误

                with open(save, 'wb') as f:
                    for data in tqdm(iterable = result.iter_content(chunk_size = 1024), total = total_size, unit = 'KB'):
                        f.write(data)

                #下载封面，添加信息
                print("Configuring information...")

                result = requests.get(self.coverlnk, stream = False, headers=fake_headers)

                mp3 = eyed3.load(save)
                mp3.tag.artist = mp3.tag.album_artist = self.artist
                mp3.tag.title = self.name
                mp3.tag.album = self.album
                mp3.tag.images.set(3, result.content, 'image/jpg')
                mp3.tag.save()

                result.close()
                print("\033[92mSaved: %s\033[0m"%(save))
        else:
            result = requests.get(self.coverlnk, stream = True, headers=fake_headers)

            total_size = int(result.headers['Content-length']) / 1024
            save = ((self.name + " - " + self.artist) if not file else file) + ".jpg"
            save = save.replace('/', ", ") #去掉"/" 否则路径会错误
            with open(save, 'wb') as f:
                for data in tqdm(iterable = result.iter_content(chunk_size = 1024), total = total_size, unit = 'KB'):
                    f.write(data)
            print("\033[92mCover saved: %s\033[0m"%(save))

def GetSongID(value):
    try:
        int(value)
        #本身就是个整数，没必要转换
        return value
    except:
        position = value.find("song?id=")
        if position != -1:
            #是一个URL
            value = value[position+8:]
            return int(value)
        else:
            return -1

###接下来的专辑类，歌单类都类似于之前的设计###
class CAlbum():
    def __init__(self, aid = 0):
        self.id = aid
        self.name = "\0"
        self.artist = "\0"
        self.description = "\0"
        self.release_date = "\0"
        self.songs = [] ##歌曲列表(ID)
    def get(self):
        if BootupDriver():
            print("Scraping album's info...")
            try:
                gDriver.get(AlbumURLPage + str(self.id))
                gDriver.switch_to.frame(gDriver.find_element_by_name("contentFrame"))
                soup = BeautifulSoup(gDriver.page_source, 'html.parser')

                self.name = soup.find("meta", property="og:title")['content']
                self.description = soup.find( attrs={"name":"description"} )['content']
                self.release_date = soup.find("meta", property="music:release_date")['content']

                #修复bug后，这里又有一个新问题:不知道如何找到歌曲名称

                for a in soup.find_all('a', href=True):
                    sid = GetSongID(str(a['href']))
                    if sid != -1:
                        self.songs.append(sid)

                return True
            except:
                print("Failed to get album info of %d."%(self.id))
                return False

    def save(self, where):
        with open(where, 'a') as f:
            f.write("#-------------------\n#%s\n" % (self.description))
            for i in range(len(self.songs)):
                f.write("%d\n" % (self.songs[i]))
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


class CPlaylist():
    def __init__(self, plid = 0):
        self.id = plid
        self.name = "\0"
        self.songsID = []
        self.songsName = []
    def get(self):
        if BootupDriver():
            print("Getting playlist's info...")
            try:
                gDriver.get(PlaylistURLPage + str(self.id))
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
                    songID = GetSongID(lst[i].find('a')['href'])
                    if songID != -1:
                        self.songsID.append(songID)
                        self.songsName.append(lst[i].find('b')['title'])
                return True

            except:
                print("Failed to get playlist info of %d."%(int(self.id)))
                return False
    def save(self, where):
        with open(where, 'a') as f:
            f.write("#-------------------\n#%s\n" % (self.name))
            for i in range(len(self.songsID)):
                f.write("%d #%s\n" % (int(self.songsID[i]), self.songsName[i]))
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

def ShowHelps():
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
    ./nd.py -l list --- Download all songs from \"list\"
    ./nd.py -a https://music.163.com/#/album?id=3076168 -f list --- Save all songs from album 3076168 to \"list\"
    ./nd.py -p https://music.163.com/#/playlist?id=116090875 -f list --- Save all songs from playlist 116090875 to \"list\"""")

####################################

try:
    opts, args = getopt.getopt(sys.argv[1:], "ht:f:dl:ica:p:v",
    ["help","target=","filename=","download","list=","info","cover","album=","playlist=","version"])

except getopt.GetoptError as err:
    print(str(err))  # will print something like "option -a not recognized"
    sys.exit()

if not opts:
    ShowHelps()
    sys.exit()

songID = albumID = playlistID = -1
filename = "\0"
downloadSong = False
getInfo = False

for opt_name,opt_value in opts:
    if opt_name == '-c': #应该在所有选项之前
        CoverOnly = True
    if opt_name == '-h':
        ShowHelps()
        sys.exit() #end
    if opt_name == '-t':
        songID = GetSongID(opt_value)
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

            songtmp = CSong()

            for i in range(len(lines)):
                lines[i] = lines[i].replace(" ", "")
                intera = GetSongID(lines[i].split('#')[0]) #注释
                if intera != -1:
                    songtmp.id = int(intera)
                    if songtmp.get():
                        songtmp.download()
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
        print("Current version: 1.2");

if songID != -1:
    if getInfo:
        tmp = CSong(songID)
        if tmp.get():
            print("Name: %s\nArtist: %s\nAlbum: %s"%(tmp.name, tmp.artist, tmp.album))
    if downloadSong:
        tmp = CSong(songID)
        if tmp.get():
            if filename[0] != '\0':
                tmp.download(filename)
            else:
                tmp.download()

if albumID != -1:
    tmp = CAlbum(albumID)
    if tmp.get():
        listFile = "\0"
        if filename[0] != '\0':
            listFile = filename
        else:
            listFile = tmp.name

        tmp.save(listFile)

if playlistID != -1:
    tmp = CPlaylist(playlistID)
    if tmp.get():
        listFile = "\0"
        if filename[0] != '\0':
            listFile = filename
        else:
            listFile = tmp.name + ".txt"

        tmp.save(listFile)

if gDriver:
    gDriver.close()
    #记住！