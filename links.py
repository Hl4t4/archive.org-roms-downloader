# from progressbar import ProgressBar, Percentage, Bar, ETA, FileTransferSpeed
import urllib.request, urllib.parse
from tqdm import tqdm
import requests
import sys
import time
from multiprocessing import Pool
import os
import subprocess
from requests.adapters import HTTPAdapter, Retry
import zipfile
from datetime import datetime
import pandas as pd

MAX_PROCCESSES = 5
CONSOLE = 'PS2'

class Game ():
    def __init__(self, name: str, url: str, size: float, update_time: datetime, console: str) -> None:
        self.__name = name
        self.__url = url
        self.__size = size
        self.__update_time = update_time
        self.__console = console

    @property
    def name(self) -> str:
        return self.__name
    
    @name.setter
    def name(self, name:str) -> None:
        self.__name = name
    
    @property
    def url(self) -> str:
        return self.__url
    
    @url.setter
    def url(self, url:str) -> None:
        self.__url = url
    
    @property
    def size(self) -> str:
        return self.__size
    
    @size.setter
    def size(self, size:float) -> None:
        self.__size = size
    
    @property
    def update_time(self) -> str:
        return self.__update_time
    
    @update_time.setter
    def update_time(self, update_time:float) -> None:
        self.__update_time = update_time
    
    @property
    def console(self) -> str:
        return self.__console
    
    @console.setter
    def console(self, console:str) -> None:
        self.__console = console

    def __str__(self) -> str:
        return f'The game {self.name} Console {self.console} - with a size {self.size}GB - url {self.url} - last updated {self.update_time}'
    
    def as_dict(self) -> dict:
        return {'file_name' : self.name, 'console' : self.console, 'file_size' : self.size, 'url' : self.url, 'last_updated' : pd.Timestamp(self.update_time)}


def filetype_checker(line):
    ######## Faltan los tipos de archivos partidos #########
    ######## .app filetype genera problemas, quizas se solucione con regex en vez de in ###########
    archives_filetypes = ['.7z', '.7zip', '.zip', '.tar.gz', '.gz', '.tar', '.gzip', '.rar']
    disk_filetypes = ['.iso', '.img', '.bin', '.cue', '.chd', '.mdf', '.mds', '.ecm', '.cso', '.gcz', '.rvz', '.cdi', '.gdi', '.sbi', '.sub', '.nrg', '.isz', '.fds', '.ndd', '.adf', '.adz', '.adf.gz', '.dms', '.ipf']
    tape_filetypes = ['.wav', '.tap', '.tzx', '.cdc', '.cas']
    rom_filetypes = ['.nes',  '.nez', '.unf', '.unif', '.smc', '.sfc', '.md', '.smd', '.gen', '.gg', '.z64', '.v64', '.n64', '.gb', '.gbc', '.gba', '.srl', '.gcm', '.gcz', '.xiso', '.nds', '.dsi', '.nds', '.ids', '.wbfs', '.wad', '.cia', '.3ds', '.nsp', '.xci', '.ngp', '.ngc', '.pce', '.vpk', '.vb', '.ws', '.wsc', '.bin', '.dat', '.lst', '.ipa', '.apk', '.obb']
    other_filetypes = ['.elf', '.pbp', '.dol', '.xbe', '.xex', '.cfg', '.ini', '.dll', '.so', '.xml', '.hsi', '.lay', '.nv', '.m3u', '.rp9', '.paq9a']
    filetypes = list()
    filetypes.extend(archives_filetypes)
    filetypes.extend(disk_filetypes)
    filetypes.extend(tape_filetypes)
    filetypes.extend(rom_filetypes)
    filetypes.extend(other_filetypes)
    for filetype in filetypes:
        if filetype in line:
            return True
    return False

def parse_links (url_body):
    url_body_lines = url_body.split('\n')
    links = []
    url_body_lines = tqdm(iterable=url_body_lines, unit='Lines', desc='Parsing')
    for line in url_body_lines:
        if filetype_checker(line):
            split_line = line.split('href=', 1)
            if len(split_line) > 1:
                split_line = split_line[1]
                split_line = split_line.split('\"', 2)
                link_url = url.geturl()
                if link_url[-1] == '/':
                    link = url.geturl() + split_line[1]
                else:
                    link = url.geturl() + '/' +  split_line[1]
                links.append([link, urllib.parse.unquote(split_line[1])])
    print (f"\nThe URL has been parsed, giving a total of {len(links)} files to download\n")
    return links

def get_size_to_gb (file_size_string):
    split_size  = file_size_string.split(' ')
    match split_size[1]:
        case 'B':
            return float(split_size[0])/(1024*1024*1024)
        case "KB":
            return float(split_size[0])/(1024*1024)
        case "KiB":
            return float(split_size[0])/(1024*1024)
        case 'MB':
            return float(split_size[0])/1024
        case 'MiB':
            return float(split_size[0])/1024
        case 'GB':
            return float(split_size[0])
        case 'GiB':
            return float(split_size[0])
        case 'TB':
            return float(split_size[0])*1024
        case 'TiB':
            return float(split_size[0])*1024
        case _:
            return float(split_size[0])
        

def parse_sizes (url_body):
    file_sizes = []
    url_body_lines = url_body.split('\n')
    url_body_lines = tqdm(iterable=url_body_lines, unit='Lines', desc='Parsing')
    for line in url_body_lines:
        if filetype_checker(line):
            # split_line = line.split('href=', 1)
            split_line = line.split('<td class="size">', 1)
            if len(split_line) > 1:
                split_line = split_line[1]
                split_line = split_line.split('</td>', 1)
                print(split_line)
                file_size = get_size_to_gb(split_line[0])
                file_sizes.append(file_size)
    return file_sizes

def get_file_name (line) -> str:
    file_name = ''
    split_line = line.split('href=', 1)
    if len(split_line) > 1:
        split_line = split_line[1]
        split_line = split_line.split('\"', 2)
        file_name = urllib.parse.unquote(split_line[1])
    return file_name
    
def get_file_size (line) -> float:
    file_size = 0
    split_line = line.split('<td class="size">', 1)
    if len(split_line) > 1:
        split_line = split_line[1]
        split_line = split_line.split('</td>', 1)
        file_size = get_size_to_gb(split_line[0])
    return file_size

def get_update_time (line) -> datetime:
    date = datetime.now()
    split_line = line.split('<td class="date">', 1)
    if len(split_line) > 1:
        split_line = split_line[1]
        split_line = split_line.split('</td>', 1)
        date = datetime.strptime(split_line[0], '%d-%b-%Y %H:%M')
    return date

def parse_games (url_body, url, console) -> list[Game]:
    games = []
    url_body_lines = url_body.split('\n')
    url_body_lines = tqdm(iterable=url_body_lines, unit='Lines', desc=f'Parsing {url}')
    for line in url_body_lines:
        if filetype_checker(line):
            file_name = get_file_name(line)
            file_size = get_file_size(line)
            update_time = get_update_time(line)
            if url[-1] == '/':
                url_with_file = url + file_name
            else:
                url_with_file = url + '/' +  file_name
            game = Game(name = file_name, url = url_with_file, size = file_size, update_time = update_time, console = console)
            games.append(game)
    return games

def download_file_wget (url_with_file_name):
    url = url_with_file_name[0]
    file_name = url_with_file_name[1]
    subprocess.run(["powershell", "wget", url])
    # subprocess.run(["powershell", "wget", '-O ' + file_name + ' ' + url])
    print(f"Data written to {file_name}\n")


######## Download con Streaming ###############
def download_file_stream (url_with_file_name):
    url = url_with_file_name[0]
    file_name = url_with_file_name[1]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'}
    session = requests.Session()
    response = session.get(url, stream=True, headers=headers)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    with open(CONSOLE + '/' + file_name, 'wb') as file:
        for data in tqdm(response.iter_content(block_size), total=total_size // block_size, unit='KB', desc='Downloading ' + file_name):
            file.write(data)

    print(f"Data written to {file_name}\n")

######### FUNCIONANDO PERO DESCARGA EL ARCHIVO DE UNA ################
def download_file_all_at_once (url_with_file_name):
    url = url_with_file_name[0]
    file_name = url_with_file_name[1]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'}
    session = requests.Session()
    response = session.get(url, headers=headers)
    total_size = sys.getsizeof(response.content)
    sleep_time = 1/total_size
    with open(CONSOLE + '/' + file_name, 'wb') as file:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc='Writing ' + file_name) as pbar:
            for i in range(total_size):
                time.sleep(sleep_time)
                # print(current_process())
                file.write(response.content[i: i+1])
                pbar.update(1)
    print(f"Data written to {file_name}\n")

def download_file (url_with_file_name, download_type):
    match download_type:
        case 'WGET':
            download_file_wget(url_with_file_name)
        case 'STREAM':
            download_file_stream(url_with_file_name)
        case 'ENTIRE':
            download_file_all_at_once(url_with_file_name)
        case _:
            print('Select a valid Download type from (WGET, STREAM or ENTIRE)')

def personal_filter_restriction(link):
    if '(Demo)' in link: 
        return True
    elif ' Demo ' in link: 
        return True
    elif not '(USA)' in link:
        return True
    return False

def personal_filter(links):
    urls = links
    to_filter = []
    for count, url in enumerate(urls):
        if personal_filter_restriction(url[1]):
            to_filter.append(count)
    for count in reversed(to_filter):
        del urls[count]
    return urls

def personal_game_filter(games) -> list[Game]:
    aux_games = games
    to_filter = []
    for count, game in enumerate(aux_games):
        if personal_filter_restriction(game.name):
            to_filter.append(count)
    for count in reversed(to_filter):
        del aux_games[count]
    return aux_games

def write_links(links, file_name='output.txt'):
    with open(file_name, 'w') as file:
        for link in links:
            file.write(link[0]+'\n')

################### GET FILE SIZE PER LINK ###################

# def get_file_size(link):
#     session = requests.Session()
#     retries = Retry(total=5,
#                 backoff_factor=0.1,
#                 status_forcelist=[ 500, 502, 503, 504 ])
#     adapter = HTTPAdapter(max_retries=retries)
#     session.mount(link[0], adapter)
#     response = session.head(link[0])
#     file_size = int(response.headers.get('content-length', 0))
#     return file_size

################### GET FILE SIZE PER LINKs ###################
# def get_files_size(links):
#     total_size = 0
#     # with Pool(MAX_PROCCESSES) as p:
#     #     p.map(get_file_size, link)
#     for link in links:
#             total_size += get_file_size(link)
#     print(f'The total size of the {len(links)} files is {(total_size/(1024*1024)):0.2f}MB aka {(total_size/(1024*1024*1024)):0.2f}GB')
#     return total_size

def iso2chd (file_name):
    path = os.path.abspath('')
    file_name_iso = path + '\\' + CONSOLE + '\\' + file_name
    file_name_split = file_name.rsplit('.', 1)
    print(file_name)
    if file_name_split[1] == 'zip':
        file_name_iso = path + '\\' + CONSOLE + '\\decompressed\\' + file_name_split[0] + '.iso'
        with zipfile.ZipFile(path + '\\' + CONSOLE + '\\' + file_name, 'r') as zip_ref:
            zip_ref.extractall(path + '\\' + CONSOLE + '\\decompressed\\')
    file_name_chd = path + '\\' + CONSOLE + '\\compressed\\' + file_name_split[0] + '.chd'
    if not os.path.exists(path + '\\' + CONSOLE + '\\compressed\\'):
        os.makedirs(path + '\\' + CONSOLE + '\\compressed\\')
    subprocess.run(["powershell", path + '\\' + "chdman.exe", "createcd", "-i", f'"{file_name_iso}"', '-o', f'"{file_name_chd}"'])

if __name__ == '__main__':

    urls = [
        ['https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation/', 'PS1'],
        ['https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%202/', 'PS2'],
        ['https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%203/', 'PS3'],
        ['https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%20Portable/', 'PSP'],
        ['https://myrient.erista.me/files/Redump/Nintendo%20-%20GameCube%20-%20NKit%20RVZ%20%5Bzstd-19-128k%5D/', 'GameCube'],
        ['https://myrient.erista.me/files/Redump/Nintendo%20-%20Wii%20-%20NKit%20RVZ%20%5Bzstd-19-128k%5D/', "Wii"],
        ['https://myrient.erista.me/files/Redump/Nintendo%20-%20Wii%20U%20-%20WUX/', 'WiiU'],
        ['https://myrient.erista.me/files/Redump/Sega%20-%20Dreamcast/', 'Dreamcast'],
        ['https://myrient.erista.me/files/Redump/Sega%20-%20Saturn/', 'Saturn'],
        ['https://myrient.erista.me/files/Redump/Microsoft%20-%20Xbox/', 'Xbox'],
        ['https://myrient.erista.me/files/Redump/Microsoft%20-%20Xbox%20360/', 'Xbox360']
    ]

    consoles = []
    every_games = []
    for url in urls:
        url_request = urllib.request.urlopen(url[0])
        url_body = url_request.read().decode("utf-8")
        games = parse_games(url_body, url[0], url[1])
        games = personal_game_filter(games)
        total_game_size = 0
        for game in games:
            total_game_size += game.size
        every_games.append(games)
        consoles.append([url[1], len(games), total_game_size])

    df_dict = {}
    for games in every_games:
        df = pd.DataFrame([game.as_dict() for game in games])
        print(df)
        df_dict[games[0].console] = df
    with pd.ExcelWriter('games.xlsx') as writer:
        for console, df in df_dict.items():
            df.to_excel(writer, sheet_name=console, index=False)

    total = 0
    with open('files_to_download.txt', 'w') as file:
        for console in consoles:
            file.write(f'{console[0]} - {console[1]} files - {console[2]:0.2f}GBs\n')
            total += console[2]
        file.write(f'Total space needed for the consoles = {total:0.2f}GBs')



    url = urllib.request.urlopen("https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%202")
    url_body = url.read().decode("utf-8")

    links = parse_links(url_body)
    links = personal_filter(links)

    file_output = False
    file_name = 'ps2.txt'
    if file_output:
        write_links(links, file_name=file_name)
    
    # total_files = False
    # if total_files:
    #     get_files_size(links)

    # ##### Auto Download ######

    end = len(links) - 1

    urls = [
        [links[end-1][0], links[end-1][1]],
        [links[end][0], links[end][1]],
        [links[0][0], links[0][1]]
    ]

    params = [
        ([links[4][0], links[4][1]], 'STREAM'),
        ([links[3][0], links[3][1]], 'STREAM'),
        ([links[10][0], links[10][1]], 'STREAM'),
    ]

    params =  []
    params2 = []
    for i in range(6):
        params.append(
            ([links[i][0], links[i][1]], 'STREAM')
        )
        params2.append(links[i][1])
    
    # download_file(params[2][0], params[2][1])
    # iso2chd(params[2][0][1])

    # with Pool(MAX_PROCCESSES) as p:
        # p.starmap(download_file, params)
        # p.map(iso2chd, params2)




####### Obtaining the links from a file #########
# with open(os.path.abspath("ps2/ps2usaredump1 directory listing.htm"), "r", encoding="utf-8") as html_file:
#     line = html_file.readline()
#     links = []
#     while line:
#         if filetype_checker(line):
#             split_line = line.split('href=', 1)
#             if len(split_line) > 1:
#                 split_line = line.split('\"', 2)
#                 links.append(split_line)
#                 # print(split_line[1])
#         line = html_file.readline()
