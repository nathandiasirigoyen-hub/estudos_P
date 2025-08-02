import json
import argparse
from datetime import datetime
from collections import defaultdict

# Professor, foi necessário alterar o 'args = parse_args' para uma lista vazia para poder rodar no jupyter, tem que tirar o '[]' pra rodar no terminal.

arquivo = 'brasileirao-2023.json'

CORES = {
    'azul': '\033[94m',
    'azul_claro': '\033[96m',
    'verde': '\033[92m',
    'vermelho': '\033[91m',
    'reset': '\033[0m'
}

MAPA_RESULTADOS = {
    'V': f"{CORES['verde']}●{CORES['reset']}",
    'E': f"●",
    'D': f"{CORES['vermelho']}●{CORES['reset']}"
}

ZONAS_CLASSIFICACAO = {
    'LIBERTADORES': range(1, 5),
    'PRE_LIBERTADORES': range(5, 7),
    'SUL_AMERICANA': range(7, 13),
    'REBAIXAMENTO': range(17, 21)
}

def carregar_dados(arquivo):
    try:
        with open(arquivo, 'r', encoding='utf-8') as arq:
            print("Arquivo JSON carregado com sucesso.")
            return json.load(arq)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo}' não foi encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{arquivo}' não é um JSON válido.")
        return None

def converter_data_flexivel(data_str):
    if not isinstance(data_str, str): return None
    formatos_para_tentar = ['%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y']
    for formato in formatos_para_tentar:
        try:
            return datetime.strptime(data_str, formato)
        except ValueError:
            pass
    return None

def obter_filtro_do_usuario():
    print("\n--- Opções de Filtro ---")
    print("(T)odas as rodadas")
    print("(U)ma rodada específica")
    print("(P)eríodo de rodadas")
    print("(D)atas específicas")
    print("(V)oltar ao menu principal")
    
    while True:
        escolha = input("Escolha o tipo de filtro: ").upper()
        if escolha in ['T', 'U', 'P', 'D', 'V']: break
        print("Opção inválida. Tente novamente.")

    if escolha == 'T': return {'tipo': 'todas'}
    if escolha == 'V': return None
    if escolha == 'U':
        while True:
            try:
                rodada = int(input("Digite o número da rodada: "))
                return {'tipo': 'rodada_unica', 'valor': rodada}
            except ValueError:
                print("Entrada inválida. Digite um número.")
    if escolha == 'P':
        while True:
            try:
                inicio = int(input("Digite a rodada inicial: "))
                fim = int(input("Digite a rodada final: "))
                if inicio > fim:
                    print("A rodada inicial não pode ser maior que a final.")
                    continue
                return {'tipo': 'periodo_rodadas', 'inicio': inicio, 'fim': fim}
            except ValueError:
                print("Entrada inválida. Digite apenas números.")
    if escolha == 'D':
        while True:
            data_inicio_str = input("Digite a data inicial (ex: 2023-04-15 ou 15/04/23): ")
            data_fim_str = input("Digite a data final (ex: 2023-12-06 ou 06/12/23): ")
            data_inicio = converter_data_flexivel(data_inicio_str)
            data_fim = converter_data_flexivel(data_fim_str)
            if data_inicio and data_fim:
                if data_inicio > data_fim:
                    print("A data inicial não pode ser posterior à data final.")
                    continue
                return {'tipo': 'periodo_datas', 'inicio': data_inicio, 'fim': data_fim}
            print("Formato de data inválido ou datas não reconhecidas. Tente novamente.")

def gerador_dados_filtrados(arquivo_completo, filtro):
    if not arquivo_completo: return

    for num_rodada_str, jogos_da_rodada in arquivo_completo.items():
        try:
            num_rodada = int(num_rodada_str)
        except ValueError:
            continue
        
        if filtro['tipo'] == 'rodada_unica' and num_rodada != filtro['valor']: continue
        if filtro['tipo'] == 'periodo_rodadas' and not (filtro['inicio'] <= num_rodada <= filtro['fim']): continue

        for jogo in jogos_da_rodada:
            data_jogo = converter_data_flexivel(jogo.get('date'))
            if filtro['tipo'] == 'periodo_datas' and (not data_jogo or not (filtro['inicio'] <= data_jogo <= filtro['fim'])): continue
            
            info_tecnico = jogo.get('coach')
            placar = jogo.get('goals') 
            yield {
                'rodada': num_rodada, 'data': data_jogo, 'time_casa': jogo.get('clubs', {}).get('home'),
                'tecnico_casa': info_tecnico.get('home') if info_tecnico else None,
                'time_visitante': jogo.get('clubs', {}).get('away'),
                'tecnico_visitante': info_tecnico.get('away') if info_tecnico else None,
                'gols_casa': int(placar.get('home')) if placar and placar.get('home') is not None else None,
                'gols_visitante': int(placar.get('away')) if placar and placar.get('away') is not None else None,
            }

def mostrar_lista_tecnicos(gerador_dados):
    tecnicos = set()
    for jogo in gerador_dados:
        if jogo['tecnico_casa']: tecnicos.add(jogo['tecnico_casa'])
        if jogo['tecnico_visitante']: tecnicos.add(jogo['tecnico_visitante'])
    if not tecnicos:
        print("\nNenhum técnico encontrado para o filtro selecionado.")
        return
    print("\n--- Técnicos Encontrados ---")
    for numero, nome in enumerate(sorted(list(tecnicos)), 1):
        print(f"{numero}. {nome}")

def mostrar_estatisticas_tecnicos(gerador_dados):
    dados_agrupados = defaultdict(lambda: {'rodadas': set(), 'datas': set()})
    for jogo in gerador_dados:
        if not jogo['data']: continue
        if jogo['tecnico_casa'] and jogo['time_casa']:
            chave = (jogo['tecnico_casa'], jogo['time_casa'])
            dados_agrupados[chave]['rodadas'].add(jogo['rodada'])
            dados_agrupados[chave]['datas'].add(jogo['data'])
        if jogo['tecnico_visitante'] and jogo['time_visitante']:
            chave = (jogo['tecnico_visitante'], jogo['time_visitante'])
            dados_agrupados[chave]['rodadas'].add(jogo['rodada'])
            dados_agrupados[chave]['datas'].add(jogo['data'])

    if not dados_agrupados:
        print("\nNenhuma estatística pôde ser gerada para o filtro selecionado.")
        return

    print("\n--- Permanência de Técnicos por Clube (Ordenado por mais dias) ---")
    resultados = {chave: {'total_rodadas': len(info['rodadas']),'dias_no_clube': (max(info['datas']) - min(info['datas'])).days + 1 if info['datas'] else 0} for chave, info in dados_agrupados.items()}
    
    resultados_ordenados = sorted(resultados.items(), key=lambda item: item[1]['dias_no_clube'], reverse=True)
    
    for (tecnico, clube), stats in resultados_ordenados:
        print(f"- {tecnico} ({clube}):")
        print(f"  - Período de {stats['dias_no_clube']} dias.")
        print(f"  - Participou de {stats['total_rodadas']} rodada(s) distintas.")

def mostrar_tabela_campeonato(gerador_dados):
    tabela = defaultdict(lambda: {'P': 0, 'J': 0, 'V': 0, 'E': 0, 'D': 0, 'GP': 0, 'GC': 0, 'SG': 0, 'ultimos_jogos': []})
    for jogo in gerador_dados:
        gols_casa, gols_visitante = jogo['gols_casa'], jogo['gols_visitante']
        if gols_casa is None or gols_visitante is None: continue
        
        time_casa, time_visitante, data_jogo = jogo['time_casa'], jogo['time_visitante'], jogo['data']
        
        tabela[time_casa]['J'] += 1
        tabela[time_visitante]['J'] += 1
        tabela[time_casa]['GP'] += gols_casa
        tabela[time_visitante]['GP'] += gols_visitante
        tabela[time_casa]['GC'] += gols_visitante
        tabela[time_visitante]['GC'] += gols_casa

        resultado_casa, resultado_visitante = 'E', 'E'
        if gols_casa > gols_visitante:
            tabela[time_casa]['P'] += 3; tabela[time_casa]['V'] += 1; tabela[time_visitante]['D'] += 1
            resultado_casa, resultado_visitante = 'V', 'D'
        elif gols_visitante > gols_casa:
            tabela[time_visitante]['P'] += 3; tabela[time_visitante]['V'] += 1; tabela[time_casa]['D'] += 1
            resultado_casa, resultado_visitante = 'D', 'V'
        else:
            tabela[time_casa]['P'] += 1; tabela[time_visitante]['P'] += 1; tabela[time_casa]['E'] += 1; tabela[time_visitante]['E'] += 1
            
        if data_jogo:
            tabela[time_casa]['ultimos_jogos'].append((data_jogo, resultado_casa))
            tabela[time_visitante]['ultimos_jogos'].append((data_jogo, resultado_visitante))

    if not tabela:
        print("\nNenhum jogo encontrado para o filtro selecionado.")
        return

    for time, stats in tabela.items():
        stats['SG'] = stats['GP'] - stats['GC']
        stats['%'] = (stats['P'] / (stats['J'] * 3)) * 100 if stats['J'] > 0 else 0
        stats['ultimos_jogos'].sort(key=lambda x: x[0])
        stats['ultimos_jogos_str'] = ' '.join(MAPA_RESULTADOS[res[1]] for res in stats['ultimos_jogos'][-5:])

    tabela_ordenada = sorted(tabela.items(), key=lambda item: (item[1]['P'], item[1]['V'], item[1]['SG'], item[1]['GP']), reverse=True)

    print("\n" + "--- Tabela do Campeonato Brasileiro ---".center(80))
    cabecalho = f"{'#':>3} {'Clube':<20} {'P':>3} {'J':>3} {'V':>3} {'E':>3} {'D':>3} {'GP':>4} {'GC':>4} {'SG':>4} {'%':>5}  {'Últimos 5 Jogos'}"
    print(cabecalho)
    print("-" * len(cabecalho))

    for i, (time, stats) in enumerate(tabela_ordenada, 1):
        cor = CORES['reset']
        if i in ZONAS_CLASSIFICACAO['LIBERTADORES']: cor = CORES['azul']
        elif i in ZONAS_CLASSIFICACAO['PRE_LIBERTADORES']: cor = CORES['azul_claro']
        elif i in ZONAS_CLASSIFICACAO['SUL_AMERICANA']: cor = CORES['verde']
        elif i in ZONAS_CLASSIFICACAO['REBAIXAMENTO']: cor = CORES['vermelho']
        
        linha = f"{i:>3} {time:<20} {stats['P']:>3} {stats['J']:>3} {stats['V']:>3} {stats['E']:>3} {stats['D']:>3} {stats['GP']:>4} {stats['GC']:>4} {stats['SG']:>4} {stats['%']:>5.1f}  {stats['ultimos_jogos_str']}"
        print(f"{cor}{linha}{CORES['reset']}")

def painel_principal():
    parser = argparse.ArgumentParser(description='Análise de dados do Campeonato Brasileiro 2023.')
    parser.add_argument('arquivo_json', nargs='?', default='brasileirao-2023.json', help='Caminho para o arquivo JSON com os dados do campeonato.')
    args = parser.parse_args([])

    dicionario_principal = carregar_dados(args.arquivo_json)
    if not dicionario_principal:
        print("Encerrando o programa.")
        return

    while True:
        print("\n--- Painel de Análise do Brasileirão ---")
        print("1. Ver lista de técnicos")
        print("2. Ver estatísticas de permanência dos técnicos")
        print("3. Ver tabela do campeonato")
        print("4. Sair")
        
        escolha_acao = input("Digite sua escolha (1, 2, 3 ou 4): ")

        if escolha_acao in ['1', '2', '3']:
            filtro = obter_filtro_do_usuario()
            if filtro is None: continue

            dados_gerador = gerador_dados_filtrados(dicionario_principal, filtro)
            
            if escolha_acao == '1': mostrar_lista_tecnicos(dados_gerador)
            elif escolha_acao == '2': mostrar_estatisticas_tecnicos(dados_gerador)
            elif escolha_acao == '3': mostrar_tabela_campeonato(dados_gerador)

        elif escolha_acao == '4':
            print("Encerrando o programa. Até mais!")
            break
        else:
            print("Escolha inválida. Por favor, digite um número de 1 a 4.")

if __name__ == "__main__":
    painel_principal()
    
carregar_dados(arquivo)
    
