import urllib2
import json
import threading

class MyClass(GeneratedClass):

    def __init__(self):
        GeneratedClass.__init__(self)

        self.base_url = "http://10.109.3.143:5000"

        self.grupo_atual = None
        self.ouvindo_ativo = False
        self.processando = False

    def onInput_onStart(self):
        tablet = self.session().service("ALTabletService")
        tablet.enableWifi()
        tablet.showWebview(self.base_url + "/")

        self.loop()

    # ------------------------
    # LOOP PRINCIPAL
    # ------------------------

    def loop(self):
        try:
            data = json.loads(urllib2.urlopen(self.base_url + "/estado_sistema").read())

            modo = data.get("modo")
            grupo = data.get("grupo_atual")

            # 🔥 chama next automaticamente
            if modo == "ouvindo" and not self.processando:
                try:
                    urllib2.urlopen(self.base_url + "/next")
                except:
                    pass

            # ------------------------
            # NOVO GRUPO
            # ------------------------
            if modo == "indo" and grupo is not None and not self.processando:
                self.processando = True
                self.grupo_atual = grupo
                self.ir_para_grupo(grupo)

            # ------------------------
            # ESCUTA
            # ------------------------
            if modo == "ouvindo" and not self.ouvindo_ativo:
                self.iniciar_reconhecimento()

            if modo != "ouvindo" and self.ouvindo_ativo:
                self.parar_reconhecimento()

        except Exception as e:
            print("Erro:", e)

        threading.Timer(2, self.loop).start()

    # ------------------------
    # MOVIMENTO
    # ------------------------

    def ir_para_grupo(self, grupo):
        self.falar("Indo até o grupo " + str(grupo))

        # NÃO trava o robô
        threading.Timer(3, lambda: self.cheguei(grupo)).start()

    def cheguei(self, grupo):
        self.falar("Cheguei no grupo " + str(grupo))

        try:
            urllib2.urlopen(self.base_url + "/atendimento_start?grupo=" + str(grupo))
        except:
            print("Erro start")

    # ------------------------
    # FALA
    # ------------------------

    def falar(self, texto):
        tts = self.session().service("ALTextToSpeech")
        tts.say(texto)

    # ------------------------
    # VOZ
    # ------------------------

    def iniciar_reconhecimento(self):
        if self.ouvindo_ativo:
            return

        self.ouvindo_ativo = True

        self.asr = self.session().service("ALSpeechRecognition")
        self.memory = self.session().service("ALMemory")

        self.asr.pause(True)
        self.asr.setLanguage("Portuguese")

        vocab = ["maker", "biologia", "laser"]
        self.asr.setVocabulary(vocab, False)

        self.asr.pause(False)
        self.asr.subscribe("ASR")

        self.subscriber = self.memory.subscriber("WordRecognized")
        self.connection = self.subscriber.signal.connect(self.onPalavra)

    def parar_reconhecimento(self):
        if not self.ouvindo_ativo:
            return

        try:
            self.asr.unsubscribe("ASR")
            self.subscriber.signal.disconnect(self.connection)
        except:
            pass

        self.ouvindo_ativo = False

    # ------------------------
    # RESPOSTA
    # ------------------------

    def onPalavra(self, valor):
        try:
            if not self.ouvindo_ativo:
                return

            if len(valor) < 2:
                return

            palavra = valor[0]
            confianca = valor[1]

            if confianca < 0.5:
                return

            palavra = palavra.lower()

            if palavra == "laser":
                self.responder("laser")

            elif palavra == "biologia":
                self.responder("biologia")

            elif palavra == "maker":
                self.responder("inicio")

        except Exception as e:
            print("Erro voz:", e)

    # ------------------------
    # INTEGRAÇÃO
    # ------------------------

    def responder(self, tipo):
        self.falar("Vou te mostrar no tablet")

        try:
            urllib2.urlopen(self.base_url + "/conteudo_set?tipo=" + tipo)
        except:
            print("Erro conteudo")

        threading.Timer(2, self.finalizar).start()

    def finalizar(self):
        try:
            urllib2.urlopen(self.base_url + "/atendimento_end?grupo=" + str(self.grupo_atual))
        except:
            print("Erro end")

        self.grupo_atual = None
        self.processando = False