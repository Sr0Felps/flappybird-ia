import pygame
import random
import sys

# Inicialização do Pygame
pygame.init()

# Configuração da Tela
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Evolução Inteligente com AG (Fase 1 Polida)")

# Parâmetros Estéticos e Cores
BG_COLOR = (135, 206, 235)  # Azul claro (Sky Blue)
GROUND_COLOR = (34, 139, 34)  # Verde Floresta (Ground)
AGENT_COLOR = (255, 255, 0)  # Amarelo Vivo
PIPE_COLOR = (46, 139, 87)  # Verde Marinho (Mais profissional)
TEXT_COLOR = (255, 255, 255)
GAMEOVER_COLOR = (255, 69, 0) # Laranja Vermelho
BLACK = (0, 0, 0)

# Parâmetros de Física e Jogo
GRAVIDADE = 1
JUMP_STRENGTH = -15
OBSTACLE_SPEED = 5
OBSTACLE_GAP = 180
PIPE_WIDTH = 50
GROUND_HEIGHT = 30 # Altura do chão visual
OBSTACLE_SPAWN_RATE = 90 # Frames entre a criação de novos obstáculos

# Configuração do Tempo (para frame rate)
clock = pygame.time.Clock()
FPS = 60

# Fonte para Placar
font = pygame.font.SysFont("Arial", 48, bold=True)
font_small = pygame.font.SysFont("Arial", 30)

# Funções Auxiliares
def draw_text(text, font_obj, color, surface, x, y, center=False):
    textobj = font_obj.render(text, True, color)
    textrect = textobj.get_rect()
    if center:
        textrect.center = (x, y)
    else:
        textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

# Classes
class Agente:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.color = AGENT_COLOR
        self.default_color = AGENT_COLOR
        self.velocidade_y = 0
        self.score = 0
        self.passed_obstacle = False
        self.alive = True

    def pular(self):
        self.velocidade_y = JUMP_STRENGTH
        self.color = (255, 165, 0)
        
    def atualizar(self):
        if self.alive:
            if self.color != self.default_color and self.velocidade_y > -5:
                self.color = self.default_color
                
            self.velocidade_y += GRAVIDADE
            self.rect.y += self.velocidade_y
            self.score += 1

    def desenhar(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)

class Obstaculo:
    def __init__(self, screen_height):
        gap_center = random.randint(100, screen_height - GROUND_HEIGHT - 100)
        
        self.rect_top = pygame.Rect(SCREEN_WIDTH, 0, PIPE_WIDTH, gap_center - OBSTACLE_GAP // 2)
        self.rect_bottom = pygame.Rect(SCREEN_WIDTH, gap_center + OBSTACLE_GAP // 2, PIPE_WIDTH, screen_height - GROUND_HEIGHT - (gap_center + OBSTACLE_GAP // 2))
        self.passed = False

    def atualizar(self):
        self.rect_top.x -= OBSTACLE_SPEED
        self.rect_bottom.x -= OBSTACLE_SPEED

    def desenhar(self, screen):
        pygame.draw.rect(screen, PIPE_COLOR, self.rect_top)
        pygame.draw.rect(screen, PIPE_COLOR, self.rect_bottom)
        pygame.draw.rect(screen, BLACK, self.rect_top, 3) 
        pygame.draw.rect(screen, BLACK, self.rect_bottom, 3)

# Variáveis Globais de Estado
agente = Agente(50, SCREEN_HEIGHT // 2)
agente.pular()
obstacles = []
obstacle_timer = 0
running = True

# Reiniciar
def reset_game():
    global agente, obstacles, obstacle_timer
    
    agente = Agente(50, SCREEN_HEIGHT // 2)
    agente.pular() 
    obstacles = []
    obstacle_timer = 0

# Função que encapsula o loop principal
def game_loop():
    # CORREÇÃO: Declarando todas as globais acessadas/modificadas
    global running, obstacle_timer, agente, obstacles, OBSTACLE_SPAWN_RATE 

    while running:
        # Gerenciamento de Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Controle Manual Temporário (Espaço)
            if agente.alive and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                agente.pular()

        # Lógica do Jogo
        if agente.alive:
            agente.atualizar()
            
            # Colisão com o chão (limite visual)
            if agente.rect.bottom >= SCREEN_HEIGHT - GROUND_HEIGHT:
                agente.rect.bottom = SCREEN_HEIGHT - GROUND_HEIGHT
                agente.alive = False 
                
            # Colisão com o teto
            elif agente.rect.top <= 0:
                agente.rect.top = 0
                agente.velocidade_y = 0 

            # Geração de Obstáculos
            obstacle_timer += 1
            if obstacle_timer >= OBSTACLE_SPAWN_RATE:
                obstacles.append(Obstaculo(SCREEN_HEIGHT))
                obstacle_timer = 0
            
            # Atualização, Colisão e Pontuação de Obstáculos
            for obstacle in list(obstacles):
                obstacle.atualizar()
                
                # Colisão Agente vs. Obstáculo
                if agente.rect.colliderect(obstacle.rect_top) or agente.rect.colliderect(obstacle.rect_bottom):
                    agente.alive = False
                
                # Pontuação de Passagem
                if not obstacle.passed and agente.rect.left > obstacle.rect_top.right:
                    agente.score += 50
                    obstacle.passed = True
                
                # Remover obstáculos fora da tela
                if obstacle.rect_top.right < 0:
                    obstacles.remove(obstacle)

        # --- Renderização ---
        screen.fill(BG_COLOR)
        
        # Desenhar Chão
        pygame.draw.rect(screen, GROUND_COLOR, (0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT))
        
        agente.desenhar(screen)
        
        for obstacle in obstacles:
            obstacle.desenhar(screen)

        # Desenhar Placar
        draw_text(f'Score: {agente.score}', font, TEXT_COLOR, screen, 10, 10)

        # Tela de FIM DE JOGO e Reiniciar
        if not agente.alive:
            draw_text('FIM DE JOGO', font, GAMEOVER_COLOR, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, center=True)
            draw_text('Pressione R para Reiniciar', font_small, TEXT_COLOR, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10, center=True)
            draw_text('Pressione Q para Sair', font_small, TEXT_COLOR, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, center=True)
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_q]:
                running = False
            
            if keys[pygame.K_r]:
                reset_game()
                
        pygame.display.flip()
        clock.tick(FPS)

# Iniciar o loop do jogo
game_loop()

# Encerramento seguro
pygame.quit()
sys.exit()