import socket
import threading
from enum import Enum
import time
import logging
import logging.config
from pydub import AudioSegment
from pydub.playback import play
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import board
import pwmio
import digitalio
import RPi.GPIO as IO


#################TO DO############################


# LIST CMD

# AV -- NO OPT -- AVANCER
# AR -- NO OPT -- RECULER
# TO_G -- NO OPT -- TOURNER A GAUCHE
# TO_D -- NO OPT -- TOURNER A DROITE
# STOP -- NO OPT -- ARRET
# BAT -- NO OPT -- REQUETE D ETAT BATTERIE #NOLOG
# VIT -- 2 DIGIT -- CHANGEMENT DE VITESSE #NOLOG
# SEC -- 1 DIGIT (0/1) -- ACTIVATION/DESACTIVATION DE LA SECURITE
# SON -- 1 DIGIT (optionnel) -- ENVOI D'UN VOCAL, OU LECTURE D'UN SON 
# CAM -- 1 DIGIT (0/1) -- ACTIVATION/DESACTIVATION DE LA CAM

# CONNECTION FTP DISPO
#  user :   "user", "12345"
#  adress : "127.0.0.1", 1026


# DEPENDENCES A PIP INSTALL 
# logging
# pydub
# pyftpdlib

class Etat_ro(Enum):
    AV = 1
    AR = 2
    TO_G = 3
    TO_D = 4
    STOP = 5

# initialisation des variables

mutex_data_rec = threading.Lock()
mutex_data_fichier = threading.Lock()

vocal_a_lire=0
son_a_lire=0
adresse = ''
data_share=''
flag_new_data=0
flag_new_vitesse=0
port = 6789
port_fichier = 6790
vitesse = 20
vitesse_2 = 20
securite = True
VALBAT =100
cam = 1
debug = 0


IO.setwarnings(False)
IO.setmode (IO.BCM)

IO.setup(13,IO.OUT)
IO.setup(19,IO.OUT)
IO.setup(18,IO.OUT)
IO.setup(12,IO.OUT)

pwm1a = IO.PWM(18, 60)
pwm1b = IO.PWM(19, 60)

pwm2a = IO.PWM(13, 60)
pwm2b = IO.PWM(12, 60)



en1 = digitalio.DigitalInOut(board.D27)
en1.direction = digitalio.Direction.OUTPUT

en2 = digitalio.DigitalInOut(board.D22)
en2.direction = digitalio.Direction.OUTPUT

em1 = digitalio.DigitalInOut(board.D26)
em1.direction = digitalio.Direction.OUTPUT
# configuration du loggers

#logging.config.dictConfig({
#    'version': 1,
#    'disable_existing_loggers': True,
#})

logging.basicConfig(filename="logkoios",
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
logging.getLogger("pyftpdlib").setLevel(logging.WARNING)
logger = logging.getLogger('__name__')

def main():


    logging.info("                         #")
    logging.info("                       #####")
    logging.info("                    ##########")
    logging.info("               ####################")
    logging.info("     ########################################")
    logging.info("###################Démarrage du programme###################")
    logging.info("     ########################################")
    logging.info("               ####################")
    logging.info("                    ##########")
    logging.info("                       #####")
    logging.info("                         ##")


    logging.info("    DEBUG MODE :"+str(debug))


    global flag_new_data
    global data_share
    global mutex_data_rec
    global mutex_data_fichier
    global flag_new_vitesse
    global securite
    global VALBAT
    global vocal_a_lire
    global son_a_lire

    VALBAT = 99  #TODO assigner avec la pin pour avoir la valeur + rapport
    vitesse = 20
    etat = Etat_ro.STOP
    etat_next = Etat_ro.STOP
    data_local = ""

    #demarrage des PWM

    #Mise a 0 des enable

    #demarrage des serveurs
    threading.Thread(target=thread_server,args=(1,)).start()
    threading.Thread(target=thread_server_fichier,args=(1,)).start()
    threading.Thread(target=thread_stream_cam,args=(1,)).start()


    while(True):

        if(vocal_a_lire==1):
            threading.Thread(target=thread_lecture_audio,args=(2,0)).start()
            mutex_data_fichier.acquire()
            vocal_a_lire=0
            mutex_data_fichier.release()

        if(son_a_lire > 0):
            threading.Thread(target=thread_lecture_audio,args=(2,son_a_lire)).start()    
            mutex_data_fichier.acquire()
            son_a_lire=0
            mutex_data_fichier.release()

        if(flag_new_data == 1):
            mutex_data_rec.acquire()
            data_local = data_share
            mutex_data_rec.release()

        if(flag_new_data == 1):
            if(data_local == "AV"):
                etat_next = Etat_ro.AV
            elif(data_local == "AR"):
                etat_next = Etat_ro.AR
            elif(data_local == "TO_G"):
                etat_next = Etat_ro.TO_G
            elif(data_local == "TO_D"):
                    etat_next = Etat_ro.TO_D
            elif(data_local == "STOP"):
                etat_next = Etat_ro.STOP
            if(securite == False or VALBAT > 20):
                if(etat_next != etat):
                    if(etat_next == Etat_ro.AV):
                        avance()
                    elif(etat_next == Etat_ro.AR):
                        arriere()
                    elif(etat_next == Etat_ro.TO_G):
                        tourne_gauche()
                    elif(etat_next == Etat_ro.TO_D):
                        tourne_droite()
                    elif(etat_next == Etat_ro.STOP):
                        stop()

                etat = etat_next

                mutex_data_rec.acquire()
                flag_new_data=0
                mutex_data_rec.release()
            else:
                if(etat != Etat_ro.STOP):
                    logging.warning("Plus de batterie, mise en arret")
                    stop()
                    etat = Etat_ro.STOP

        if(flag_new_vitesse == 1 and (securite == False or VALBAT > 20)):
            if(etat == Etat_ro.AV):
                avance()
            if(etat == Etat_ro.AR):
                arriere()
            elif(etat == Etat_ro.TO_G):
                tourne_gauche()
            elif(etat == Etat_ro.TO_D):
                tourne_droite()
            mutex_data_rec.acquire()
            flag_new_vitesse = 0
            mutex_data_rec.release()
            

def thread_server(name):
    global flag_new_data
    global flag_new_vitesse
    global data_share
    global mutex_data_rec
    global mutex_data_fichier
    global vitesse
    global VALBAT
    global securite
    global vocal_a_lire
    global son_a_lire
    global cam
    global debug

    logging.info("Démarrage serveur TCP")
    serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur.bind((adresse,port))
    logging.info("Serveur TCP pret")

    start_time = time.time()
    while(True):        
        serveur.listen(1)
        client, adresseClient = serveur.accept()
        logging.info("Connexion de "+ str(adresseClient))
        connected = True
        message_return=""
        while(connected):
            donnees = client.recv(1024)
            if donnees:
                donnees = donnees[:(len(donnees)-1)].decode("utf-8")
                #print("donnees:"+str(donnees))
                start_time = time.time()

                mutex_data_rec.acquire()
                data_share = donnees
                if(donnees != "BAT" and donnees[:3] != "VIT" and donnees[:3] != "SEC" and donnees[:3] != "SON" and donnees[:3] != "CAM" and donnees[:5] != "DEBUG"):
                        flag_new_data = 1
                        logging.info("Reception de :"+ str(donnees))
                if(donnees == "BAT"):
                    message_return = "VALBAT"+str(VALBAT)
                elif(donnees[:3] == "VIT" and ( len(donnees) == 5 or len(donnees) == 7)): #ne pas oublier de rajouter le 0 quand <10 du cote client
                    if(debug == 1):
                        threading.Thread(target=thread_lecture_audio,args=(2,5)).start()
                        vitesse = int(donnees[3:5])
                        vitesse_2 = int(donnees[5:7])
                        logging.info("Changement vitesse: Mot1:"+str(vitesse)+" Mot2:"+str(vitesse_2))
                    else:
                        vitesse = int(donnees[3:5])
                    logging.info("Changement vitesse:"+str(vitesse))
                    flag_new_vitesse = 1
                    
                elif(donnees[:3] == "SEC" and len(donnees) == 4):
                    if(donnees[3:4] == "1"):
                        securite = True
                        logging.info("Activation de la sécurité")
                    else:
                        securite = False
                        logging.info("Désactivation de la sécurité")
                    if(debug == 1):
                        threading.Thread(target=thread_lecture_audio,args=(2,5)).start()
                elif(donnees[:3] == "CAM" and len(donnees) == 4):
                    if(donnees[3:4] == "1"):
                        cam = 1
                        logging.info("Activation de la caméra")
                    else:
                        cam = 0
                        logging.info("Désactivation de la caméra")
                    if(debug == 1):
                        threading.Thread(target=thread_lecture_audio,args=(2,5)).start()
                elif(donnees[:3] == 'SON'):
                    if(len(donnees) == 4):
                        mutex_data_fichier.acquire()
                        son_a_lire = donnees[3:4]
                        mutex_data_fichier.release()
                    else:
                        mutex_data_fichier.acquire()
                        vocal_a_lire = 1
                        mutex_data_fichier.release()
                    if(debug == 1):
                        threading.Thread(target=thread_lecture_audio,args=(2,5)).start()
                elif(donnees[:5] == "DEBUG" and len(donnees) == 6):
                    if(int(donnees[5:6]) == 1 ):
                        logging.info("Activation du DEBUG")
                    else:
                        logging.info("Desactivation du DEBUG")
                    debug = int(donnees[5:6])
                if not(donnees[:3] == "BAT"):
                    message_return = "OK"
                mutex_data_rec.release()

                try:
                      client.send(message_return)
                except:
                    logging.error("Erreur lors de l'envoi de réponse")
            end_time = time.time()
            if( (end_time - start_time) > 1 ):
                try:
                      client.send("OUT")
                except:
                    logging.error("Erreur lors de l'envoi de réponse")
                connected=False
        client.close()
        logging.warning("Client TCP deconnecté")
    serveur.close()
    logging.warning("Serveur TCP deconnecté")


def thread_server_fichier(name):
    authorizer = DummyAuthorizer()
    authorizer.add_user("user", "12345", "/home/pi/sound/", perm="elradfmw")

    handler = FTPHandler
    handler.authorizer = authorizer

    server = FTPServer(("127.0.0.1", 1026), handler)
    logging.info("Serveur FTP pret")
    server.serve_forever()

def thread_lecture_audio(name,vocal):
    #song = AudioSegment.from_wav("/home/user/sound/fichier.wav")
    # possible from_mp3 / from_ogg / from_flv / from_file(mp4,wma,aac)
    # pour 3gp => sound = AudioSegment.from_file(filename, "3gp") 
    if(vocal == 0):
        name="fichier.wav"
    else:
        name=str(vocal)+".wav"
    logging.info('lecture de '+str(name))
    print('lecture de '+str(name))
    #play(song)
def thread_stream_cam(name):

    global cam

    while(True):
        while(cam == 1):
            pass
        #arret cam
    


def avance():

    global en1
    global en2
    global pwm1a
    global pwm1b
    global pwm2a
    global pwm2b
    global vitesse

    logging.info("Fonction avancer")
    print("JAVANCE:"+str(vitesse))

    en1.value = True
    en2.value = True

    pwm1a.start(vitesse)
    pwm1b.start(0)

    pwm2a.start(vitesse*0.85)
    pwm2b.start(0)

    #mise a 1 des deux enable + sens
def arriere():

    global en1
    global en2
    global pwm1a
    global pwm1b
    global pwm2a
    global pwm2b
    global vitesse

    logging.info("Fonction reculer:"+str(vitesse))

    en1.value = True
    en2.value = True

    pwm1a.start(0)
    pwm1b.start(vitesse*0.85)

    pwm2a.start(0)
    pwm2b.start(vitesse)

    #mise a 1 des deux enable + sens
    print("JERECULE")

def tourne_gauche():

    global en1
    global en2
    global pwm1a
    global pwm1b
    global pwm2a
    global pwm2b
    global vitesse

    logging.info("Fonction tourner a gauche")
    print("JE TOURNE A GAUCHE:"+str(vitesse))
    en1.value = True
    en2.value = False

    pwm1a.start(vitesse)
    pwm1b.start(0)

    pwm2a.start(0)
    pwm2b.start(0)
    # mise a 1 de un enable
def tourne_droite():

    global en1
    global en2
    global pwm1a
    global pwm1b
    global pwm2a
    global pwm2b
    global vitesse

    logging.info("Fonction tourner a droite")
    print("JE TOURNE A DROITE:"+str(vitesse))
    # mise a 1 de un enable
    en1.value = False
    en2.value = True

    pwm1a.start(0)
    pwm1b.start(0)

    pwm2a.start(vitesse)
    pwm2b.start(0)
def stop():

    global en1
    global en2
    global pwm1a
    global pwm1b
    global pwm2a
    global pwm2b
    global vitesse

    logging.info("Fonction tourner arret")
    print("JE STOP")
    en1.value = False
    en2.value = False

    pwm1a.start(0)
    pwm1b.start(0)

    pwm2a.start(0)
    pwm2b.start(0)
    # mise a 0 des deux enable
if __name__ == "__main__":
    main()