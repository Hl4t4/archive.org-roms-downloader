import os

def filetype_checker(line):
    ######## Faltan los tipos de archivos partidos #########
    archives_filetypes = ['.7z', '.7zip', '.zip', '.tar.gz', '.gz', '.tar', '.gzip', '.rar']
    disk_filetypes = ['.iso', '.img', '.bin', '.cue', '.chd', '.mdf', '.mds', '.ecm', '.cso', '.gcz', '.rvz', '.cdi', '.gdi', '.sbi', '.sub', '.nrg', '.isz', '.fds', '.ndd', '.adf', '.adz', '.adf.gz', '.dms', '.ipf']
    tape_filetypes = ['.wav', '.tap', '.tzx', '.cdc', '.cas']
    rom_filetypes = ['.nes',  '.nez', '.unf', '.unif', '.smc', '.sfc', '.md', '.smd', '.gen', '.gg', '.z64', '.v64', '.n64', '.gb', '.gbc', '.gba', '.srl', '.gcm', '.gcz', '.xiso', '.nds', '.dsi', '.nds', '.app', '.ids', '.wbfs', '.wad', '.cia', '.3ds', '.nsp', '.xci', '.ngp', '.ngc', '.pce', '.vpk', '.vb', '.ws', '.wsc', '.bin', '.dat', '.lst', '.ipa', '.apk', '.obb']
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

with open(os.path.abspath("ps2/ps2usaredump1 directory listing.htm"), "r", encoding="utf-8") as html_file:
    line = html_file.readline()
    links = []
    while line:
        if filetype_checker(line):
            split_line = line.split('href=', 1)
            if len(split_line) > 1:
                split_line = line.split('\"', 2)
                print(split_line[1])
        line = html_file.readline()
