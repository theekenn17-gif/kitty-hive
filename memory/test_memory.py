import chromadb

client = chromadb.PersistentClient(path="./database")

collection = client.get_or_create_collection(
    name="kitty_memory"
)

collection.add(
    documents=[
        "Kitty is Queen of the Hive AI system.",
        "Ken is building an AI empire."
    ],
    ids=["1","2"]
)

print("Kitty memory online")
