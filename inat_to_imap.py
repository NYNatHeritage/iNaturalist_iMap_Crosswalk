import arcpy, requests, json, urllib.parse, pickle, sys, os
from datetime import datetime, timezone

inat_session = requests.Session()
inat_session.verify = "W:\\Projects\\iMap\\imap3_scripts\\ca-bundle.pem"

full_imap_url = 'https://imapdev.natureserve.org/imap/services'

inat_records = None

#with open('W:\\Projects\\iMap\\imap3_scripts\\imap3_workspace\\from_inat\\observations_inat_sample.json','r', encoding='utf-8') as thefile:
#    inat_records = json.load(thefile)

inat_response = inat_session.get('https://api.inaturalist.org/v1/observations?place_id=48&taxon_id=324726&quality_grade=research&order=desc&order_by=created_at')
inat_records = inat_response.json()

iMapSession = requests.Session()
iMapSession.verify = "W:\\Projects\\iMap\\imap3_scripts\\ca-bundle.pem"
with open('H:\\Workspace\\iMap\\misc\\cookie_storage.txt','rb') as thefile:
    iMapSession.cookies.update(pickle.load(thefile))


print(inat_records['total_results'])


def buffer_constructor(origX, origY):
    r = 5
    piEightSinVal = 1.913417161825448858642299920152
    piEightCosVal = 4.6193976625564337806409159469839
    piFourSinVal = 3.5355339059327376220042218105242
    return [[(origX + r), (origY + 0)],[(origX + piEightCosVal), (origY + piEightSinVal)],[(origX + piFourSinVal), (origY + piFourSinVal)],[(origX + piEightSinVal), (origY + piEightCosVal)],[(origX + 0), (origY + r)],[(origX + -piEightSinVal), (origY + piEightCosVal)],[(origX + -piFourSinVal), (origY + piFourSinVal)],[(origX + -piEightCosVal), (origY + piEightSinVal)],[(origX + -r), (origY + 0)],[(origX + -piEightCosVal), (origY + -piEightSinVal)],[(origX + -piFourSinVal), (origY + -piFourSinVal)],[(origX + -piEightSinVal), (origY + -piEightCosVal)],[(origX + 0), (origY + -r)],[(origX + piEightSinVal), (origY + -piEightCosVal)],[(origX + piFourSinVal), (origY + -piFourSinVal)],[(origX + piEightCosVal), (origY + -piEightSinVal)],[(origX + r), (origY + 0)]]


def project_point(in_json):
    x = in_json['coordinates'][0]
    y = in_json['coordinates'][1]

    input_sr = arcpy.SpatialReference(4326)
    out_sr = arcpy.SpatialReference(102008)
    
    point = arcpy.Point(x, y)
    point_geom = arcpy.PointGeometry(point,input_sr)
    
    return json.loads(point_geom.projectAs(out_sr).JSON)

def createNewAOI(polygon, input_date, input_presence):
    thePreparedDict = {"areaOfInterestId":None,"organization":None,"createdBy":{"id": 16500},"leadContactId":None,"leadContact":None,"comments":None,"landscapeTypeComments":None,"disturbanceComments":None,"deletedInd":False,"sensitiveInd":False,"dataEntryDate":None,"damageToHost":None,"bulkUploadId":None,"permissionReceived":None,"siteAddress":None,"sourceUniqueId":None,"searchDate":input_date,"targetTreatmentNeeded":None,"searchGoals":None,"followUp":None,"ownershipComments":None,"crewPaidHours":None,"crewVolunteerHours":None,"siteName":None,"crewComments":None,"crewVolunteerNum":None,"crewNumPaid":None,"airTemperature":None,"waterTemperature":None,"weatherComments":None,"windSpeed":None,"survey123Version":None,"modifiedDate":None,"modifiedBy":None,"samplingDetails":None,"searchedAreaPostTreatment":None,"searchedAreaMaps":[],"treatmentsInSearchedArea":[],"searchedAreaAquatic":None,"areaOfInterestPolygon":{"shape": {"rings":polygon, "spatialReference":{"wkid":102008}}},"photos":[],"presences":[input_presence],"presentSpeciesIds":[],"absence":None,"notDetectedSpeciesIds":[],"treatments":[],"treatmentIds":[],"dwaterTemperatureUnitId":None,"dwindSpeedUnitId":None,"jsearchFocusAreasAquatic":[],"jsearchFocusAreasTerrestrial":[],"dairTemperatureUnitId":None,"dwindDirectionId":None,"jsamplingMethods":[],"jwaterBodyTypes":[],"dsiteDisturbanceTypeId":None,"dsiteDisturbanceSeverityId":None,"dlandscapeTypeId":None,"dstateId":32,"lazy":False,"dremovedReasonId":None,"dcloudCoverId":None,"dsurveyTypeId":None,"jownerships":[],"jhostSpecies":[],"dnativeVegetationDistributionId":None,"dpresenceDeterminationMethodId":None}
    thePreparedDictToJSON = json.dumps(thePreparedDict)

    # url encode the string
    thePreparedJSON = urllib.parse.quote(thePreparedDictToJSON)

    #with open('from_inat\\imap3_upload_debug.json', 'w') as f:
    #    f.write(thePreparedDictToJSON)
    
    # format the record for iMap REST API POST request
    theRequest = "record=" + thePreparedJSON

    # set headers for proper POST request
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    # POST the data to iMap REST API
    iMapDataPost = iMapSession.post(full_imap_url + '/aoi/update',data=theRequest,headers=headers)
    print (iMapDataPost.status_code)

    #with open('from_inat\\imap3_upload_debug_response.html', 'w', encoding="utf-8") as f:
    #    f.write(iMapDataPost.text)

    # check if anything went wrong with the POST request
    iMapDataPost.raise_for_status()
    iMapResponse = iMapDataPost.json()
    # if everything works as expected, the AOI ID of the newly-created feature will print to the console
    print(iMapResponse["areaOfInterestId"])
    

# inat_record = inat_records['results'][1]

for inat_record in inat_records['results']:
    inat_record_date = datetime(inat_record['observed_on_details']['year'], inat_record['observed_on_details']['month'], inat_record['observed_on_details']['day'],4,0,0,0, tzinfo=timezone.utc)
    inat_record_date_timestamp = int(inat_record_date.timestamp() * 1000)

    projected_point_test = project_point(inat_record['geojson'])
    searched_area_buffer = [buffer_constructor(projected_point_test['x'],projected_point_test['y'])]

    presence = {"presenceId":None,"areaOfInterest":None,"areaOfInterestId":None,"observer":{"id":12903},"createdBy":{"id":16500,"name":"NY iMapInvasives Batch Record Creator Tool - 16500"},"observationDate":inat_record_date_timestamp,"timeLengthSearched":None,"approximateInd":False,"approximationNotes":None,"bufferDistance":None,"modifiedDate":None,"modifiedBy":None,"presenceLine":None,"presencePoint":{"shape":{"x":projected_point_test['x'],"y":projected_point_test['y'],"spatialReference":{"wkid":102008}}},"presencePolygon":None,"speciesList":[{"presentSpeciesId":None,"presenceId":None,"nationalSpeciesList":{"nationalSpeciesListId":4779,"higherClassificationUnitId":None,"modifiedById":None,"modifiedBy":None,"createdById":None,"createdBy":None,"speciesId":"2-IMAP99","scientificName":"Fake Species (for testing)","commonName":"Fake Species (for testing)","taxonomicNameComments":None,"kingdom":"Plantae","phylum":None,"taxaClass":"Dicotyledoneae","taxaOrder":None,"taxaFamily":"Onagraceae","photoIdUrl":None,"photoCredit":None,"infoUrl":None,"statesTrackedIn":[{"id":332,"name":"Arizona"},{"id":1498,"name":"New York"},{"id":3056,"name":"Vermont"}],"statesRegulatedIn":[],"minSeparationDistance":None,"modifiedDate":1507694400000,"createdDate":1507694400000,"itisTsn":None,"genus":"Fake","editableFields":[],"domainTableValues":{},"dhabitatTypeId":2,"dspeciesTypeId":4,"dgenericSpeciesTypeId":2,"dgrowthHabitId":None},"stateSpeciesList":{"stateSpeciesListId":1498,"nationalSpeciesListId":4779,"modifiedById":2323,"modifiedBy":{"id":2323,"name":"Jennifer Dean_Admin - 2323"},"createdById":2578,"createdBy":{"id":2578,"name":"Stephen W Hodge - 2578"},"stateCommonName":"Fake Species (for testing)","localUrl":"http://newyork.plantatlas.usf.edu/Results.aspx?q=Fake+Species+(for+testing)","stateSpeciesComments":None,"trackedInd":True,"trackedStatusChangeDate":1530158400000,"trackingComments":"t","stateIrankChangeDate":1530158400000,"legallyRegulatedInStateInd":False,"stateLegalStatusChangeDate":1530158400000,"stateLegalStatusComments":None,"stateMinSeparationDistance":None,"stateMinSeparationDistanceComments":None,"stateSuspiciousDistance":500000.0,"stateSuspiciousDistanceComments":"Set to 500 km to prevent suspicious distance alerts from triggering","modifiedDate":1562008635290,"createdDate":None,"commonSpeciesInd":False,"stateScientificName":"Fake Species (for testing)","photoIdUrl":None,"photoCredit":None,"infoUrl":None,"irankDetails":None,"photoSuggestions":None,"sensitiveInd":False,"editableFields":["stateCommonName","localUrl","stateSpeciesComments","trackedInd","trackingComments","legallyRegulatedInStateInd","stateLegalStatusComments","stateMinSeparationDistance","stateMinSeparationDistanceComments","stateSuspiciousDistance","stateSuspiciousDistanceComments","commonSpeciesInd","stateScientificName","photoIdUrl","photoCredit","infoUrl","irankDetails","photoSuggestions","sensitiveInd","dstateLegalStatusId","dstateHabitatId","dstateIrankId"],"domainTableValues":{},"dstateId":32,"dstateIrankId":None,"dstateLegalStatusId":None,"dstateHabitatId":None},"speciesVerifiedBy":None,"statusChangedBy":None,"confirmedInd":False,"confirmingComments":None,"comments":("Record crosswalked from iNaturalist. Source: " + inat_record['uri']),"adminComments":None,"statusChangedDate":None,"sourceUniqueId":None,"significantRecord":False,"suspiciousDistanceInd":False,"numberFound":None,"sourceRecordUrl":inat_record['uri'],"sensitiveInd":False,"invasiveImpact":None,"repositoryInfo":None,"infestedArea":None,"biocontrolSpeciesFoundComments":None,"modifiedDate":None,"modifiedBy":None,"uuid":None,"photos":[],"underTreatmentInd":False,"confirmer":True,"editableFields":["adminComments","jspeciesIdMethods","confirmedInd","confirmingComments","speciesVerifiedBy","statusChangedBy","stateSpeciesList","taggedProjects","sensitiveInd","dfollowUpId","dremovedReasonId","deleted","comments","numberFound","sourceRecordUrl","photos","invasiveImpact","repositoryInfo","devaluationTypeId","dbioagentSpeciesId","biocontrolSpeciesFoundComments","psPlant.dcoverClassId","psPlant.dplantDistributionId","psPlant.percentCover","psPlant.dwoodyPlantMaturityId","psPlant.jphenologies","psPlant.intentionalPlantingInd"],"lazy":False,"deleted":False,"psAnimal":None,"psPlant":{"presentSpeciesId":None,"percentCover":None,"intentionalPlantingInd":None,"dcoverClassId":None,"jphenologies":[],"dwoodyPlantMaturityId":None,"dplantDistributionId":None},"psAnimalVertebrate":None,"psAnimalVertebrateAquatic":None,"psAnimalInsect":None,"psAnimalOtherInvertebrate":None,"psMicroOrganism":None,"dfollowUpId":None,"devaluationTypeId":None,"dbioagentSpeciesId":None,"jspeciesIdMethods":[],"dremovedReasonId":None,"taggedProjects":[]}],"editableFields":["dremovedReasonId","deleted","observer","observationDate","timeLengthSearched","presenceLine","presencePoint","presencePolygon","speciesList"],"lazy":False,"deleted":False,"counties":[],"countries":[],"waterbodies":[],"ismas":[],"hydrobasins":[],"states":[],"createdDate":None,"usgsTopos":[],"imap2Id":None,"dremovedReasonId":None,"conservationLands":[],"ddataEntryMethodId":3}

    createNewAOI(searched_area_buffer, inat_record_date_timestamp, presence)
