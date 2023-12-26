import pika
import json


# f is the file that is being uploaded
# fs is the gridfs instance
# channel is the rabbitmq channel
# access is the access token (json header)
def upload(f, fs, channel, access):
    # upload file to mongodb using gridfs
    try:
        # this is an object
        file_id = fs.put(f)
    except Exception as err:
        return "Internal server error: " + str(err), 500

    # define message
    message = {
        "video_fid": str(file_id),
        "mp3_fid": None,
        "username": access["username"],
    }

    # send message to rabbitmq (queue)
    try:
        channel.basic_publish(
            exchange="",  # default exchange (direct)
            routing_key="video",  # name of queue
            body=json.dumps(message),  # object to json string
            properties=pika.BasicProperties(
                # persistente Message, bis von Queue verschwindet
                # -> wenn Pod failed, neustartet, etc.  und herunterfahren muss, sollen Nachrichten immernoch da sein
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        # if sending message to queue fails, delete file from gridfs
        # -> we don't want to have a file in the database that is not in the queue and not needeed
        fs.delete(file_id)
        return (
            "Internal server error: Could not send message to queue: " + str(err),
            500,
        )
