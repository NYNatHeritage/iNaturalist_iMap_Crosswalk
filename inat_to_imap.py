import requests, json, urllib.parse, pickle, sys, os, math, pyproj, inat_photo
from time import sleep
from datetime import datetime, timezone

inat_session = requests.Session()

full_imap_url = 'https://imapinvasives.natureserve.org/imap/services'

allowed_photo_licenses = {
    "cc0": {
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/"
    },
    "cc-by-nc": {
        "license_url": "https://creativecommons.org/licenses/by-nc/4.0/"
    },
    "cc-by": {
        "license_url": "https://creativecommons.org/licenses/by/4.0/"
    }
}

disallowed_photo_licenses = [
    "CC-BY-SA",
    "CC-BY-ND",
    "CC-BY-NC-SA",
    "CC-BY-NC-ND"
]

# NY iNat Person ID
observer = 20882

# a project to tag records uploaded via this process
taggedProjects = [{"project": { "id": 1052}}]

# load taxa cross-walk
with open('taxa_cross-walk.json','r', encoding='utf-8') as taxa_file:
   taxa_cross_walk = json.load(taxa_file)

# sample iNat response
# with open('observations_inat_sample.json','r', encoding='utf-8') as thefile:
#    inat_records = json.load(thefile)

# sample iNat API call for all verifiable SLF records in NY
inat_api_call = 'https://api.inaturalist.org/v1/observations?place_id=48&taxon_id=324726&verifiable=true&order=asc&order_by=created_at&id_above=56480848'
# inat_api_call = "https://api.inaturalist.org/v1/observations/32173553"

# get the iNat records to upload
inat_response = inat_session.get(inat_api_call)
inat_records = inat_response.json()

iMapSession = requests.Session()
# iMapSession.verify = "W:\\Projects\\iMap\\imap3_scripts\\ca-bundle.pem"
with open('/Users/nynhp/Documents/imap3_scripts/imap3_workspace/agol_to_imap3/cookie_storage.txt','rb') as thefile:
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

    # initialize a list to construct the Present Species comment
    present_species_comment = []

    present_species_comment.append("iNaturalist Source: {0}".format(inat_record["uri"]))

    if inat_record["description"]:
        present_species_comment.append("\n\nOriginal Submitter Comment: {0}".format(inat_record["description"]))

    present_species_comment.append("\n\nReported GPS Accuracy: {0} meters".format(str(inat_record["positional_accuracy"])))
    present_species_comment.append("\n\niNaturalist Quality Grade upon upload to iMap: {0}".format(inat_record["quality_grade"]))

    distinct_photo_licenses = []

    # create a list of all distinct photo licenses used in the record
    for photo in inat_record["photos"]:
        if photo["license_code"] not in distinct_photo_licenses:
            distinct_photo_licenses.append(photo["license_code"])

    # loop through list of distinct licenses and insert the appropriate photo license info
    for photo_license in distinct_photo_licenses:
        if photo_license in allowed_photo_licenses:
            present_species_comment.append("\n\nPhoto(s) used in this record are licensed under the Creative Commons. License: {0}".format(allowed_photo_licenses[photo["license_code"]]["license_url"]))
        elif photo_license is None or photo_license in disallowed_photo_licenses:
            present_species_comment.append("\n\nSee source record for photo (not uploaded to iMap due to licensing restrictions)")

    # convert the comment list into a string
    final_present_species_comment = "".join(present_species_comment)

    presence = {
        "presenceId":None,
        "areaOfInterest":None,
        "areaOfInterestId":None,
        "observer":{"id": observer},
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
                "comments": final_present_species_comment,
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
                "photos": inat_photo.inat_imap_photo_handler(allowed_photo_licenses, inat_record["photos"], iMapSession, full_imap_url),
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
                "taggedProjects":taggedProjects
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
