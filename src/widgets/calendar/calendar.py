############################################################################
# WHEN MODULE RUNS IT PERFORMS A SETUP
############################################################################

if __name__ == "__main__":
    params = {"pageSize": 50, "pageToken": ""}
    result = []
    response = auth.session.get(
        "https://photoslibrary.googleapis.com/v1/albums", params=params
    ).json()
    result += response["albums"]
    while "nextPageToken" in response:
        params = {"pageSize": 50, "pageToken": response["nextPageToken"]}
        response = auth.session.get(
            "https://photoslibrary.googleapis.com/v1/albums", params=params
        ).json()
        result += response["albums"]
    print("Google Photos - Album Titles")
    print("----------------------------")
    for album in result:
        if "title" in album:
            print(album["title"])
