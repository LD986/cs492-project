#!/usr/bin/env python3
import os
import subprocess
import threading
import time
import tempfile
import shutil
import signal
import sys

# -------- CONFIG --------
FUSE_BINARY = "fsx492"          # your compiled FS
FUSE_ARGS = ["-f", "-d", "-s"]  # run single threaded debug mode
MOUNT_TIMEOUT = 10              # seconds


"""
    enum {
    FSX492_MAGIC    = 0xC492F11E,   // superblock magic number
    FSX492_BLKSZ    = 1024,         // block size in bytes
    FSX492_DIRENTSZ = 32,           // directory entry size in bytes
    FSX492_INODESZ  = 64,           // inode size in bytes
    };
    from fsx492.h

    ensure the following are the same values as their fsx492.h variants if they ever were to change (bc hardcoded)

    only using FSX492_BLKSZ and FSX492_DIRENTSZ for now because those are required for test_add_rem_mult_block_simul(mountpoint)
"""
FSX492_BLKSZ = 1024
FSX492_DIRENTSZ = 32

# ------------------------


##############################################################################
# BEGIN TEST DEFINITIONS
##############################################################################

# define tests below by creating functions that are prefixed with "test_"

def test_add_rem_from_sub(mountpoint):
    print(f"[test] adding and removing files from subdirectories {mountpoint}")
    os.mkdir('somecoolfoldername')
    subdirpath = os.path.join(mountpoint, "somecoolfoldername")
    assert os.path.exists(subdirpath), "adding and removing files from subdirectories failure(1)"
    path = os.path.join(subdirpath, "weloveryan.txt")
    with open (path, 'w') as f:
        f.write('duncan is cool!') #deciding not to test write because overwrite test exists, this is just to make the file exist
    assert os.path.exists(path), "adding and removing files from subdirectories failure(2)"
    os.remove('weloveryan.txt')
    assert not os.path.exists(path), "adding and removing files from subdirectories failure(3)"
    os.rmdir(subdirpath)
    assert not os.path.exists(subdirpath, "adding and removing files from subdirectories failure(4)")
    print("[test] adding and removing more than a block's worth of directories (at once) passed")
#https://pytutorial.com/python-os-module-file-system-operations-guide/#creating-files




def test_add_rem_mult_block_simul(mountpoint):
    print(f"[test] adding and removing more than a block's worth of directories (at once) {mountpoint}")
    #SEE CONFIG ABOVE IF CONFUSED
    n = (FSX492_BLKSZ/FSX492_DIRENTSZ)*2 #number of directories to add/remove at once (double the amount a blocks worth of directories)
    print("wow")
    #make a subdir to make life easier and change to there


    #something breaks before cool print after wow print
    subdirpath = os.path.join(mountpoint, "somecoolfoldername")
    os.mkdir(subdirpath)
    print("cool")
    assert os.path.exists(subdirpath), "adding and removing more than a block's worth of directories (at once) failure(1)"

    #https://www.tutorialspoint.com/article/make-multiple-directories-based-on-a-list-using-python
    #make list of directories to add (each directory name is testdir_i, 
    #where i is a number incremented by 1 bc 0 index, last directory number should be equal to n)
    list_of_dir_names = []
    for i in range(0, n):
        list_of_dir_names.append("testdir_"+str(i+1))
    for dir_name in list_of_dir_names:
        sub_subdirpath = os.path.join(subdirpath, "testdir_"+dir_name)
        os.mkdir(sub_subdirpath)
        assert os.path.exists(sub_subdirpath), "adding and removing more than a block's worth of directories (at once) failure(2)"

    #https://pynative.com/python-delete-files-and-directories/
    os.cwd('..')
    shutil.rmtree('somecoolfoldername') #https://stackoverflow.com/questions/10873364/shutil-rmtree-clarification

    for dir_name in list_of_dir_names:
        sub_subdirpath = os.path.join(subdirpath, "testdir_"+dir_name)
        assert not os.path.exists(sub_subdirpath), "adding and removing more than a block's worth of directories (at once) failure(3)"

    assert not os.path.exists(subdirpath), "adding and removing more than a block's worth of directories (at once) failure(4)"
    print("[test] adding and removing more than a block's worth of directories (at once) passed")



def test_file_overwrite(mountpoint):
    print(f"[test] overwriting a file (see `open` behavior) {mountpoint}")
    path = os.path.join(mountpoint, "randomfilename.txt")

    print("check1")

    with open(path, "w") as f: #make content to overwrite in test
        f.write("philippe")
    with open(path, "r") as f:
        olddata = f.read()
    print(olddata);
    assert "philippe" == olddata, "overwriting content of file failure(1)"

    print("check2")

    write_time = str(time.time()) #https://www.geeksforgeeks.org/python/python-time-module/, ensures test integrity
    with open(path, "w") as f:
        f.write(write_time) #https://www.geeksforgeeks.org/python/open-a-file-in-python/
    with open(path, "r") as f:
        newdata = f.read()
    assert write_time == newdata, "overwriting content of file failure (2)"
    assert "philippe" not in newdata, "overwriting content of file failure(3)" #data overwritten
    print("[test] overwriting a file (see `open` behavior) passed")

def test_open_file_in_append(mountpoint):
    print(f"[test] opening a file in \"append\" mode (see `open` behavior) {mountpoint}")
    path = os.path.join(mountpoint, "randomfilename.txt")
    with open(path, "w") as f: #make content to append to in test
        f.write("philippe")
    with open(path, "r") as f:
        olddata = f.read()
    assert "philippe" == olddata, "opening a file in append mode failure(1)"

    append_time = str(time.time()) #https://www.geeksforgeeks.org/python/python-time-module/, ensures test integrity
    with open(path, "a") as f:
        f.write(append_time) #https://www.geeksforgeeks.org/python/open-a-file-in-python/
    with open(path, "r") as f:
        newdata = f.read()
    print(newdata)
    assert "philippe"+append_time == newdata, "opening a file in append mode failure(2)" #file content should be "philippe<remove_<>_and_time_goes_here>"
    print("[test] opening a file in \"append\" mode (see `open` behavior) passed")

def test_count_hard_links(mountpoint):
    print(f"[test] counting hard links {mountpoint}")
    #st = os.stat(mountpoint)
    path_a = os.path.join(mountpoint, "weloveryan.txt")
    path_b = os.path.join(mountpoint, "somefilename.txt")
    path_c = os.path.join(mountpoint, "onemorefileforgoodluck.txt")
    with open (path_a, 'w') as f:
        f.write('duncan is cool!') #deciding not to test write because overwrite test exists, this is just to make the file exist
    assert os.path.exists(path_a), "counting hard links failure(1)"
    oldst = os.stat(path_a)
    assert oldst.st_nlink == 1, "counting hard links failure(2)" #https://docs.python.org/3/library/stat.html, file properly created with a singular link

    #https://www.geeksforgeeks.org/python/python-os-link-method/
    os.link(path_a, path_b)
    os.link(path_a, path_c)
    newst = os.stat(path_a)
    assert newst.st_nlink == 3, "counting hard links failure(3)" #https://docs.python.org/3/library/stat.html, file properly linked with 2 other files

    os.unlink(path_c) #https://www.delftstack.com/api/python/python-os-unlink/
    newestst = os.stat(path_a)
    assert newestst.st_nlink == 2, "counting hard links failure(4)" #https://docs.python.org/3/library/stat.html, file properly unlinked
    print("[test] counting hard links passed")




def test_acc_or_mod_time(mountpoint):
    print(f"update access/modification time {mountpoint}")
    st = os.stat(mountpoint)
    old_atime = st.st_atime
    old_mtime = st.st_mtime
    os.utime(mountpoint,(1330712280, 1330712292)) #https://www.tutorialspoint.com/python/os_utime.htm, https://stackoverflow.com/questions/11348953/how-can-i-set-the-last-modified-time-of-a-file-from-python
    new_st = os.stat(mountpoint)
    new_atime = new_st.st_atime
    new_mtime = new_st.st_mtime
    assert old_atime != new_atime, "update access time failure(1)"
    assert old_mtime != new_mtime, "update modification time failure(1)"
    assert new_atime == 1330712280, "update access time failure(2)"
    assert new_mtime == 1330712292, "update modification time failure(2)"
    print("[test] update access/modification time passed")




def test_change_perms(mountpoint):
    print(f"[test] changing permissions {mountpoint}")
    os.chmod(mountpoint, 0o444) #https://stackoverflow.com/questions/16249440/changing-file-permission-in-python
    st = os.stat(mountpoint)
    assert os.access(mountpoint, os.R_OK), "changing perms failure(1)"
    assert os.access(mountpoint, os.W_OK), "changing perms failure(2)"
    assert os.access(mountpoint, os.X_OK), "changing perms failure(3)"
    #https://www.tutorialspoint.com/article/How-to-check-the-permissions-of-a-file-using-Python
    print("[test] changing permissions passed")




def test_basic(mountpoint):

    # TEST: directory listing

    print(f"[test] list {mountpoint}")
    entries = os.listdir(mountpoint)
    print(entries)
    assert "hello.txt" in entries, "readdir missing file"

    # TEST: file existence
    path = os.path.join(mountpoint, "hello.txt")
    print(f"[test] file existence: {path}")
    assert os.path.exists(path), "file missing"

    # TEST: read
    print(f"[test] read {path}")
    with open(path, "r") as f:
        data = f.read()
    assert "hello" in data, "unexpected file content"

    # TEST: partial read
    print(f"[test] partial read {path}")
    with open(path, "r") as f:
        f.seek(6)
        data = f.read()
    assert "world" in data, "partial read failed"

    # TEST: out of bounds read
    print(f"[test] out of bounds read {path}")
    with open(path, "r") as f:
        f.seek(30)
        data = f.read()
    assert len(data) == 0, "out of bounds read should return nothing"

    # TEST: stat
    print(f"[test] stat {path}")
    st = os.stat(path)
    assert st.st_size == len("hello world!\n"), "invalid file size"


    print("[test] passed basic")

def test_large_file(mountpoint):

    # TEST: large file copy
    src = "./data/gospels.txt"
    assert os.path.exists(src), "src not found: {}".format(src)

    dst = f"{mountpoint}/{os.path.basename(src)}"
    shutil.copy(src, dst)
    assert os.path.exists(dst), "copy failed: {} does not exist".format(dst)

    with open(src, 'rb') as f:
        srcdata = f.read()

    with open(dst, 'rb') as f:
        dstdata = f.read()

    assert len(srcdata) == len(dstdata), \
        "length check failed: {} (src) != {} (dst)".format(
            len(srcdata), len(dstdata))

    diff = -1
    for i in range(len(srcdata)):
        if srcdata[i] != dstdata[i]:
            diff = i
            break

    assert diff < 0, "data different @ {}:\nsrc: {}\ndst: {}".format(
        diff, srcdata[diff:diff+10], dstdata[diff:diff+10])

    print("[test] passed large file")



##############################################################################
# END TEST DEFINITIONS
##############################################################################

TESTS = {
    k.lstrip('test_'): v for k, v in globals().items() if k.startswith('test_')
}


def reset_mount(mountpoint, fs_name=FUSE_BINARY):
    """reset fuse filesystem mountpoint after failure"""
    result = subprocess.run(
        ['mount'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False)

    if fs_name in result.stdout:
        subprocess.run(
            ['fusermount', '-u', mountpoint],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False)

    try:
        shutil.rmtree(mountpoint)
    except Exception:
        pass

    os.makedirs(mountpoint, exist_ok=True)

def is_mounted(mountpoint, fs_name=None):
    mountpoint = os.path.abspath(mountpoint)

    try:
        with open("/proc/self/mounts", "r") as f:
            lines = [line.strip() for line in f.readlines()]

        for line in lines:
            parts = line.split()
            if len(parts) < 3:
                continue

            dev, mnt, fstype = parts[:3]

            if os.path.abspath(mnt) == mountpoint:
                if fs_name is None:
                    return True
                if fs_name in dev or fs_name in fstype:
                    return True
        return False
    except Exception:
        return False


def wait_for_mount(mountpoint, timeout=MOUNT_TIMEOUT):
    """Wait until mountpoint is ready by probing it."""
    start = time.time()
    while time.time() - start < timeout:
        if is_mounted(mountpoint, fs_name="fsx492"):
            return True
        time.sleep(0.1)
    return False


def run_filesystem(mountpoint, ready_event, stop_event, logfile="fsx492.log"):
    """Run the FUSE filesystem."""
    cmd = ['stdbuf', '-oL', '-eL'] + [f"./{FUSE_BINARY}"] + FUSE_ARGS + [mountpoint]

    # unmount file system if needed first
    reset_mount(mountpoint)

    log = open(logfile, 'w')
    proc = subprocess.Popen(
        cmd,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Wait until mount is ready
    if wait_for_mount(mountpoint):
        print("[fs] mounted")
        ready_event.set()
    else:
        print("[fs] mount timeout")
        proc.terminate()
        return

    # Keep process alive until stop_event
    while not stop_event.is_set():
        if proc.poll() is not None:
            print("[fs] process exited early!")
            return
        time.sleep(0.2)

    log.close()
    print("[fs] shutting down...")
    proc.send_signal(signal.SIGINT)

    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def run_tests(test, mountpoint, ready_event, stop_event):
    """Run filesystem tests."""
    ready_event.wait()

    print(f"[test] starting test: {test}")

    try:
        TESTS[test](mountpoint)
    except AssertionError as e:
        print(f"[test] FAILED: {e}")
    finally:
        stop_event.set()


if __name__ == "__main__":
    DEFAULT_MOUNTPOINT = './testfs'
    DEFAULT_IMAGE = 'data/test.img'
    import argparse
    parser = argparse.ArgumentParser('test.py',
        description="test script for fsx492")
    parser.add_argument('test', type=str, default='basic',
        help=f"options: {','.join(TESTS.keys())}")
    parser.add_argument('--mountpoint', type=str, default=DEFAULT_MOUNTPOINT,
        help=f"the path to mount at (default {DEFAULT_MOUNTPOINT})")
    parser.add_argument('--img', type=str, default='data/test.img',
        help=("the path to the image file, which will be restored from backup "
            f"(default: {DEFAULT_IMAGE})"))

    args = parser.parse_args()

    mountpoint = args.mountpoint
    assert args.test in TESTS, "test not found: {}".format(args.test)
    assert callable(TESTS[args.test]), "not callable: {}".format(args.test)

    imgpath = args.img
    assert os.path.exists(imgpath), "file not found: {}".format(imgpath)
    imgbkp = f"{imgpath}.bkp"
    assert os.path.exists(imgbkp), "could not find backup: {}".format(imgbkp)

    print(f"[main] cwd: {os.getcwd()}")
    print(f"[main] mountpoint: {mountpoint}")
    print(f"[main] restoring {imgpath} from {imgbkp}")
    shutil.copy(imgbkp, imgpath)

    ready_event = threading.Event()
    stop_event = threading.Event()

    fs_thread = threading.Thread(
        target=run_filesystem,
        args=(mountpoint, ready_event, stop_event),
        daemon=True
    )

    test_thread = threading.Thread(
        target=run_tests,
        args=(args.test, mountpoint, ready_event, stop_event),
        daemon=True
    )

    fs_thread.start()
    test_thread.start()

    test_thread.join()
    stop_event.set()
    fs_thread.join()

    # Try to unmount (Linux)
    print("[main] unmounting...")
    subprocess.run(["fusermount", "-u", mountpoint],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

    shutil.rmtree(mountpoint)
    print("[main] done")