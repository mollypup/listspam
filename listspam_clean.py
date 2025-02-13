from atproto import Client, models


def main():
    handle, pwd = 'handle.here', 'pwd-here'
    repo = resolve_handle(handle)
    pds = resolve_pds(repo)
    # session = 'run create client and get a session key and put it here'
    session = None
    target_list = "list uri"
    actor = "target did"
    # hi chat (fuck you willow)
    client = create_client(pds, handle, pwd, session)
    dids = gather_followers(client, actor)

    spam_list_items(client, dids, repo, target_list)


def create_client(pds, user, pwd, session=None):
    client = Client(pds)
    if session is not None:
        profile = client.login(session_string=session)
    else:
        profile = client.login(user, pwd)
        print(client.export_session_string())

    print('Welcome,', profile.display_name)
    return client


def gather_followers(client, actor):
    cursor = None
    dids = []
    print("Gathering Followers")
    while True:
        response = client.app.bsky.graph.get_followers(
            params=models.app.bsky.graph.get_followers.Params(
                actor=actor,
                cursor=cursor,
                limit=100
            )
        )

        cursor = response.cursor

        did_i = [f.did for f in response.followers]
        dids.extend(did_i)

        if not cursor:
            break
    print("Followers Gathered")
    return dids


def spam_list_items(client, dids, repo, target_list):
    created_at = client.get_current_time_iso()
    list_items = [models.AppBskyGraphListitem.Record(
        created_at=created_at,
        list=target_list,
        subject=did
    ) for did in dids]

    list_of_writes = [
        models.com.atproto.repo.apply_writes.Create(
            collection="app.bsky.graph.listitem",
            value=l_i
        )
        for l_i in list_items
    ]

    splitty = split_list(list_of_writes, 200)

    print("Spamming!")
    for i, s in enumerate(splitty):
        client.com.atproto.repo.apply_writes(
            data=models.com.atproto.repo.apply_writes.Data(
                repo=repo,
                writes=s
            )
        )
        print(f"spammed! {i}")


def resolve_pds(did):
    if did.startswith("did:plc:"):
        r = httpx.get(f"https://plc.directory/{did}")
        r.raise_for_status()
    elif did.startswith("did:web"):
        r = httpx.get(f"https://{did.lstrip("did:web")}/.well-known/did.json")
        r.raise_for_status()
    else:
        raise ValueError("Invalid DID Method")
    for service in r.json()["service"]:
        if service["id"] == "#atproto_pds":
            return service["serviceEndpoint"]


def resolve_handle(user):
    if user.startswith("did:"):
        did = user
    else:
        pub = Client("https://public.api.bsky.app")
        did = pub.resolve_handle(user).did

    return did


def split_list(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def reverse(client, actor, repo):
    cursor = None
    records = []
    print("Gathering Records")
    while True:
        response = client.com.atproto.repo.list_records(
            params=models.com.atproto.repo.list_records.Params(
                collection="app.bsky.graph.listitem",
                cursor=cursor,
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

    truckers = set(gather_followers(client2, actor))
    truckers_to_save = []
    for record in records:
        if record.value.subject in truckers:
            truckers_to_save.append(record.uri.split('/')[-1])

    items_to_delete = [
        models.com.atproto.repo.apply_writes.Delete(
            collection="app.bsky.graph.listitem",
            rkey=rkey
        )
        for rkey in truckers_to_save
    ]

    splitty = split_list(items_to_delete, 200)
    print("Saving!")
    for i, s in enumerate(splitty):
        client.com.atproto.repo.apply_writes(
            data=models.com.atproto.repo.apply_writes.Data(
                repo=repo,
                writes=s
            )
        )
        print(f"spammed! {i}")


if __name__ == '__main__':
    main()
