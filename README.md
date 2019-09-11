# NCM-DL
用Python爬虫从网易云音乐上批量下载歌曲<br/>
使用BeautifulSoup + selenium webdriver<br/>
(要使用脚本，你必须要有Chrome driver!)<br/>

参数:<br/>
    -h 显示帮助<br/>
    -v 显示版本<br/>
    -t 目标歌曲的ID (也可以是歌曲页面链接)<br/>
    -d 单次下载<br/>
    -f 输出的文件名<br/>
    -l 下载列表文件里所有的歌曲<br/>
    -i 获取单曲信息<br/>
    -c 只下载封面而不是歌曲<br/>
    -a 保存一个专辑内所有的歌曲到一个列表文件<br/>
    -p 保存一个歌单内所有的歌曲到一个列表文件<br/>

(第一次用Python写爬虫还是有挺多bug的:P)

Using Python web scraping to download songs from Netease Music<br/>
BeautifulSoup + selenium webdriver<br/>
(To use this script, you must have Chrome driver!)<br/>
Parameters:<br/>
    -h Show helps<br/>
    -v Show version<br/>
    -t Target a song by its ID (Also can be link)<br/>
    -d Once download<br/>
    -f Output filename<br/>
    -l Download songs from a file (IDs list)<br/>
    -i Get a song's info<br/>
    -c Downloading only for covers(SRC)<br/>
    -a Save all songs from an album to a list<br/>
    -p Save all songs from a playlist to a list<br/>
(It's first time I code spider in Python, it may have unknow bugs :P)
