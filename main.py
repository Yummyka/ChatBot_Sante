from huggingface_hub import InferenceClient
import os
import json
from datetime import datetime
import time

# Import de la clef d'API (via variable d'environnement) et du modèle
api_key = os.getenv("HF_API_KEY")
modelID="meta-llama/Llama-3.2-3B-Instruct"

#Classe permettant la discussion suivie sur plusieurs messages avec l'utilisateur 
class Discussion ():
    def __init__(self, modelID, api_key, window=5, max_token=500, temp=0.2):
        self.client = InferenceClient(api_key=api_key)
        self.modelID = modelID
        self.window = window #longueur de la fenêtre glissante de mémoire
        self.max_token = max_token #longueur de la réponse de l'IA
        self.temp = temp
        self.hist = []
        self.intent = None
        
        #Définition des prompts système en fonction du type de discussion
        self.prompt_sys = {}

    def save_log(self, filename="./logs/log_discussion"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename}_{timestamp}.json"
        
        data_to_save = {
            "metadata": {
                "intent": self.intent,
                "timestamp": timestamp
            },
            "history": self.hist
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        print(f"Historique sauvegardé avec succès dans : {filename}")
    
    def load_syst_prompt(self, filename):
        prompts = {}
        current_key = None
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    current_key = line[1:-1]
                    prompts[current_key] = ""
                elif current_key and line:
                    prompts[current_key] += line + " "
        self.prompt_sys=prompts

    
    def call_AI(self, context):
        answer_gen = self.client.chat.completions.create(
                model=self.modelID,
                messages=context,
                max_tokens=self.max_token,
                temperature=self.temp)
        return answer_gen.choices[0].message.content
    
    def process_input(self, user_input):
        self.hist.append({"role":"user","content":user_input}) #Ajout de l'entrée de l'utilisateur à l'historique
        
        #Test de l'intention si elle n'a pas encore été détectée
        if self.intent is None : 
            context_detection = [{"role":"system","content":self.prompt_sys["INTENT"]}] + self.hist[-1:]
            intent = self.call_AI(context_detection).upper()

            if "MEDICAL" in intent: self.intent = "MEDICAL"
            elif "ADMIN" in intent: self.intent = "ADMIN"
            else: self.intent = "AUTRE"

        #Réponse à la requete en fonction de l'intention
        if self.intent == "AUTRE":
            answer_fin= self.prompt_sys["AUTRE"]
            self.intent = None
        else :
            #Créer la fenêtre de contexte :
            context = [{"role":"system","content":self.prompt_sys[self.intent]}] + self.hist[-self.window:]
            
            #Call l'IA pour répondre :
            answer_fin = self.call_AI(context)
            
        self.hist.append({"role":"assistant","content":answer_fin})

        return answer_fin

def print_chat(chat, word_width=12):
    print("ChatBot : ")
    for paragraph in chat.split('\n'):
        paragraph = paragraph.split()
        margin = "                               "
        for i in range(0,len(paragraph),word_width):
            print(margin, *paragraph[i:i+word_width])
    print()

if __name__ == "__main__":
    chat = Discussion(modelID=modelID,api_key=api_key)

    #Extraction des différents prompts depuis le fichier texte
    chat.load_syst_prompt("prompt_syst.txt")

    print_chat("Bonjour, je suis un assistant spécialisé dans les questions médicales. Quelle est votre requette ?.\nJe vous invite à être le plus précis possible afin que je puisse vous répondre correctement.\nPour terminer la discussion à tout moment tapez FIN.")

    t_start = time.time()
    while (time.time()-t_start) < 3600 : #Ferme automatiquement le chat au bout d'une heure
        user_input= input("Vous : ")
        print()

        if user_input.upper() == "FIN":
            print("\n--- Fin de la simulation ---")
            break
        
        answer = chat.process_input(user_input=user_input)
        print_chat(answer)
    
    chat.save_log()

    