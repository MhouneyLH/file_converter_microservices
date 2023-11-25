# file_converter_microservices

A simple microservice-project for converting video files to mp3 files that is orchestrated using Kubernetes.

## My notes

### General

- venv (Virtual Environment) für Python verwenden -> für dieses Umgebung dann Dinge installieren
- Erstellung venv: `python3 -m venv venv`
- Aktivierung venv (wenn in Root von Repo): `source python/src/auth/venv/bin/activate`
- Überprüfung von aktuellen venv in Umgebungsvariablen: `env | grep VIRTUAL`
- Database erstellen mit init-Skript: `mysql -u root`
- SQL-Datei ausführen: `mysql -u root < init.sql`
- einzelnen Befehl ausführen: `mysql -u root -e "BEFEHL"`
- Database leeren: `mysql -u root -e "DROP DATABASE auth"`
- User entfernen: `mysql -u root -e "DROP USER auth_user@localhost"`
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
