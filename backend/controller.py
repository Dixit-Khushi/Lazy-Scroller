import pyautogui
import platform

class InputController:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        pyautogui.FAILSAFE = False

    def move_mouse(self, x, y):
        """Moves mouse to normalized coordinates (0.0 to 1.0)."""
        target_x = int(x * self.screen_width)
        target_y = int(y * self.screen_height)
        pyautogui.moveTo(target_x, target_y)

    def click(self):
        pyautogui.click()

    def scroll(self, amount):
        """
        Scrolls the screen.
        amount: Positive for UP, Negative for DOWN (Windows standard).
        """
        pyautogui.scroll(amount)

    def drag(self, x, y):
        """Drags mouse to normalized coordinates."""
        target_x = int(x * self.screen_width)
        target_y = int(y * self.screen_height)
        pyautogui.dragTo(target_x, target_y)
