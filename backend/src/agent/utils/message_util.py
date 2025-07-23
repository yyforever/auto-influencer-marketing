from typing import List
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage



def get_user_query(messages: List[AnyMessage]) -> str:
    """
    Get the user query from the messages.
    """
    # check if request has a history and combine the messages into a single string
    if len(messages) == 1:
        user_query = messages[-1].content
    else:
        user_query = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                user_query += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                user_query += f"Assistant: {message.content}\n"
    return user_query