import requests, json, urllib.parse, pickle, sys, os, math, pyproj
from time import sleep
from datetime import datetime, timezone

inat_session = requests.Session()

full_imap_url = 'https://imapdev.natureserve.org/imap/services'

# taxa cross-walk
with open('taxa_cross-walk.json','r', encoding='utf-8') as taxa_file:
   taxa_cross_walk = json.load(taxa_file)

# sample iNat response
# with open('observations_inat_sample.json','r', encoding='utf-8') as thefile:
#    inat_records = json.load(thefile)

# sample iNat API call for all verifiable SLF records in NY
inat_api_call = 'https://api.inaturalist.org/v1/observations?place_id=48&taxon_id=324726&verifiable=true&order=desc&order_by=created_at'

# get the iNat records to upload
inat_response = inat_session.get(inat_api_call)
inat_records = inat_response.json()

iMapSession = requests.Session()
# iMapSession.verify = "W:\\Projects\\iMap\\imap3_scripts\\ca-bundle.pem"
with open('','rb') as thefile:
    iMapSession.cookies.update(pickle.load(thefile))

def getPresentSpeciesRecord(species_id):
    # GET the data from the iMap REST API
    iMapDataGet = iMapSession.get(full_imap_url + '/presentSpecies/new/' + str(species_id))

    # check if anything went wrong with the POST request
    iMapDataGet.raise_for_status()

    iMapResponse = iMapDataGet.json()

    return iMapResponse

def buffer_constructor(origX, origY):
    r = 5
    piEightSinVal = 5 * (math.sin(math.pi / 8))
    piEightCosVal = 5 * (math.cos(math.pi / 8))
    piFourSinVal = 5 * (math.sin(math.pi / 4))

    # construct a 5m buffer circular polygon to represent the searched area 
    return [
        [(origX + r),(origY + 0)],
        [(origX + piEightCosVal), (origY + piEightSinVal)],
        [(origX + piFourSinVal), (origY + piFourSinVal)],
        [(origX + piEightSinVal), (origY + piEightCosVal)],
        [(origX + 0), (origY + r)],
        [(origX + -piEightSinVal), (origY + piEightCosVal)],
        [(origX + -piFourSinVal), (origY + piFourSinVal)],
        [(origX + -piEightCosVal), (origY + piEightSinVal)],
        [(origX + -r), (origY + 0)],
        [(origX + -piEightCosVal), (origY + -piEightSinVal)],
        [(origX + -piFourSinVal), (origY + -piFourSinVal)],
        [(origX + -piEightSinVal), (origY + -piEightCosVal)],
        [(origX + 0), (origY + -r)],
        [(origX + piEightSinVal), (origY + -piEightCosVal)],
        [(origX + piFourSinVal), (origY + -piFourSinVal)],
        [(origX + piEightCosVal), (origY + -piEightSinVal)],
        [(origX + r), (origY + 0)]
        ]

def project_point(in_json):
    # project coordinates to apply buffer
    input_longitude = in_json['coordinates'][0]
    input_latitude = in_json['coordinates'][1]

    # project to UTM 18N
    project_coords = pyproj.Transformer.from_crs(4326, 32618)
    
    return project_coords.transform(input_latitude, input_longitude)

def createNewAOI(polygon, input_date, input_presence):
    thePreparedDict = {
        "areaOfInterestId": None,
        "organization": None,
        "createdBy": {"id": 16500},
        "leadContactId": None,
        "leadContact": None,
        "comments": None,
        "landscapeTypeComments": None,
        "disturbanceComments": None,
        "deletedInd": False,
        "sensitiveInd": False,
        "dataEntryDate": None,
        "damageToHost": None,
        "bulkUploadId": None,
        "permissionReceived": None,
        "siteAddress": None,
        "sourceUniqueId": None,
        "searchDate": input_date,
        "targetTreatmentNeeded": None,
        "searchGoals": None,
        "followUp": None,
        "ownershipComments": None,
        "crewPaidHours": None,
        "crewVolunteerHours": None,
        "siteName": None,
        "crewComments": None,
        "crewVolunteerNum": None,
        "crewNumPaid": None,
        "airTemperature": None,
        "waterTemperature": None,
        "weatherComments": None,
        "windSpeed": None,
        "survey123Version": None,
        "modifiedDate": None,
        "modifiedBy": None,
        "samplingDetails": None,
        "searchedAreaPostTreatment": None,
        "searchedAreaMaps": [],
        "treatmentsInSearchedArea": [],
        "searchedAreaAquatic": None,
        "areaOfInterestPolygon": {
            "shape": {
                "rings":polygon,
                "spatialReference":{"wkid": 32618}}
            },
        "photos": [],
        "presences": [input_presence],
        "presentSpeciesIds": [],
        "absence": None,
        "notDetectedSpeciesIds": [],
        "treatments": [],
        "treatmentIds": [],
        "dwaterTemperatureUnitId": None,
        "dwindSpeedUnitId": None,
        "jsearchFocusAreasAquatic": [],
        "jsearchFocusAreasTerrestrial": [],
        "dairTemperatureUnitId": None,
        "dwindDirectionId": None,
        "jsamplingMethods": [],
        "jwaterBodyTypes": [],
        "dsiteDisturbanceTypeId": None,
        "dsiteDisturbanceSeverityId": None,
        "dlandscapeTypeId": None,
        "dstateId": 32,
        "lazy": False,
        "dremovedReasonId": None,
        "dcloudCoverId": None,
        "dsurveyTypeId": None,
        "jownerships": [],
        "jhostSpecies": [],
        "dnativeVegetationDistributionId": None,
        "dpresenceDeterminationMethodId": None
        }
    thePreparedDictToJSON = json.dumps(thePreparedDict)

    # url encode the string
    thePreparedJSON = urllib.parse.quote(thePreparedDictToJSON)

    with open('imap3_upload_debug.json', 'w') as f:
       f.write(thePreparedDictToJSON)
    
    # format the record for iMap REST API POST request
    theRequest = "record=" + thePreparedJSON

    # set headers for proper POST request
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    # POST the data to iMap REST API
    iMapDataPost = iMapSession.post(full_imap_url + '/aoi/update',data=theRequest,headers=headers)
    print (iMapDataPost.status_code)

    with open('imap3_upload_debug_response.html', 'w', encoding="utf-8") as f:
       f.write(iMapDataPost.text)

    # check if anything went wrong with the POST request
    iMapDataPost.raise_for_status()
    iMapResponse = iMapDataPost.json()

    # write the new record to a log file for future reference
    with open('inat_imap3_created_records.txt', 'a') as f:
        f.write(str(iMapResponse["areaOfInterestId"]) + ',' + str(iMapResponse["presences"][0]["speciesList"][0]["sourceUniqueId"]) + ',' + datetime.today().isoformat() + '\n')
    
    # if everything works as expected, the AOI ID of the newly-created feature will print to the console
    print(iMapResponse["areaOfInterestId"])

# inat_record = inat_records['results'][1]

for inat_record in inat_records['results']:
    sleep(1) # slow process by one second to reduce load on server

    # cross-walk the iNat record date to a timestamp for iMap
    inat_record_date = datetime(inat_record['observed_on_details']['year'], inat_record['observed_on_details']['month'], inat_record['observed_on_details']['day'],4,0,0,0, tzinfo=timezone.utc)
    inat_record_date_timestamp = int(inat_record_date.timestamp() * 1000)

    projected_point = project_point(inat_record['geojson'])
    searched_area_buffer = [buffer_constructor(projected_point[0],projected_point[1])]

    # get a new present species record
    new_present_species = getPresentSpeciesRecord(taxa_cross_walk[str(inat_record["taxon"]["id"])]["ny_species_list_id"])

    presence = {
        "presenceId":None,
        "areaOfInterest":None,
        "areaOfInterestId":None,
        "observer":{"id":17047},
        "createdBy":{"id":16500,"name":"NY iMapInvasives Batch Record Creator Tool - 16500"},
        "observationDate":inat_record_date_timestamp,
        "timeLengthSearched":None,
        "approximateInd":False,
        "approximationNotes":None,
        "bufferDistance":None,
        "modifiedDate":None,
        "modifiedBy":None,
        "presenceLine":None,
        "presencePoint": {"shape":{"x":projected_point[0],"y":projected_point[1],"spatialReference":{"wkid": 32618}}},
        "presencePolygon":None,
        "speciesList":
            [
                {"presentSpeciesId":None,
                "presenceId":None,
                "nationalSpeciesList": new_present_species["nationalSpeciesList"],
                "stateSpeciesList": new_present_species["stateSpeciesList"],
                "speciesVerifiedBy":None,
                "statusChangedBy":None,
                "confirmedInd":False,
                "confirmingComments":None,
                "comments":("Record automatically crosswalked from iNaturalist.\nSource: " + inat_record["uri"] + "\nReported GPS Accuracy: " + str(inat_record["positional_accuracy"]) + " meters" + "\niNat Quality Grade upon upload to iMap: " + inat_record["quality_grade"]),
                "adminComments": None,
                "statusChangedDate":None,
                "sourceUniqueId": inat_record["id"],
                "significantRecord":False,
                "suspiciousDistanceInd":False,
                "numberFound":None,
                "sourceRecordUrl":inat_record["uri"],
                "sensitiveInd":False,
                "invasiveImpact":None,
                "repositoryInfo":None,
                "infestedArea":None,
                "biocontrolSpeciesFoundComments":None,
                "modifiedDate":None,
                "modifiedBy":None,
                "uuid":None,
                "photos":[],
                "underTreatmentInd":False,
                "confirmer":True,
                "lazy":False,
                "deleted":False,
                "psAnimal":None,
                "psPlant":{
                    "presentSpeciesId":None,
                    "percentCover":None,
                    "intentionalPlantingInd":None,
                    "dcoverClassId":None,
                    "jphenologies":[],
                    "dwoodyPlantMaturityId":None,
                    "dplantDistributionId":None
                },
                "psAnimalVertebrate":None,
                "psAnimalVertebrateAquatic":None,
                "psAnimalInsect":None,
                "psAnimalOtherInvertebrate":None,
                "psMicroOrganism":None,
                "dfollowUpId":None,
                "devaluationTypeId":None,
                "dbioagentSpeciesId":None,
                "jspeciesIdMethods":[],
                "dremovedReasonId":None,
                "taggedProjects":[]
            }],
            "lazy":False,
            "deleted":False,
            "counties":[],
            "countries":[],
            "waterbodies":[],
            "ismas":[],
            "hydrobasins":[],
            "states":[],
            "createdDate":None,
            "usgsTopos":[],
            "imap2Id":None,
            "dremovedReasonId":None,
            "conservationLands":[],
            "ddataEntryMethodId":3
            }

    createNewAOI(searched_area_buffer, inat_record_date_timestamp, presence)
