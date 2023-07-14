import os
import requests
import shutil
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, send_file, abort

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0"

app = Flask(__name__)

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

    return render_template("index.html", files=files)

@app.route("/download/<filename>", methods=["GET"])
def download_zip(filename):
    # Specify the path to the zip files directory
    directory = "/home/pi/webclone/sites"

    # Get the full path of the requested zip file
    zip_file_path = os.path.join(directory, filename)

    # Check if the zip file exists
    if os.path.isfile(zip_file_path):
        # Return the zip file as a downloadable attachment
        return send_file(zip_file_path, as_attachment=True)
    else:
        # If the zip file does not exist, return a 404 error
        abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5150)
