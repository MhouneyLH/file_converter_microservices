# file_converter_microservices

A simple microservice-project for converting video files to mp3 files that is orchestrated using Kubernetes.

## My notes

### General

- venv (Virtual Environment) für Python verwenden -> für dieses Umgebung dann Dinge installieren
- Erstellung venv: `python3 -m venv venv`
- Aktivierung venv (wenn in Root von Repo): `source python/src/auth/venv/bin/activate`
- Deaktivierung venv: `deactivate`
- Überprüfung von aktuellen venv in Umgebungsvariablen: `env | grep VIRTUAL`
- Database erstellen mit init-Skript: `mysql -u root`
- SQL-Datei ausführen: `mysql -u root < init.sql`
- einzelnen Befehl ausführen: `mysql -u root -e "BEFEHL"`
- Database leeren: `mysql -u root -e "DROP DATABASE auth"`
- User entfernen: `mysql -u root -e "DROP USER 'auth_user@localhost'"`
- Cursor = Zeiger auf Zeile in der Datenbank -> bspw. Traversieren der Ergebnisse einer Query

### JSON Web Token

- JWT = **J**SON **W**eb **T**oken
- Client Zugriff außerhalb von Cluster über Gateway + Funktionen werden darüber abgebildet mit Endpoints (bspw. `/upload`)
- Frage klären: Wann Zugriff erlauben?
- Basic Access Authentication = Username + Passwort -> wird bei jedem Request mitgeschickt -> nicht wirklich sicher
- an sich ist JWT einfach ein Token, welcher in base64 kodierte Daten enthält (s. Bsp.)
  `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c`
- dekodiert sind es 3 JSON-Dateien, die durch Punkte getrennt sind

  - Header: verwendeter Algorithmus und Token-Typ
    - HS256 = symmetrisch (also nur 1 Private Key) -> NUR auth-service kennt diesen
    - Bsp.: `{"alg": "HS256", "typ": "JWT"}`
  - Payload: Nutzdaten, welche übermittelt werden sollen
    - Bsp.:`{"sub": "1234567890", "name": "John Doe", "iat": 1516239022}`
  - Verify Signature: digitale Signatur basierend auf Header und Payload + Secrets (Private Key)
    - Bsp.:`HMACSHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), secret)`

- Zusammengefasster Auth-Flow:

  1. Nutzer meldet sich mittels Basic Access Authentication an
  2. Auth-service erstellt ein JWT
  3. Auth-service verschlüsselt diesen JWT mit dem Private Key
  4. JTW kommt zurück an Client
  5. nochmal Anfrage von Client an Gateway: nur mit JWT
  6. auth-service kann einfach mit Private Key + angewandten Algorithmus vergleichen, ob JWT valide ist
  7. Zugriffsrechte dann über payload überprüfen (für uns nur ein Feld a la: `admin: true / false`) -> wenn Admin, dann Zugriff auf alle Endpoints

### Auth Service implementation

- Variable `__name__` wird zu `__main__` wenn Programm direkt ausgeführt wird
  ```python
  if __name__ == '__main__':
      print(__name__)
  ```
- am besten einfach für alles pip3 und python3 verwenden
- `CC=gcc pip3 install flask_mysqldb`, um spezifischen Compiler zu verwenden (geht auch mit anderen Paketen mit anderen Bedingungen)

- Container bekommt eigene IP-Adresse -> so können wir bspw. dann den Server ansprechen (Flask muss aber diese IP-Adresse kennen) -> IP-Adresse von Container ändert sich jedes Mal, deswegen für Host-Config `0.0.0.0` (= alle möglichen IP-Adressen)

### IaC with Kubernetes

- use `s` on a container in k9s to directly open the shell of the container
- `kubectl apply -f <file>`: apply a configuration file (or a directory with multiple files to apply all of them)
- k8s schaut immer, ob die aktuelle Konfiguration mit der gewünschten Konfiguration übereinstimmt -> wenn nicht, dann wird die aktuelle Konfiguration angepasst
- spec-Format in kubernetes-Konfig-Dateien ist verschieden je nach angegebenem Typ (Deployment, Service, etc.)
- Kubernetes-API: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/
- überall, wo man `kind` als Attribut sieht, zählt als Kubernetes-Objekt

### Gateway Service implementation

- gridfs = Grid File System -> für große Dateien (> 16MB), die nicht in MongoDB gespeichert werden können
- dafür wird große Datei in viele kleine Dateien aufgeteilt und in MongoDB gespeichert
- Vorgehensweise mit Hilfe von RabbitMQ (= Message Broker, der verwendet wird, um Nachrichten zwischen Microservices zu senden):

  1. Gateway speichert Video in MongoDB
  2. Message in RabbitMQ, dass Video in MongoDB gespeichert wurde
  3. Converter-Service nimmt Message von der Queue, nimmt ID des Videos und weiß somit wo es in MongoDB gespeichert liegt
  4. Video in mp3 konvertieren
  5. mp3 in MongoDB speichern
  6. Message in RabbitMQ (von Converter-Service), dass mp3 in MongoDB gespeichert wurde
  7. Notification-Service nimmt Message von der Queue und kennt ja die ID der mp3
  8. Senden von bspw. E-Mail an Client, dass mp3 fertig ist mit einer ID
  9. Client kann über Gateway mp3 herunterladen (mit Hilfe von JWT und ID)

- **Interservice Communication** (ISC) = Kommunikation zwischen Microservices

  - **synchron**: Client wartet auf Antwort (bspw. Gateway bei Login mit auth-service)
    - Blockierend (Client kann nichts anderes machen)
    - hohe Kopplung zwischen Gateway und Service
  - **asynchron**: Client wartet nicht auf Antwort (bspw. Gateway bei Upload mit converter-service)
    - Nicht-Blockierend (Client kann andere Dinge machen)
    - meistens mit Hilfe von Message Broker (bspw. RabbitMQ), also hier eine Queue
    - niedrige Kopplung zwischen Gateway und Service

- **Konsistenz**: alle Microservices müssen immer auf dem gleichen Stand sein

  - **Strong Consistency**: alle Microservices sind immer auf dem gleichen Stand
    - bspw. User kann Video erst herunterladen, wenn es konvertiert wurde (bspw. wenn Gateway blockiert wäre bis Converter fertig ist)
  - **Eventual Consistency**: irgendwann sind alle Microservices auf dem gleichen Stand
    - bspw. User hätte somit Möglichkeit Video direkt herunterzuladen, obwohl es nocht nicht konvertiert wurde

- mit Datei `__init__.py` kann man Ordner als Package kennzeichnen

### Wie funktiniert RabbitMQ genau?

![](./assets/images/rabbitmq.png)

- **Producer** = Service, der message schickt -> hier: Gateway
- **Consumer** = Service, der message empfängt -> hier: bspw. Converter
- **Broker** = RabbitMQ-Instanz
- gesendet wird an Exchange -> Weiterleiten an richtige Queue (gibt meistens mehrere Queues mit 1 Rabbitmq-Instanz = 1 Message Broker)
- von korrekter Queue dann an Consumer
- **Competing Consumer Pattern** = mehrere Consumer können von einer Queue lesen -> Message 1 an Cons. 1, Message 2 an Cons. 2, Message 3 wieder an Cons. 1, etc.
- gibt verschiedene Arten von Exchanges (bspw. Fanout, Direct, Topic, Headers) -> hier: Direct (einfach beim Parameter `exchange` einen leeren String angeben)
- **Message** = JSON-Objekt mit 2 Feldern: `routing_key` und `body`
- **Routing Key** = Name der Queue, an die die Message gesendet werden soll
- **Body** = Payload der Message

### Kuberentes Ingress

- **Service** = Gruppe von Pods, die die gleiche Funktionalität haben (mit Hilfe von bspw. Label-Selector)
- **Ingress** = Haupt-Eingangspunkt von außen + Regeln, die den Zugriff / Routing auf Services definieren (bspw. über Hostname, Pfad, etc.)
- für Konfiguration, dass man einfach mp3converter.com eingeben kann auf lokaler Maschine und das auf localhost gemappt wird, habe ich folgendes geamcht:

  ```bash
  echo "127.0.0.1 mp3converter.com" | sudo tee -a /etc/hosts

  # ingress-addon for minikube
  minikube addons list
  minikube addons enable ingress

  # start tunnel
  minikube tunnel --bind-address "127.0.0.1"
  ```

- um Cluster runter zu skalieren: `kubectl scale deployment <deployment-name> --replicas=0`

### StatefulSet

- **StatefulSet** = wie Deployment, aber mit ein paar Unterschieden:
  - **Pods** haben einen Namen (id), der sich nicht ändert (bspw. `auth-service-0`) -> wenn Pod failt, ist es leichter existierende Volumes zu den neuen Pods zu mappen
  - **Pods** haben einen eigenen **Persistent Volume Claim** (PVC), der sich nicht ändert
  - **Pods** werden in einer bestimmten Reihenfolge gestartet und beendet
  - **Pods** werden in einer bestimmten Reihenfolge neu gestartet
  - **Pods** haben einen eigenen **Headless Service**, der sich nicht ändert
- die einzelnen Pods verhalten sich als **Slaves** (also können nur von PVCs lesen)
- die Queue-Instanz verhält sich als **Master** (also kann auch schreiben) -> die Master-Slaves-Speicher werden die ganze Zeit mit Master-Speicher synchronisiert
- Mounting von lokalen Storage mit Storage von Container notwendig -> wenn etwas schiefgeht bei Container wird es dann bei uns lokal gespeichert -> Container wird redeployed und kann dann wieder auf lokalen Storage zugreifen
- RabbitMQ speichert Messages von Queue in `/var/lib/rabbitmq`
- **PVC** = **P**ersistent **V**olume **C**laim -> wird in StatefulSet verwendet, um lokalen Storage zu mounten
- in Pod wird auf PVC gemountet -> PVC besitzt ein Persistent Volume (PV) -> mit diesem PV wird dann auf tatsächlichen lokalen Storage gemountet
- **Nutzen** = wenn Pod failt, dann wird neuer Pod erstellt und kann auf lokalen Storage zugreifen
- GUI für RabbitMQ muss ähnlich wie unsere "Domain" von Container auf lokale Maschine gemappt werden (gleiche Adresse, wie für mp3converter.com verwenden!)
  ```bash
  echo "127.0.0.1 rabbitmq-manager.com" | sudo tee -a /etc/hosts
  ```
- Erhalten von Informationen über Pod: `kubectl describe pod rabbitmq`
- Konfiguration von PVC ist immutable (als kann während Laufzeit nicht mehr geändert werden) -> wenn da ein Fehler war, alles, was damit in Verbindung steht, neustarten
  ```bash
  kubectl delete -f ./
  kubectl apply -f ./
  ```
- wenn rabbitmq UI erreichbar sein soll: daran denken, dass `minikube tunnel --bind-address "127.0.0.1"` ausgeführt wird
- Default-Anmeldedaten für RabbitMQ: `guest:guest`

## Testen, ob bis hierhin die Queues schonmal funktionen

- Was sollte passieren?
  - convertete Videos stauen sich in video-Queue auf, weil ich die ja noch nicht von der Queue abhole
- Testen mit

  ```bash
  youtube-dl {file-url}

  # create JWT
  curl -X POST http://mp3converter.com/login -u lucas@email.com:Auth123

  # upload video
  curl -X POST -F 'file=@{path/to/your/file}' -H 'Authorization: Bearer {the-jwt-you-got}' http://mp3converter.com/upload

  # You should get a message like: "Success: File uploaded!"
  ```

- Was ist Bearer?
  - Typ-Attribut im HTTP-Header
  - to bear = etwas vorlegen
  - Inhaber von Token ist berechtigt, auf Ressource zuzugreifen, indem einfach vorgelegt wird (Besitz davon allein reicht also aus, um Zugriff zu erhalten)
- Now you should see the video in the mp3-queue in the RabbitMQ UI
  ![](./assets/images/video_upload_in_rabbitmq.png)
