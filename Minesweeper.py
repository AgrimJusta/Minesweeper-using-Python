import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QMessageBox, QGridLayout, QVBoxLayout, QAction, QMenu, QMenuBar

from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt


class Cell(QPushButton):
    def __init__(self, x, y, parent):
        super().__init__(parent)
        self.x = x
        self.y = y
        self.setFixedSize(34, 34)
        self.setFont(QFont("Consolas", 11, QFont.Bold))
        self.setStyleSheet("background-color: #444; color: white; border-radius: 6px;")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_click)

        self.is_mine = False
        self.adjacent_mines = 0
        self.revealed = False
        self.flagged = False

    def reset(self):
        self.setText("")
        self.setStyleSheet("background-color: #444; color: white; border-radius: 6px;")
        self.is_mine = False
        self.adjacent_mines = 0
        self.revealed = False
        self.flagged = False

    def reveal(self):
        if self.revealed or self.flagged:
            return
        self.revealed = True
        if self.is_mine:
            self.setText("💣")
            self.setStyleSheet("background-color: #e63946; color: white;")
        else:
            self.setStyleSheet("background-color: #2b2b2b; color: #bde0fe;")
            if self.adjacent_mines > 0:
                self.setText(str(self.adjacent_mines))

    def right_click(self):
        if self.revealed:
            return
        if not self.flagged:
            self.setText("🚩")
            self.flagged = True
            self.parent().window().update_flag_count(1)
        else:
            self.setText("")
            self.flagged = False
            self.parent().window().update_flag_count(-1)


class GameWidget(QWidget):
    def __init__(self, window, rows, cols, mines):
        super().__init__()
        self.window_ref = window
        self.rows = rows
        self.cols = cols
        self.total_mines = mines
        self.flags = 0
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        self.setLayout(self.grid)
        self.setStyleSheet("background-color: #2c2c2e; padding: 8px;")

        self.cells = [[Cell(x, y, self) for y in range(cols)] for x in range(rows)]
        for x in range(rows):
            for y in range(cols):
                self.grid.addWidget(self.cells[x][y], x, y)
                self.cells[x][y].clicked.connect(lambda _, cx=x, cy=y: self.cell_clicked(cx, cy))

        self.place_mines()
        self.calculate_adjacency()

    def window(self):
        return self.window_ref

    def place_mines(self):
        positions = random.sample([(x, y) for x in range(self.rows) for y in range(self.cols)], self.total_mines)
        for x, y in positions:
            self.cells[x][y].is_mine = True

    def calculate_adjacency(self):
        for x in range(self.rows):
            for y in range(self.cols):
                if self.cells[x][y].is_mine:
                    continue
                count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.rows and 0 <= ny < self.cols and self.cells[nx][ny].is_mine:
                            count += 1
                self.cells[x][y].adjacent_mines = count

    def cell_clicked(self, x, y):
        cell = self.cells[x][y]
        if cell.is_mine:
            cell.reveal()
            self.reveal_all()
            self.game_over_popup()
        else:
            self.reveal_cell(x, y)

    def reveal_cell(self, x, y):
        cell = self.cells[x][y]
        if cell.revealed or cell.flagged:
            return
        cell.reveal()
        if cell.adjacent_mines == 0:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.rows and 0 <= ny < self.cols:
                        self.reveal_cell(nx, ny)

    def reveal_all(self):
        for row in self.cells:
            for cell in row:
                cell.reveal()

    def update_flag_count(self, change):
        self.flags += change
        self.window().update_status()

    def game_over_popup(self):
        msg = QMessageBox()
        msg.setWindowTitle("💥 Game Over")
        msg.setText("You clicked on a mine!\nDo you want to restart?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setIcon(QMessageBox.Warning)
        result = msg.exec_()

        if result == QMessageBox.Yes:
            self.window().new_game()
        else:
            self.window().close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minesweeper")
        self.setWindowIcon(QIcon("C:/Users/Bablu/Pictures/Camera Roll/WhatsApp Image 2023-11-05 at 20.24.10_2371d500.jpg"))
        self.setStyleSheet("background-color: #1c1c1e; color: white;")

        self.status_label = QLabel("Flags: 0 | Mines: 0")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.setCentralWidget(QWidget())
        self.layout = QVBoxLayout()
        self.centralWidget().setLayout(self.layout)

        self.menu = self.menuBar()
        game_menu = self.menu.addMenu("Game")

        new_game_action = QAction("New Game", self)
        new_game_action.triggered.connect(self.new_game)
        game_menu.addAction(new_game_action)

        difficulty_menu = QMenu("Difficulty", self)
        game_menu.addMenu(difficulty_menu)

        for name, (rows, cols, mines) in [("Easy", (9, 9, 10)), ("Medium", (16, 16, 40)), ("Hard", (24, 24, 99))]:
            act = QAction(name, self)
            act.triggered.connect(lambda _, r=rows, c=cols, m=mines: self.set_difficulty(r, c, m))
            difficulty_menu.addAction(act)

        game_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        game_menu.addAction(exit_action)

        self.layout.addWidget(self.status_label)
        self.difficulty = (9, 9, 10)
        self.board = None
        self.new_game()

    def set_difficulty(self, rows, cols, mines):
        self.difficulty = (rows, cols, mines)
        self.new_game()

    def new_game(self):
        if self.board:
            self.layout.removeWidget(self.board)
            self.board.setParent(None)
        rows, cols, mines = self.difficulty
        self.board = GameWidget(self, rows, cols, mines)
        self.layout.addWidget(self.board)
        self.update_status()

    def update_status(self):
        self.status_label.setText(f"🚩 Flags: {self.board.flags} | 💣 Mines: {self.board.total_mines}")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
