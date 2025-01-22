from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, LVector3, CollisionTraverser, CollisionHandlerPusher, CollisionSphere, CollisionNode
from panda3d.core import AmbientLight, DirectionalLight, TextNode
from direct.gui.OnscreenText import OnscreenText
from direct.task.Task import Task
import pickle
import os
import math


class FirstPersonGame(ShowBase):
    def __init__(self):
        super().__init__()

        # Ustawienia okna gry
        self.disableMouse()  # Wyłącz automatyczne sterowanie kamerą
        props = WindowProperties()
        props.setTitle("Ethernal Echoes")
        props.setCursorHidden(True)
        self.win.requestProperties(props)

        # Gracz i linie czasu
        self.player = self.loader.loadModel("models/box")  # Tymczasowy model gracza
        self.player.setScale(0.5)
        self.player.setPos(0, 0, 1)
        self.player.reparentTo(self.render)
        self.current_timeline = 0  # Aktualna linia czasu

        # Kamera
        self.camera.reparentTo(self.player)
        self.camera.setPos(0, 0, 1.5)
        self.camera_heading = 0
        self.camera_pitch = 0

        # Kontrolery klawiatury i myszki
        self.keys = {"forward": False, "backward": False, "left": False, "right": False}
        self.accept("w", self.setKey, ["forward", True])
        self.accept("w-up", self.setKey, ["forward", False])
        self.accept("s", self.setKey, ["backward", True])
        self.accept("s-up", self.setKey, ["backward", False])
        self.accept("a", self.setKey, ["left", True])
        self.accept("a-up", self.setKey, ["left", False])
        self.accept("d", self.setKey, ["right", True])
        self.accept("d-up", self.setKey, ["right", False])

        # Zmiana linii czasu
        self.accept("space", self.switch_timeline)

        # Pauza
        self.paused = False
        self.accept("escape", self.toggle_pause)

        # Kolizje
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()

        collider = self.player.attachNewNode(CollisionNode("player"))
        collider.node().addSolid(CollisionSphere(0, 0, 0, 0.5))
        self.pusher.addCollider(collider, self.player)
        self.cTrav.addCollider(collider, self.pusher)

        # Oświetlenie
        ambient_light = AmbientLight("ambientLight")
        ambient_light.setColor((0.5, 0.5, 0.5, 1))
        self.render.setLight(self.render.attachNewNode(ambient_light))

        directional_light = DirectionalLight("directionalLight")
        directional_light.setDirection(LVector3(-1, -1, -1))
        directional_light.setColor((1, 1, 1, 1))
        self.render.setLight(self.render.attachNewNode(directional_light))


        self.environments = [
            self.create_environment(color=(0.5, 0.8, 1)),
            self.create_environment(color=(0.2, 0.5, 0.2)),
        ]
        self.set_environment(self.current_timeline)


        self.taskMgr.add(self.update, "update")


        self.pause_menu = None

    def create_environment(self, color):

        env = self.loader.loadModel("models/environment")
        env.setColor(*color, 1)
        env.setScale(0.25, 0.25, 0.25)
        env.setPos(-8, 42, 0)
        env.reparentTo(self.render)
        env.hide()
        return env

    def set_environment(self, timeline):
        """Ustawia aktywne środowisko dla danej linii czasu."""
        for i, env in enumerate(self.environments):
            if i == timeline:
                env.show()
            else:
                env.hide()

    def switch_timeline(self):
        """Przełącza między liniami czasu."""
        self.current_timeline = (self.current_timeline + 1) % len(self.environments)
        self.set_environment(self.current_timeline)
        print(f"Przełączono na linię czasu: {self.current_timeline}")

    def setKey(self, key, value):
        """Ustawia stan klawisza."""
        self.keys[key] = value

    def update_camera(self, dt):
        """Aktualizuje pozycję i rotację kamery."""
        md = self.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        self.win.movePointer(0, self.win.getProperties().getXSize() // 2, self.win.getProperties().getYSize() // 2)


        self.camera_heading -= (x - self.win.getProperties().getXSize() // 2) * 0.1
        self.camera_pitch -= (y - self.win.getProperties().getYSize() // 2) * 0.1
        self.camera_pitch = max(-90, min(90, self.camera_pitch))

        self.player.setH(self.camera_heading)
        self.camera.setP(self.camera_pitch)

    def update(self, task):

        if self.paused:
            return Task.cont

        dt = globalClock.getDt()
        move_speed = 5 * dt

        if self.keys["forward"]:
            self.player.setY(self.player, move_speed)
        if self.keys["backward"]:
            self.player.setY(self.player, -move_speed)
        if self.keys["left"]:
            self.player.setX(self.player, -move_speed)
        if self.keys["right"]:
            self.player.setX(self.player, move_speed)

        self.update_camera(dt)
        return Task.cont

    def toggle_pause(self):
        """Przełączanie trybu pauzy."""
        self.paused = not self.paused

        if self.paused:
            self.show_pause_menu()
        else:
            self.hide_pause_menu()

    def show_pause_menu(self):
        """Wyświetla menu pauzy."""
        self.pause_menu = OnscreenText(
            text="Pauza\n[1] Zapisz grę\n[2] Wczytaj grę\n[3] Wyjście",
            pos=(0, 0),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=False
        )
        self.accept("1", self.save_game)
        self.accept("2", self.load_game)
        self.accept("3", self.exit_game)

    def hide_pause_menu(self):
        """Ukrywa menu pauzy."""
        if self.pause_menu:
            self.pause_menu.destroy()
            self.pause_menu = None

    def save_game(self):
        """Zapisuje stan gry."""
        save_data = {
            "player_pos": self.player.getPos(),
            "player_heading": self.camera_heading,
            "current_timeline": self.current_timeline
        }
        with open("savegame.pkl", "wb") as f:
            pickle.dump(save_data, f)
        print("Gra zapisana!")

    def load_game(self):
        """Wczytuje stan gry."""
        if os.path.exists("savegame.pkl"):
            with open("savegame.pkl", "rb") as f:
                save_data = pickle.load(f)
            self.player.setPos(save_data["player_pos"])
            self.camera_heading = save_data["player_heading"]
            self.current_timeline = save_data["current_timeline"]
            self.set_environment(self.current_timeline)
            print("Gra wczytana!")
        else:
            print("Brak zapisanego stanu gry!")

    def exit_game(self):
        """Zamyka grę."""
        print("Wyjście z gry...")
        self.userExit()

if __name__ == "__main__":
    game = FirstPersonGame()
    game.run()
