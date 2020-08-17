import requests, json, urllib.parse, pickle

# # initiate a session
# iMapSession = requests.Session()

# # load a previously-saved session
# with open('/Users/nynhp/Documents/imap3_scripts/imap3_workspace/agol_to_imap3/cookie_storage.txt','rb') as thefile:
#     iMapSession.cookies.update(pickle.load(thefile))

def upload_photo(file_name, in_file, file_format, session, imap_url):
    files = {'file': (file_name, in_file, file_format)}

    imap_img_url = '{0}/image'.format(imap_url)

    # POST the data to iMap REST API
    iMapDataPost = session.post(imap_img_url,files=files)

    # raise an error if an unexpected response is returned from iMap
    iMapDataPost.raise_for_status()

    # if the request was successful, return the resulting JSON
    if iMapDataPost.status_code == 200:
        response_json = iMapDataPost.json()
        return response_json
    else:
        raise ValueError("200 was not returned from iMap upon photo upload!")

def imap_photo_format_handler(uploaded_photos):
    imap_formatted_photos = []
    
    for uploaded_photo in uploaded_photos:
        imap_formatted_photos.append({"presentSpeciesPhotoId": None, "presentSpeciesId": None, "photoUrl": uploaded_photo['photo_url'], "photoCredit": uploaded_photo['credit']})

    return imap_formatted_photos

def inat_imap_photo_handler(allowed_licenses, inat_photos, session, imap_url):
    # initialize a list to store the uploaded photos to iMap
    imap_photos = []

    # loop through iNat photos and prepare upload
    for photo in inat_photos:
        # ensure photo license is permitted
        if photo['license_code'] in allowed_licenses:
            # download the individual photo from iNat
            # less than ideal way to determine URL to full resolution photo
            inat_photo_url = photo['url'].replace('square', 'original')
            inat_photo_name = 'inat_photo_{0}.jpg'.format(photo['id'])

            # download photo from iNat
            raw_photo = requests.get(inat_photo_url)

            # upload the photo to the iMap and return its temporary URL
            uploaded_photo = upload_photo(inat_photo_name, raw_photo.content, 'image/jpeg', session, imap_url)
            
            # append the new iMap photo to the output list
            imap_photos.append({"photo_url": uploaded_photo['url'], "credit": photo['attribution']})

    # prepare for formatted list of photos ready for association with imap records
    formatted_imap_photos = imap_photo_format_handler(imap_photos)

    return formatted_imap_photos

# test_inat_photo = [{"id":89130810,"license_code":"cc-by-nc","url":"https://static.inaturalist.org/photos/89130810/square.jpeg?1597004423","attribution":"(c) Chris Ricker, some rights reserved (CC BY-NC)","original_dimensions":{"width":1536,"height":2048},"flags":[]}]

# print(inat_imap_photo_handler(test_inat_photo, iMapSession, 'https://imapdev.natureserve.org/imap/services'))
