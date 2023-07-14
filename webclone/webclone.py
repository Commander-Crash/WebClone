import os
import requests
import shutil
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, send_file

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0"

app = Flask(__name__)

def get_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def clone_webpage(url, directory):
    response = requests.get(url, headers={"User-Agent": USER_AGENT})
    soup = BeautifulSoup(response.content, "html.parser")

    # Clone the webpage and save it to the directory
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, "index.html"), "w") as f:
        f.write(str(soup))

    # Find all links to other files (CSS, JS, images, etc.) and clone them
    for link in soup.find_all(["link", "script", "img"]):
        if link.has_attr("href"):
            file_url = urljoin(url, link["href"])
            file_path = os.path.join(directory, urlparse(file_url).path.lstrip("/"))
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                download_file(file_url, file_path)
        elif link.has_attr("src"):
            file_url = urljoin(url, link["src"])
            file_path = os.path.join(directory, urlparse(file_url).path.lstrip("/"))
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                download_file(file_url, file_path)

    # Create a ZIP file of the cloned directory
    zip_file = shutil.make_archive(directory, "zip", directory)

    # Delete the cloned files and directory
    shutil.rmtree(directory)

    return zip_file

def download_file(url, file_path):
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True)
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        website_url = request.form["url"]
        save_as = request.form["save_as"]
        directory = os.path.join("/home/pi/webclone/sites", save_as)

        zip_file = clone_webpage(website_url, directory)

        # Provide the zip file as a download
        return send_file(zip_file, as_attachment=True)

    directory = "/home/pi/webclone/sites"
    files = [f for f in os.listdir(directory) if f.endswith(".zip")]

    return render_template("index.html", files=files, get_directory_size=get_directory_size)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5150)
