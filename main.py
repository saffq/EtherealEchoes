from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import (
    WindowProperties, LVector3, CollisionTraverser, CollisionHandlerPusher,
    CollisionNode, CollisionBox, AmbientLight, PointLight, Vec4, Vec3,
    CardMaker
)
from direct.gui.OnscreenText import OnscreenText
from direct.task.Task import Task
import pickle
import os

# -----------------------------------------------------
# --------------------- MAP EDITOR --------------------
# -----------------------------------------------------
class MapEditor:
    def __init__(self, render, loader):
        self.render = render
        self.loader = loader
        self.maps = []
        self.active_map = None

    def create_map(self, objects):
        new_map = self.render.attachNewNode(f"Map-{len(self.maps)}")
        for obj in objects:
            model = self.loader.loadModel("models/misc/rgbCube")
            model.setScale(*obj["scale"])
            model.setPos(*obj["position"])
            model.setColor(*obj["color"])
            model.reparentTo(new_map)
            collider = model.attachNewNode(CollisionNode("collider"))
            collider.node().addSolid(CollisionBox(
                LVector3(-obj["scale"][0]/2, -obj["scale"][1]/2, -obj["scale"][2]/2),
                LVector3(obj["scale"][0]/2, obj["scale"][1]/2, obj["scale"][2]/2)
            ))
        new_map.hide()
        self.maps.append(new_map)
        return new_map

    def switch_map(self, index):
        if self.active_map:
            self.active_map.hide()
        self.active_map = self.maps[index]
        self.active_map.show()

# -----------------------------------------------------
# ---------------------- NPC CLASS --------------------
# -----------------------------------------------------
class NPC:
    def __init__(self, render, loader, start_pos, movement_path):
        self.model = loader.loadModel("models/misc/rgbCube")
        self.model.setScale(0.5)
        self.model.setPos(*start_pos)
        self.model.reparentTo(render)
        self.movement_path = movement_path
        self.current_target = 0
        self.speed = 2

    def update(self, dt):
        if self.current_target >= len(self.movement_path):
            self.current_target = 0
        target = self.movement_path[self.current_target]
        current_pos = self.model.getPos()
        direction = LVector3(target) - current_pos
        distance = direction.length()
        if distance < 0.1:
            self.current_target += 1
        else:
            direction.normalize()
            self.model.setPos(current_pos + direction * self.speed * dt)

# -----------------------------------------------------
# -------------------- MAIN GAME ----------------------
# -----------------------------------------------------
class EternalEchoes(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        props = WindowProperties()
        props.setTitle("Eternal Echoes")
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(props)
        self.keys = {
            "forward": False, "backward": False,
            "left": False, "right": False,
            "sprint": False, "jump": False
        }
        self.accept("w", self.setKey, ["forward", True])
        self.accept("w-up", self.setKey, ["forward", False])
        self.accept("s", self.setKey, ["backward", True])
        self.accept("s-up", self.setKey, ["backward", False])
        self.accept("a", self.setKey, ["left", True])
        self.accept("a-up", self.setKey, ["left", False])
        self.accept("d", self.setKey, ["right", True])
        self.accept("d-up", self.setKey, ["right", False])
        self.accept("shift", self.setKey, ["sprint", True])
        self.accept("shift-up", self.setKey, ["sprint", False])
        self.accept("space", self.doJump)
        self.accept("escape", self.toggle_pause)
        self.accept("v", self.switch_timeline)
        self.player = self.loader.loadModel("models/misc/rgbCube")
        self.player.setScale(0.5)
        self.player.setPos(0, 0, 1)
        self.player.reparentTo(self.render)
        self.camera.reparentTo(self.player)
        self.camera.setPos(0, 0, 1.0)
        self.camera_heading = 0.0
        self.camera_pitch = 0.0
        self.mouse_sensitivity = 1.5
        self.gravity = -20
        self.jump_speed = 8
        self.vertical_speed = 0
        self.is_jumping = False
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()
        collider = self.player.attachNewNode(CollisionNode("player"))
        collider.node().addSolid(CollisionBox(LVector3(-0.25, -0.25, -0.25),
                                             LVector3(0.25, 0.25, 0.25)))
        self.pusher.addCollider(collider, self.player)
        self.cTrav.addCollider(collider, self.pusher)
        ambient_light = AmbientLight("ambientLight")
        ambient_light.setColor(Vec4(0.5, 0.5, 0.5, 1))
        self.render.setLight(self.render.attachNewNode(ambient_light))
        point_light = PointLight("pointLight")
        point_light_node = self.render.attachNewNode(point_light)
        point_light_node.setPos(0, 0, 10)
        self.render.setLight(point_light_node)
        self.map_editor = MapEditor(self.render, self.loader)
        self.map_editor.create_map(
            objects=[
                {"position": (0, 5, 0), "scale": (2, 2, 2), "color": (1, 0, 0, 1)},
                {"position": (5, 10, 0), "scale": (1, 1, 1), "color": (0, 1, 0, 1)},
            ]
        )
        self.map_editor.create_map(
            objects=[
                {"position": (-5, -5, 1), "scale": (1, 1, 1), "color": (0, 0, 1, 1)},
                {"position": (-7, -5, 1), "scale": (2, 1, 1), "color": (1, 1, 0, 1)},
            ]
        )
        self.current_timeline = 0
        self.map_editor.switch_map(self.current_timeline)
        self.npc = NPC(
            self.render,
            self.loader,
            start_pos=(10, 10, 1),
            movement_path=[(10, 10, 1), (15, 10, 1), (15, 15, 1), (10, 15, 1)]
        )
        cm = CardMaker("ground_card")
        cm.setFrame(-1, 1, -1, 1)
        self.ground = self.render.attachNewNode(cm.generate())
        self.ground.setScale(50, 50, 1)
        self.ground.setPos(0, 0, 0)
        ground_tex = self.loader.loadTexture("textures/brick.jpg")
        self.ground.setTexture(ground_tex, 1)
        self.is_paused = False
        self.pause_text = None
        self.message_text = None
        self.message_timer = 0.0
        self.taskMgr.add(self.update, "update")

    def setKey(self, key, value):
        self.keys[key] = value

    def doJump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.vertical_speed = self.jump_speed

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_text = OnscreenText(
                text="Pause\n[1] Save game\n[2] Load game\n[3] Quit",
                pos=(0, 0), scale=0.07
            )
            self.accept("1", self.save_game)
            self.accept("2", self.load_game)
            self.accept("3", self.exit_game)
        else:
            if self.pause_text:
                self.pause_text.destroy()
                self.pause_text = None

    def save_game(self):
        save_data = {
            "player_pos": self.player.getPos(),
            "player_hpr": self.player.getHpr()
        }
        with open("savegame.pkl", "wb") as f:
            pickle.dump(save_data, f)
        self.show_message("Game saved.")

    def load_game(self):
        if os.path.exists("savegame.pkl"):
            with open("savegame.pkl", "rb") as f:
                save_data = pickle.load(f)
            self.player.setPos(save_data["player_pos"])
            self.player.setHpr(save_data["player_hpr"])
            self.show_message("Save loaded")
        else:
            self.show_message("No save file")

    def exit_game(self):
        self.userExit()

    def show_message(self, text):
        if self.message_text:
            self.message_text.destroy()
        self.message_text = OnscreenText(
            text=text,
            pos=(0, 0.5),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=0
        )
        self.message_timer = 2.0

    def switch_timeline(self):
        self.current_timeline = (self.current_timeline + 1) % len(self.map_editor.maps)
        self.map_editor.switch_map(self.current_timeline)
        self.show_message(f"Timeline: {self.current_timeline}")

    def update(self, task):
        dt = globalClock.getDt()
        self.cTrav.traverse(self.render)
        if self.message_text:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message_text.destroy()
                self.message_text = None
        if self.is_paused:
            return Task.cont
        mw = self.mouseWatcherNode
        if mw.hasMouse():
            dx = mw.getMouseX()
            dy = mw.getMouseY()
            self.camera_heading -= dx * self.mouse_sensitivity
            self.camera_pitch += dy * self.mouse_sensitivity
            self.camera_pitch = max(-80, min(80, self.camera_pitch))
            self.player.setH(self.camera_heading)
            self.camera.setP(self.camera_pitch)
        move_speed = 5.0
        if self.keys["sprint"]:
            move_speed *= 2.5
        if self.keys["forward"]:
            self.player.setY(self.player, move_speed * dt)
        if self.keys["backward"]:
            self.player.setY(self.player, -move_speed * dt)
        if self.keys["left"]:
            self.player.setX(self.player, -move_speed * dt)
        if self.keys["right"]:
            self.player.setX(self.player, move_speed * dt)
        self.vertical_speed += self.gravity * dt
        new_z = self.player.getZ() + self.vertical_speed * dt
        floor_level = 1.0
        if new_z < floor_level:
            new_z = floor_level
            self.vertical_speed = 0
            self.is_jumping = False
        self.player.setZ(new_z)
        self.npc.update(dt)
        return Task.cont

if __name__ == "__main__":
    game = EternalEchoes()
    game.run()
