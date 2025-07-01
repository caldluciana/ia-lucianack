import openai
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from config import OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
from twilio.rest import Client

# Configuração da OpenAI e Twilio
openai.api_key = OPENAI_API_KEY
twilio_client = Client (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Nome da vendedora
NOME_VENDEDORA = "Luciana"

# Base de conhecimento e roteiro personalizado da Luciana
CONHECIMENTO_CK = f"""
Você é a Luciana, consultora do grupo CK. Você nunca se apresenta como robô, IA ou atendente automática.
Seu jeito de conversar é exatamente como humano, consultivo, empático e informativo.
Sempre se apresente no início da ligação como Luciana, consultora do grupo CK, e use frases como um profissional de vendas experiente.
Sempre ESCUTE primeiro, pergunte antes de sugerir, nunca faça discurso de máquina.
Evite frases como ‘sou uma inteligência artificial’ ou ‘sou assistente virtual’.
Ofereça ajuda sem forçar, seja simpática, responda dúvidas técnicas e, se necessário, se dispõe a transferir a ligação para outro especialista humano.

Exemplo de apresentação:
'Olá, quem fala é a Luciana, consultora do Grupo CK. Tudo bem? Te liguei porque percebi que sua empresa trabalha com transporte ou automação industrial, queria entender um pouquinho sobre seu processo e ver se consigo te trazer alguma solução diferente, pode ser?'

Exemplo de perguntas:
- Me conta um pouco, hoje vocês usam helicoides ou roscas transportadoras em qual parte do processo?
- Vocês costumam ter algum tipo de desgaste rápido nessas peças ou manutenção indesejada?
- Se você quiser, posso te ajudar a analisar algum ponto específico ou montar um comparativo sem compromisso.

Explique os diferenciais do Grupo Ck usando linguagem humana, sem “fala de robô”.

Seja sempre natural nas perguntas e respostas, cole informações como nome, empresa, telefone, aplicação e desafios do cliente de forma espontânea e simpática.
"""

class IAVendedora:
    def _init_(self):
        self.historico_conversa = []
        
    def responder_cliente(self, pergunta_cliente):
        prompt_completo = f"""
{CONHECIMENTO_CK}

Conversa anterior: {self.historico_conversa}

Cliente falou: {pergunta_cliente}

Responda como Luciana, consultora do grupo CK, de forma simpática, consultiva, objetiva e natural (máximo 3 frases):
"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt_completo}],
                max_tokens=200,
                temperature=0.65
            )
            resposta = response.choices[0].message.content.strip()
            self.historico_conversa.append(f"Cliente: {pergunta_cliente}")
            self.historico_conversa.append(f"Luciana: {resposta}")
            return resposta
        except Exception as e:
            return "Desculpe, tive um probleminha técnico aqui. Você pode repetir, por favor?"

ia_vendedora = IAVendedora()

# Início da ligação
from flask import Flask

app = Flask(__name__)


@app.route("/atender_ligacao", methods=['POST'])
def atender_ligacao():
    response = VoiceResponse()
    response.say(
        "Olá, quem fala é a Luciana, consultora do Grupo CK. Tudo bem contigo? Queria entender um pouquinho sobre sua empresa, posso te ajudar em alguma coisa?",
        language='pt-BR', voice='Polly.Camila'
    )
    response.gather(input='speech', language='pt-BR', timeout=10,
                    action='/processar-fala', method='POST')
    return str(response)

@app.route("/processar-fala", methods=['POST'])
def processar_fala():
    fala_cliente = request.form.get('SpeechResult', '')
    if fala_cliente:
        resposta_ia = ia_vendedora.responder_cliente(fala_cliente)
        response = VoiceResponse()
        response.say(
            resposta_ia,
            language='pt-BR', voice='Polly.Camila'
        )
        response.gather(input='speech', language='pt-BR', timeout=10,
                        action='/processar-fala', method='POST')
    else:
        response = VoiceResponse()
        response.say("Desculpa, não consegui ouvir o que você disse. Pode repetir, por favor?",
                     language='pt-BR', voice='Polly.Camila')
        response.gather(input='speech', language='pt-BR', timeout=10,
                        action='/processar-fala', method='POST')
    return str(response)

def ligar_para_cliente(numero_telefone):
    try:
        call = twilio_client.calls.create(
            url='http://SEU-SERVIDOR.com/atender-ligacao',
            to=numero_telefone,
            from_=TWILIO_PHONE_NUMBER
        )
        print(f"Ligação iniciada: {call.sid}")
        return call.sid
    except Exception as e:
        print(f"Erro ao ligar: {e}")
        return None

if __name__ == "__main__":
    print("IA Luciana, consultora do Grupo CK iniciada!")
    app.run(debug=True, port=5000)