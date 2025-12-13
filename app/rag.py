from typing import List
import os
import logging
from groq import Groq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
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

# Initialize Embeddings (Global variable to load model once)
# Using a small, fast model suitable for CPU
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = None

async def build_vector_store():
    """
    Fetch all users from DB and build/rebuild the vector store.
    In production, this would be an incremental update to a persistent vector DB.
    """
    global vector_store
    try:
        db = await get_database()
        cursor = db["users"].find()
        users = await cursor.to_list(length=1000) # Fetch more users
        
        documents = []
        for u in users:
            # Create a rich text representation for embedding
            page_content = f"User Name: {u.get('name')}\nEmail: {u.get('email')}\nRole: {u.get('role')}\nBio: {u.get('bio', 'N/A')}"
            
            # Metadata allows us to filter or reference source data if needed
            metadata = {
                "id": str(u.get("_id")),
                "role": u.get("role")
            }
            
            documents.append(Document(page_content=page_content, metadata=metadata))
            
        if documents:
            logger.info(f"Building vector store with {len(documents)} users...")
            vector_store = FAISS.from_documents(documents, embeddings)
            logger.info("Vector store built successfully.")
        else:
            logger.warning("No users found to build vector store.")
            vector_store = None
            
    except Exception as e:
        logger.error(f"Error building vector store: {e}")

async def retrieve_context(query: str) -> str:
    """
    Retrieve relevant users using semantic search.
    """
    global vector_store
    
    # Lazy initialization / Rebuild check (simple approach)
    # Ideally, we should update this on database changes or have a background job.
    if vector_store is None:
        await build_vector_store()
        
    if vector_store is None:
        return "No user data available."
        
    try:
        # Perform similarity search
        # k=5 means we retrieve the top 5 most relevant users
        docs = vector_store.similarity_search(query, k=5)
        
        context_str = "Found relevant Users:\n\n"
        for i, doc in enumerate(docs, 1):
            context_str += f"--- Result {i} ---\n{doc.page_content}\n\n"
            
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
