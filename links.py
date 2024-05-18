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

MAX_PROCCESSES = 5
CONSOLE = 'PS2'

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

def write_links(links, file_name='output.txt'):
    with open(file_name, 'w') as file:
        for link in links:
            file.write(link[0]+'\n')

def get_file_size(link):
    session = requests.Session()
    retries = Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount(link[0], adapter)
    response = session.head(link[0])
    file_size = int(response.headers.get('content-length', 0))
    return file_size

def get_files_size(links):
    total_size = 0
    # with Pool(MAX_PROCCESSES) as p:
    #     p.map(get_file_size, link)
    for link in links:
            total_size += get_file_size(link)
    print(f'The total size of the {len(links)} files is {(total_size/(1024*1024)):0.2f}MB aka {(total_size/(1024*1024*1024)):0.2f}GB')

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

    url = urllib.request.urlopen("https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%202")
    url_body = url.read().decode("utf-8")

    links = parse_links(url_body)
    links = personal_filter(links)

    file_output = False
    file_name = 'ps2.txt'
    if file_output:
        write_links(links, file_name=file_name)
    
    total_files = False
    if total_files:
        get_files_size(links)

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

    print(params2)

    with Pool(MAX_PROCCESSES) as p:
        # p.starmap(download_file, params)
        p.map(iso2chd, params2)




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
