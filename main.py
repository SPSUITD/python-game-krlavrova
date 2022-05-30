import arcade
from const import *

#загрузка текстуры и автоматическое отражение по горизонтали
def load_texture_pair(filename):
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]
#класс анимации персонажа
class PlayerCharacter(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.character_face_direction = RIGHT_FACING
        self.cur_texture = 0

        #загружаем кадры анимации
        main_path = "char"
        self.idle_texture_pair = load_texture_pair(f"{main_path}/idle1.png")
        self.walk_textures = []
        for i in range(5):
            texture = load_texture_pair(f"{main_path}/run{i}.png")
            self.walk_textures.append(texture)

    def update_animation(self, delta_time: float = 1 / 10):
        #через движение по икс определяем в какую сторону смотрит персонаж
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return
        #переключаем кадры анимации
        self.cur_texture += 1
        if self.cur_texture > 4 * UPDATES_PER_FRAME:
            self.cur_texture = 0
        frame = self.cur_texture // UPDATES_PER_FRAME
        direction = self.character_face_direction
        self.texture = self.walk_textures[frame][direction]

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.scene = None
        self.player_sprite = None
        self.physics_engine = None
        self.coin_list = None
        self.enemy_list = None
        self.camera = None
        self.gui_camera = None
        self.score = 0
        self.lives = 3
        self.end_of_map = 0
        self.collect_sound = arcade.load_sound("sound/drops.mp3")
        self.kill_sound = arcade.load_sound("sound/kill.mp3")
        self.jump_sound = arcade.load_sound("sound/jump.wav")
        self.tile_map = None
        self.background = None
        self.level = 1

    def setup(self):
        self.camera = arcade.Camera()
        self.gui_camera = arcade.Camera()
        #загрузка карты
        map_name = f"maps/map_{self.level}/map_{self.level}.json"
        layer_options = {
            LAYER_NAME_PLATFORMS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_MOVING_PLATFORMS: {
                "use_spatial_hash": False,
            },
        }
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.score = 0
        self.coin_list = arcade.SpriteList(use_spatial_hash=True)
        self.enemy_list = arcade.SpriteList(use_spatial_hash=True)

        if self.level == 1:
            coins_coordinate_list = [[832, 288], [992, 352], [736, 608], [1376, 96], [1824, 160],
                                     [1632, 672], [1312, 864], [2208, 544], [2720, 96], [2976, 416],
                                     [3424, 544], [3808, 800], [3872, 352]]
            enemy_coordinate_list = [[940,366], [1700, 174], [2848, 430], [3800, 366]]
            self.background = arcade.load_texture("maps/bg1.png")
        elif self.level == 2:
            coins_coordinate_list = [[480, 480], [864, 608], [1184, 416], [1248, 800], [1568, 96],
                                     [1888, 608], [2080, 288], [2272, 160], [2400, 160], [2400, 672],
                                     [2528, 672], [2784, 96], [3296, 288], [3680, 864], [3936, 352]]
            enemy_coordinate_list = [[1888, 366], [2208, 174], [2400, 686], [3296, 302], [3936, 366]]
            self.background = arcade.load_texture("maps/bg2.png")

        for coordinate in coins_coordinate_list:
            coin = self.coins = arcade.load_animated_gif("maps/carrot/c.gif")
            coin.position = coordinate
            self.coin_list.append(coin)

        for coordinate in enemy_coordinate_list:
            enemy = self.enemy = arcade.load_animated_gif("maps/enemies/a1.gif")
            enemy.position = coordinate
            enemy.boundary_left = enemy.center_x - 50
            enemy.boundary_right = enemy.center_x + 100
            enemy.change_x = 0.7
            self.enemy_list.append(enemy)

        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = 64
        self.player_sprite.center_y = 300
        self.scene.add_sprite("Player", self.player_sprite)
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            gravity_constant=GRAVITY,
            walls=self.scene[LAYER_NAME_PLATFORMS],
            platforms=self.scene[LAYER_NAME_MOVING_PLATFORMS]
        )
        moving_platforms_list = self.scene[LAYER_NAME_MOVING_PLATFORMS]
        for platform in moving_platforms_list:
            platform.boundary_left = platform.center_x - 100
            platform.boundary_right = platform.center_x + 150
            platform.change_x = 0.3

        water_list = self.scene[LAYER_NAME_WATER]
        for water in water_list:
            water.boundary_left = water.center_x - 100
            water.boundary_right = water.center_x + 100
            water.change_x = 0.1

    def on_draw(self):
        self.clear()
        arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)
        self.camera.use()
        self.scene.draw()
        self.coin_list.draw()
        self.enemy_list.draw()
        self.gui_camera.use()
        lives_text = f"Lives: {self.lives}/3"
        score_text = f"Score: {self.score}/15"
        arcade.draw_text(score_text, 10, 10, arcade.csscolor.LIGHT_GRAY, 40, font_name="Kenney Pixel")
        arcade.draw_text(lives_text, 10, 680, arcade.csscolor.LIGHT_GRAY, 40, font_name="Kenney Pixel")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                arcade.play_sound(self.jump_sound)
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0

    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (self.camera.viewport_height / 2)
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        if screen_center_x > 2880:
            screen_center_x = 2880
        player_centered = screen_center_x, screen_center_y
        self.camera.move_to(player_centered)

    def on_update(self, delta_time):
        self.player_sprite.update()
        self.player_sprite.update_animation()
        self.physics_engine.update()
        self.coin_list.update_animation()
        self.enemy_list.update_animation()
        self.enemy_list.update()
        self.scene.update([LAYER_NAME_MOVING_PLATFORMS])
        self.scene.update([LAYER_NAME_WATER])

        for enemy in self.enemy_list:
            if (enemy.boundary_right and enemy.right > enemy.boundary_right and enemy.change_x > 0):
                enemy.change_x *= -1
            if (enemy.boundary_left and enemy.left < enemy.boundary_left and enemy.change_x < 0):
                enemy.change_x *= -1

        for water in self.scene[LAYER_NAME_WATER]:
            if (water.boundary_right and water.right > water.boundary_right and water.change_x > 0):
                water.change_x *= -1
            if (water.boundary_left and water.left < water.boundary_left and water.change_x < 0):
                water.change_x *= -1

        enemy_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.enemy_list)
        for enemy in enemy_hit_list:
            x = int(self.player_sprite.center_y - 50)
            y = int(enemy.center_y)
            if x == y or x > y:
                enemy.remove_from_sprite_lists()
                arcade.play_sound(self.kill_sound)
            elif (self.lives > 0):
                self.game_over = arcade.load_sound(":resources:sounds/gameover1.wav")
                self.lives -= 1
                arcade.play_sound(self.game_over)
                self.player_sprite.center_x = 64
                self.player_sprite.center_y = 300
            else:
                self.window.show_view(GameOverView())

        coin_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.coin_list)
        for coin in coin_hit_list:
            coin.remove_from_sprite_lists()
            arcade.play_sound(self.collect_sound)
            self.score += 1

        if self.player_sprite.center_y < -100:
            view = GameOverView()
            self.window.show_view(view)

        if arcade.check_for_collision_with_list(self.player_sprite, self.scene[LAYER_NAME_WATER]):
            if (self.lives > 0):
                self.game_over = arcade.load_sound(":resources:sounds/gameover1.wav")
                self.lives -= 1
                arcade.play_sound(self.game_over)
                self.player_sprite.center_x = 64
                self.player_sprite.center_y = 300
            else:
                self.window.show_view(GameOverView())

        if self.player_sprite.center_x >= self.end_of_map and self.level<2:
            self.level += 1
            self.setup()
        elif self.player_sprite.center_x >= self.end_of_map:
            view = GameEndView()
            self.window.show_view(view)

        self.center_camera_to_player()

class InstructionView(arcade.View):
    def on_show(self):
        self.texture = arcade.load_texture("main_view.png")
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        self.clear()
        self.texture.draw_sized(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                                SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_text("Welcome!", self.window.width / 2 + 170, self.window.height / 2 - 80,
                         arcade.color.WHITE, font_size=120, anchor_x="center", font_name="Kenney Pixel")
        arcade.draw_text("Press mouse button to continue", self.window.width / 2 + 170, self.window.height / 2 - 155,
                         arcade.color.WHITE, font_size=40, anchor_x="center", font_name="Kenney Pixel")

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

class GameOverView(arcade.View):
    def __init__(self):
        self.game_over = arcade.load_sound(":resources:sounds/gameover1.wav")
        super().__init__()
        self.texture = arcade.load_texture("game_over.png")
        arcade.set_viewport(0, SCREEN_WIDTH - 1, 0, SCREEN_HEIGHT - 1)
        arcade.play_sound(self.game_over)

    def on_draw(self):
        self.clear()
        self.texture.draw_sized(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                                SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_text("GAME OVER", self.window.width / 2 + 60, self.window.height / 2,
                         arcade.color.WHITE, font_size=120, anchor_x="center", font_name="Kenney Pixel")
        arcade.draw_text("Press mouse button to continue", self.window.width / 2 + 60, self.window.height / 2 - 75,
                         arcade.color.WHITE, font_size=40, anchor_x="center", font_name="Kenney Pixel")

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

class GameEndView(arcade.View):
    def __init__(self):
        self.game_end = arcade.load_sound("sound/win.mp3")
        super().__init__()
        self.texture = arcade.load_texture("game_end.png")
        arcade.play_sound(self.game_end)

    def on_draw(self):
        self.clear()
        self.texture.draw_sized(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                                SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_text("YOU WIN!", self.window.width / 2, self.window.height / 2 + 100,
                         arcade.color.WHITE, font_size=120, anchor_x="center", font_name="Kenney Pixel")

    def on_mouse_press(self, _x, _y, _button, _modifiers):
            game_view =  InstructionView()
            self.window.show_view(game_view)

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = InstructionView()
    window.show_view(start_view)
    arcade.run()

if __name__ == "__main__":
    main()
