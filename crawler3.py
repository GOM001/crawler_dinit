# -*- coding: utf-8 -*-
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from conf import CHAVE_ANTICAPTCHA as chave
import requests
import scrapy
import time
import json
import os
import re
import logging

options = Options()
# options.headless = True 
profile = webdriver.FirefoxProfile()
profile.add_extension('resorces/anticaptcha-plugin_v0.50.xpi')
logging.basicConfig(level=logging.DEBUG)
tt = time.time()


def acp_api_send_request(driver, message_type, data={}):
    message = {
        'receiver': 'antiCaptchaPlugin',
        'type': message_type,
        **data
    }
    return driver.execute_script("return window.postMessage({});".format(json.dumps(message)))

def t(s):
    time.sleep(s)


def simples(placa, renavam, driver):
    multas = driver.find_elements_by_css_selector('.row.no-gutters.align-items-center.row-grid.table-cell.mb-3')
    multas_list = []
    
    for multa in multas:

        z = multa.find_element_by_css_selector('div.col-md-9.p-3.table-body.table-body-left')
        detalhes_list = z.find_elements_by_css_selector('span')
        detalhes_titulos = [x.text for x in detalhes_list[::2]]
        detalhes_valores = [x.text for x in detalhes_list[1::2]]
        detalhes_dict = {x:y for x,y in zip(detalhes_titulos, detalhes_valores)}
        
        datahora = detalhes_dict.get('Data e Hora:')
        ndatahora = datahora.replace('às ', '').replace('h', ':').replace('min', ':00')
        valor = detalhes_dict.get('Valor Original:')
        nvalor = valor.replace('R$ ', '').replace(',', '.')
        multa_dict = {
            'ait': multa.find_element_by_css_selector('span[title="Auto da Infração"]').text,
            'causa_cancelamento': None,
            'cnpj': None,
            'codigo_enquadramento': None,
            'codigo_proprietario': None,
            'cpf': None,
            'datahora': datahora,
            'desconto_sne': detalhes_dict.get('Desc. 40% SNE:'),
            'descricao': detalhes_dict.get('Descrição'),
            'enquadramento': detalhes_dict.get('Descrição'),
            'fase_atual': None,
            'gravidade': detalhes_dict.get('Amparo e Gravidade:'),
            'local': detalhes_dict.get('Local:'),
            'municipio': detalhes_dict.get('Município:'),
            'normalizado_cnpj': None,
            'normalizado_cpf': None,
            'normalizado_datahora': ndatahora,
            'normalizado_valor': nvalor,
            # 'normalizado_valor_guia': None,
            'orgao_autuador': 'Dnit',
            'placa': placa,
            'placa_uf': None,
            'situacao': detalhes_dict.get('Situação:'),
            'url_foto': None            
        }
        multas_list.append(multa_dict)
    
    resposta = {
        'placa': placa,
        'status': "OK",
        'consulta': "simples",
        'data_count': len(multas_list),
        'data': multas_list
    }
    if len(multas_list) == 0:
        raise Exception("Erro na execução")

    return resposta

def craw(data):
    logging.debug('Iniciando Crawl')
    data = json.loads(data)

    logging.debug('Iniciando Driver')
    driver = webdriver.Firefox(profile, options=options)
    driver.implicitly_wait(1)
    driver.set_page_load_timeout(10)
    logging.debug('Configurando Captcha')
    #GET AntiCaptcha
    driver.get('https://antcpt.com/blank.html')



    veiculos_list = []

    logging.debug(f'Executando lista de veículos com {len(data)} Itens')

    for veiculo in data:
        try:
            driver.get('http://servicos.dnit.gov.br/multas/')
        except TimeoutException:
            driver.execute_script("window.stop();")
        print('Time consuming:', time.time() - tt)
        acp_api_send_request(driver,
            'setOptions',
            {'options': {'antiCaptchaApiKey': chave}}
        )
        t(3)
        placa = veiculo.get('placa')
        renavam = veiculo.get('renavam')
        logging.info(f'In Crawl Placa = {placa}, Renavam = {renavam}')
        t(1)
        driver.find_element_by_css_selector('#placa').click()
        t(1)
        driver.find_element(By.ID, "placa").send_keys(placa)
        t(1)
        driver.find_element_by_css_selector('#renavam').click()
        t(1)
        driver.find_element(By.ID, "renavam").send_keys(renavam)
        # this is the point
        try:
            t(2)
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-block")))
            driver.find_element(By.CSS_SELECTOR, ".btn-block").click()
            t(15)
        except:
            final = {"placa":placa, "status": 'Erro de coleta 1ª URL'}
            veiculos_list.append(final)
            continue

        #WebDriverWait(driver, 120).until(lambda x: x.find_element_by_css_selector('.antigate_solver.solved'))
        # IPLEMENTAR ERRO --- VERIFICAR URL ---
        # SE A MULTA NÃO FOI ENCONTRADA DEVEMOS SABER E SE POSSÍVEL O MOTIVO
        # INFORMAR DENTRO veiculos_list.append(ERRO)
        # CONTINUE PARA PULAR VEÍCULO
        if driver.current_url == 'http://servicos.dnit.gov.br/multas/':
            logging.warning(f'Erro -- Sem Info')
            erro = driver.find_element_by_css_selector('span.help.color-danger').text
            final = {"placa":placa, "status": erro}
            veiculos_list.append(final)
            continue
        while True:
            try:
                driver.find_element(By.CSS_SELECTOR, ".br-button.primary.m-3.mx-auto").click()
            except:
                break
            
        try:
            # OBTENÇÃO DO LINK PARA FILTRAR TOKEN
            t(2)
            link_multa = driver.find_element_by_css_selector('span.link-custom')
            link_multa.click()
            t(2)
            # TROCA DE TELA
            window_after = driver.window_handles[1]
            driver.switch_to_window(window_after)
            t(2)
            # OBETENDO O LINK
            link = driver.current_url
            # FECHANDO TELA SECUNDÁRIA
            driver.close()
            t(2)
            # MOVE PARA TELA PRINCIPAL
            driver.switch_to_window(driver.window_handles[0])
            t(2)
            # FILTRA O TOKEN
            token = re.search('token=(.*)', link).group(1)

            # CONFIGURAÇÃO DE PARÂMETROS PARA REQUISIÇÃO COM TOKEN
            headers = {
                    'Connection': 'keep-alive',
                    'Accept': 'application/json, text/plain, */*',
                    'DNT': '1',
                    'X-Requested-With': 'XMLHttpRequest',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                    'Authorization': f'Bearer {token}',
                    'Referer': 'http://servicos.dnit.gov.br/multas/consulta?ordenacaoCrescente=true',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
                }
            params = (
                ('skip', '0'),
                ('pageSize', '50'),
                ('ordenacaoCrescente', 'true'),
            )

            # RESQUISIÇÃO E OBTENÇÃO DO DADO
            response = requests.get('http://servicos.dnit.gov.br/multas/api/Infracao', headers=headers, params=params, verify=False)
            multas = json.loads(response.text)
            
            # TRATAMENTO DO DADO
            final = []
            for multa in multas.get('infracoes'):
                selecao = {}
                # VERIFICA SE TEM BOLETO ABERTO
                boleto = multa.get("indicadorGuiaPagamento")

                selecao['ait'] = multa.get("numeroAuto")
                
                if boleto == True:
                    selecao['boleto_ait'] = multa.get("numeroAuto")
                    selecao['boleto_valor'] = multa.get("valorMultaOriginal")
                    selecao['boleto_vencimento'] = multa.get("naDataVencimentoAtual")

                selecao['causa_cancelamento'] = multa.get("causaCancelamento")
                
                selecao['cnpj'] = multa.get("proprietarioCpfCnpj") if len(multa.get("proprietarioCpfCnpj")) > 11 else None
                
                selecao['codigo_enquadramento'] = multa.get('codigoInfracaoEnquadramento')
                selecao['codigo_proprietario'] = multa.get('codigoInfracaoProprietario')

                selecao['cpf'] = multa.get("proprietarioCpfCnpj") if len(multa.get("proprietarioCpfCnpj")) == 11 else None
                
                selecao['datahora'] = multa.get('dataHora')

                selecao['desconto_sne'] = "Sim" if multa.get('isSimplified') else "Não"

                selecao['descricao'] = multa.get('enquadramento')
                selecao['enquadramento'] = multa.get('enquadramento')
                selecao['fase_atual'] = multa.get('situacaoFase')
                selecao['gravidade'] = multa.get('gravidade')
                selecao['local'] = multa.get('local')
                selecao['municipio'] = multa.get('municipio')

                #selecao['normalizado_boleto_valor']

                selecao['normalizado_cnpj'] = multa.get("proprietarioCpfCnpj") if len(multa.get("proprietarioCpfCnpj")) > 11 else None
                selecao['normalizado_cpf'] = multa.get("proprietarioCpfCnpj") if len(multa.get("proprietarioCpfCnpj")) == 11 else None

                selecao['normalizado_datahora'] = multa.get('dataHora').replace('às ', '').replace('h', ':').replace('min', ':00')
                selecao['normalizado_valor'] = multa.get("valorMultaOriginal").replace('R$ ', '').replace(',', '.')

                # selecao['normalizado_valor_guia'] = multa.get("")
                selecao['orgao_autuador'] = 'Dnit'

                selecao['placa'] = multa.get('veiculoPlaca')

                uf = multa.get('veiculoPlacaUF')
                try:
                    uf = uf.split('/')[1].strip()
                except:
                    uf = None
                selecao['placa_uf'] = multa.get(uf)

                selecao['situacao'] = multa.get('situacaoFase') + '-' + multa.get('causaCancelamento')
                
                selecao['url_foto'] = multa.get('imagemPrincipalNomeFisico').replace('\\\\', 'http://servicos.dnit.gov.br/multas/api/Infracao/GetImagemInfracao?fileName=\\') if multa.get('imagemPrincipalNomeFisico') else None
                
                if boleto == True:
                    selecao['url_guia'] = f'http://servicos.dnit.gov.br/api-sior/gru/gerarregistrado?codigo={multa.get("codigoProcessoEncrypted")}&auto={multa.get("numeroAuto")}&token={token}'
                # ADICIONANDO MULTA A LISTA FINAL
                final.append(selecao)
            # FINALIZANDO ARQUIVO FINAL
            final = {"placa":placa, 'status': 'OK', 'data_count': multas.get('total'), 'data':final}
            # ENCERRAMENTO DO NAVEGADOR
        except:
            try:
                logging.warning('Coleta com boleto não pode ser realizada, tentando simples')
                final = simples(placa, renavam, driver)
                logging.debug('simples realizada com sucesso')
            except:
                logging.error('Coleta não pode ser realizada')
                # FINALIZANDO ARQUIVO FINAL
                final = {"placa":placa, "status": "Erro - Problema Na Execução"}

        # ADICIONANDO RESULTADOS A LISTA DE VEÍCULOS
        veiculos_list.append(final)

    # ENCERRAMENTO DO NAVEGADOR
    logging.debug('encerrando Navegador')
    driver.quit()
    return(veiculos_list)

if __name__ == "__main__":
    data = [{"placa":"","renavam":""}]
    print(craw(json.dumps(data)))
