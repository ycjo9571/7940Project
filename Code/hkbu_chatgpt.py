import configparser
import requests

# apiKey = "92cffbed-50ac-4520-ab38-f9a07770a3c6"
# basicUrl = "https://genai.hkbu.edu.hk/general/rest"
# modelName = "gpt-4-o-mini"
# apiVersion = "2024-05-01-preview"


class HKBU_ChatGPT():
    def __init__(self, config_='./config.ini'):

        if type(config_) == str:
            self.config = configparser.ConfigParser()
            self.config.read(config_)
        elif type(config_) == configparser.ConfigParser:
            self.config = config_

    def submit(self, message):

        # print(self.config['CHATGPT']['BASICURL'])
        # print(self.config['CHATGPT']['MODELNAME'])
        # print(self.config['CHATGPT']['APIVERSION'])
        # print(self.config['CHATGPT']['ACCESS_TOKEN'])

        conversation = [{"role": "user", "content": message}]
        url = (self.config['CHATGPT']['BASICURL']) + "/deployments/" + (self.config['CHATGPT']
                                                                        ['MODELNAME']) + "/chat/completions/?api-version=" + (self.config['CHATGPT']['APIVERSION'])

        # url = basicUrl + "/deployments/" + modelName + \
        #     "/chat/completions/?api-version=" + apiVersion

        # print(f"url: {url}")
        headers = {'Content-Type': 'application/json',
                   'api-key': (self.config['CHATGPT']['ACCESS_TOKEN'])}
        # headers = {'Content-Type': 'application/json', 'api-key': apiKey}
        payload = {'messages': conversation}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']

        else:
            return 'Error:', response


if __name__ == '__main__':
    ChatGPT_test = HKBU_ChatGPT()

    while True:
        user_input = input("Typing anything to ChatGPT:\t")
        response = ChatGPT_test.submit(user_input)
        print(response)
