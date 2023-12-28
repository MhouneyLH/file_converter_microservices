import smtplib, os, json
from email.message import EmailMessage


def notification(message):
    try:
        message = json.loads(message)
        mp3_file_id = message["mp3_fid"]

        sender_address = os.environ.get("GMAIL_ADDRESS")
        sender_password = os.environ.get("GMAIL_PASSWORD")
        receiver_address = message["username"]

        msg = EmailMessage()
        # user should then use this file id to download the mp3 file from the /download endpoint
        msg.set_content(f"mp3 file_id: {mp3_file_id}")
        msg["Subject"] = "Your mp3 file is ready!"
        msg["From"] = sender_address
        msg["To"] = receiver_address

        # connect to googles smtp server
        TLS_PORT = 587
        session = smtplib.SMTP("smtp.gmail.com", TLS_PORT)
        session.starttls()
        session.login(sender_address, sender_password)
        session.send_message(msg, sender_address, receiver_address)
        session.quit()
        print("Email sent")
    except Exception as err:
        print("Error sending email: ", err)
        return "Internal server error: " + str(err), 500
