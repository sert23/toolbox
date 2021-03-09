import os
import subprocess
import json

def download_Drive(input_folder):
    dest_file = os.path.join(input_folder, "drive.json")

    with open(dest_file, "r") as read_file:
        data = json.load(read_file)

    k = [data.keys()][0]
    atts = data[k]
    name = os.path.join(input_folder, atts[0])
    url = atts[2]
    token = atts[3]

    downloading = os.path.join(input_folder, "downloading")
    os.system("touch " + downloading)
    command_list = ["curl", "-H", '"Authorization: Bearer ' + token + '"',
                    url, "-o", '"' + name + '"']

    subprocess.Popen(command_list)
    # curl -H "Authorization: Bearer $token" "https://www.googleapis.com/drive/v3/files/$id?alt=media" -o "$file"

    print(input_folder)