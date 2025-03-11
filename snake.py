import random

EMOJI_SNAKE = "🟩"
EMOJI_APPLE = "🟥"
EMOJI_WALL = "⬛"
EMOJI_FIELD = "⬜"

class Snake:
    def __init__(self, width=25, height=25):
        """Метод инициализации"""
        self.width = width
        self.height = height
        self.body = [(width // 2, height // 2)]
        self.direction = (0, 0)
        self.grow = False

    def move(self):
        """Метод, двигающий змейку"""
        head = self.body[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        if new_head in self.body:
            return False

        self.body.insert(0, new_head)
        if not self.grow:
            self.body.pop()
        else:
            self.grow = False
        return True

    def change_direction(self, direction):
        """Метод указывающий направление змейки"""
        if (direction[0] * -1, direction[1] * -1) != self.direction:
            self.direction = direction

    def check_collision(self, apple):
        """Метод, который проверяет случай когда змейка наступила на яблоко"""
        return self.body[0] == apple.position

    def check_wall_collision(self):
        """Метод, который проверяет случай когда змейка наступила на стену"""
        return (self.body[0][0] < 0 or self.body[0][0] >= self.width or
                self.body[0][1] < 0 or self.body[0][1] >= self.height)

class Apple:
    def __init__(self, width=25, height=25):
        """Метод инициализации"""
        self.width = width
        self.height = height
        self.position = self.generate_position()

    def generate_position(self, snake_body=None):
        """Метод, который генерирует новую позицию для яблока"""
        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if not snake_body or (x, y) not in snake_body:
                return (x, y)

class Game:
    def __init__(self, width=25, height=25):
        """Метод инициализации"""
        self.width = width
        self.height = height
        self.snake = Snake(width, height)
        self.apple = Apple(width, height)
        self.score = 0
        self.game_over = False

    def update(self):
        """Метод обновления состояния игры"""
        if not self.snake.move():
            self.game_over = True
            return None

        if self.snake.check_wall_collision():
            self.game_over = True
            return None

        if self.snake.check_collision(self.apple):
            self.snake.grow = True
            self.score += 10
            self.apple.position = self.apple.generate_position(self.snake.body)

    def get_field(self):
        """Метод создающий игровое поле"""
        field = [[EMOJI_FIELD for empty in range(self.width)] for empty in range(self.height)]

        for x_snake, y_snake in self.snake.body:
            field[y_snake][x_snake] = EMOJI_SNAKE

        x_apple, y_apple = self.apple.position
        field[y_apple][x_apple] = EMOJI_APPLE

        for i in range(self.width):
            field[0][i] = EMOJI_WALL
            field[self.height - 1][i] = EMOJI_WALL
        for i in range(self.height):
            field[i][0] = EMOJI_WALL
            field[i][self.width - 1] = EMOJI_WALL

        return "\n".join("".join(row) for row in field)