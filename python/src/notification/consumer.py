import pika, sys, os
from send import email


def main():
    # rabbitmq connection
    # rabbitmq = service name und dieser wird zu host ip für rabbitmq service resolved
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    # wird jedes Mal ausgeführt, wenn Message von Queue genommen wird
    def callback(channel, method, properties, body):
        err = email.notification(body)
        if err:
            # nack = Negative Acknowledgement -> Message wurde nicht processes -> Message wird nicht von Queue entfernt
            # später kann es ja nochmal versucht werden das Video zu konvertieren
            # delivery_tag = ID der Message -> RabbitMQ weiß, dass diese nicht removed werden soll
            channel.basic_nack(delivery_tag=method.delivery_tag)
        else:
            channel.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("MP3_QUEUE"),
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
