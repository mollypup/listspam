from atproto import Client, client_utils, models
from time import time
import datetime
import json

def main():
    pds = 'https://pds.here'
    user, pwd = 'handle.here', 'pwd-here'
    session = 'run create client and get a session key and put it here' 
    repo = "your did"
    target_list = "list uri"
    actor = "target did" 

    client = create_client(pds,user,pwd,session) 
    dids = gather_followers(client,actor)

    with open("dids.json") as f: 
        dids = json.load(f) 

    
    spam_list_items(client,dids,repo,target_list)

def create_client(pds,user,pwd,session=None):
    client = Client(pds)
    if session is not None: 
        profile = client.login(session_string=session)
    else: 
        profile = client.login(user,pwd)
        print(client.export_session_string())

    print('Welcome,', profile.display_name)
    return client

def gather_followers(client,actor):
    cursor = None
    dids = [] 
    print("Gathering Followers")
    while True:
        response = client.app.bsky.graph.get_followers(
            params = models.app.bsky.graph.get_followers.Params(
                actor = actor,
                cursor = cursor,
                limit = 100
            )
        )

        cursor = response.cursor

        did_i = [f.did for f in response.followers]
        dids.extend(did_i)

        if not cursor: 
            break 
    print("Followers Gathered")
    return dids 

def spam_list_items(client,dids,repo,target_list):
    created_at = unix_to_iso_string(time())
    list_items = [models.AppBskyGraphListitem.Record(
        created_at = created_at,
        list = target_list,
        subject = did
    ) for did in dids] 

    list_of_writes = [
        models.com.atproto.repo.apply_writes.Create(
            collection = "app.bsky.graph.listitem",
            value = l_i 
        ) 
        for l_i in list_items
    ] 

    splitty = split_list(list_of_writes, 200)
    
    print("Spamming!")
    for i, s in enumerate(splitty):
        client.com.atproto.repo.apply_writes(
            data = models.com.atproto.repo.apply_writes.Data(
                repo = repo, 
                writes = s
            )
        )
        print(f"spammed! {i}")

def unix_to_iso_string(timestamp: float | int):
    """
    Returns JavaScript-like timestamp strings
    e.g. 2000-01-01T00:00:00.000Z
    """
    return (
        datetime.datetime.fromtimestamp(timestamp).isoformat(
            timespec="milliseconds"
        )
        + "Z"
    )

def iso_string_now():
    return unix_to_iso_string(time.time())

def split_list(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]   

def reverse(client,actor,repo): 
    cursor = None
    records = [] 
    print("Gathering Records")
    while True: 
        response = client.com.atproto.repo.list_records(
            params=models.com.atproto.repo.list_records.Params(
                collection  = "app.bsky.graph.listitem",
                cursor = cursor,
                limit=100,
                repo=repo

            )
        )

        cursor = response.cursor
        records.extend(response.records)

        if not cursor:
            break
    
    print("Records Gathered") 

    client2 = Client("https://public.api.bsky.app") 

    truckers = set(gather_followers(client2,actor))
    truckers_to_save = []
    for record in records: 
        if record.value.subject in truckers:
            truckers_to_save.append(record.uri.split('/')[-1])


    items_to_delete = [
        models.com.atproto.repo.apply_writes.Delete(
            collection = "app.bsky.graph.listitem",
            rkey = rkey
        ) 
        for rkey in truckers_to_save
    ] 

    splitty = split_list(items_to_delete, 200)
    print("Saving!")
    for i, s in enumerate(splitty):
        client.com.atproto.repo.apply_writes(
            data = models.com.atproto.repo.apply_writes.Data(
                repo = repo, 
                writes = s
            )
        )
        print(f"spammed! {i}")

if __name__ == '__main__':
    main()