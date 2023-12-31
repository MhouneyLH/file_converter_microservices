import pika, json, tempfile, os
from bson.objectid import ObjectId
import moviepy.editor  # für Konvertierung von Video zu mp3


def start(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)

    # empty temp file
    temp_file = tempfile.NamedTemporaryFile()

    # video content von Datenbank auslesen
    # s. bei upload.py für Felder in der Datenbank
    out = fs_videos.get(ObjectId(message["video_fid"]))

    # add video contents to empty file
    temp_file.write(out.read())

    # create audio from video
    audio = moviepy.editor.VideoFileClip(temp_file.name).audio
    temp_file.close()

    # write audio to temp file
    temp_file_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(temp_file_path)

    # Save file to mongo database
    # rb = read binary
    file = open(temp_file_path, "rb")
    data = file.read()
    # hier wird es richtig in gridfs gespeichert
    file_id = fs_mp3s.put(data)
    file.close()
    os.remove(temp_file_path)

    # Message updaten
    message["mp3_fid"] = str(file_id)

    channel.basic_publish(
        exchange="",
        routing_key=os.environ.get("MP3_QUEUE"),
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ),
    )
