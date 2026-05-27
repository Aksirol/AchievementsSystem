import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Налаштування головного вікна
        self.setWindowTitle("Система обліку позакласних досягнень")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)

        # Додавання тестового тексту
        label = QLabel("Середовище налаштовано успішно. Головне вікно працює.", self)
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()