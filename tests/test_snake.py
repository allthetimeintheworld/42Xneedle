import unittest
from src.snake import SnakeGame

class TestSnakeGame(unittest.TestCase):
    def test_initialization(self):
        game = SnakeGame()
        self.assertEqual(game.score, 0)
        self.assertEqual(game.level, 1)
        self.assertIsNotNone(game.snake)

    def test_snake_movement(self):
        game = SnakeGame()
        initial_head = game.snake[0][:]
        game.change_direction = 'RIGHT'
        game.move_snake()
        self.assertEqual(game.snake[0], [initial_head[0] + 10, initial_head[1]])

    def test_collision_with_wall(self):
        game = SnakeGame()
        game.snake = [[0, 0]]
        game.change_direction = 'LEFT'
        game.move_snake()
        self.assertTrue(game.game_over)

    def test_collision_with_self(self):
        game = SnakeGame()
        game.snake = [[100, 100], [90, 100], [80, 100], [80, 90], [90, 90], [100, 90]]
        game.change_direction = 'DOWN'
        game.move_snake()
        self.assertTrue(game.game_over)

    def test_food_collision(self):
        game = SnakeGame()
        game.food = [100, 100]
        game.snake = [[90, 100], [80, 100]]
        game.change_direction = 'RIGHT'
        game.move_snake()
        self.assertEqual(game.snake[0], [100, 100])
        self.assertNotEqual(game.food, [100, 100])  # food should respawn

    def test_powerup_collision(self):
        game = SnakeGame()
        game.power_up = [100, 100]
        game.snake = [[90, 100], [80, 100]]
        game.change_direction = 'RIGHT'
        game.move_snake()
        self.assertIsNone(game.power_up)  # power-up consumed
        self.assertEqual(game.score, 5)  # assuming power-up gives 5 points

if __name__ == '__main__':
    unittest.main()
