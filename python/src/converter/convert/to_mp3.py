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
    # after closing it will get automatically deleted
    temp_file.close()

    # write audio to temp file
    # no naming collision check needed, because the video id is unique
    temp_file_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    # here a file gets created, that has to be deleted later manually
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

    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        # if sending message to queue fails, delete file from gridfs -> it wont be processes anyway
        # durch nack wird die Message aber nicht von der Queue entfernt und kann später nochmal versucht werden
        fs_mp3s.delete(file_id)

        return "Failed to publish message"
