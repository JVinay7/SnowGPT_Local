from snowflake.snowpark import Session
from config import *
from langchain.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Pinecone
import pinecone
import streamlit as st
import snowflake.connector

conn = {
    "user"  : snowflake_user,
    "password": snowflake_password,
    "account": snowflake_account,
    "warehouse": snowflake_warehouse,
    "database": snowflake_database,
    "schema": snowflake_schema
}

connection = snowflake.connector.connect(**conn)

cur = connection.cursor()
cur.execute("SELECT DISTINCT METADATA$FILENAME AS File_name FROM @SNOWGPT_DB.STG.SNOWGPT_S3_STAGE")
results = cur.fetchall()

print("results : ",results)
# st.write("results : ",results)

cur.execute("SELECT File_name FROM SNOWGPT_DB.AUDIT.AUDIT_TB;")
audit_files = cur.fetchall()

print("audit files : ",audit_files)
# st.write("audit files : ",audit_files)

presigned_urls = []

for i in results:
    if i not in audit_files:
        i = i[0]
        cur.execute(f"INSERT INTO SNOWGPT_DB.AUDIT.AUDIT_TB (File_name, File_size, Move_to, Created_by) VALUES ('{i}', 11 ,'INTERNAL STAGE','AKSHAT')")
        cur.execute(f"SELECT DISTINCT GET_PRESIGNED_URL(@SNOWGPT_DB.STG.SNOWGPT_S3_STAGE, '{i}') FROM @SNOWGPT_DB.STG.SNOWGPT_S3_STAGE")
        urls = cur.fetchall()
        print(urls[0][0])
        presigned_urls.append(urls[0][0])

print(presigned_urls)
# st.write(presigned_urls)

# loader = UnstructuredURLLoader(urls=presigned_urls)
# documents = loader.load()
# print("Documents : ",len(documents))


# def split_docs(documents,chunk_size=500,chunk_overlap=20):
#   text_splitter= RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap)
#   docs=text_splitter.split_documents(documents)
#   return docs

# docs=split_docs(documents)
# # st.write("Vectors : ",len(docs))

# embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
# # st.write(embeddings)

# pinecone.init(
#     api_key=api_key,
#     environment=environment
# )

# index = Pinecone.from_documents(docs,embeddings,index_name=index_name)
















