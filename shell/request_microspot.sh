#################################################################################################
# Requete sur microspot
# devices == [1084] = id_microcapteur, si vide tous les µcapteurs sont requetes
# aggregation = "15 m" ou "1 h"
# observationTypeCodes == ["24"], si vide tous les poll sont requetes
#

# WARNING=====WARNING=====WARNING=====WARNING=====WARNING=====WARNING=====WARNING=====WARNING
#
# NOTE: LA CLE '9cef3755de20cb20b933895bebc835cb' est unique a AtmoSud NE PAS PARTAGER A L'EXTERIEUR
#
# WARNING=====WARNING=====WARNING=====WARNING=====WARNING=====WARNING=====WARNING=====WARNING
#
#################################################################################################

curl --insecure --location --request POST 'https://spot.atmo-france.org/export-api/observations' \
  --header 'Authorization: Bearer 9cef3755de20cb20b933895bebc835cb' \
  --header 'Content-Type: application/json' \
  --data-raw '{
 "timezone": "Europe/Paris",
 "studies": [],
  "campaigns": [],
  "observationTypeCodes": [],
  "devices": [1488],
  "aggregation": "1 h",
  "dateRange": [
  "2024-01-01T01:00:00+00:00",
  "2024-03-01T01:00:00+00:00"
  ]
}' > reponse # | jq > contes.json
