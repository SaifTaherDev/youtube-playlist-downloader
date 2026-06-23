import os
import time
import shutil
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import re
from flask import Flask, request, send_file, jsonify
import threading

app = Flask(__name__)
driver_lock = threading.Lock()  # prevent concurrent downloads

def init_driver(download_path):
    options = Options()
    os.makedirs(download_path, exist_ok=True)

    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    if os.name != "nt":  # not Windows → Docker/Linux
        options.binary_location = "/usr/bin/chromium"

    return Chrome(options)

def get_crdownld_path(download_path):
    for root, dirs, files in os.walk(download_path):
        for filename in files:
            if filename.endswith('.crdownload'):
                return os.path.join(download_path, filename)
    return ""

def get_crdownld_size(download_path):
    crdownld_path = get_crdownld_path(download_path)
    size = 0 if crdownld_path == "" else os.path.getsize(crdownld_path)
    
    return size

def prettify_num(num, n_places, is_float=False, n_decimal_places=0):
    if (not is_float):
        str_num = str(num)
    else:
        str_num = f"%.{n_decimal_places}f" % num

    len_str = len(str_num)
    n_places = max(len_str, n_places)
    n_zeros = n_places - len_str
    
    return "0" * n_zeros + str_num

def wait_for_download(download_path, id, size, timeout=60):
    seconds = 0
    dl_wait = True
    
    frames_per_sec = 10
    frame_t = 1 / frames_per_sec
    n_frames = 0
    percentage_per_dot = 1
    n_dots = int(round(100 / percentage_per_dot))
    hundred_percent = prettify_num(100, 4, True, 1)
    update_interval = 1
    
    while dl_wait and seconds < timeout:
        time.sleep(frame_t)
        seconds += frame_t
        n_frames += 1
        
        if not check_item_exists_dir(download_path, id):
            if n_frames % update_interval == 0:
                crdownld_size = get_crdownld_size(download_path)
                progress = crdownld_size / size
                n_blocks = min(int(round(progress * n_dots)), n_dots)
                bar = f"[{n_blocks * '\u2588'}{(n_dots - n_blocks) * ' '}]"
                progress_percent = prettify_num(progress * 100, 4, True, 1)
                if progress >= 1:
                    progress_percent = hundred_percent
                print(f"\033[2K\033[1GDownload progress: {bar} - {progress_percent}%", end="", flush=True)
        else:
            dl_wait = False

    if seconds >= timeout:
        print(f"\nTimed out waiting for download after {timeout} seconds.")
        return False
    else:
        print(f"\033[2K\033[1GDownload progress: [{n_dots * '\u2588'}] - {hundred_percent}%", flush=True)
        print(f"{id} downloaded! Took {"%.1f" % seconds} seconds.")
        
        wait_count = 0
        while get_crdownld_path(download_path) != "" and wait_count <= 4:
            wait_count += 1
            time.sleep(1)
        
        cr_downld = get_crdownld_path(download_path)
        if cr_downld != "":
            try:
                os.remove(cr_downld)
            except Exception as e:
                pass
        
        return True

def scroll_to_load_all(driver):
    last_count = 0
    while True:
        renderers = driver.find_elements(By.XPATH, "//ytd-playlist-video-renderer")
        current_count = len(renderers)
        if current_count == last_count:
            break

        last_count = current_count

        driver.execute_script("arguments[0].scrollIntoView();", renderers[-1])
        time.sleep(1)

def get_ids(driver, url, timeout_t):    
    pattern = r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/.*list=([\w-]+)(?:\?|&)?.*"
    playlist_id = re.search(pattern, url).group(1)
    _url = f"https://www.youtube.com/playlist?list={playlist_id}"
    driver.get(_url)
    
    wait = WebDriverWait(driver, timeout_t)
    wait.until(EC.presence_of_element_located((By.XPATH, "//ytd-playlist-video-renderer")))
    scroll_to_load_all(driver)

    vid_title_xpath = """//ytd-item-section-renderer/div[@id="contents"]/ytd-playlist-video-list-renderer/div[@id="contents"]/ytd-playlist-video-renderer/div[@id="content"]/div[@id="container"]/div[@id="meta"]/h3/a"""
    playlist_name_xpath = """//head/meta[@name="title"]"""

    songs = driver.find_elements(By.XPATH, vid_title_xpath)
    playlist_title_element = wait.until(EC.presence_of_element_located((By.XPATH, playlist_name_xpath)))
    playlist_title = playlist_title_element.get_attribute("content")

    links_titles = []

    for song in songs:
        links_titles.append((song.get_attribute("href"), song.get_attribute("title")))

    pattern = r"(?:https:\/\/)?(?:www\.)?(?:(?:youtube\.com\/watch\?v=)|(?:youtu\.be\/))([\w-]+)(?:\?|\&)?.*"
    IDs = [(re.search(pattern, link_title[0]).group(1), link_title[1]) for link_title in links_titles]

    return playlist_title, _url, IDs

def timeout_msg(driver, e, element_msg, id, timeout_t, download_path, override_msg=False):
    driver.quit()

    if (override_msg):
        print(element_msg)
    else:
        print(f"Timed out waiting for the {element_msg} at id={id}. Error class: {e} Reinitializing driver...")

    driver = init_driver(download_path)
    return driver, WebDriverWait(driver, timeout_t)

def sanitize_filename(title, replacement="_"):
    illegal_chars_regex = r"[\<\>\:\"\/\\\|\?\*\x00-\x1f]"
    clean_title = re.sub(illegal_chars_regex, replacement, title)
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()

    return clean_title

def trim_newest_filename(download_path, id, title):
    title_raw = sanitize_filename(title)
    id = clean_underscore(id)
    pattern = fr"YTDown_YouTube_?(.*)_Media_?{id}.*"
    compiled_pattern = re.compile(pattern)
    suffix_i = 0
    success = False
    
    for root, dirs, files in os.walk(download_path):
        for filename in files:
            if compiled_pattern.search(filename):
                old_path = os.path.join(root, filename)
                new_filename_prefix = title_raw if len(title_raw) > 0 else id
                
                while not success:
                    try:
                        suffix = "" if suffix_i == 0 else f"_{suffix_i}"
                        new_filename = f"{new_filename_prefix}{suffix}.m4a"
                        new_file_path = os.path.join(download_path, new_filename)
                        
                        os.rename(old_path, new_file_path)
                        success = True
                    except Exception as e:
                        suffix_i += 1

    return new_filename

def clean_underscore(id):
    return re.sub(r"__", "_", id)

def check_item_exists_dir(download_path, id):
    id = clean_underscore(id)
    for root, dirs, files in os.walk(download_path):
        for filename in files:
            if id in filename:
                return True
            
    return False

def convert_size_2_byte(size):
    size = size.strip().split()
    unit = size[1]
    size = float(size[0])
    multiplier = 1
    
    match unit:
        case "B":
            multiplier = 1
        case "KB":
            multiplier = 1000
        case "MB":
            multiplier = 1_000_000
        case "GB":
            multiplier = 1_000_000_000
        case "TB":
            multiplier = 1_000_000_000_000
            
    return size * multiplier

def download_songs(driver, prefix, downloader, download_path, timeout_t, download_timeout, IDs, can_retry = True):
    wait = WebDriverWait(driver, timeout_t)

    success_count, counter, tries = 0, 0, 0
    failures = []
    
    while counter < len(IDs):
        id = IDs[counter][0]
        title = IDs[counter][1]
        
        if tries >= 2:
            print(f"{id} failed too many times. Skipping download...")
            failures.append((id, title))
            counter += 1
            tries = 0
            continue

        try:
            driver.get(downloader)
        except Exception as e:
            driver, wait = timeout_msg(driver, e, "navigation", id, timeout_t, download_path)
            tries += 1
            continue

        try:
            text_box = wait.until(EC.element_to_be_clickable((By.XPATH, """//form/div[@class="input-group"]/input""")))
        except Exception as e:
            driver, wait = timeout_msg(driver, e, "textbox", id, timeout_t, download_path)
            tries += 1
            continue

        try:
            driver.execute_script(f"arguments[0].setAttribute('value', '{prefix + id}');", text_box)
        except Exception as e:
            driver, wait = timeout_msg(driver, e, f"Could not type address into textbox at {id}. Retrying...", id, timeout_t, download_path, True)
            tries += 1
            continue

        try:
            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, """//button[@type="submit"]""")))
        except Exception as e:
            driver, wait = timeout_msg(driver, e, "search button", id, timeout_t, download_path)
            tries += 1
            continue

        try:
            submit_button.click()
        except Exception as e:
            driver, wait = timeout_msg(driver, e, f"Could not click search button at {id}. Retrying...", id, timeout_t, download_path, True)
            tries += 1
            continue

        print(f"Processing ID: {id}")

        try:
            wait.until(EC.presence_of_element_located((By.XPATH, """//select[@class="download-option"]""")))
        except Exception as e:
            driver, wait = timeout_msg(driver, e, "dropdown", id, timeout_t, download_path)
            tries += 1
            continue

        try:
            m4a_xpath = """//select[@class="download-option"]/option[contains(text(), "M4A") and contains(text(), "128K")]"""
            m4a_option = driver.find_element(By.XPATH, m4a_xpath)
            size = m4a_option.get_attribute("data-filesize")
            size = convert_size_2_byte(size)
            estimated_download_time = max(download_timeout, size / min_download_speed)
            driver.execute_script("arguments[0].selected = true;", m4a_option)
            
        except Exception as e:
            driver, wait = timeout_msg(driver, e, "m4a selection", id, timeout_t, download_path)
            tries += 1
            continue

        try:
            download_button = driver.find_element(By.XPATH, """//a[@id="downloadButton"]""")
            download_button.click()
        except Exception as e:
            driver, wait = timeout_msg(driver, e, "download button", id, timeout_t, download_path)
            tries += 1
            continue

        if (not wait_for_download(download_path, id, size, estimated_download_time)):
            e = Exception("Download timeout.")
            driver, wait = timeout_msg(driver, e, "Re-initializing driver...", id, timeout_t, download_path, True)
            tries += 1
            continue
        
        time.sleep(2)

        check_counts = 0
        while (not check_item_exists_dir(download_path, id) and check_counts <= 3):
            print(f"{id} failed to save to localhost. Re-checking download...")
            time.sleep(3 + check_counts)
            check_counts += 1

        if check_counts == 4:
            print(f"{id} failed to save to localhost. Redownloading...")
            tries += 1
            continue

        success_count = len([f for f in os.listdir(download_path) if (os.path.isfile(os.path.join(download_path, f)) and not f.endswith('.crdownload'))])
        print(f"{id} successfully saved to localhost! # of saved songs: {success_count}")
        counter += 1
        tries = 0
        
        print(f"Renaming {id}...")
        
        try:
            new_name = trim_newest_filename(download_path, id, title)
            print(f"{id} successfully renamed to {new_name}!")
        except Exception as e:
            print(f"Failed to rename {id}. Skipping...")
    
    if (can_retry):
        print("Retrying to download failed songs...")
        download_songs(driver, prefix, downloader, download_path, timeout_t, download_timeout, failures, False)

def zip_playlist(download_path, zip_path, playlist_title, suffix_i):
    os.makedirs(zip_path, exist_ok=True)
    zip_name = f"{playlist_title}_{suffix_i}" if suffix_i != 0 else f"{playlist_title}"
    
    try:
        shutil.make_archive(os.path.join(zip_path, zip_name), "zip", download_path)
    except Exception as e:
        print(f"Failed to convert playlist to ZIP. Error: {e}")
        return
    
@app.route("/download", methods=["POST"])
def handle_download():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "Missing 'url' field in JSON body"}), 400

    with driver_lock:  # one download at a time
        abs_cwd = os.path.abspath(os.getcwd())
        download_path_base = os.path.join(abs_cwd, "playlist_downloads")
        zip_path = os.path.join(abs_cwd, "zip")
        playlist_title = ""

        # temporary download_path so init_driver can create the folder
        download_path = download_path_base

        driver = init_driver(download_path)

        try:
            playlist_title, url, IDs = get_ids(driver, url, timeout_t)      # sets playlist_title as a side-effect
        except Exception as e:
            driver.quit()
            return jsonify({"error": f"Failed to fetch playlist: {e}"}), 500

        # resolve unique subfolder
        suffix_i = 1
        download_path = os.path.join(download_path_base, playlist_title)
        while os.path.isdir(download_path):
            download_path = os.path.join(download_path_base, f"{playlist_title}_{suffix_i}")
            suffix_i += 1

        driver = init_driver(download_path)         # reinit so prefs pick up the new download_path
        download_songs(driver, prefix, downloader, download_path, timeout_t, download_timeout, IDs)
        zip_playlist(download_path, zip_path, playlist_title, suffix_i - 1)
        driver.quit()

        # locate the ZIP that zip_playlist() just created
        zip_name = f"{playlist_title}_{suffix_i - 1}" if suffix_i - 1 != 0 else playlist_title
        zip_file = os.path.join(zip_path, f"{zip_name}.zip")

        if not os.path.exists(zip_file):
            return jsonify({"error": "ZIP was not created — check server logs"}), 500

        return send_file(
            zip_file,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{zip_name}.zip"
        )

if __name__ == "__main__":
    # globals still needed by the functions that reference them
    min_download_speed = 1.25 * 1_000_000 # 1.25 MBps == 10 Mbps
    prefix = "https://youtu.be/"
    downloader = "https://app.ytdown.to/en27/"
    url = ""
    playlist_title = ""
    download_path = os.path.abspath("playlist_downloads")
    zip_path = os.path.abspath("zip")
    timeout_t = 10
    download_timeout = 30
    driver = None

    app.run(host="0.0.0.0", port=5000)