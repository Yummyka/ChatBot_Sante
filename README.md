# Prototype de ChatBot Médical 
Ce projet est un prototype d'assistant virtuel pour des questions médicales. Il utilise un LLM pour répondre aux besoins de l'utilisateur et lui fournir des informations sûres et adaptées.

## Fonctionnement global :
- Détection de l'intention de l'utilisateur (médical, administratif ou autre) afin de répondre de façon adaptée avec des prompts système propres. (voir tableau ci-dessous).
- Détection d'urgence vitale et redirection immédiate vers les services de secours.
- Gestion de la mémoire contextuelle via une fenêtre glissante.
- Enregistrement automatique de l'historique en format JSON afin de pouvoir auditer les discussions.

|Catégorie|Description|Contenu du prompt|
|:-:|:-:|:-:|
|INTENT|Permet la détection de l'intention de l'utilisateur|Description de chaque intention, ne renvoie que la catégorie de l'intention.|
|MEDICAL|Contient toutes les questions relative à des symptomes, des renseignements sur des pathologies ou des inquiétudes.|Classe les demandes en 3 niveaux (urgence, besoin médical, information générale) afin d'adapter la réponse. Interdiction de poser un diagnostique, détection de cas d'urgence vitale necessitant l'appel des secours, proposition de téléconsultation si pertinent.|
|ADMIN|Contient toutes les questions relatives au fonctionnement de Tessan ou du monde médical.|Redirection vers la FAQ de Tessan pour plus d'information.|
|AUTRE|Contient toute autre question ne relevant pas de la compétence du chatbot|Contient une phrase automatique envoyée (pas d'appel à l'IA)|

Nb : Sources symptomes d'urgence : SFMU.org et Ameli.fr

## Pipeline du projet : 
La pipeline est assurée par la classe `Discussion` qui contient des méthodes pour chaque étape.
1. Reception du message utilisateur et enregistrement dans l'historique.
2. Classification de l'intention via un premier appel au LLM. Cette étape permet de charger les consignes de sécurité spécifiques au domaine dès le début.
3. Gestion de la mémoire via une fenêtre glissante qui extrait les N derniers messages afin d'assurer un suivi cohérent de la discussion.
4. Exécution du LLM avec les instructions spécifiques au contexte. Gestion des urgences. Gestion des troncatures accidentelles de texte pour assurer des réponses complètes.
5. Exportation de la session en format JSON afin de permettre une analyse à posteriori.


## Installation du projet :
Pour que le projet fonctionne sur votre ordinateur veuillez suivre les étapes suivantes : 
#### Intallation des bibliothèques 
Ce projet utilise la bibliothèque huggingface_hub.
```bash
pip install huggingface_hub
```
#### Configuration
Ce projet utilise une clef d'API Hugging Face enregistrée en variable d'environnement. Vous pouvez en avoir une gratuitement en vous connectant sur le site de Hugging Face. Il suffit ensuite de l'enregistrer.
```bash
# Sur Linux/Mac
export HF_API_KEY="votre_clef"

# Sur Windows (PowerShell)
$env:HF_API_KEY="votre_clef"
```
#### Fichiers nécessaires
- `main.py` : Le script principal à executer.
- `prompt_syst.txt` : Le fichier contenant les prompts système.


## Structure du projet : 
```bash
.
├── 📄 main.py    # Fichier principal à executer pour lancer la discussion
├── ⚙️ prompt_syst.txt    # Fichier des prompts système
├── 📂 logs/    # Dossier contenant l'historique des discussion
│   └── 📜 discussion_20260302_1422.json    # Fichier JSON horodaté d'une discussion
├── 📘 README.md    # Documentation technique et guide d'installation
└── 📋 test.ipynb    # Notebook de tests
```

## Exemple de discussion : 
Vous trouverez des exemples de discussion dans les fichiers suivants : 
- [Cas d'urgence](./logs/?)
- [Symptomes classiques](./logs/??)
- [Question administrative](./logs/???)
- [Question hors-sujet](./logs/????)