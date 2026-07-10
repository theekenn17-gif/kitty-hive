import chromadb
import ollama

client = chromadb.PersistentClient(
    path="./database"
)

memory = client.get_or_create_collection(
    name="kitty_long_term_memory"
)

def remember(text):
    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )

    memory.add(
        ids=[str(memory.count())],
        documents=[text],
        embeddings=[response["embedding"]]
    )

    print("Kitty remembered:", text)


def recall(question):
    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=question
    )

    results = memory.query(
        query_embeddings=[response["embedding"]],
        n_results=3
    )

    print("Kitty recall:")
    print(results["documents"])


remember("Ken is building Kitty Hive, a local AI system.")
remember("Kitty has Queen, Worker and Soldier agents.")
remember("The goal is to build income systems and automation.")

recall("What is Ken building?")
