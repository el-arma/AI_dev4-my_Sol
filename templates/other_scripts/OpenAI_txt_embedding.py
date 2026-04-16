from openai import OpenAI
import numpy as np

client = OpenAI()

def get_embedding(text: str) -> np.ndarray:
    resp = client.embeddings.create(
        model="text-embedding-3-large",
        # vector: [3072 floatów]
        # model="text-embedding-3-small",
        input=text
    )
    return np.array(resp.data[0].embedding)


def similarity_percent(a: str, b: str) -> float:
    emb_a = get_embedding(a)
    emb_b = get_embedding(b)

    print("emb_a: ", emb_a)
    print("emb_b: ", emb_b)

    # cosine similarity
    sim = np.dot(emb_a, emb_b) / (
        np.linalg.norm(emb_a) * np.linalg.norm(emb_b)
    )

    print("sim: ", sim)

    # map [-1,1] -> [0,100]
    percent = (sim + 1) / 2 * 100
    return percent

# Samples:
# a = "Observed values stay controlled, the platform behaves exactly as intended, and I approved the report as normal for this review iteration."
# b = "Observed values stay controlled, the report matches previous healthy cycles, and I kept the system in normal mode for this capture moment."

# a = "The recent snapshot is reassuring, the readings align with normal patterns, so I logged it as routine for the latest service snapshot."
# b = "The recent snapshot is reassuring, we are still in a safe operating zone, so monitoring continues unchanged for the active shift period."

a = "This run finished without surprises, the latest sample fits reference behavior, so I logged it as routine for the current control interval."
b = "This run finished without surprises, there is no sign of abnormal activity, so I logged it as routine for the latest service snapshot."


score = similarity_percent(a, b)

print(f"Similarity: {score:.2f}%")