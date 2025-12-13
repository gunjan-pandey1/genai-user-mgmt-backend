from typing import List
import os
import logging
import asyncio
from groq import Groq
import chromadb
from chromadb.config import Settings
from .database import get_database

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure LLM
# Expects GROQ_API_KEY in environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not found in environment variables")
client = Groq(api_key=GROQ_API_KEY)

# Model Name
MODEL_NAME = "llama-3.1-8b-instant"

# Initialize ChromaDB client
# ChromaDB uses default embeddings (all-MiniLM-L6-v2) built-in
# Supports both remote (Railway) and local (in-memory) modes
CHROMA_HOST = os.getenv("CHROMA_HOST_ADDR")
CHROMA_PORT = os.getenv("CHROMA_HOST_PORT", "8000")

# Initialize client as None, will be created on first use
chroma_client = None

def get_chroma_client():
    """Get or create ChromaDB client with error handling."""
    global chroma_client
    
    if chroma_client is not None:
        return chroma_client
    
    try:
        if CHROMA_HOST:
            # Remote ChromaDB connection (Railway deployment)
            logger.info(f"Connecting to remote ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
            chroma_client = chromadb.HttpClient(
                host=CHROMA_HOST,
                port=int(CHROMA_PORT),
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
        else:
            # In-memory ChromaDB (local development)
            logger.info("Using in-memory ChromaDB for local development")
            chroma_client = chromadb.Client(Settings(
                anonymized_telemetry=False,
                allow_reset=True
            ))
        
        return chroma_client
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        logger.warning("ChromaDB unavailable, RAG functionality will be limited")
        return None

COLLECTION_NAME = "users"
collection = None
vector_building = False

async def build_vector_store():
    global collection
    
    # Get ChromaDB client with error handling
    client = get_chroma_client()
    if client is None:
        logger.error("ChromaDB client unavailable, cannot build vector store")
        collection = None
        return
    
    try:
        db = await get_database()
        cursor = db["users"].find()
        users = await cursor.to_list(length=1000) # Fetch more users
        
        if not users:
            logger.warning("No users found to build vector store.")
            collection = None
            return
        
        try:
            client.delete_collection(name=COLLECTION_NAME)
        except:
            pass
        
        collection = client.create_collection(name=COLLECTION_NAME)
        
        documents = []
        metadatas = []
        ids = []
        
        for u in users:
            # Create a rich text representation for embedding
            page_content = f"User Name: {u.get('name')}\nEmail: {u.get('email')}\nRole: {u.get('role')}\nBio: {u.get('bio', 'N/A')}"
            
            # Metadata allows us to filter or reference source data if needed
            metadata = {
                "id": str(u.get("_id")),
                "role": u.get("role", "user"),
                "name": u.get("name", ""),
                "email": u.get("email", "")
            }
            
            documents.append(page_content)
            metadatas.append(metadata)
            ids.append(str(u.get("_id")))
        
        logger.info(f"Building vector store with {len(documents)} users...")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info("Vector store built successfully.")
            
    except Exception as e:
        logger.error(f"Error building vector store: {e}")

async def _build_vector_store_background():
    global vector_building
    if vector_building:
        return
    vector_building = True
    try:
        await build_vector_store()
    finally:
        vector_building = False


async def retrieve_context(query: str) -> str:
    global collection, vector_building

    if collection is None and not vector_building:
        asyncio.create_task(_build_vector_store_background())

    try:
        if collection is not None:
            results = collection.query(
                query_texts=[query],
                n_results=5
            )

            if results and results.get("documents") and results["documents"][0]:
                context_str = "Found relevant Users:\n\n"
                for i, doc in enumerate(results["documents"][0], 1):
                    context_str += f"--- Result {i} ---\n{doc}\n\n"
                return context_str

        db = await get_database()
        cursor = db["users"].find()
        users = await cursor.to_list(length=1000)

        if not users:
            return "No user data available."

        context_str = "Users:\n\n"
        for u in users:
            context_str += (
                f"User Name: {u.get('name')}\n"
                f"Email: {u.get('email')}\n"
                f"Role: {u.get('role')}\n"
                f"Bio: {u.get('bio', 'N/A')}\n\n"
            )

        return context_str
    except Exception as e:
        logger.error(f"Error searching vector store: {e}")
        return "Error searching user data."

async def ask_question(query: str):
    try:
        context = await retrieve_context(query)
        
        template = f"""
        You are an intelligent AI assistant for a User Management System.
        Your goal is to answer questions based strictly on the provided context.
        
        Context (Relevant Users):
        {context}

        Question: {query}

        Instructions:
        1. Analyze the context to find the answer.
        2. If the answer is found, provide a clear and concise response.
        3. If the answer is NOT in the context, explicitly state that you cannot find the information in the database. Do not hallucinate.
        4. When listing users, include their roles.

        Answer:
        """
        
        # Call Groq API
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": template
                }
            ],
            temperature=0.5, # Lower temperature for more factual answers
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None
        )
        
        return completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Error connecting to LLM or processing request: {e}")
        return f"I encountered an error while processing your request. Error details: {str(e)}"
