from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.chat_models import ChatOpenAI
import streamlit as st
from streamlit_chat import message
from utils import *
from config import *
import snowflake.connector
import openai
from streamlit_modal import Modal
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder
)

# Define Snowflake connection parameters
conn = {
    "user"  : snowflake_user,
    "password": snowflake_password,
    "account": snowflake_account,
    "warehouse": snowflake_warehouse,
    "database": snowflake_database,
    "schema": snowflake_schema
}
# Create a Snowflake connection
connection = snowflake.connector.connect(**conn)

st.set_page_config(layout="wide")

st.markdown(
    """
    <div style="display: flex; justify-content: center; margin-top: -86px;">
    <img src="https://stanu001.blob.core.windows.net/img/SnowGPT.png" width="700" />
    </div>
    """,
    unsafe_allow_html=True
)
    
with st.sidebar:
    modal = Modal(key="Demo Key",title=" ")
    open_modal = st.button(label='How to use')
    
content = '<p style="color: Black;">Unlock the Power of Snowflake: Your Personal Snowflake Documentation Chatbot. Say hello to your go-to resource for seamless access to Snowflake platform knowledge and instant answers to all your queries.</p>'
st.write(content, unsafe_allow_html=True)


text_color = "#006A53"

if open_modal:
    st.markdown(f"""
                <div  style="position: fixed; top:300px; right:30px; width: 250px; height: 25%; background-color: #f5f5f0; box-shadow: -5px 0 5px rgba(0, 0, 0, 0.2); color: {text_color};">
                <p style="font-size: 15px;">How to Use: Using our chatbot is effortless – simply type in your Snowflake-related questions, and it will provide you with precise and up-to-date information from the vast Snowflake documentation.</p> """,unsafe_allow_html=True)
    with st.sidebar:
        st.button("close-info")
    st.markdown("""</div>""",unsafe_allow_html=True)

if 'responses' not in st.session_state:
    st.session_state['responses'] = ["How can I help you"]

if 'requests' not in st.session_state:
    st.session_state['requests'] = []
    
# Iterate through query history and insert into history_table  
def add_query_history(query):
    print(query)
    cursor = connection.cursor()
    insert_query = f"INSERT INTO history_table (history) VALUES ('{query}');"
    cursor.execute(insert_query)
    cursor.close()  

#Function to fetch query history from the history_table
def fetch_query_history():
    cursor = connection.cursor()
    query = "SELECT history FROM history_table"
    cursor.execute(query)
    history = [row[0] for row in cursor]
    cursor.close()
    return history
    
def query_refiner(conversation, query):
    response = openai.Completion.create(
    model="text-davinci-003",
    prompt=f"Given the following user query and conversation log, formulate a question that would be the most relevant to provide the user with an answer from a knowledge base.\n\nCONVERSATION LOG: \n{conversation}\n\nQuery: {query}\n\nRefined Query:",
    temperature=0.7,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    return response['choices'][0]['text'] 

# Function to check if the API key is valid
def is_valid_api_key(openai_api_key):
    return openai_api_key and openai_api_key.startswith('sk-') and len(openai_api_key) == 51

openai_api_key_container = st.sidebar.empty()                               # Create an empty container to conditionally display the API Key input field
openai_api_key = openai_api_key_container.text_input('OpenAI API Key')# Get the OpenAI API key from the user

if not openai_api_key:
    with st.sidebar:
        st.warning('Please enter your OpenAI API key!', icon='⚠️')
        
elif is_valid_api_key(openai_api_key):
    with st.sidebar:
            st.success('API Key is valid! You can proceed.', icon='✅')
            
    openai_api_key_container.empty() # Hide the openai_api_key input field
    openai.api_key = openai_api_key
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key)

    if 'buffer_memory' not in st.session_state:
                st.session_state.buffer_memory=ConversationBufferWindowMemory(k=3,return_messages=True)

    system_msg_template = SystemMessagePromptTemplate.from_template(template="""Answer the question as truthfully as possible using the provided context, 
    and if the answer is not contained within the text below, say 'I don't know'""")

    human_msg_template = HumanMessagePromptTemplate.from_template(template="{input}")
    prompt_template = ChatPromptTemplate.from_messages([system_msg_template, MessagesPlaceholder(variable_name="history"), human_msg_template])
    conversation = ConversationChain(memory=st.session_state.buffer_memory, prompt=prompt_template, llm=llm, verbose=True)

    # container for chat history
    response_container = st.container()
    # container for text box
    textcontainer = st.container()

    with textcontainer:
        query = st.chat_input("Ask me anything in snowflake: ", key="input")
        if query:
            with st.spinner("typing..."):
                conversation_string = get_conversation_string()
                # st.code(conversation_string)
                refined_query = query_refiner(conversation_string, query)
                # st.subheader("Refined Query:")
                # st.write(refined_query)
                context = find_match(refined_query)
                # print(context)  
                response = conversation.predict(input=f"Context:\n {context} \n\n Query:\n{query}")
            st.session_state.requests.append(query)
            st.session_state.responses.append(response)
            add_query_history(query)
         
    with response_container:
            if st.session_state['responses']:
                for i in range(len(st.session_state['responses'])):
                    res = st.chat_message("assistant")
                    res.write(st.session_state['responses'][i],key=str(i))
                    # message(st.session_state['responses'][i],key=str(i))
                    if i < len(st.session_state['requests']):
                        req = st.chat_message("user")
                        req.write(st.session_state['requests'][i],is_user=True,key=str(i)+ '_user')
                        # message(st.session_state["requests"][i], is_user=True,key=str(i)+ '_user')
                    
    with st.sidebar.expander("Query History"):
        history_data = fetch_query_history()
        if history_data:
            for i, request in enumerate(history_data):
                st.write(f"{i + 1}. {request}")
        else:
            st.write("No query history available.")
            
else:
    with st.sidebar:
        st.warning('Please enter a valid open API key!', icon='⚠')

connection.close()

          