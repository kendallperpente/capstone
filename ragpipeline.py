import os  
os.environ['GOOGLE_API_KEY'] = "Your_Gemini_API_Key" 
os.environ['CHROMA_GOOGLE_GENAI_API_KEY']="Your_Gemini_API_Key" 
os.environ["OPENAI_API_KEY"] = "Your_OpenAI_API_key" 
os.environ['CHROMA_OPENAI_API_KEY']="Your_OpenAI_API_key" 

#Preprocessing the data
from langchain.text_splitter import RecursiveCharacterTextSplitter 
 
# Read the data from the text file 
text = open("bug_republic.txt","r").read() 
 
# Create a text splitter 
splitter = RecursiveCharacterTextSplitter( 
    chunk_size=500, 
    chunk_overlap=50, 
    separators=["\n\n", "\n", "."] 
) 
 
# Convert the input text into chunks 
chunks = splitter.split_text(text) 

#Import data into a vector database
import chromadb 
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction 
 
# Initialize Chroma Client 
chroma_client = chromadb.PersistentClient(path="/home/aditya1117/codes/codecademy_resources/chromadb") 
 
# Initialize an embedding function 
embedding_fn  = GoogleGenerativeAiEmbeddingFunction(model_name="models/gemini-embedding-001") 
 
# Use the following code to initialize an embedding function using OpenAI models 
# from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction 
# embedding_fn  = OpenAIEmbeddingFunction(model_name="text-embedding-3-small") 
 
# Create a ChromaDB collection 
collection = chroma_client.create_collection(name = "bug_republic", 
                                             metadata={ 
                                                 "description": "Collection for storing information about Bug Republic."}, 
                                            embedding_function = embedding_fn) 
 
# Create document IDs 
num_chunks=len(chunks) 
ids=["doc_"+str(i) for i in range(num_chunks)] 
 
# Add documents to the collection 
collection.add( 
    ids=ids, 
    documents=chunks 
) 

#Build a retriever
import chromadb 
from langchain_chroma import Chroma 
from langchain_google_genai import GoogleGenerativeAIEmbeddings 
 
# Create a Chroma Client 
chroma_client = chromadb.PersistentClient(path="/home/aditya1117/codes/codecademy_resources/chromadb") 
 
# Initialize an embedding function 
embedding_fn = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001") 
 
# Use the following code to initialize the embedding function if you are using OpenAI models 
# from langchain_openai import OpenAIEmbeddings 
# embedding_fn = OpenAIEmbeddings(model="text-embedding-3-small") 
 
# Create a vector store 
vectorstore = Chroma( 
    client = chroma_client, 
    collection_name = "bug_republic", 
    embedding_function = embedding_fn 
) 
retriever = vectorstore.as_retriever(search_kwargs={"k": 4}) 

#Create a document chain
from langchain.prompts import ChatPromptTemplate 
from langchain.chains.combine_documents import create_stuff_documents_chain 
from langchain.chains import create_retrieval_chain 
from langchain_google_genai import ChatGoogleGenerativeAI  
 
# Create an LLM object 
llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash") 
 
# Use the following code if you are using OpenAI models 
# from langchain_openai import ChatOpenAI 
# llm = ChatOpenAI(model="gpt-4o-mini") 
 
 
# Define a prompt template 
prompt_template = ChatPromptTemplate.from_template(""" 
Answer the question based only on the following context: 
 
{context} 
 
Question: {input} 
""") 
 
# Create document combination chain using LLM and prompt template 
document_chain = create_stuff_documents_chain(llm, prompt_template) 
 
# Create RAG chain using retriever and document chain 
rag_chain = create_retrieval_chain(retriever, document_chain) 

#Generate an answer
query = "What is the national currency of Bug Republic?" 
response = rag_chain.invoke({"input": query}) 
query_answer = response.get("answer") 
 
print("The query is:") 
print(query) 
print("The response is:") 
print(query_answer) 

