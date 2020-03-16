#####################################<br>
############################ Abstract<br>
<br>
Le centrali elettriche virtuali (Virtual Power Plant) sono sistemi energetici che integrano diversi tipi di fonti rinnovabili e non, carichi e dispositivi di accumulo. Un tipico VPP è un grande impianto industriale con elevati carichi elettrici e termici (parzialmente shiftabili), generatori di energia rinnovabili e depositi elettrici e termici.

Il lavoro oggetto di questa tesi implementa un modello di ottimizzazione in due fasi per la generazione di flussi energetici.
L'ottimizzazione avviene in due fasi: la prima, offline, consiste in un approccio robusto per la modellazione dell'incertezza basata su scenari, che cerca di minimizzare il valore della funzione obiettivo lungo l'orizzonte temporale considerando diverse tipologie di funzioni obiettivo. La fase seguente, online, è costituita da un algoritmo greedy che utilizza i valori ottimizzati della domanda di carica ottenuti dalla fase offline e genera i valori dei flussi energetici. 
Tramite un'interfaccia appositamente realizzata è possibile personalizzare l'intero processo di ottimizzazione selezionando i componenti, lo step (offline, online), se e dove applicare l'incertezza, quale funzione obiettivo utilizzare. Tali scelte determinano risoluzioni diverse del modello elaborato in base alle quali il comportamento dei VPP si adatta. Il procedimento complessivo simula la fase decisionale dell’EMS, ovvero il centro decisionale nella gestione del VPP.

###################################### <br>
################# Struttura della Repo<br>
<br>
- Progetto: Sono contenute le directory del progetto in Spring complete e funzionanti
- Definitive: script in python per l'esecuzione degli step del modello e integrazione con l'interfaccia


#######################################<br>
########################## Requirements<br>
<br>
Per il corretto funzionamento del progetto serve installare un IDE (usato IntellJ), un application server (Wildfly 18.0.1 - Final), MysQL. 
Per la corretta esecuzione degli script serve installare Anaconda con Python, Pyomo e il solver Gurobi. 
