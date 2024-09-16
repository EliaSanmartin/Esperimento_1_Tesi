import json
from openai import OpenAI
import replicate
import google.generativeai as genai
#from transformers import pipeline
import os
import time
from langchain_ollama import OllamaLLM

cartella_api_key = "secrets.json"
#Classi per i vari modelli
class Chatbot_rep():
    def __init__(self):
        with open(cartella_api_key) as f:
            secrets = json.load(f)
            REPLICATE_API_TOKEN = secrets["rep_key"]
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
    def message(self, text:str):
        response = replicate.run(
            "mistralai/mixtral-8x7b-instruct-v0.1",

            input={"prompt": f"{text}"})
        risp = ''
        for el in response:
            risp = risp + el
        return risp

class Chatbot_gpt():
    def __init__(self):
        with open(cartella_api_key) as f:
            secrets = json.load(f)
            api_key = secrets["api_key"]
        self.client = OpenAI(api_key=api_key)

    def message(self, text:str):
        messages=[
                {
                    "role": "user",
                    "content": f"{text}",
                },
            ]
        response = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, temperature=0.9, top_p=1)

        return response.choices[0].message.content

class Chatbot_llama():
    def __init__(self):
        self.model = OllamaLLM(model="llama3")

    def message(self, text:str):

        response = self.model.invoke(input=text)
        return response

class Chatbot_gemini():
    def __init__(self):
        with open(cartella_api_key) as f:
            secrets = json.load(f)
            api_key = secrets["gem_key"]
        genai.configure(api_key=api_key)
        generation_config = {"temperature":0.9,
                             "top_p":1,
                             "top_k":1,
                             "max_output_tokens":2040,
                             }
        model = genai.GenerativeModel(model_name="gemini-1.0-pro",
                                      generation_config=generation_config)
        self.convo = model.start_generation(history=[])
    def message(self, text:str):
        self.convo.send_message(text)
        return self.convo.last.text

#Questa classe, dopo aver generato la domanda da fare al modello, lo stampa su terminale, e si aspetta la risposta
# tramite input, l'ho utilizzata per testare modelli senza api copiando e incollando domanda e risposta
class Chatbot_manuale():
    def message(self, text:str):
        print(f"\n\n{text}\n\n")
        return input()

def to_string(lista:list) -> str:
    stringa = ""
    for el in lista:
        stringa = f"{stringa}\n{str(el)}"
    return stringa


def file(nome_file:str):
    # Apri il file in modalità lettura
    with open(nome_file, "r", encoding='utf-8') as file:
        frasi = []
        # Leggi ogni riga del file
        for riga in file:
            # Stampa la riga
            frasi.append(riga.strip())  # Rimuovi eventuali spazi o caratteri di newline
    # Chiudi il file automaticamente alla fine del blocco "with"
    return frasi


if __name__ == "__main__":

    numero_caso = '2'#selezione del caso clinico
    classif = {"_MEDICO_":1, "_PAZIENTE_":2, "MEDICO":1, "PAZIENTE":2}#i possibili output del classificatore


    n_files = ["classificatore.txt", "medico.txt", "paziente.txt"]#nomi file da leggere
    files = []#dove verranno salvati il contenuto dei vari file

    #Apro già in precedenza i file da cui leggere le informazioni e li salvo in "files"
    for nome in n_files:
        frasi = file(f"istruzioni//{nome}")
        frase = ""
        for el in frasi:
            frase += f'\n{el}'
        files.append(frase)

    # dentro questa lista verranno salvati il testo con le invormazioni sul paziente per parlare col medico e col paziente
    caso_clinico = []
    frasi = file(f"casi_clinici//medico{numero_caso}.txt")
    frase = to_string(frasi)

    caso_clinico.append(frase)
    frasi = file(f"casi_clinici//paziente{numero_caso}.txt")
    frase = to_string(frasi)
    caso_clinico.append(frase)


#---------SCELTA CLASSE---------------
    ia = Chatbot_gpt()
#-------------------------------------
    print("Sistema operativo")
    frasi_p = []#qua verranno salvate le frasi col paziente
    frasi_m = []#qua verranno salvate le frasi col medico/infermiere

    #Ciclo while dal quale può uscire solo se si scrive stop a terminale
    while (1):


        domanda = input("Utente: ")#ottengo la domanda

        if domanda == "stop":
            break

        istruzione = files[0]  # classificatore
        istruzione += f"\nUtente: {domanda}\nIA:"


        tempo_impiegato = time.time()

        risposta = ia.message(istruzione)#classifico la domanda

        tempo_impiegato = time.time() - tempo_impiegato
        print(f"Il tempo trascorso per classificare è di: {tempo_impiegato} secondi")

        risposta = risposta.upper()
        print(f"Classificatore: {risposta}")  # stampo cosa il classificatore ha scelto

        istruzione = files[classif[risposta]]#capisco la risposta del classificatore

        # Ottieni il tempo corrente
        current_time = time.localtime()

        # Formatta il tempo in una stringa leggibile
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", current_time)
        istruzione = f"{istruzione}, Questa è la data di oggi {formatted_time}.   "

        if classif[risposta] == 1:#caso operatore sanitario
            #preparo la domanda per rispondere all'operatore sanitario
            istruzione += f"{caso_clinico[0]}\nContinua la seguente conversazione:\n"
            istruzione += f"{to_string(frasi_m)}\nOperatore sanitario: {domanda}\nIA:"

            risposta = ia.message(istruzione)#genero risposta

            #Aggiungo alla cronologia della conversazione con l'operatore
            frasi_m.append(f"\nOperatore sanitario: {domanda}")
            frasi_m.append(f"\nIA: {risposta}")
        else:#caso paziente
            # preparo la domanda per rispondere al paziente
            istruzione += f"{caso_clinico[1]}\nContinua la seguente conversazione:\n"
            istruzione += f"{to_string(frasi_p)}\nPaziente: {domanda}\nIA:"

            risposta = ia.message(istruzione)#genero risposta

            # Aggiungo alla cronologia della conversazione con il paziente
            frasi_p.append(f"\nPaziente: {domanda}")
            frasi_p.append(f"\nIA: {risposta}")

        #stampo la risposta ia
        print(f"IA: {risposta}")


    #----FINE LOOP WHILE-----

    print("-----\n")
    print("frasi paziente:")
    for el in frasi_p:
        print(el)
    print("-----\n")
    print("frasi medico")
    for el in frasi_m:
        print(el)
