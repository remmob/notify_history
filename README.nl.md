[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![nl](https://img.shields.io/badge/lang-nl-orange.svg)](README.nl.md)

# Notification History voor Home Assistant

Een Home Assistant custom integratie die alle `notify.*` service-aanroepen en persistent notifications vastlegt in een lokale opslag en toont in een doorzoekbaar zijbalkpaneel. Nooit meer twijfelen welke notificatie er is verstuurd, wanneer, en aan wie.

> **Disclaimer**: dit is een onafhankelijke, door de community gebouwde integratie. Deze is niet verbonden aan, goedgekeurd door, of ondersteund door Nabu Casa of het Home Assistant project. De software wordt geleverd zoals ze is (zie [LICENSE](LICENSE)).

## Functionaliteit

- Legt elke `notify.*` service-aanroep vast (mobile app push, `notify.send_message` entiteiten en elk ander notify-platform), inclusief titel, bericht, ontvanger en tijdstip.
- Legt persistent notifications vast, ook wanneer ze programmatisch door andere integraties worden aangemaakt.
- Zijbalkpaneel **Notifications** met:
  - Vrije tekst zoeken in titel, bericht, ontvanger en service.
  - Filteren op ontvanger en op datum (vandaag / laatste 7 dagen).
  - Live updates: nieuwe notificaties verschijnen direct in het paneel, zonder verversen.
  - Uitklapbare details per record (aangeroepen service, extra data payload, gebruiker die de aanroep deed).
  - "Clear history"-actie, alleen voor beheerders.
- Leesbare ontvangernamen: `notify.mobile_app_*` services en `notify.send_message` entiteiten worden vertaald naar hun apparaat- of entiteitsnaam.
- Instelbare bewaartermijn: maximale leeftijd in dagen (standaard 7, tot 365) en maximaal aantal records (standaard 200, tot 5000).
- Negeerlijst: sluit specifieke notify services uit van registratie.
- Volledig lokaal: de geschiedenis wordt opgeslagen in de eigen opslag van Home Assistant (`.storage`), er verlaat niets je machine.
- Volledig in te stellen en aan te passen via de Home Assistant UI - geen YAML nodig.

## Installatie

### HACS Custom Repository

1. Open HACS in Home Assistant.
2. Klik op het menu met de drie puntjes (⋮) rechtsboven.
3. Kies 'Custom repositories'.
4. Voeg deze repository-URL toe: `https://github.com/remmob/notify_history`.
5. Zet de categorie op **Integration**.
6. Klik op 'Add' om op te slaan.

Zie de [officiële HACS documentatie](https://hacs.xyz/docs/faq/custom_repositories/) voor meer details.

### Handmatig

1. Download of kopieer de map `notify_history` uit deze repository:
	[`custom_components/notify_history`](custom_components/notify_history)
2. Plaats deze map in je Home Assistant installatie onder:
	`config/custom_components/notify_history`
3. Herstart Home Assistant.
4. Voeg de integratie toe via het Integraties-scherm in de Home Assistant UI.

Meer info en updates:
- [GitHub: remmob/notify_history](https://github.com/remmob/notify_history)

## De integratie toevoegen

Ga naar de Integraties-pagina in Home Assistant en klik op "Integratie toevoegen". Zoek naar "Notification History" en selecteer deze. Er valt tijdens de installatie niets in te stellen - bevestig, en het paneel **Notifications** verschijnt in de zijbalk. De integratie kan maar één keer worden toegevoegd.

## Het paneel gebruiken

Open **Notifications** in de zijbalk. De nieuwste notificaties staan bovenaan; nieuwe verschijnen realtime.

- Gebruik het zoekveld om te filteren op tekst in de titel, het bericht, de ontvanger of de servicenaam.
- Gebruik de ontvanger-dropdown om alleen notificaties aan een specifiek apparaat of entiteit te tonen.
- Gebruik de datum-dropdown om de lijst te beperken tot vandaag of de laatste 7 dagen.
- Klik op een record om deze uit te klappen en de aangeroepen service, de extra `data` payload (maximaal 1 kB) en, indien beschikbaar, de gebruiker die de aanroep deed te bekijken.
- Beheerders kunnen de volledige geschiedenis wissen met de knop "Clear history" (met bevestiging).

## De integratie configureren

Alle instellingen kunnen na de installatie worden gewijzigd, zonder de integratie te verwijderen. Open de integratie en klik op het tandwiel-icoon.

- **Maximale leeftijd (dagen)**: records ouder dan dit worden automatisch opgeschoond (1-365, standaard 7).
- **Maximaal aantal records**: groeit de geschiedenis hier voorbij, dan vervallen de oudste records (10-5000, standaard 200).
- **Genegeerde services**: kies (of typ) notify services waarvan aanroepen niet vastgelegd moeten worden, bijvoorbeeld een druk TTS-doel.

## Hoe het werkt

- `notify.*` service-aanroepen worden opgevangen via de Home Assistant event bus; aanroepen zonder `message` worden genegeerd.
- Persistent notifications worden opgevangen via de persistent notification component zelf, zodat ook notificaties die door andere integraties worden aangemaakt (niet via een service-aanroep) worden geregistreerd. Duplicaten binnen een venster van 5 seconden worden onderdrukt.
- De geschiedenis wordt met een vertraagde schrijfactie opgeslagen in `.storage/notify_history.history` en bij elk nieuw record opgeschoond volgens je bewaarinstellingen.
- Het paneel is een op zichzelf staande webcomponent die door de integratie zelf wordt geserveerd; het communiceert via de Home Assistant websocket-API en rendert alle inhoud XSS-veilig. Een minimale markdown-subset (vet, cursief, links) in berichten wordt ondersteund.

## Privacy

De inhoud van notificaties kan gevoelig zijn. Alles wat deze integratie opslaat blijft op je Home Assistant instantie, in een privé opslagbestand dat alleen door Home Assistant leesbaar is. Het wissen van de geschiedenis verwijdert de opgeslagen records permanent.
