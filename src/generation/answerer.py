
class Answerer:
    def __init__(self, retriever: Retriever, model_name:str):
        self.retriever = retriever
        self.llm = model_name

