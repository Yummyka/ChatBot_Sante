from huggingface_hub import InferenceClient
import os
import json
from datetime import datetime
import time

# Import de la clef d'API Hugging Face (via variable d'environnement) et du modèle
api_key = os.getenv("HF_API_KEY") 
modelID="meta-llama/Llama-3.2-3B-Instruct"


class Discussion ():
    """ 
    Cette classe gère le cycle de vie d'une conversation entre l'utilisateur et le chatbot.
    Elle assure la détection d'intention, l'import des prompts système, la gestion du contexte et l'enregistrement des échanges.
    """
    def __init__(self, modelID, api_key, window=5, max_token=500, temp=0.2):
        """
        Initialise la discussion.

        Args : 
            modelID (str): Identifiant du modèle d'IA sur HuggingFace.
            api_key (str) : Clef d'API pour l'inférence.
            window (int) : Longueur de la fenêtre glissante de mémoire.
            max_token (int) : Longueur maximale de la réponse générée par l'IA.
            temp (float) : Température du modèle (privilégier une température faible pour limiter les risques d'hallucination).
        """
        self.client = InferenceClient(api_key=api_key)
        self.modelID = modelID
        self.window = window
        self.max_token = max_token
        self.temp = temp
        self.hist = []
        self.intent = None
        self.prompt_sys = {} #Les prompts sont importés plus loin

    def save_log(self, filename="./logs/log_discussion"):
        """
        Cette fonction exporte l'intégralité de la discussion au format JSON.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename}_{timestamp}.json"
        
        if not os.path.exists("./logs"):
            os.makedirs("./logs")

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
        """
        Cette fonction importe les prompts systèmes depuis un fichier texte.
        Pour fonctionner, le fichier texte doit comporter des balises de type [NOM_DU_PROMPT]
        """
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

    
    def call_AI(self, context, max_tokens=None):
        """
        Cette fonction effectue un appel API.
        Permet de vérifier si le message a été tronqué ou non.

        Returns : 
            tuple : (Contenu de la réponse, Raison de fin de réponse)
        """
        max_tokens = max_tokens if max_tokens else self.max_token #Pour pouvoir allonger le message si besoin

        answer_gen = self.client.chat.completions.create(
                model=self.modelID,
                messages=context,
                max_tokens=max_tokens,
                temperature=self.temp)
        return answer_gen.choices[0].message.content, answer_gen.choices[0].finish_reason
    
    
    def process_input(self, user_input):
        """
        Cette fonction traite l'entrée de l'utilisateur et génère une réponse. 
        Elle permet également la détection de l'intention du message si elle est encore inconnue.
        """
        self.hist.append({"role":"user","content":user_input}) #Ajout de l'entrée de l'utilisateur à l'historique
        
        #Test de l'intention si elle n'a pas encore été détectée
        if self.intent is None : 
            context_detection = [{"role":"system","content":self.prompt_sys["INTENT"]}] + self.hist[-1:]
            intent,_ = self.call_AI(context_detection)
            intent = intent.upper()

            if "MEDICAL" in intent: self.intent = "MEDICAL"
            elif "ADMIN" in intent: self.intent = "ADMIN"
            else: self.intent = "AUTRE"

        #Réponse à la requete en fonction de l'intention
        if self.intent == "AUTRE":
            answer_fin= self.prompt_sys["AUTRE"]
            self.intent = None #Annule la détection d'intention afin de pouvoir relancer la discussion
        else :
            #Création de la fenêtre de contexte :
            context = [{"role":"system","content":self.prompt_sys[self.intent]}] + self.hist[-self.window:]
            
            #Appel de l'IA pour répondre :
            answer_fin, stop_reason = self.call_AI(context)
            i = 0
            while stop_reason !="stop" and i<3: #Vérifie que le prompt n'a pas été tronqué
                i += 1
                answer_fin, stop_reason = self.call_AI(context, max_tokens=(self.max_token+i*100)) #Augmente le nombre de token si besoin
                            
        self.hist.append({"role":"assistant","content":answer_fin})

        return answer_fin

def print_chat(chat, word_width=12):
    """
    Affiche la réponse de l'IA avec un décalage à droite pour plus de lisibilité.
    """
    print("> ChatBot : ")
    for paragraph in chat.split('\n'):
        paragraph = paragraph.split()
        margin = "                               "
        for i in range(0,len(paragraph),word_width):
            print(margin, *paragraph[i:i+word_width])
    print()


# Pipeline principale
if __name__ == "__main__":
    chat = Discussion(modelID=modelID,api_key=api_key)

    #Extraction des différents prompts depuis le fichier texte
    chat.load_syst_prompt("prompt_syst.txt")

    print_chat("Bonjour, je suis un assistant spécialisé dans les questions médicales. Quelle est votre requette ?.\nJe vous invite à être le plus précis possible afin que je puisse vous répondre correctement.\nPour terminer la discussion à tout moment tapez FIN.")

    t_start = time.time()
    while (time.time()-t_start) < 3600 : #Ferme automatiquement le chat au bout d'une heure
        user_input= input("> Vous : ")
        print()

        if user_input.upper() == "FIN":
            print("\n--- Fin de la discussion ---")
            break
        
        answer = chat.process_input(user_input=user_input)
        print_chat(answer)
    
    chat.save_log()

    