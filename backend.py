import os
import re
from fastapi import FastAPI, UploadFile, File
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from graphviz import Digraph
import chromadb
import google.generativeai as genai
import fitz


app = FastAPI()


UPLOAD_FOLDER = "uploads"


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


chroma_client = chromadb.Client()


collection = chroma_client.get_or_create_collection(
    name="robot_manuals"
)


tokenizer = AutoTokenizer.from_pretrained(
    "distilbert-base-uncased"
)


embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


def chunk_text(text, chunk_size=500):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks



@app.get("/")
def home():
    return {"message": "app is working"}



@app.post("/tokenize")
def tokenize_text(data: dict):
    text = data["text"]
    tokens = tokenizer(
        text,
        padding=True,
        truncation=True,
        return_tensors="pt"
    )
    return {
        "input_ids": tokens["input_ids"].tolist(),
        "attention_mask": tokens["attention_mask"].tolist()
    }



@app.post("/test")
def test():
    return {"message": "hello"}



@app.post("/chat")
def chat(data: dict):
    try:
        question = data.get("prompt", "")

        if not question:
            return {
                "response": "Please enter a question."
            }

        query_embedding = embedding_model.encode(
            question
        ).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        if not results["documents"]:
            return {
                "response": "No documents found in the database."
            }

        retrieved_chunks = results["documents"][0]

        context = "\n\n".join(
            retrieved_chunks
        )

        rag_prompt = f"""You are an AI Robot Hardware Installation Assistant.
Your job is to help technicians understand robot manuals, hardware installation guides, assembly instructions, and industrial documentation.
Guidelines:

* Answer directly.
* Use natural language.
* Write like an experienced engineer.
* Explain technical concepts clearly.
* Keep answers concise.
* Do not say "Based on the provided context".
* Do not mention the manual or context.
* If the information is unavailable, say: "I could not find that information in the uploaded manual."
Information:
{context}
Question:
{question}
Answer: """

        response = model.generate_content(rag_prompt)

        answer = response.text

        return {
            "question": question,
            "response": answer,
            "retrieved_chunks": retrieved_chunks
        }

    except Exception as e:
        return {
            "response": f"Error: {str(e)}"
        }



@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    chunks = chunk_text(text)
    embeddings = embedding_model.encode(chunks)

    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[
                f"Manual Content: {chunk}"
            ],
            embeddings=[embeddings[i].tolist()],
            ids=[f"{file.filename}_chunk_{i}"]
        )

    return {
        "message": "PDF uploaded successfully",
        "filename": file.filename,
        "total_chunks": len(chunks),
        "embedding_dimension": len(embeddings[0]),
        "stored_in_chromadb": True
    }



@app.post("/generate-flowchart")
def generate_flowchart(data: dict):
    print("FLOWCHART STARTED")

    topic = data.get("topic", "")

    query_embedding = embedding_model.encode(
        topic
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2
    )
    print("CHROMA SEARCH DONE")

    if not results["documents"] or not results["documents"][0]:
        return {
            "error": "No relevant manual content found."
        }

    retrieved_chunks = results["documents"][0][:2]
    context = "\n\n".join(retrieved_chunks)

    prompt = f"""
You are a Bosch robotics engineer.

Manual information:
{context}

Question:
{topic}

Extract the REAL procedure from the manual.

Rules:
- Return ONLY numbered steps.
- Return between 4 and 8 steps.
- Do not invent information.
- Do not explain anything.
- Do not use examples.
"""

    print("GEMINI STARTING")

    try:
        response = model.generate_content(prompt)

        steps_text = response.text
        print("GEMINI FINISHED")

    except Exception as e:
        print(f"GEMINI REQUEST FAILED: {str(e)}")
        return {"error": f"Gemini request failed: {str(e)}"}

    print("\nLLM OUTPUT:\n")
    print(steps_text)
    print("\n")

    steps = []
    for line in steps_text.split("\n"):
        line = line.strip()
        if line:
            line = re.sub(r'^\d+[\.\-\)]\s*', '', line)
            steps.append(line)

    if not steps:
        return {"error": "The model did not generate any distinct parsing steps."}

    print("GRAPHVIZ STARTING")
    flowchart = Digraph()

    for i, step in enumerate(steps):
        flowchart.node(str(i), step)
        if i > 0:
            flowchart.edge(str(i - 1), str(i))

    output_path = "uploads/flowchart"

    try:
        flowchart.render(
            output_path,
            format="png",
            cleanup=True
        )
    except Exception as gv_err:
        print(f"Graphviz failed to render: {str(gv_err)}")
        return {"error": f"Graphviz layout engine failed: {str(gv_err)}"}

    print("FLOWCHART COMPLETE")
    return {
        "steps": steps,
        "image_path": "uploads/flowchart.png"
    }