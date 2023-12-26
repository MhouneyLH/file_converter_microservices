import pika, sys, os, time
from pymongo import MongoClient
import gridfs
from convert import to_mp3


def main():
    client = MongoClient("mongodb-service", 27017)
    # Syntax: client.{datenbank_die_existiert}
    db_videos = client.videos
    db_mp3s = client.mp3s

    # gridfs
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # rabbitmq connection
    # rabbitmq = service name und dieser wird zu host ip für rabbitmq service resolved
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    # wird jedes Mal ausgeführt, wenn Message von Queue genommen wird
    def callback(channel, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, channel)
        if err:
            # nack = Negative Acknowledgement -> Message wurde nicht processes -> Message wird nicht von Queue entfernt
            # später kann es ja nochmal versucht werden das Video zu konvertieren
            # delivery_tag = ID der Message -> RabbitMQ weiß, dass diese nicht removed werden soll
            channel.basic_nack(delivery_tag=method.delivery_tag)
        else:
            channel.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"),
        on_message_callback=callback,
    )

    print("Waiting for messages. To exit press CTRL+C")

    # Consumer wird gestartet und wartet auf Nachrichten
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        # try to graceful shutdown
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
