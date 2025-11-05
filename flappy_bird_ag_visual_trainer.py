import pygame
import random
import sys
import numpy as np
import csv
import time
import matplotlib.pyplot as plt
import pandas as pd
import os

# --- 1. CONFIGURAÇÕES DO ALGORITMO GENÉTICO (AG) ---
POPULATION_SIZE = 100      
NUM_GENERATIONS = 100      
ELITE_SIZE = 10            
MUTATION_RATE = 0.05       
MUTATION_SIGMA = 0.25      
OBSTACLE_PASS_BONUS = 1000 
# VISUALIZAÇÃO: Ocorre somente na última geração (Ver Loop Principal)

# Nome do arquivo de log e gráfico
CSV_FILENAME = 'evolucao_fitness.csv'
GRAPH_FILENAME = 'evolucao_ag_fitness.png'

# --- DIFICULDADE DINÂMICA CONSTANTES ---
DIFF_INCREMENT_RATE = 10    # A cada 10 obstáculos, a velocidade aumenta
DIFF_INCREMENT_VALUE = 0.5  # Aumento na velocidade por incremento

# Representação Genética (Pesos para um Perceptron Simples)
NUM_GENES = 3 

# --- 2. CONFIGURAÇÃO DO PYGAME E PARÂMETROS FÍSICOS ---

GRAVIDADE = 1
JUMP_STRENGTH = -15
OBSTACLE_SPEED_BASE = 5 
OBSTACLE_GAP = 180
PIPE_WIDTH = 50
GROUND_HEIGHT = 30
OBSTACLE_SPAWN_RATE = 90
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Variáveis globais de visualização
screen = None
clock = None
font = None
font_small = None
VISUAL_MODE = False

# Cores
BG_COLOR = (135, 206, 235)
GROUND_COLOR = (34, 139, 34)
AGENT_COLOR = (255, 255, 0)
PIPE_COLOR = (46, 139, 87)
TEXT_COLOR = (0, 0, 0) 
GAMEOVER_COLOR = (255, 69, 0)
BLACK = (0, 0, 0)

# --- LÓGICA DE DIFICULDADE DINÂMICA ---
def get_current_speed(obstacles_passed):
    """Calcula a velocidade atual com base nos obstáculos passados."""
    num_increments = obstacles_passed // DIFF_INCREMENT_RATE
    current_speed = OBSTACLE_SPEED_BASE + (num_increments * DIFF_INCREMENT_VALUE)
    return min(current_speed, 15) 

# --- FUNÇÕES AUXILIARES DE PYGAME ---
def init_pygame_visuals():
    global screen, clock, font, font_small, VISUAL_MODE
    
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Treinamento AG (Visualização Final)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 36, bold=True)
    font_small = pygame.font.SysFont("Arial", 20)
    VISUAL_MODE = True

def draw_text(text, font_obj, color, surface, x, y, center=False):
    if not VISUAL_MODE: return
    textobj = font_obj.render(text, True, color)
    textrect = textobj.get_rect()
    if center:
        textrect.center = (x, y)
    else:
        textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

# --- 3. CLASSES (Versão Híbrida) ---

class Agente:
    def __init__(self, x, y):
        # Inicializa o Rect corretamente para o modo atual
        self.rect = self._create_headless_rect(x, y) if not VISUAL_MODE else pygame.Rect(x, y, 30, 30)
        
        self.color = AGENT_COLOR
        self.default_color = AGENT_COLOR
        self.velocidade_y = 0
        self.alive = True
        self.frames_survived = 0 
        self.obstacles_passed = 0 
        self.genoma = np.random.uniform(low=-2.5, high=2.5, size=NUM_GENES) 
        
    def _create_headless_rect(self, x, y):
        class HeadlessRect:
            def __init__(self, x, y, width, height):
                self.x, self.y, self.width, self.height = x, y, width, height
                self.update_bounds()
            def update_bounds(self):
                self.top, self.bottom = self.y, self.y + self.height
                self.left, self.right = self.x, self.x + self.width
                self.centery = self.y + self.height // 2
            def colliderect(self, other):
                return (self.left < other.right and self.right > other.left and
                        self.top < other.bottom and self.bottom > other.top)
            def move_ip(self, dx, dy):
                self.x += dx
                self.y += dy
                self.update_bounds()
        return HeadlessRect(x, y, 30, 30)

    def pular(self):
        self.velocidade_y = JUMP_STRENGTH
        if VISUAL_MODE: self.color = (255, 165, 0)
        
    def atualizar(self):
        if self.alive:
            if VISUAL_MODE and self.color != self.default_color and self.velocidade_y > -5:
                self.color = self.default_color
                
            self.velocidade_y += GRAVIDADE
            
            if VISUAL_MODE:
                self.rect.y += self.velocidade_y
            else:
                 self.rect.move_ip(0, self.velocidade_y) 

            self.frames_survived += 1

    def desenhar(self, screen):
        if VISUAL_MODE and self.alive:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=5)

    def decidir_acao(self, obstaculos):
        if not self.alive: return

        proximo_obstaculo = None
        for obs in obstaculos:
            if obs.rect_bottom.right > self.rect.left:
                proximo_obstaculo = obs
                break

        if proximo_obstaculo:
            W_dist_x, W_dist_y, Bias = self.genoma[0], self.genoma[1], self.genoma[2]

            dist_x = proximo_obstaculo.rect_top.left - self.rect.right
            Input_X = dist_x / SCREEN_WIDTH 

            gap_center_y = proximo_obstaculo.rect_top.bottom + OBSTACLE_GAP // 2
            dist_y_relativa = gap_center_y - self.rect.centery
            Input_Y = dist_y_relativa / SCREEN_HEIGHT
            
            saida = (W_dist_x * Input_X) + (W_dist_y * Input_Y) + Bias
            
            if saida > 0.0: self.pular()


class Obstaculo:
    def __init__(self, screen_height):
        gap_center = random.randint(100, screen_height - GROUND_HEIGHT - 100)
        
        Rect_Class = pygame.Rect if VISUAL_MODE else self._create_headless_rect
        
        self.rect_top = Rect_Class(SCREEN_WIDTH, 0, PIPE_WIDTH, gap_center - OBSTACLE_GAP // 2)
        self.rect_bottom = Rect_Class(SCREEN_WIDTH, gap_center + OBSTACLE_GAP // 2, PIPE_WIDTH, screen_height - GROUND_HEIGHT - (gap_center + OBSTACLE_GAP // 2))
        self.passed = False 

    def _create_headless_rect(self, x, y, width, height):
        class HeadlessRect:
            def __init__(self, x, y, width, height):
                self.x, self.y, self.width, self.height = x, y, width, height
                self.update_bounds()
            def update_bounds(self):
                self.top, self.bottom = self.y, self.y + self.height
                self.left, self.right = self.x, self.x + self.width
            def colliderect(self, other):
                return (self.left < other.right and self.right > other.left and
                        self.top < other.bottom and self.bottom > other.top)
            def move_ip(self, dx, dy):
                self.x += dx
                self.y += dy
                self.update_bounds()
        return HeadlessRect(x, y, width, height)

    def atualizar(self, current_speed):
        if VISUAL_MODE:
            self.rect_top.x -= current_speed
            self.rect_bottom.x -= current_speed
        else:
            self.rect_top.move_ip(-current_speed, 0)
            self.rect_bottom.move_ip(-current_speed, 0)

    def desenhar(self, screen):
        if VISUAL_MODE:
            pygame.draw.rect(screen, PIPE_COLOR, self.rect_top)
            pygame.draw.rect(screen, PIPE_COLOR, self.rect_bottom)
            pygame.draw.rect(screen, BLACK, self.rect_top, 3) 
            pygame.draw.rect(screen, BLACK, self.rect_bottom, 3)

# --- 4. FUNÇÕES DO AG (Sem alteração) ---

def calcular_fitness(agente):
    return agente.frames_survived + (agente.obstacles_passed * OBSTACLE_PASS_BONUS) 

def selecionar_pais(populacao, fitnesses):
    pais_selecionados = []
    for _ in range(len(populacao)):
        idx1, idx2 = random.sample(range(len(populacao)), 2)
        if fitnesses[idx1] > fitnesses[idx2]:
            pais_selecionados.append(populacao[idx1].genoma)
        else:
            pais_selecionados.append(populacao[idx2].genoma)
    return pais_selecionados

def cruzamento_simples(genoma1, genoma2):
    ponto_corte = random.randint(1, NUM_GENES - 1)
    novo_genoma = np.concatenate((genoma1[:ponto_corte], genoma2[ponto_corte:]))
    return novo_genoma

def mutacao_gaussiana(genoma):
    if random.random() < MUTATION_RATE:
        idx = random.randint(0, NUM_GENES - 1)
        genoma[idx] += random.gauss(0, MUTATION_SIGMA)
        genoma[idx] = np.clip(genoma[idx], -5, 5)
    return genoma

def gerar_proxima_populacao(populacao_atual, fitnesses):
    proxima_populacao = []
    
    indices_ordenados = np.argsort(fitnesses)[::-1] 
    elite_indices = indices_ordenados[:ELITE_SIZE]
    
    for idx in elite_indices:
        novo_agente = Agente(50, SCREEN_HEIGHT // 2)
        novo_agente.genoma = populacao_atual[idx].genoma.copy()
        proxima_populacao.append(novo_agente)

    pais_genomas = selecionar_pais(populacao_atual, fitnesses)
    
    while len(proxima_populacao) < POPULATION_SIZE:
        pai1_genoma = random.choice(pais_genomas)
        pai2_genoma = random.choice(pais_genomas)
        
        filho_genoma = cruzamento_simples(pai1_genoma, pai2_genoma)
        filho_genoma = mutacao_gaussiana(filho_genoma)

        novo_agente = Agente(50, SCREEN_HEIGHT // 2)
        novo_agente.genoma = filho_genoma
        proxima_populacao.append(novo_agente)
        
    return proxima_populacao

# --- 5. LOG E GERAÇÃO DE GRÁFICO (Fase 3, Item 2) ---

def log_statistics_to_csv(geracao, melhor_fitness, media_fitness, melhor_obs):
    """Salva dados de evolução em um arquivo CSV."""
    file_exists = os.path.exists(CSV_FILENAME) and os.path.getsize(CSV_FILENAME) > 0

    with open(CSV_FILENAME, 'a', newline='') as csvfile:
        fieldnames = ['Geracao', 'Melhor_Fitness', 'Media_Fitness', 'Melhor_Obs_Passados']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'Geracao': geracao,
            'Melhor_Fitness': melhor_fitness,
            'Media_Fitness': round(media_fitness, 2),
            'Melhor_Obs_Passados': melhor_obs
        })

def generate_evolution_graph():
    """Gera um gráfico da evolução do fitness ao longo das gerações (Fase 3, Item 2)."""
    print("\n--- Gerando Gráfico de Evolução ---")
    
    try:
        df = pd.read_csv(CSV_FILENAME)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print(f"Erro: Arquivo '{CSV_FILENAME}' não encontrado ou vazio. O gráfico não pode ser gerado.")
        return
    
    plt.figure(figsize=(12, 6))
    
    geracoes = df['Geracao']
    melhor_fitness = df['Melhor_Fitness']
    media_fitness = df['Media_Fitness']

    plt.plot(geracoes, melhor_fitness, label='Melhor Fitness da Geração', color='blue', linewidth=2)
    plt.plot(geracoes, media_fitness, label='Fitness Médio da Geração', color='green', linestyle='--', linewidth=1)
    
    plt.title('Evolução do Algoritmo Genético em Flappy Bird (Dificuldade Dinâmica)', fontsize=16)
    plt.xlabel('Geração', fontsize=14)
    plt.ylabel('Fitness (Pontos + Bônus de Obstáculos)', fontsize=14)
    
    plt.legend(loc='upper left')
    plt.grid(True, linestyle=':', alpha=0.7)
    
    plt.xlim(1, geracoes.max())
    
    plt.savefig(GRAPH_FILENAME)
    plt.close()
    
    print(f"Gráfico de evolução salvo como: {GRAPH_FILENAME}")

# --- 6. SIMULAÇÃO HEADLESS E VISUAL ---

def simular_agente_headless(agente, max_frames=50000):
    """Simula a vida de um agente em modo rápido com dificuldade dinâmica."""
    
    agente.alive = True
    agente.frames_survived = 0
    agente.obstacles_passed = 0 
    
    # GARANTIA DE LARGADA IMEDIATA
    obstacles = [Obstaculo(SCREEN_HEIGHT)]
    obstacle_timer = 0
    
    while agente.alive and agente.frames_survived < max_frames: 
        
        current_speed = get_current_speed(agente.obstacles_passed)
        
        agente.decidir_acao(obstacles) 
        agente.atualizar()
        
        obstacle_timer += 1
        if obstacle_timer % OBSTACLE_SPAWN_RATE == 0:
            obstacles.append(Obstaculo(SCREEN_HEIGHT))
            obstacle_timer = 0
            
        for obstacle in list(obstacles):
            obstacle.atualizar(current_speed) 
            
            # Colisão
            if agente.rect.colliderect(obstacle.rect_top) or agente.rect.colliderect(obstacle.rect_bottom):
                agente.alive = False
            
            if agente.rect.bottom >= SCREEN_HEIGHT - GROUND_HEIGHT or agente.rect.top <= 0:
                agente.alive = False
            
            # RASTREAMENTO DE PONTUAÇÃO
            if not obstacle.passed and agente.rect.left > obstacle.rect_top.right:
                agente.obstacles_passed += 1
                obstacle.passed = True
            
            if obstacle.rect_top.right < 0:
                obstacles.remove(obstacle)
    
    return calcular_fitness(agente)

def visualizar_melhor_agente(melhor_agente, geracao):
    """Roda o melhor agente com visualização Pygame (Somente no final)."""
    global VISUAL_MODE, screen, clock
    
    if screen is None:
        init_pygame_visuals()

    agente_visual = Agente(50, SCREEN_HEIGHT // 2)
    agente_visual.genoma = melhor_agente.genoma.copy()
    
    obstacles = [Obstaculo(SCREEN_HEIGHT)]
    obstacle_timer = 0
    running = True

    while running and agente_visual.alive:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        current_speed = get_current_speed(agente_visual.obstacles_passed)

        agente_visual.decidir_acao(obstacles)
        agente_visual.atualizar()
        
        obstacle_timer += 1
        if obstacle_timer >= OBSTACLE_SPAWN_RATE:
            obstacles.append(Obstaculo(SCREEN_HEIGHT))
            obstacle_timer = 0
        
        for obstacle in list(obstacles):
            obstacle.atualizar(current_speed)
            
            if agente_visual.rect.colliderect(obstacle.rect_top) or agente_visual.rect.colliderect(obstacle.rect_bottom):
                agente_visual.alive = False
            
            if agente_visual.rect.bottom >= SCREEN_HEIGHT - GROUND_HEIGHT or agente_visual.rect.top <= 0:
                agente_visual.alive = False
            
            if not obstacle.passed and agente_visual.rect.left > obstacle.rect_top.right:
                agente_visual.obstacles_passed += 1
                obstacle.passed = True
            
            if obstacle.rect_top.right < 0:
                obstacles.remove(obstacle)

        # --- Renderização ---
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GROUND_COLOR, (0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT))
        
        agente_visual.desenhar(screen)
        for obstacle in obstacles:
            obstacle.desenhar(screen)

        # Info de Geração e Fitness
        draw_text(f'Geração: {geracao} (Final)', font, TEXT_COLOR, screen, 10, 10)
        draw_text(f'Passou: {agente_visual.obstacles_passed} Obs', font, TEXT_COLOR, screen, 10, 50)
        draw_text(f'Velocidade: {current_speed:.1f}', font_small, TEXT_COLOR, screen, 10, 90)

        pygame.display.flip()
        clock.tick(60)

    # Exibe FIM DE JOGO
    screen.fill(BG_COLOR)
    draw_text('MELHOR AGENTE FINALIZOU', font, GAMEOVER_COLOR, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True)
    draw_text(f'Obs Passados: {agente_visual.obstacles_passed}', font_small, BLACK, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, center=True)
    draw_text('Pressione Q para Sair', font_small, TEXT_COLOR, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90, center=True)
    pygame.display.flip()

    # Espera por Q
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                return
        time.sleep(0.05)
    
# --- 7. LOOP PRINCIPAL DE TREINAMENTO (Fase 3) ---

def treinamento_ag():
    global VISUAL_MODE
    
    # Remove arquivo CSV antigo
    try:
        os.remove(CSV_FILENAME)
    except FileNotFoundError:
        pass
    
    VISUAL_MODE = False
    populacao_atual = [Agente(50, SCREEN_HEIGHT // 2) for _ in range(POPULATION_SIZE)]
    melhor_agente_geral = populacao_atual[0]
    melhor_fitness_geral = -1
    
    print("--- Iniciando Treinamento AG com Log e Dificuldade Dinâmica ---")
    
    for geracao in range(NUM_GENERATIONS):
        
        # 1. Simulação Headless
        agentes_headless = []
        for agente_old in populacao_atual:
             novo_agente = Agente(50, SCREEN_HEIGHT // 2)
             novo_agente.genoma = agente_old.genoma
             agentes_headless.append(novo_agente)
        
        fitnesses = [simular_agente_headless(agente) for agente in agentes_headless]

        # 2. Estatísticas
        melhor_fitness_geracao = max(fitnesses)
        melhor_idx = np.argmax(fitnesses)
        media_fitness_geracao = np.mean(fitnesses)
        
        agente_melhor_geracao = Agente(50, SCREEN_HEIGHT // 2)
        agente_melhor_geracao.genoma = agentes_headless[melhor_idx].genoma.copy()
        agente_melhor_geracao.frames_survived = agentes_headless[melhor_idx].frames_survived
        agente_melhor_geracao.obstacles_passed = agentes_headless[melhor_idx].obstacles_passed

        # 3. Atualiza o melhor agente de todos os tempos
        if melhor_fitness_geracao > melhor_fitness_geral:
            melhor_fitness_geral = melhor_fitness_geracao
            melhor_agente_geral = agente_melhor_geracao
            
            print(f"Geração {geracao + 1}/{NUM_GENERATIONS}: NOVO RECORDE! Fitness={melhor_fitness_geral} (Passou {melhor_agente_geral.obstacles_passed} obs)")
        else:
             print(f"Geração {geracao + 1}/{NUM_GENERATIONS}: Melhor Fitness={melhor_fitness_geracao}, Média={media_fitness_geracao:.2f}")

        # 4. Log para CSV
        log_statistics_to_csv(geracao + 1, melhor_fitness_geracao, media_fitness_geracao, agente_melhor_geracao.obstacles_passed)
        
        # 5. Visualização Periódica (Apenas na última geração)
        if geracao == NUM_GENERATIONS - 1:
            print("\n--- VISUALIZANDO O MELHOR AGENTE (FINAL) ---")
            VISUAL_MODE = True
            visualizar_melhor_agente(melhor_agente_geral, geracao + 1)
            VISUAL_MODE = False
            
        # 6. Geração da Próxima População
        if geracao < NUM_GENERATIONS - 1:
            populacao_atual = gerar_proxima_populacao(agentes_headless, fitnesses)
            
    return melhor_agente_geral

# Iniciar o Treinamento
if __name__ == '__main__':
    try:
        melhor_agente_final = treinamento_ag()
        
        # 7. Geração do Gráfico Final
        generate_evolution_graph()
        
        print("\n--- TREINAMENTO AG CONCLUÍDO ---")
        print(f"Arquivo de log salvo em: {CSV_FILENAME}")
        print(f"Gráfico de evolução salvo em: {GRAPH_FILENAME}")
        print(f"Melhor Agente (Genoma): [{', '.join(f'{g:.2f}' for g in melhor_agente_final.genoma)}]")
        print(f"Melhor Fitness Geral Alcançado: {melhor_agente_final.frames_survived} frames, {melhor_agente_final.obstacles_passed} obstáculos")

    except Exception as e:
        print(f"Ocorreu um erro durante o treinamento: {e}")
    finally:
        if pygame.get_init():
            pygame.quit()
        sys.exit()