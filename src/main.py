"""
Aplicación principal para la automatización de eFootball

Este módulo integra todas las funcionalidades desarrolladas para la automatización
de eFootball en una única aplicación con interfaz de línea de comandos.

Permite:
1. Fichar jugadores específicos
2. Realizar entrenamientos de habilidad a jugadores
3. Jugar partidos contra la CPU hasta cumplir objetivos de eventos
4. Saltar banners iniciales al iniciar el juego
"""

import os
import sys
import argparse
import time

# Importar los módulos desarrollados
from gamepad_controller import GamepadController, GamepadType
from screen_recognizer import ScreenRecognizer
from banner_skipper import BannerSkipper
from player_signer import PlayerSigner
from player_trainer import PlayerTrainer
from match_player import MatchPlayer

class EFootballAutomation:
    """
    Clase principal que integra todas las funcionalidades para la automatización de eFootball.
    """
    
    def __init__(self, gamepad_type="xbox360"):
        """
        Inicializa la aplicación de automatización de eFootball.
        
        Args:
            gamepad_type (str): Tipo de gamepad a emular ("xbox360", "xboxone", "dualshock4")
        """
        print("Inicializando aplicación de automatización de eFootball...")
        
        # Convertir el tipo de gamepad a la enumeración correspondiente
        if gamepad_type.lower() == "xbox360":
            self.gamepad_type = GamepadType.XBOX360
        elif gamepad_type.lower() == "xboxone":
            self.gamepad_type = GamepadType.XBOXONE
        elif gamepad_type.lower() in ["dualshock4", "ds4", "playstation"]:
            self.gamepad_type = GamepadType.DS4
        else:
            print(f"Tipo de gamepad no reconocido: {gamepad_type}. Usando Xbox 360 por defecto.")
            self.gamepad_type = GamepadType.XBOX360
        
        # Inicializar el controlador de gamepad
        self.gamepad = GamepadController(self.gamepad_type)
        
        # Inicializar el reconocedor de pantalla
        self.recognizer = ScreenRecognizer()
        
        # Inicializar los módulos de funcionalidad
        self.banner_skipper = BannerSkipper(self.gamepad, self.recognizer)
        self.player_signer = PlayerSigner(self.gamepad, self.recognizer)
        self.player_trainer = PlayerTrainer(self.gamepad, self.recognizer)
        self.match_player = MatchPlayer(self.gamepad, self.recognizer)
        
        # Directorio para logs
        self.logs_dir = "/home/ubuntu/efootball_automation/logs"
        os.makedirs(self.logs_dir, exist_ok=True)
        
        print(f"Aplicación inicializada con gamepad tipo: {self.gamepad_type.value}")
    
    def skip_banners(self):
        """
        Ejecuta la funcionalidad para saltar banners iniciales.
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print("\n=== INICIANDO PROCESO PARA SALTAR BANNERS INICIALES ===")
        
        try:
            # Ejecutar el saltador de banners
            result = self.banner_skipper.run()
            
            if result:
                print("Proceso para saltar banners iniciales completado exitosamente")
            else:
                print("No se pudo completar el proceso para saltar banners iniciales")
            
            return result
        
        except Exception as e:
            print(f"Error al saltar banners iniciales: {e}")
            return False
    
    def sign_player(self, player_name=None, filters=None, player_index=0):
        """
        Ejecuta la funcionalidad para fichar un jugador específico.
        
        Args:
            player_name (str, optional): Nombre del jugador a fichar
            filters (dict, optional): Filtros para buscar al jugador
            player_index (int): Índice del jugador a seleccionar si no se especifica nombre
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print("\n=== INICIANDO PROCESO PARA FICHAR JUGADOR ===")
        
        try:
            # Ejecutar el fichador de jugadores
            result = self.player_signer.run(player_name, filters, player_index)
            
            if result:
                print(f"Proceso para fichar jugador {player_name if player_name else f'en posición {player_index}'} completado exitosamente")
            else:
                print(f"No se pudo completar el proceso para fichar jugador {player_name if player_name else f'en posición {player_index}'}")
            
            return result
        
        except Exception as e:
            print(f"Error al fichar jugador: {e}")
            return False
    
    def train_player(self, player_name):
        """
        Ejecuta la funcionalidad para entrenar a un jugador específico.
        
        Args:
            player_name (str): Nombre del jugador a entrenar
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print(f"\n=== INICIANDO PROCESO PARA ENTRENAR JUGADOR: {player_name} ===")
        
        try:
            # Ejecutar el entrenador de jugadores
            result = self.player_trainer.run(player_name)
            
            if result:
                print(f"Proceso para entrenar jugador {player_name} completado exitosamente")
            else:
                print(f"No se pudo completar el proceso para entrenar jugador {player_name}")
            
            return result
        
        except Exception as e:
            print(f"Error al entrenar jugador: {e}")
            return False
    
    def play_matches(self, max_matches=10, event_mode=True, difficulty="normal"):
        """
        Ejecuta la funcionalidad para jugar partidos contra la CPU.
        
        Args:
            max_matches (int): Número máximo de partidos a jugar
            event_mode (bool): Si True, intenta seleccionar partidos de evento
            difficulty (str): Dificultad de los partidos ("easy", "normal", "hard")
        
        Returns:
            bool: True si se completó correctamente, False en caso contrario
        """
        print(f"\n=== INICIANDO PROCESO PARA JUGAR PARTIDOS (Máx: {max_matches}, Modo evento: {event_mode}, Dificultad: {difficulty}) ===")
        
        try:
            # Ejecutar el jugador de partidos
            result = self.match_player.run(max_matches, event_mode, difficulty)
            
            if result:
                print("Proceso para jugar partidos completado exitosamente: objetivo alcanzado")
            else:
                print("No se pudo completar el objetivo de los partidos")
            
            return result
        
        except Exception as e:
            print(f"Error al jugar partidos: {e}")
            return False
    
    def run_all(self):
        """
        Ejecuta todas las funcionalidades en secuencia.
        
        Returns:
            dict: Resultados de cada funcionalidad
        """
        print("\n=== INICIANDO PROCESO COMPLETO DE AUTOMATIZACIÓN ===")
        
        results = {
            "skip_banners": False,
            "sign_player": False,
            "train_player": False,
            "play_matches": False
        }
        
        # 1. Saltar banners iniciales
        print("\nPaso 1: Saltar banners iniciales")
        results["skip_banners"] = self.skip_banners()
        
        # 2. Fichar un jugador
        print("\nPaso 2: Fichar jugador")
        filters = {
            "position": "Delantero",
            "club": "Barcelona",
            "price_max": 100000
        }
        results["sign_player"] = self.sign_player(filters=filters, player_index=0)
        
        # 3. Entrenar un jugador
        print("\nPaso 3: Entrenar jugador")
        results["train_player"] = self.train_player("Raquel")
        
        # 4. Jugar partidos
        print("\nPaso 4: Jugar partidos")
        results["play_matches"] = self.play_matches(max_matches=5, event_mode=True, difficulty="normal")
        
        # Resumen de resultados
        print("\n=== RESUMEN DE RESULTADOS ===")
        for task, result in results.items():
            print(f"{task}: {'Éxito' if result else 'Fallido'}")
        
        return results

def parse_arguments():
    """
    Parsea los argumentos de línea de comandos.
    
    Returns:
        argparse.Namespace: Argumentos parseados
    """
    parser = argparse.ArgumentParser(description="Automatización de eFootball")
    
    # Argumento para el tipo de gamepad
    parser.add_argument("--gamepad", type=str, default="xbox360",
                        choices=["xbox360", "xboxone", "dualshock4", "ds4"],
                        help="Tipo de gamepad a emular (default: xbox360)")
    
    # Subparsers para los diferentes comandos
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando para saltar banners
    skip_parser = subparsers.add_parser("skip", help="Saltar banners iniciales")
    
    # Comando para fichar jugador
    sign_parser = subparsers.add_parser("sign", help="Fichar jugador")
    sign_parser.add_argument("--name", type=str, help="Nombre del jugador a fichar")
    sign_parser.add_argument("--position", type=str, help="Posición del jugador")
    sign_parser.add_argument("--club", type=str, help="Club del jugador")
    sign_parser.add_argument("--price", type=int, help="Precio máximo del jugador")
    sign_parser.add_argument("--index", type=int, default=0, help="Índice del jugador a seleccionar (default: 0)")
    
    # Comando para entrenar jugador
    train_parser = subparsers.add_parser("train", help="Entrenar jugador")
    train_parser.add_argument("name", type=str, help="Nombre del jugador a entrenar")
    
    # Comando para jugar partidos
    play_parser = subparsers.add_parser("play", help="Jugar partidos")
    play_parser.add_argument("--max", type=int, default=10, help="Número máximo de partidos (default: 10)")
    play_parser.add_argument("--event", action="store_true", help="Jugar en modo evento")
    play_parser.add_argument("--difficulty", type=str, default="normal",
                            choices=["easy", "normal", "hard"],
                            help="Dificultad del partido (default: normal)")
    
    # Comando para ejecutar todo
    all_parser = subparsers.add_parser("all", help="Ejecutar todas las funcionalidades")
    
    return parser.parse_args()

def main():
    """Función principal de la aplicación"""
    # Parsear argumentos
    args = parse_arguments()
    
    # Inicializar la aplicación
    app = EFootballAutomation(gamepad_type=args.gamepad)
    
    # Ejecutar el comando correspondiente
    if args.command == "skip":
        app.skip_banners()
    
    elif args.command == "sign":
        # Construir filtros si se proporcionan
        filters = {}
        if args.position:
            filters["position"] = args.position
        if args.club:
            filters["club"] = args.club
        if args.price:
            filters["price_max"] = args.price
        
        # Ejecutar el fichador de jugadores
        app.sign_player(player_name=args.name, filters=filters if filters else None, player_index=args.index)
    
    elif args.command == "train":
        app.train_player(args.name)
    
    elif args.command == "play":
        app.play_matches(max_matches=args.max, event_mode=args.event, difficulty=args.difficulty)
    
    elif args.command == "all":
        app.run_all()
    
    else:
        print("Comando no reconocido. Use --help para ver los comandos disponibles.")

if __name__ == "__main__":
    print("Aplicación de automatización de eFootball")
    print("Esta aplicación permite automatizar diversas tareas en eFootball")
    print("utilizando técnicas de visión por computadora y emulación de gamepad.")
    print("\nEjecutando aplicación...")
    main()
