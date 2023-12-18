import pygame
import csv
import time
import threading
import sys
from mutagen.mp3 import MP3
from pyfirmata2 import ArduinoMega, util

# Inicialização do Pygame
pygame.init()

# Configurações da tela
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Guitar Hero Simplificado")

# Carrega a imagem do fundo
background_image = pygame.image.load(r'C:\Users\mathe\Downloads\Guitar_Hero_POO\fundo_guitarhero_6.jpg').convert()

# Redimensiona a imagem do fundo para o tamanho da tela
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Carrega a imagem de fogo e redimensiona para 70x70 pixels
fire_image = pygame.image.load(r'C:\Users\mathe\Downloads\Guitar_Hero_POO\fogo_normal.png').convert_alpha()
fire_image = pygame.transform.scale(fire_image, (70, 70))

# Carrega a imagem de fogo e redimensiona para 70x70 pixels
fire_image_blue = pygame.image.load(r'C:\Users\mathe\Downloads\Guitar_Hero_POO\fogo_azul-removebg-preview.png').convert_alpha()
fire_image_blue = pygame.transform.scale(fire_image_blue, (70, 70))


# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Distância entre as colunas
COLUMN_DISTANCE = SCREEN_WIDTH // 6

# Posições das colunas (ajustadas)
COLUMN_GREEN = COLUMN_DISTANCE * 1.95
COLUMN_RED = COLUMN_DISTANCE * 2.65
COLUMN_YELLOW = COLUMN_DISTANCE * 3.35
COLUMN_BLUE = COLUMN_DISTANCE * 4.05

class Background(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()

    def draw(self, tela):
        tela.blit(self.image, (0, 0))

        # Desenhar a coluna preta no meio
        largura_coluna = 460
        altura_coluna = SCREEN_HEIGHT
        pos_x_coluna = SCREEN_WIDTH // 2 - largura_coluna // 2
        pos_y_coluna = 0
        pygame.draw.rect(tela, BLACK, (pos_x_coluna, pos_y_coluna, largura_coluna, altura_coluna))

        # Desenhar linhas brancas no meio da coluna
        qtd_linhas = 3
        distancia_entre_linhas = largura_coluna // (qtd_linhas + 1)
        for i in range(1, qtd_linhas + 1):
            x = pos_x_coluna + i * distancia_entre_linhas
            pygame.draw.line(tela, WHITE, (x, 0), (x, SCREEN_HEIGHT), 5)

# Classe para representar as notas móveis
class Note(pygame.sprite.Sprite):
    def __init__(self, color, column_x,input_manager):
        super().__init__()
        self.color = color
        self.column_x = column_x
        self.image = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLACK, (35, 35), 30)
        pygame.draw.circle(self.image, BLACK, (35, 35), 28)
        pygame.draw.circle(self.image, self.color, (35, 35), 26)
        pygame.draw.circle(self.image, BLACK, (35, 35), 16)
        pygame.draw.circle(self.image, WHITE, (35, 35), 12)
        self.rect = self.image.get_rect()
        self.rect.centerx = self.column_x
        self.rect.y = 0
        self.hit = False  # Atributo 'hit' para controlar se a nota foi acertada
        self.input_manager = input_manager

    def update(self):
        self.rect.y += 10
        if self.rect.y > SCREEN_HEIGHT:
            if not self.hit:
                self.input_manager.correct_notes_count = 0  # Zera o contador
                #self.input_manager.game.pino_motor_1.write(1)  # Ligar o motor 1
                #self.input_manager.game.pino_motor_2.write(1)  # Ligar o motor 2
                #threading.Timer(0.1, self.input_manager.turn_off_motor).start()  # Desligar o motor após 0.5 segundos
            self.kill()            


class FixedNote(pygame.sprite.Sprite):
    def __init__(self, color, column_x):
        super().__init__()
        self.default_color = color
        self.highlight_color = (255, 255, 255)  # Cor de destaque (branca)
        self.image = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (35, 35), 30)  # Desenha o círculo da cor padrão
        pygame.draw.circle(self.image, self.default_color, (35, 35), 28)  # Desenha o círculo da cor padrão
        self.rect = self.image.get_rect()
        self.rect.centerx = column_x
        self.rect.y = SCREEN_HEIGHT - 80

    def highlight(self):
        self.image.fill(pygame.SRCALPHA)  # Limpa a imagem
        pygame.draw.circle(self.image, WHITE, (35, 35), 30)  
        pygame.draw.circle(self.image, self.default_color + (100,), (35, 35), 28)  # Redesenha o círculo com a cor padrão
        self.highlighted = True
    
    def unhighlight(self):
        self.image.fill(pygame.SRCALPHA)  # Limpa a imagem
        pygame.draw.circle(self.image, WHITE, (35, 35), 30)  
        pygame.draw.circle(self.image, self.default_color, (35, 35), 28)  # Redesenha o círculo com a cor padrão
        self.highlighted = False


# Classe para gerenciar a reprodução da música (definição da classe para o MusicPlayer)
class MusicPlayer:
    def __init__(self, music_path, delay):
        self.music_path = music_path
        self.delay = delay
        self.paused = False  # Add a paused attribute to track the pause state

    def play(self):
        if not self.paused:
            time.sleep(self.delay)  # Aguarda o atraso
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.play()

    def pause(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.paused = True

    def resume(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            
    def get_length(self):
        audio = MP3(self.music_path)
        return audio.info.length
        

# Classe para ler vetores de um arquivo CSV (definição da classe para o VectorReader)
class VectorReader:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path

    def read_vectors(self):
        vectors = []
        with open(self.csv_file_path, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            for row in csv_reader:
                vector = [int(value) for value in row]
                vectors.append(vector)
        return vectors
   
# Classe para gerenciar o input do jogador
class InputManager:
    def __init__(self, game):
        self.game = game
        self.correct_notes_count = 0  # Contador para notas corretas
        self.score = 0
        self.multiplicador = 1
        self.correct_notes_count = 0
        self.notas_totais = 0
        self.recorde = 0

    def handle_key_press(self, key):
        if key in self.game.key_to_color:
            note_color = self.game.key_to_color[key]
            self.game.note_states[note_color] = True
            # Destaca a nota fixa correspondente
            self.game.highlight_fixed_note(note_color)
    
            # Verifica a colisão aqui e atualiza a pontuação e mensagens de acerto/erro
            note_hit = False  # Variável para rastrear se a nota foi acertada
            for note in self.game.all_notes:
                collisions = pygame.sprite.spritecollide(note, self.game.fixed_notes, False)
                for fixed_note in collisions:
                    if self.game.custom_collision(note, fixed_note):
                        if note.color == note_color:
                            note.hit = True
                            self.game.input_manager.increase_score()
                            self.correct_notes_count += 1  # Incrementa o contador
                            self.notas_totais += 1
                            if self.correct_notes_count >= 30:
                                self.game.fire_manager.add_fire_image(note, fire_image_blue)  # Adiciona a imagem de fogo
                            else:
                                self.game.fire_manager.add_fire_image(note, fire_image)  # Adiciona a imagem de fogo
                            note.kill()
                            note_hit = True
                            if self.correct_notes_count > self.recorde:
                                self.recorde = self.correct_notes_count
                            break
            if not note_hit:
                self.correct_notes_count = 0  # Zera o contador quando erra
                self.game.pino_motor_1.write(1)  # Liga o Motor 1
                self.game.pino_motor_2.write(1)  # Liga o Motor 2
                threading.Timer(0.1, self.turn_off_motor).start() 

    def turn_off_motor(self):
        # Desligar o motor após 0.5 segundos
        self.game.pino_motor_1.write(0)
        self.game.pino_motor_2.write(0)
        
    def handle_key_release(self, key):
        if key in self.game.key_to_color:
            note_color = self.game.key_to_color[key]
            self.game.note_states[note_color] = False
            # Remove o destaque da nota fixa correspondente
            self.game.unhighlight_fixed_note(note_color)
            
    def increase_score(self):
        self.score += 50 * self.multiplicador
        if ((self.correct_notes_count + 1) % 10 == 0 )and (self.multiplicador < 4):
            self.multiplicador += 1
        elif self.multiplicador == 4:
            self.multiplicador = 4            

    def get_score(self):
        return self.score
    
    def get_multiplicador(self):
        if self.correct_notes_count == 0:
            self.multiplicador = 1
        return self.multiplicador
    
    def get_sequencia(self):
        return self.correct_notes_count
    
    def get_total(self):
        return self.notas_totais
    
    def get_recorde(self):
        return self.recorde
            
class FireManager:
    def __init__(self):
        self.fire_images = {}

    def add_fire_image(self, note, fire_image):
        self.fire_images[note] = (fire_image, pygame.time.get_ticks())

    def remove_expired_fire_images(self):
        current_time = pygame.time.get_ticks()
        for note, (fire_img, start_time) in list(self.fire_images.items()):
            if current_time - start_time > 200:  # 200 milissegundos (0,2 segundos)
                del self.fire_images[note]

    def draw_fire_images(self, screen):
        for note, (fire_img, _) in self.fire_images.items():
            fire_x = note.rect.centerx - fire_img.get_width() // 2
            fire_y = SCREEN_HEIGHT - 80
            screen.blit(fire_img, (fire_x, fire_y))
            
class Text:
    def __init__(self, screen, text, font_size, color, position):
        self.screen = screen
        self.font = pygame.font.SysFont('cambria', font_size)
        self.text = text
        self.color = color
        self.position = position

    def render_text(self):
        self.text_surface = self.font.render(self.text, True, self.color)
        self.text_rect = self.text_surface.get_rect()
        self.text_rect.topleft = self.position
        self.bg_rect = pygame.Rect(self.position, (self.text_rect.width + 5, self.text_rect.height))
        pygame.draw.rect(self.screen, (0, 0, 0), self.bg_rect)
        self.screen.blit(self.text_surface, self.text_rect)

         
# Classe para gerenciar o jogo (definição da classe para o Game)
class Game:
    def __init__(self, music_player, vector_reader, vectors):
        
        self.note_hit_results = []  # Lista para rastrear os resultados das tentativas
                
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.all_notes = pygame.sprite.Group()
        self.fixed_notes = pygame.sprite.Group()
        
        # Criação de instâncias das classes MusicPlayer e VectorReader
        self.music_player = music_player
        self.vector_reader = vector_reader
        self.vectors = vectors

        # Adiciona as notas fixas
        self.fixed_notes.add(FixedNote(RED, COLUMN_RED))
        self.fixed_notes.add(FixedNote(GREEN, COLUMN_GREEN))
        self.fixed_notes.add(FixedNote(BLUE, COLUMN_BLUE))
        self.fixed_notes.add(FixedNote(YELLOW, COLUMN_YELLOW))
        
        # Criação da instância Background
        self.background = Background(background_image)
        
        self.note_data = []  # Lista para armazenar as notas a serem exibidas
        self.note_index = 0  # Índice para acompanhar a próxima nota a ser processada
       
        self.key_to_color = {
            pygame.K_s: RED,
            pygame.K_a: GREEN,
            pygame.K_k: BLUE,
            pygame.K_j: YELLOW,

        }
        
        self.note_states = {
            RED: False,
            GREEN: False,
            BLUE: False,
            YELLOW: False
        }
        
        
        self.font = pygame.font.SysFont('cambria', 36)  # Fonte para exibir o texto
        
        # Instancia o gerenciador de input
        self.input_manager = InputManager(self)

        self.fire_manager = FireManager() 
        self.is_paused = False # Linha para registar o estado do jogo
                
        self.setup_arduino()    

        self.key_to_color_arduino = {
            
            self.botão_vermelho.read(): RED,
            self.botão_verde.read(): GREEN,
            self.botão_azul.read(): BLUE,
            self.botão_amarelo.read(): YELLOW,

        }
               
    def handle_arduino_input(self):
        key_mapping = { 
            self.botão_vermelho.read: pygame.K_s,
            self.botão_amarelo.read: pygame.K_j,
            self.botão_azul.read: pygame.K_k,
            self.botão_verde.read: pygame.K_a
        }
    
        if not hasattr(self, 'prev_button_states'):
            self.prev_button_states = {method: False for method in key_mapping.keys()}
    
        for button_method, key in key_mapping.items():
            button_pressed = button_method()
            prev_button_pressed = self.prev_button_states[button_method]
    
            if button_pressed and not prev_button_pressed:
                keydown_event = pygame.event.Event(pygame.KEYDOWN, key=key)
                pygame.event.post(keydown_event)
            elif not button_pressed and prev_button_pressed:
                keyup_event = pygame.event.Event(pygame.KEYUP, key=key)
                pygame.event.post(keyup_event)
    
            self.prev_button_states[button_method] = button_pressed        
    def setup_arduino(self):
        self.port = ArduinoMega.AUTODETECT
        self.board = ArduinoMega(self.port)
    
        it = util.Iterator(self.board)
        it.start()
    
        self.pino_motor_1 = self.board.get_pin('d:24:o')
        self.pino_motor_2 = self.board.get_pin('d:26:o')
        self.botão_verde = self.board.get_pin('d:30:i')
        self.botão_vermelho = self.board.get_pin('d:28:i')
        self.botão_amarelo = self.board.get_pin('d:32:i')
        self.botão_azul = self.board.get_pin('d:34:i')


    def pause(self):
        self.is_paused = True
        self.music_player.pause()
        #self.pause_menu.run()

    def follow(self):
        self.is_paused = False
        self.music_player.resume()

    def read_note_data(self, csv_file_path):
        with open(csv_file_path, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            for row in csv_reader:
                if len(row) >= 5:  # Verifica se há pelo menos 5 valores na linha
                    time_ms, x, y, z, w = map(int, row[:5])  # Converte para inteiros
                    self.note_data.append((time_ms, x, y, z, w))
                else:
                    print("Linha inválida no arquivo:", row)  # Tratamento de erro

    def check_collisions(self):
        for note in self.all_notes:
            for fixed_note in self.fixed_notes:
                if self.note_states[fixed_note.default_color]:  # Verifica se o botão não está pressionado
                    if pygame.sprite.collide_rect_ratio(0.4)(note, fixed_note):
                        self.input_manager.increase_score()
                        note.kill()
                        return True  # Retorna True se houver uma colisão
        return False  # Retorna False se não houver colisão

                    
    def play_music_with_delay(self, music_player, delay):
        def play_music():
            time.sleep(delay)
            music_player.play()

        music_thread = threading.Thread(target=play_music)
        music_thread.start()
         
    def run(self):
        # Inicia a reprodução da música com atraso
        self.play_music_with_delay(self.music_player, 0)
    
        current_note_index = 0
        start_time = pygame.time.get_ticks()  # Tempo de início do jogo em milissegundos
        elapsed_time = 0  # Tempo decorrido enquanto o jogo está pausado
    
        # Obtém a duração da música em milissegundos
        music_duration = int(self.music_player.get_length() * 1000)
    
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:  # 'p' é a tecla para pausar o jogo
                        self.pause()
                        elapsed_time = pygame.time.get_ticks() - start_time
                    elif event.key == pygame.K_f:  # 'f' é a tecla para retomar o jogo
                        self.follow()
                        start_time = pygame.time.get_ticks() - elapsed_time
                    else:
                        self.input_manager.handle_key_press(event.key)
                elif event.type == pygame.KEYUP:
                    self.input_manager.handle_key_release(event.key)
    
            if not self.is_paused:
                
                #Chamar a função para lidar com a entrada do Arduino
                self.handle_arduino_input()
                
                current_time = pygame.time.get_ticks() - start_time  # Tempo decorrido em milissegundos
    
                if current_note_index < len(self.note_data):
                    note_time, x, y, z, w = self.note_data[current_note_index]
                    if current_time >= note_time:
                        if x == 1:
                            self.all_notes.add(Note(GREEN, COLUMN_GREEN, self.input_manager))
                        if y == 1:
                            self.all_notes.add(Note(RED, COLUMN_RED, self.input_manager))
                        if z == 1:
                            self.all_notes.add(Note(YELLOW, COLUMN_YELLOW, self.input_manager))
                        if w == 1:
                            self.all_notes.add(Note(BLUE, COLUMN_BLUE, self.input_manager))
                        current_note_index += 1
    
                self.all_notes.update()
    
                # Limpeza da tela
                self.screen.fill(WHITE)
    
                # Desenha o fundo
                self.background.draw(self.screen)
    
                # Desenhar as notas fixas
                self.fixed_notes.draw(self.screen)
    
                # Desenhar as notas móveis na tela
                self.all_notes.draw(self.screen)
    
                score = self.input_manager.get_score()
                pontuacao = Text(self.screen, f'Pontuação: {score}', 32, (255, 165, 0), (5, 5))
                pontuacao.render_text()
    
                multiplicador = self.input_manager.get_multiplicador()
                combo = Text(self.screen, f'Combo: {multiplicador}x', 32, (255, 165, 0), (5, 55))
                combo.render_text()
    
                correct_notes_count = self.input_manager.get_sequencia()
                notas_corretas = Text(self.screen, f'Sequência: {correct_notes_count}', 32, (255, 165, 0), (5, 105))
                notas_corretas.render_text()
                                
                game.fire_manager.remove_expired_fire_images()
                game.fire_manager.draw_fire_images(game.screen)
    
                pygame.display.flip()
                self.clock.tick(75.5)
                    
                # Se a música terminou, saia do loop principal
                if current_time >= music_duration:
                    break
    
        self.board.exit()
    
    def custom_collision(self, note, fixed_note):
        # Área da interseção entre a nota e a nota fixa
        intersection = note.rect.clip(fixed_note.rect)
    
        # Calcula a área da interseção
        area_intersection = intersection.width * intersection.height
    
        # Calcula a área da nota
        area_note = note.rect.width * note.rect.height
    
        # Calcula a porcentagem da área da nota que está dentro da nota fixa
        overlap_percentage = (area_intersection / area_note) * 100
    
        # Retorna True se a sobreposição for maior ou igual a 20%
        return overlap_percentage >= 10


    def highlight_fixed_note(self, color):
        for note in self.fixed_notes:
            if note.default_color == color:
                note.highlight()

    def unhighlight_fixed_note(self, color):
        for note in self.fixed_notes:
            if note.default_color == color:
                note.unhighlight()
                   
        
class Button:
    def __init__(self, color, x, y, width, height, text=''):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.visible = True

    def draw(self, screen, outline=None):
        if self.visible:
            if outline:
                pygame.draw.rect(screen, outline, (self.x-2, self.y-2, self.width+4, self.height+4), 0)
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), 0)
            if self.text != '':
                font = pygame.font.SysFont('Cambria', 50)
                text = font.render(self.text, 1, (0, 0, 0))
                screen.blit(text, (self.x + (self.width/2 - text.get_width()/2), self.y + (self.height/2 - text.get_height()/2)))

    def is_over(self, pos):
        if self.x < pos[0] < self.x + self.width:
            if self.y < pos[1] < self.y + self.height:
                return True
        return False

class GameMenu:
        
    def run(self):
        button_width = 300
        button_height = 100
        settings_button = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT//3 - button_height//2, button_width, button_height, 'Dificuldade')
        credits_button = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT//2 - button_height//2, button_width, button_height, 'Créditos')
        musics_button = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT*2//3 - button_height//2, button_width, button_height, 'Músicas')
    
        run = True
        while run:
            
            screen.blit(background_image, (0, 0))
            
            settings_button.draw(screen, (255, 255, 255))
            credits_button.draw(screen, (255, 255, 255))
            musics_button.draw(screen, (255, 255, 255))
    
            pygame.display.update()
    
            for event in pygame.event.get():
                pos = pygame.mouse.get_pos()
                
                if event.type == pygame.QUIT:
                    return 'quit'
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if settings_button.is_over(pos):
                        print("Apertou settings")
                        return 0                    
                    if credits_button.is_over(pos):
                        print("Apertou credits")
                        return 1
                    if musics_button.is_over(pos):
                        print("Apertou musics")
                        return 2
                
                if event.type == pygame.MOUSEMOTION:
                    if settings_button.is_over(pos):
                        settings_button.color = (255, 0, 0)
                    else:
                        settings_button.color = (0, 255, 0)
                    if credits_button.is_over(pos):
                        credits_button.color = (255, 0, 0)
                    else:
                        credits_button.color = (0, 255, 0)
                    if musics_button.is_over(pos):
                        musics_button.color = (255, 0, 0)
                    else:
                        musics_button.color = (0, 255, 0)            
     
class MusicMenu:      
    
    def run(self):
        button_width = 500
        button_height = 100
        music1 = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT//3 - button_height//2, button_width, button_height, 'You Only Live Once')
        music2 = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT//2 - button_height//2, button_width, button_height, 'Dani California')
        music3 = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT*2//3 - button_height//2, button_width, button_height, 'Everlong')
    
        menu_button = Button((0, 255, 0), 10, 10, 200, 100, 'Menu')
    
        run = True
        while run:
            
            screen.blit(background_image, (0, 0))
            
            music1.draw(screen, (255, 255, 255))
            music2.draw(screen, (255, 255, 255))
            music3.draw(screen, (255, 255, 255))
            menu_button.draw(screen, (255, 255, 255))
    
            pygame.display.update()
    
            for event in pygame.event.get():
                pos = pygame.mouse.get_pos()
    
                if event.type == pygame.QUIT:
                    return 'quit'
    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if music1.is_over(pos):
                        return 3                    
                    if music2.is_over(pos):
                        return 4
                    if music3.is_over(pos):
                        return 5
                    if menu_button.is_over(pos):
                        return "menu"
                    
                if event.type == pygame.MOUSEMOTION:
                    if music1.is_over(pos):
                        music1.color = (255, 0, 0)
                    else:
                        music1.color = (0, 255, 0)
                    if music2.is_over(pos):
                        music2.color = (255, 0, 0)
                    else:
                        music2.color = (0, 255, 0)
                    if music3.is_over(pos):
                        music3.color = (255, 0, 0)
                    else:
                        music3.color = (0, 255, 0)
                    if menu_button.is_over(pos):
                        menu_button.color = (255, 0, 0)
                    else:
                        menu_button.color = (0, 255, 0)   
    
class SettingsMenu:

    def __init__(self):
        self.button_width = 300
        self.button_height = 100
        self.easy_button = Button((0, 255, 0), SCREEN_WIDTH//2 - self.button_width//2, SCREEN_HEIGHT // 2 - self.button_height // 2 - (self.button_height//2 + 8), self.button_width, self.button_height, 'Fácil')
        self.medium_button = Button((0, 255, 0), SCREEN_WIDTH//2 - self.button_width//2, SCREEN_HEIGHT // 2 - self.button_height // 2 + (self.button_height//2 + 8), self.button_width, self.button_height, 'Médio')
    
    def run(self):
            
        button_width = 500
        button_height = 100
        easy_button = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT // 2 - button_height // 2 - (button_height//2 + 8), button_width, button_height, 'Fácil')
        medium_button = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT // 2 - button_height // 2 + (button_height//2 + 8), button_width, button_height, 'Médio')
    
        menu_button = Button((0, 255, 0), 10, 10, 200, 100, 'Menu')
    
        run = True
        while run:
            
            screen.blit(background_image, (0, 0))
            
            easy_button.draw(screen, (255, 255, 255))
            medium_button.draw(screen, (255, 255, 255))
            menu_button.draw(screen, (255, 255, 255))
    
            pygame.display.update()
    
            for event in pygame.event.get():
                pos = pygame.mouse.get_pos()
    
                if event.type == pygame.QUIT:
                    run = False
                    return 'quit'
    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if easy_button.is_over(pos):
                        return 6                 
                    if medium_button.is_over(pos):
                        return 7
                    if menu_button.is_over(pos):
                        return "menu"
    
                if event.type == pygame.MOUSEMOTION:
                    if easy_button.is_over(pos):
                        easy_button.color = (255, 0, 0)
                    else:
                        easy_button.color = (0, 255, 0)
                    if medium_button.is_over(pos):
                        medium_button.color = (255, 0, 0)
                    else:
                        medium_button.color = (0, 255, 0)
                    if menu_button.is_over(pos):
                        menu_button.color = (255, 0, 0)
                    else:
                        menu_button.color = (0, 255, 0)
class CreditsMenu:               
    
    def run(self):
        # Configurações da tela
        menu_button = Button((0, 255, 0), 10, 10, 200, 100, 'Menu')
        
        run = True
        font = pygame.font.SysFont('cambria', 50)
        while run:
            
            screen.fill((0, 0, 0))
            
            menu_button.draw(screen, (255, 255, 255))
            
            text1 = font.render("Matheus Ferreira Palú", 1, (255, 255, 255))
            text2 = font.render("Engenharia de Controle e Automação", 1, (255, 255, 255))
            text3 = font.render("Instituto Mauá de Tecnologia", 1, (255, 255, 255))
            screen.blit(text1, (SCREEN_WIDTH//2 - text1.get_width()//2, SCREEN_HEIGHT//2 - text2.get_height()//2 - 75 - text1.get_height()//2))
            screen.blit(text2, (SCREEN_WIDTH//2 - text2.get_width()//2, SCREEN_HEIGHT//2 - text2.get_height()//2))
            screen.blit(text3, (SCREEN_WIDTH//2 - text3.get_width()//2, SCREEN_HEIGHT//2 - text2.get_height()//2 + 75 + text3.get_height()//2)) 
            pygame.display.update()
    
            for event in pygame.event.get():
                
                pos = pygame.mouse.get_pos()
                
                if event.type == pygame.QUIT:
                    run = False
                    return 'quit'
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_button.is_over(pos):
                        return "menu"
                    
                if event.type == pygame.MOUSEMOTION:
                    if menu_button.is_over(pos):
                        menu_button.color = (255, 0, 0)
                    else:
                        menu_button.color = (0, 255, 0)
                    
class ExitMenu:               
        
    def __init__(self, input_manager, total):
        self.input_manager = input_manager
        self.total = total
    
    def run(self):

        pontos = self.input_manager.get_score()
        porcentagem = int((self.input_manager.get_total()/self.total)*100)
        recorde = self.input_manager.get_recorde()

        button_width = 300
        button_height = 100
        
        # Configurações da tela
        
        menu_button = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT // 2 - button_height // 2 - (button_height//2 + 8 + 30), button_width, button_height, 'Menu')
        exit_button = Button((0, 255, 0), SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT // 2 - button_height // 2 + (button_height//2 + 8 - 30), button_width, button_height, 'Sair')

        font = pygame.font.SysFont('cambria', 40)
        text_surface = font.render(f'Pontuação: {pontos}', True, (255, 165, 0))
        text_rect = text_surface.get_rect()
        
        font_2 = pygame.font.SysFont('cambria', 40)
        text_surface_2 = font_2.render(f'Porcentagem: {porcentagem}%', True, (255, 165, 0))
        text_rect_2 = text_surface_2.get_rect()

        font_3 = pygame.font.SysFont('cambria', 40)
        text_surface_3 = font_3.render(f'Recorde: {recorde} notas seguidas', True, (255, 165, 0))
        text_rect_3 = text_surface_3.get_rect()

        run = True
        font = pygame.font.SysFont('cambria', 50)
        while run:
            
            screen.blit(background_image, (0, 0))  # Draw the background image
                      
            position = (SCREEN_WIDTH//2 - text_rect.centerx, 440)
            text = Text(screen, f'Pontuação: {pontos}', 40, (255, 165, 0), position)
            text.render_text()
            
            position_2 = (SCREEN_WIDTH//2 - text_rect_2.centerx, 495)
            text_2 = Text(screen, f'Porcentagem: {porcentagem}%', 40, (255, 165, 0), position_2)
            text_2.render_text()
            
            position_3 = (SCREEN_WIDTH//2 - text_rect_3.centerx, 550)
            text_3 = Text(screen, f'Recorde: {recorde} notas seguidas', 40, (255, 165, 0), position_3)
            text_3.render_text()
            
            menu_button.draw(screen, (255, 255, 255))
            exit_button.draw(screen, (255, 255, 255))
            
            pygame.display.update()
    
            for event in pygame.event.get():
                
                pos = pygame.mouse.get_pos()
                
                if event.type == pygame.quit:
                    run = False
                    return 'quit'
                               
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_button.is_over(pos):
                        print("Apertou Menu")
                        return "voltar"               
                    if exit_button.is_over(pos):
                        print("Apertou Exit")
                        pygame.quit()
                        sys.exit()
                        run = False
                        return "quit"
                    
                if event.type == pygame.MOUSEMOTION:
                    if menu_button.is_over(pos):
                        menu_button.color = (255, 0, 0)
                    else:
                        menu_button.color = (0, 255, 0)
                    if exit_button.is_over(pos):
                        exit_button.color = (255, 0, 0)
                    else:
                        exit_button.color = (0, 255, 0)
                        
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        run = False

dificuldade = "facil"

while True:
    
    menu = GameMenu()
    menu_result = menu.run()
    
    music = MusicMenu()
    
    settings = SettingsMenu()
    
    credits_menu = CreditsMenu()
        
    if menu_result == 'quit':
        break

    if menu_result == 0:
        settings_result = settings.run()
        if settings_result == 'quit':
            break
        if settings_result == 6:
            print("Dificuldade: Fácil")
            dificuldade = "facil"
        elif settings_result == 7:
            print("Dificuldade: Médio")
            dificuldade = "medio"

    elif menu_result == 1:
        credits_result = credits_menu.run()  
        if credits_result == 'quit': 
            break

    elif menu_result == 2:
        music_result = music.run()
        if music_result == 'quit': 
            break
        if music_result == 3 and dificuldade == "facil":
            
            music_player = MusicPlayer(r'C:/Users/mathe/Downloads\Guitar_Hero_POO/The-Strokes-You-Only-Live-Once-_lyrics_.mp3', 0.1)
            vector_reader = VectorReader('yolo_facil_new.csv')
            vectors = vector_reader.read_vectors()
            
            game = Game(music_player, vector_reader, vectors)
            game.read_note_data('yolo_facil_new.csv')

            game.run()
            
            total = 577
            pause_menu = ExitMenu(game.input_manager,total)
            pause_menu.run()
            
        if music_result == 3 and dificuldade == "medio":
            
            music_player = MusicPlayer(r'C:/Users/mathe/Downloads\Guitar_Hero_POO/The-Strokes-You-Only-Live-Once-_lyrics_.mp3', 0.1)
            vector_reader = VectorReader('yolo_novo_medio.csv')
            vectors = vector_reader.read_vectors()
            
            game = Game(music_player, vector_reader, vectors)
            game.read_note_data('yolo_novo_medio.csv')

            game.run()
            
            total = 757
            pause_menu = ExitMenu(game.input_manager,total)
            pause_menu.run()
            
        if music_result == 4 and dificuldade == "facil":
            
            music_player = MusicPlayer(r'C:\Users\mathe\Downloads\Guitar_Hero_POO\Red Hot Chilli Peppers_ Dani California (Lyrics).mp3', 0.1)
            vector_reader = VectorReader('dani_facil_novo.csv')
            vectors = vector_reader.read_vectors()
            
            game = Game(music_player, vector_reader, vectors)
            game.read_note_data('dani_facil_novo.csv')

            game.run()
            
            total = 453
            pause_menu = ExitMenu(game.input_manager,total)
            pause_menu.run()
            
        if music_result == 4 and dificuldade == "medio":
            
            music_player = MusicPlayer(r'C:\Users\mathe\Downloads\Guitar_Hero_POO\Red Hot Chilli Peppers_ Dani California (Lyrics).mp3', 0.1)
            vector_reader = VectorReader('dani_new_medium.csv')
            vectors = vector_reader.read_vectors()
            
            game = Game(music_player, vector_reader, vectors)
            game.read_note_data('dani_new_medium.csv')

            game.run()
            
            total = 840
            pause_menu = ExitMenu(game.input_manager,total)
            pause_menu.run()
            
        if music_result == 5 and dificuldade == "facil":
            
            music_player = MusicPlayer(r'C:\Users\mathe\Downloads\Guitar_Hero_POO\Foo Fighters - Everlong.mp3', 0.1)
            vector_reader = VectorReader('novo_everlong_easy.csv')
            vectors = vector_reader.read_vectors()
            
            game = Game(music_player, vector_reader, vectors)
            game.read_note_data('novo_everlong_easy.csv')

            game.run()
            
            total = 323
            pause_menu = ExitMenu(game.input_manager,total)
            pause_menu.run()
            
        if music_result == 5 and dificuldade == "medio":
            
            music_player = MusicPlayer(r'C:\Users\mathe\Downloads\Guitar_Hero_POO\Foo Fighters - Everlong.mp3', 0.1)
            vector_reader = VectorReader('everlong_medio_new.csv')
            vectors = vector_reader.read_vectors()
            
            game = Game(music_player, vector_reader, vectors)
            game.read_note_data('everlong_medio_new.csv')

            game.run()
            
            total = 968
            pause_menu = ExitMenu(game.input_manager,total)
            pause_menu.run()
            
pygame.quit() 