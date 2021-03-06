# grundschmutz-tools

Dieses Repository enthält ein Script, welches die Daten des [IT-Grundschutz-Kompendiums](https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/IT-Grundschutz-Kompendium/it-grundschutz-kompendium_node.html) des [Bundesamts für Sicherheit in der Informationstechnik (BSI)](https://www.bsi.bund.de/) herunterlädt, konvertiert, parst und im Anschluss als JSON bereitstellt.

## Howto

Das Script funktioniert unter Linux und benötigt zusätzlich das Tool/Package ```pdftohtml```.
Vor dem Ausführen müssen die Python-Abhängigkeiten installiert werden:
> pip install -r [tools/requirements.txt](tools/requirements.txt)

> python3 [```tools/download_and_convert.py```](tools/download_and_convert.py)

Die Daten werden im "data" Ordner abgelegt.

## Howto Docker Alternative

Wenn man unabhängig vom Betriebssystem sein will, kann so vorgegangen werden:

> docker build -t grundschmutz-tools:latest .

> docker run --rm -v $(pwd)/data:/home/user/data grundschmutz-tools

Der Teil  ```$(pwd)/data``` muss ggf. je nach Betriebssystem angepasst werden (siehe [docs.docker.com VOLUME](https://docs.docker.com/engine/reference/run/#volume-shared-filesystems)).

## Intention

Nach dem Prinzip von [Open Data](https://de.wikipedia.org/wiki/Open_Data) sollten alle öffentlichen Daten möglichst [maschinenlesbar](https://en.wikipedia.org/wiki/Machine-readable_data) zur Verfügung gestellt werden, damit man sie filtern, verknüpfen oder anderweitig verarbeiten kann.

Seit der Version 2021 stellt das BSI das Kompendium nur noch in Form von *nicht* barrierefreien PDF-Dateien bereit.
Selbst auf mehrere Informationsfreiheitsanfragen bzgl. dessen wurde ablehnend und intransparent reagiert:
- https://fragdenstaat.de/anfrage/bausteine-aus-it-grundschutz-kompendium-in-maschinenlesbarer-form/
- https://fragdenstaat.de/anfrage/bsi-grundschutz-kompedium-2021-nach-12a-egovg/

Für die Version 2022 stellt das BSI das Kompendium zusätzlich als XML ([DocBook](https://en.wikipedia.org/wiki/DocBook)) zur Verfügung.
Dieses Format eignet sich jedoch nur zur Erstellung von technischer Dokumentation, jedoch hilft es nicht dabei, die Daten zu attributieren und zu linken.

Daraus ergibt sich die Notwendigkeit dieses Repositorys, welches strukturierte Daten (aus den offiziellen Quellen) unter Einhaltung des definierten [Datenschemas](schema) erzeugt.

## Lizenz

Für alle aktuellen Dateien in diesem Repository gilt folgende [Lizenz](LICENSE).
